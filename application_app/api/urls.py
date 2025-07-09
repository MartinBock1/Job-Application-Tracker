from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ContactViewSet, ApplicationViewSet, NoteViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
