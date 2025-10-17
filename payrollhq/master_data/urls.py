from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'compliance-settings', views.ComplianceSettingViewSet)
router.register(r'payroll-constants', views.PayrollConstantsViewSet)
router.register(r'audit-logs', views.ComplianceAuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]