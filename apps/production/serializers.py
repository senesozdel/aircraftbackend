from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Aircraft, Part, Team, Personnel, ProducedAircraft, PartStock,
    PartType, AircraftPartRequirement, AircraftPart
)
from django.db import models, transaction 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class PartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartType
        fields = ('id', 'name', 'is_deleted')

class PartStockSerializer(serializers.ModelSerializer):
    part_type = PartTypeSerializer()
    aircraft_name = serializers.CharField(source='aircraft.name', read_only=True)
    class Meta:
        model = PartStock
        fields = ['part_type', 'stock_quantity','aircraft_name']

class TeamSerializer(serializers.ModelSerializer):
    responsible_part = PartTypeSerializer(read_only=True)
    responsible_part_id = serializers.PrimaryKeyRelatedField(
        queryset=PartType.objects.all(),
        source='responsible_part',
        write_only=True
    )

    class Meta:
        model = Team
        fields = ('id', 'name', 'responsible_part', 'responsible_part_id', 'is_deleted')

class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = ('id', 'name', 'is_deleted')

class AircraftPartRequirementSerializer(serializers.ModelSerializer):
    part_type_name = serializers.CharField(source='part_type.name', read_only=True)
    aircraft_name = serializers.CharField(source='aircraft.name', read_only=True)

    class Meta:
        model = AircraftPartRequirement
        fields = ('id', 'aircraft', 'aircraft_name', 'part_type', 
                 'part_type_name', 'required_quantity')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=AircraftPartRequirement.objects.all(),
                fields=['aircraft', 'part_type']
            )
        ]

class PartSerializer(serializers.ModelSerializer):
    part_type_name = serializers.CharField(source='part_type.name', read_only=True)
    aircraft_name = serializers.CharField(source='aircraft.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Part
        fields = ('id', 'part_type', 'part_type_name', 'aircraft', 
                 'aircraft_name', 'team', 'team_name', 'status', 
                 'status_display',  'is_deleted')
        read_only_fields = ('team',)  # team alanını read-only yap

    def validate(self, data):
        # Team bilgisi context'ten al
        team = self.context.get('team')
        if not team:
            raise serializers.ValidationError("Takım bilgisi bulunamadı")

        # Üretim takımının sorumlu olduğu parça tipini kontrol et
        if team.responsible_part != data['part_type']:
            raise serializers.ValidationError(
                f"{team.name} takımı {data['part_type'].name} üretemez."
            )
        return data


class PersonnelSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = Personnel
        fields = ('id', 'user', 'team', 'team_name', 'is_deleted')

class PersonnelRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(write_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = Personnel
        fields = ('username', 'email', 'password', 'team', 'team_name', 'is_deleted')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu kullanıcı adı zaten kullanımda.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu e-posta adresi zaten kullanımda.")
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():  # Transaction ekleyelim
                # User verilerini ayır
                username = validated_data.pop('username')
                email = validated_data.pop('email')
                password = validated_data.pop('password')
                
                # User oluştur
                user = User.objects.create_user(  # create_user kullanımı önemli!
                    username=username,
                    email=email,
                    password=password,  # Hash'leme otomatik yapılacak
                    is_active=True  # Direkt aktif yapalım test için
                )

                # Personnel oluştur
                personnel = Personnel.objects.create(
                    user=user,
                    **validated_data
                )
                
                return personnel
        except Exception as e:
            raise serializers.ValidationError(f"Kullanıcı oluşturma hatası: {str(e)}")


class AircraftPartSerializer(serializers.ModelSerializer):
    part_type_name = serializers.CharField(source='part.part_type.name', read_only=True)
    status = serializers.CharField(source='part.status', read_only=True)

    class Meta:
        model = AircraftPart
        fields = ('id', 'produced_aircraft', 'part', 'part_type_name', 'status')

    def validate(self, data):
        if data['part'].status != 'stock':
            raise serializers.ValidationError("Bu parça zaten kullanılmış.")
        return data

class ProducedAircraftSerializer(serializers.ModelSerializer):
    aircraft_name = serializers.CharField(source='aircraft.name', read_only=True)
    parts = AircraftPartSerializer(many=True, read_only=True, source='aircraftpart_set')

    class Meta:
        model = ProducedAircraft
        fields = ('id', 'aircraft', 'aircraft_name', 'parts', 'date', 'is_deleted')
        read_only_fields = ('date',)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

class LoginResponseSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email')
    username = serializers.CharField(source='user.username')
    team_name = serializers.CharField(source='team.name')
    token = serializers.CharField(read_only=True)

    class Meta:
        model = Personnel
        fields = ('username', 'email', 'team_name', 'token')

class TeamMateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    class Meta:
        model = Personnel
        fields = ('id', 'username', 'team_name')