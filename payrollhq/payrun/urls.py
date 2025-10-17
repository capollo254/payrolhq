from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'batches', views.PayrollBatchViewSet, basename='payrollbatch')

urlpatterns = [
    path('', include(router.urls)),
]