from django.shortcuts import render, get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import viewsets, permissions, status, generics 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from drf_yasg import openapi
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from .models import (
    Aircraft, Part, Team, Personnel, ProducedAircraft,PartStock,
    PartType, AircraftPart, AircraftPartRequirement, STATUS_CHOICES
)
from .serializers import (
    AircraftSerializer, PartSerializer, TeamSerializer, 
    PersonnelSerializer, ProducedAircraftSerializer,
    PersonnelRegisterSerializer, PartTypeSerializer,
    AircraftPartRequirementSerializer, AircraftPartSerializer,LoginSerializer,LoginResponseSerializer,PartStockSerializer,TeamMateSerializer
)

class BaseViewSet(viewsets.ModelViewSet):
    """
    Tüm ViewSet'ler için temel sınıf.
    Bu sınıf, ortak authentication, permission ve silme işlemlerini içerir.
    """
    
    # JWT token ile kimlik doğrulama yapılmasını sağlar
    authentication_classes = [JWTAuthentication]
    
    # Sadece giriş yapmış (authenticate olmuş) kullanıcıların erişimine izin verir
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Veritabanından kayıtları getirirken sadece silinmemiş
        olan kayıtları filtreler.
        """
        return super().get_queryset().filter(is_deleted=False)

    def perform_destroy(self, instance):
        """
        Soft delete işlemi gerçekleştirir.
        Kaydı veritabanından silmek yerine is_deleted alanını True yapar.

        """
        instance.is_deleted = True
        instance.save()


class BaseDataTableViewSet(BaseDatatableView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    model = None
    columns = []
    order_columns = []
    searchable_columns = []
    
    def get_initial_queryset(self):
        return self.model.objects.filter(is_deleted=False)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q()
            for column in self.searchable_columns:
                q |= Q(**{f"{column}__icontains": search})
            qs = qs.filter(q)
        return qs

    def render_response(self, data):
        return Response({
            'draw': int(self.request.GET.get('draw', 1)),
            'recordsTotal': self.total_records,
            'recordsFiltered': self.total_display_records,
            'data': data
        })

class AircraftViewSet(BaseViewSet):
    
    # Tüm uçak kayıtlarını getir
    queryset = Aircraft.objects.all()
    
    # Uçak verilerinin serializasyonu için kullanılacak sınıf
    serializer_class = AircraftSerializer

    @action(detail=True, methods=['get'])
    def part_requirements(self, request, pk=None):
        """
        Belirli bir uçak modeli için gerekli parça listesini döndürür.
        
        """
        aircraft = self.get_object()
        requirements = AircraftPartRequirement.objects.filter(aircraft=aircraft)
        serializer = AircraftPartRequirementSerializer(requirements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def datatable(self, request):
        """
        Uçak listesini DataTable formatında döndürür.
        """
        return AircraftDatatableView.as_view()(request)


class PartTypeViewSet(BaseViewSet):
    queryset = PartType.objects.all()
    serializer_class = PartTypeSerializer

class PartViewSet(BaseViewSet):
    serializer_class = PartSerializer

    def get_queryset(self):
        """
        Kullanıcının yetkisine göre filtrelenmiş parça listesini döndürür.
        """
        user = self.request.user
        try:
            personnel = Personnel.objects.select_related('team').get(user=user)
            if personnel.team.name == 'Montaj Takımı':
                return Part.objects.filter(status='stock', is_deleted=False)
            return Part.objects.filter(team=personnel.team, is_deleted=False)
        except Personnel.DoesNotExist:
            return Part.objects.none()

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "part_type": openapi.Schema(type=openapi.TYPE_INTEGER, description="Part type ID"),
                "aircraft": openapi.Schema(type=openapi.TYPE_INTEGER, description="Aircraft ID"),
                "status": openapi.Schema(type=openapi.TYPE_STRING, description="Part status"),
                "stock": openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of parts to add", default=1),
            },
            required=["part_type", "aircraft"]
        ),
        responses={
            201: openapi.Response("Part(s) created successfully"),
            400: openapi.Response("Invalid input data"),
            403: openapi.Response("User not authorized"),
        }
    )
    def create(self, request, *args, **kwargs):
        try:
            # Personel kontrolü
            personnel = Personnel.objects.select_related('team').get(user=request.user)

            # Aircraft ve PartType kontrolü
            aircraft_id = request.data.get('aircraft')
            part_type_id = request.data.get('part_type')

            try:
                aircraft = Aircraft.objects.get(id=aircraft_id)
                part_type = PartType.objects.get(id=part_type_id)
            except (Aircraft.DoesNotExist, PartType.DoesNotExist):
                return Response(
                    {"error": "Geçersiz Aircraft ID veya Part Type ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Takım yetkisi kontrolü
            if personnel.team.responsible_part_id != part_type_id:
                return Response(
                    {"error": f"{personnel.team.name} takımı bu parçayı üretemez"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Stock sayısı kontrolü
            stock_count = int(request.data.get('stock', 1))
            if stock_count < 1:
                return Response(
                    {"error": "Stock değeri en az 1 olmalıdır"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                created_parts = []
                
                # PartStock güncelle - belirli aircraft için
                part_stock, created = PartStock.objects.get_or_create(
                    part_type=part_type,
                    aircraft=aircraft,
                    defaults={'stock_quantity': 0}
                )

                # Parçaları oluştur
                for _ in range(stock_count):
                    part = Part.objects.create(
                        part_type=part_type,
                        aircraft=aircraft,
                        team=personnel.team,
                        status=request.data.get('status', 'stock')
                    )
                    serializer = self.get_serializer(part)
                    created_parts.append(serializer.data)

                # Stok miktarını güncelle
                part_stock.stock_quantity += stock_count
                part_stock.save()

                return Response({
                    "message": f"{stock_count} adet parça başarıyla oluşturuldu",
                    "parts": created_parts,
                    "stock_info": {
                        "aircraft": aircraft.name,
                        "part_type": part_type.name,
                        "current_stock": part_stock.stock_quantity,
                        "added_stock": stock_count
                    }
                }, status=status.HTTP_201_CREATED)

        except Personnel.DoesNotExist:
            return Response(
                {"error": "Personel bilgisi bulunamadı"},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Beklenmeyen bir hata oluştu: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            part = self.get_object()
            
            # Parça stokta ise, stok sayısını güncelle
            if part.status == 'stock':
                with transaction.atomic():
                    part_stock = PartStock.objects.get(
                        part_type=part.part_type,
                        aircraft=part.aircraft
                    )
                    if part_stock.stock_quantity >= 0:
                        part_stock.stock_quantity -= 1
                        part_stock.save()

            # Parçayı silmek yerine is_deleted'ı True yap
            part.is_deleted = True
            part.save()

            return Response({
                "message": "Parça başarıyla silindi",
                "part_info": {
                    "id": part.id,
                    "part_type": part.part_type.name,
                    "aircraft": part.aircraft.name
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Parça silinirken bir hata oluştu: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        part = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(STATUS_CHOICES):
            part.status = new_status
            part.save()
            return Response({'status': 'başarılı'})
        return Response(
            {'error': 'Geçersiz status değeri'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def datatable(self, request):
        return PartDatatableView.as_view()(request)

class TeamMateListView(generics.ListAPIView):
    """
    Giriş yapmış kullanıcının aynı takımındaki diğer personelleri listeler.
    """
    serializer_class = TeamMateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Giriş yapmış kullanıcının Personnel kaydını bul
        current_personnel = Personnel.objects.get(user=self.request.user)
        
        # Aynı takımdaki diğer personelleri getir
        return Personnel.objects.filter(
            team=current_personnel.team,
            is_deleted = False
        ).exclude(id=current_personnel.id)  # Kendisini listeden çıkar


class TeamViewSet(BaseViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]
    
class PersonnelRegisterView(generics.CreateAPIView):
    """
    Yeni personel ve ilişkili kullanıcı hesabı oluşturur.
    """

    serializer_class = PersonnelRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            personnel = serializer.save()
            response_data = {
                'message': 'Kullanıcı başarıyla oluşturuldu',
                'username': personnel.user.username,
                'email': personnel.user.email,
                'team': personnel.team.name
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Kullanıcı oluşturma hatası: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PersonnelViewSet(BaseViewSet):
    queryset = Personnel.objects.all()
    serializer_class = PersonnelSerializer


class ProducedAircraftViewSet(BaseViewSet):
    queryset = ProducedAircraft.objects.all()
    serializer_class = ProducedAircraftSerializer

    def create(self, request, *args, **kwargs):
        
        try:
            # Montaj takımı kontrolü
            personnel = Personnel.objects.get(user=request.user)
            if personnel.team.name != 'Montaj Takımı':
                return Response(
                    {"error": "Sadece montaj takımı uçak üretebilir"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                # Üretilecek uçak modelini al
                aircraft = get_object_or_404(
                    Aircraft, 
                    id=request.data.get('aircraft')
                )
                
                # Uçak için gerekli parça gereksinimlerini al
                requirements = AircraftPartRequirement.objects.filter(
                    aircraft=aircraft
                ).select_related('part_type')
                
                # Stok kontrolü ve kullanılacak parçaları topla
                missing_parts = []
                parts_to_use = {}  # Her part_type için kullanılacak parçaları tutacak

                for requirement in requirements:
                    try:
                        # Aircraft'a özel stok kontrolü
                        part_stock = PartStock.objects.get(
                            part_type=requirement.part_type,
                            aircraft=aircraft
                        )
                        
                        # Stokta yeterli parça var mı kontrol et
                        if part_stock.stock_quantity < requirement.required_quantity:
                            missing_parts.append({
                                'part_type': requirement.part_type.name,
                                'aircraft': aircraft.name,
                                'required': requirement.required_quantity,
                                'available': part_stock.stock_quantity,
                                'missing': requirement.required_quantity - part_stock.stock_quantity
                            })
                            continue

                        # Kullanılacak parçaları bul
                        available_parts = Part.objects.filter(
                            part_type=requirement.part_type,
                            aircraft=aircraft,
                            status='stock',
                            is_deleted=False
                        )[:requirement.required_quantity]

                        if len(available_parts) < requirement.required_quantity:
                            missing_parts.append({
                                'part_type': requirement.part_type.name,
                                'aircraft': aircraft.name,
                                'required': requirement.required_quantity,
                                'available': len(available_parts),
                                'missing': requirement.required_quantity - len(available_parts)
                            })
                            continue

                        parts_to_use[requirement.part_type.id] = list(available_parts)

                    except PartStock.DoesNotExist:
                        missing_parts.append({
                            'part_type': requirement.part_type.name,
                            'aircraft': aircraft.name,
                            'required': requirement.required_quantity,
                            'available': 0,
                            'missing': requirement.required_quantity
                        })

                # Eksik parça varsa hata dön
                if missing_parts:
                    return Response({
                        'error': 'Stokta yeterli parça bulunmuyor',
                        'missing_parts': missing_parts
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Tüm gereksinimler karşılanıyorsa uçağı üret
                produced_aircraft = ProducedAircraft.objects.create(
                    aircraft=aircraft
                )

                # Her parça tipi için gerekli sayıda parçayı kullan
                for requirement in requirements:
                    # Aircraft'a özel stok güncelleme
                    part_stock = PartStock.objects.get(
                        part_type=requirement.part_type,
                        aircraft=aircraft
                    )
                    part_stock.stock_quantity -= requirement.required_quantity
                    part_stock.save()

                    # Kullanılan parçaları işaretle ve AircraftPart oluştur
                    for part in parts_to_use[requirement.part_type.id]:
                        # Parçayı kullanıldı olarak işaretle
                        part.is_deleted = True

                        part.save()

                        # Parçayı üretilen uçağa bağla
                        AircraftPart.objects.create(
                            produced_aircraft=produced_aircraft,
                            part=part
                        )

                serializer = self.get_serializer(produced_aircraft)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Personnel.DoesNotExist:
            return Response(
                {"error": "Personel bilgisi bulunamadı"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class LoginView(APIView):
    """
    Kullanıcı adı ve şifre ile kimlik doğrulama yaparak JWT token üretir.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            401: 'Unauthorized - Geçersiz kimlik bilgileri',
            404: 'Not Found - Personel bulunamadı',
            400: 'Bad Request - Geçersiz istek'
        },
        operation_description="Kullanıcı girişi için kullanılır. Username ve password gereklidir."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                try:
                    personnel = Personnel.objects.get(user=user)
                    # Sadece access token oluştur
                    token = AccessToken.for_user(user)
                    
                    response_data = LoginResponseSerializer(personnel).data
                    response_data.update({
                        'token': str(token)
                    })
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                    
                except Personnel.DoesNotExist:
                    return Response(
                        {'error': 'Personel kaydı bulunamadı'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {'error': 'Kullanıcı adı veya şifre hatalı'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PartStockViewSet(BaseViewSet):
    """
    Parça stoklarının yönetimi
    Stok görüntüleme, güncelleme ve stok ekleme işlemlerini sağlar.
    """

    queryset = PartStock.objects.all()
    serializer_class = PartStockSerializer

    @action(detail=False, methods=['post'])
    def add_stock(self, request):
        """
        Belirtilen parça tipine stok ekler.
        Eğer parça tipi için stok kaydı yoksa yeni kayıt oluşturur.
        """
        part_type_id = request.data.get('part_type')
        quantity = request.data.get('quantity')

        try:
            part_type = PartType.objects.get(id=part_type_id)
            part_stock, created = PartStock.objects.get_or_create(part_type=part_type)
            part_stock.stock_quantity += int(quantity)
            part_stock.save()
            return Response({'status': 'Stok güncellendi'})
        except PartType.DoesNotExist:
            return Response(
                {'error': 'Parça tipi bulunamadı'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class AircraftPartViewSet(BaseViewSet):
    queryset = AircraftPart.objects.all()
    serializer_class = AircraftPartSerializer

class AircraftPartRequirementViewSet(BaseViewSet):
    """
    Uçak parça gereksinimleri 
    Her uçak modeli için gerekli parça tiplerini ve miktarlarını yönetir.
    """
       
    queryset = AircraftPartRequirement.objects.all()
    serializer_class = AircraftPartRequirementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        aircraft_id = self.request.query_params.get('aircraft', None)
        if aircraft_id:
            queryset = queryset.filter(aircraft_id=aircraft_id)
        return queryset

# DataTable Views
class AircraftDatatableView(BaseDataTableViewSet):
    model = Aircraft
    columns = ['id', 'name', 'description']
    order_columns = ['id', 'name', 'description']
    searchable_columns = ['name', 'description']

class PartDatatableView(BaseDataTableViewSet):
    model = Part
    columns = ['id', 'part_type__name', 'aircraft__name', 'team__name', 'status', 'stock']
    order_columns = ['id', 'part_type__name', 'aircraft__name', 'team__name', 'status', 'stock']
    searchable_columns = ['part_type__name', 'aircraft__name', 'team__name']

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        try:
            personnel = Personnel.objects.get(user=self.request.user)
            if personnel.team.name == 'Montaj Takımı':
                return qs.filter(status='stock')
            return qs.filter(team=personnel.team)
        except Personnel.DoesNotExist:
            return Part.objects.none()

    def render_column(self, row, column):
        if column == 'part_type__name':
            return row.part_type.name if row.part_type else ''
        elif column == 'aircraft__name':
            return row.aircraft.name if row.aircraft else ''
        elif column == 'team__name':
            return row.team.name if row.team else ''
        else:
            return super().render_column(row, column)

class ProducedAircraftDatatableView(BaseDataTableViewSet):
    model = ProducedAircraft
    columns = ['id', 'aircraft__name', 'date']
    order_columns = ['id', 'aircraft__name', 'date']
    searchable_columns = ['aircraft__name']

    def render_column(self, row, column):
        if column == 'aircraft__name':
            return row.aircraft.name if row.aircraft else ''
        else:
            return super().render_column(row, column)
        
