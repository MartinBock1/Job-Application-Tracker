from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ContactViewSet, ApplicationViewSet, NoteViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'notes', NoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
]
