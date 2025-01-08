from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AircraftViewSet,
    PartViewSet,
    TeamViewSet,
    PersonnelViewSet,
    ProducedAircraftViewSet,
    PersonnelRegisterView,
    PartTypeViewSet,
    AircraftPartViewSet,
    AircraftPartRequirementViewSet,
    LoginView,
    PartStockViewSet,
    TeamMateListView
)

# Router yapılandırması
router = DefaultRouter()
router.register('aircrafts', AircraftViewSet)
router.register('parts', PartViewSet, basename='part')
router.register('teams', TeamViewSet)
router.register('personnels', PersonnelViewSet)
router.register('produced-aircrafts', ProducedAircraftViewSet)
router.register('part-types', PartTypeViewSet)
router.register('aircraft-parts', AircraftPartViewSet)
router.register('part-requirements', AircraftPartRequirementViewSet)
router.register('part-stock', PartStockViewSet, basename='part-stock')

# URL patterns
urlpatterns = [
    # API root
    path('', include(router.urls)),
    
    # Takım arkadaşları listesi
    path('teammates/', TeamMateListView.as_view(), name='teammates-list'),
    
    # Kullanıcı işlemleri
    path('auth/', include([
        path('register/', PersonnelRegisterView.as_view(), name='register'),
        path('login/', LoginView.as_view(), name='login'),
    ])),
    
    # DataTable endpoints
    path('datatable/', include([
        path('aircrafts/', AircraftViewSet.as_view({'get': 'datatable'}), name='aircraft-datatable'),
        path('parts/', PartViewSet.as_view({'get': 'datatable'}), name='part-datatable'),
        path('produced-aircrafts/', ProducedAircraftViewSet.as_view({'get': 'datatable'}), name='produced-aircraft-datatable'),
    ])),
]

# API URL patterns için app_name tanımlaması
app_name = 'api'
