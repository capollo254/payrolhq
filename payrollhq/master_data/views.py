"""
API Views for Master Data module

This module provides DRF views for managing compliance settings,
payroll constants, and other master data.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import date

from .models import ComplianceSetting, PayrollConstants, ComplianceAuditLog
from .serializers import (
    ComplianceSettingSerializer,
    ComplianceSettingListSerializer,
    ComplianceSettingDetailSerializer,
    PayrollConstantsSerializer,
    ComplianceAuditLogSerializer
)


class ComplianceSettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing compliance settings.
    
    Provides CRUD operations for compliance settings with proper
    filtering, validation, and audit logging.
    """
    
    queryset = ComplianceSetting.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['compliance_type', 'is_active', 'effective_date']
    search_fields = ['compliance_type', 'notes']
    ordering_fields = ['effective_date', 'compliance_type', 'created_at']
    ordering = ['-effective_date', 'compliance_type']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ComplianceSettingListSerializer
        elif self.action == 'retrieve':
            return ComplianceSettingDetailSerializer
        return ComplianceSettingSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Add any organization-specific filtering if needed
        # For now, return all settings as they're system-wide
        return queryset
    
    def perform_create(self, serializer):
        """Create compliance setting with audit logging."""
        # Get user information
        user = self.request.user
        
        # Save the compliance setting
        compliance_setting = serializer.save(
            created_by=user.username,
            created_at=timezone.now()
        )
        
        # Create audit log
        ComplianceAuditLog.objects.create(
            compliance_setting=compliance_setting,
            action='CREATE',
            new_data=serializer.validated_data,
            changed_by=user.username,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            reason=f"Created new {compliance_setting.get_compliance_type_display()}"
        )
    
    def perform_update(self, serializer):
        """Update compliance setting with audit logging."""
        user = self.request.user
        old_instance = self.get_object()
        old_data = ComplianceSettingSerializer(old_instance).data
        
        # Save the updated compliance setting
        compliance_setting = serializer.save()
        
        # Create audit log
        ComplianceAuditLog.objects.create(
            compliance_setting=compliance_setting,
            action='UPDATE',
            old_data=old_data,
            new_data=serializer.validated_data,
            changed_by=user.username,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            reason=f"Updated {compliance_setting.get_compliance_type_display()}"
        )
    
    def get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=False, methods=['get'])
    def current_settings(self, request):
        """Get all current active compliance settings."""
        current_date = request.query_params.get('date', date.today())
        if isinstance(current_date, str):
            try:
                current_date = date.fromisoformat(current_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        current_settings = {}
        
        for compliance_type, _ in ComplianceSetting.COMPLIANCE_TYPES:
            setting = ComplianceSetting.get_current_setting(compliance_type, current_date)
            if setting:
                serializer = ComplianceSettingSerializer(setting)
                current_settings[compliance_type] = serializer.data
        
        return Response(current_settings)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a compliance setting."""
        compliance_setting = self.get_object()
        user = request.user
        
        if compliance_setting.approved_by:
            return Response(
                {'error': 'This setting is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        compliance_setting.approved_by = user.username
        compliance_setting.approved_at = timezone.now()
        compliance_setting.save(update_fields=['approved_by', 'approved_at'])
        
        # Create audit log
        ComplianceAuditLog.objects.create(
            compliance_setting=compliance_setting,
            action='APPROVE',
            changed_by=user.username,
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            reason=f"Approved {compliance_setting.get_compliance_type_display()}"
        )
        
        serializer = self.get_serializer(compliance_setting)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def validate_current_setup(self, request):
        """Validate that all required compliance settings are configured."""
        required_types = [
            'PAYE_TAX_BANDS', 'PERSONAL_RELIEF', 'NSSF_RATES', 
            'SHIF_RATES', 'AHL_RATES'
        ]
        
        validation_results = {
            'is_valid': True,
            'missing_settings': [],
            'warnings': []
        }
        
        current_date = date.today()
        
        for compliance_type in required_types:
            setting = ComplianceSetting.get_current_setting(compliance_type, current_date)
            if not setting:
                validation_results['is_valid'] = False
                validation_results['missing_settings'].append(compliance_type)
            elif not setting.approved_by:
                validation_results['warnings'].append(
                    f"{compliance_type} is not approved"
                )
        
        return Response(validation_results)


class PayrollConstantsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payroll constants.
    """
    
    queryset = PayrollConstants.objects.all()
    serializer_class = PayrollConstantsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['constant_type', 'is_active']
    ordering_fields = ['constant_type', 'effective_date']
    ordering = ['constant_type']
    
    @action(detail=False, methods=['get'])
    def all_constants(self, request):
        """Get all active payroll constants as a dictionary."""
        constants = {}
        
        for constant in self.get_queryset().filter(is_active=True):
            constants[constant.constant_type] = constant.constant_value
        
        return Response(constants)


class ComplianceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for compliance audit logs.
    """
    
    queryset = ComplianceAuditLog.objects.all()
    serializer_class = ComplianceAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['compliance_setting', 'action', 'changed_by']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']
    
    def get_queryset(self):
        """Filter audit logs based on compliance setting."""
        queryset = super().get_queryset()
        
        compliance_setting_id = self.request.query_params.get('compliance_setting')
        if compliance_setting_id:
            queryset = queryset.filter(compliance_setting_id=compliance_setting_id)
        
        return queryset