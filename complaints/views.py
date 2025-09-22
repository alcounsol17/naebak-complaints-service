"""
Views لخدمة الشكاوى - منصة نائبك.كوم
"""

import os
import zipfile
import tempfile
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    Complaint, ComplaintAttachment, ComplaintHistory, 
    ComplaintCategory, ComplaintTemplate
)
from .serializers import (
    ComplaintListSerializer, ComplaintDetailSerializer, ComplaintCreateSerializer,
    ComplaintUpdateSerializer, ComplaintAssignSerializer, ComplaintResponseSerializer,
    ComplaintAttachmentSerializer, ComplaintHistorySerializer, ComplaintCategorySerializer,
    ComplaintTemplateSerializer, ComplaintStatsSerializer, ComplaintExportSerializer
)


class ComplaintViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة الشكاوى"""
    
    queryset = Complaint.objects.all().select_related('category').prefetch_related('attachments', 'history')
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'content', 'reference_number', 'citizen_name']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """تحديد Serializer المناسب حسب العملية"""
        if self.action == 'list':
            return ComplaintListSerializer
        elif self.action == 'create':
            return ComplaintCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ComplaintUpdateSerializer
        else:
            return ComplaintDetailSerializer
    
    def get_queryset(self):
        """تصفية الشكاوى حسب نوع المستخدم"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # إذا كان المستخدم مواطن، عرض شكاواه فقط
        if hasattr(user, 'user_type') and user.user_type == 'citizen':
            return queryset.filter(citizen_id=user.id)
        
        # إذا كان المستخدم نائب، عرض الشكاوى المُسندة إليه
        elif hasattr(user, 'user_type') and user.user_type == 'representative':
            return queryset.filter(assigned_representative_id=user.id)
        
        # الأدمن يرى جميع الشكاوى
        return queryset
    
    def perform_create(self, serializer):
        """إنشاء شكوى جديدة"""
        # الحصول على بيانات المواطن من خدمة المصادقة
        user = self.request.user
        citizen_data = self.get_citizen_data(user.id)
        
        serializer.save(
            citizen_id=user.id,
            citizen_name=citizen_data.get('name', user.username),
            citizen_email=citizen_data.get('email', user.email)
        )
    
    def get_citizen_data(self, citizen_id):
        """جلب بيانات المواطن من خدمة المصادقة"""
        # TODO: تكامل مع خدمة المصادقة
        # في الوقت الحالي نستخدم بيانات وهمية
        return {
            'name': f'مواطن {citizen_id}',
            'email': f'citizen{citizen_id}@example.com',
            'phone': f'010{citizen_id:08d}'
        }
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """إسناد الشكوى لنائب"""
        complaint = self.get_object()
        serializer = ComplaintAssignSerializer(data=request.data)
        
        if serializer.is_valid():
            # تحديث الشكوى
            complaint.assigned_representative_id = serializer.validated_data['representative_id']
            complaint.assigned_representative_name = serializer.validated_data['representative_name']
            complaint.assigned_at = timezone.now()
            complaint.assigned_by_admin_id = request.user.id
            complaint.status = 'assigned'
            complaint.save()
            
            # إضافة سجل في التاريخ
            ComplaintHistory.objects.create(
                complaint=complaint,
                action='assigned',
                description=f'تم إسناد الشكوى للنائب: {complaint.assigned_representative_name}',
                performed_by_id=request.user.id,
                performed_by_name=request.user.username,
                additional_data={'notes': serializer.validated_data.get('notes', '')}
            )
            
            return Response({'message': 'تم إسناد الشكوى بنجاح'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """الرد على الشكوى"""
        complaint = self.get_object()
        serializer = ComplaintResponseSerializer(data=request.data)
        
        if serializer.is_valid():
            response_type = serializer.validated_data['response_type']
            response_text = serializer.validated_data['response_text']
            
            # تحديث الرد حسب نوع المستخدم
            if response_type == 'admin':
                complaint.admin_response = response_text
            else:
                complaint.representative_response = response_text
            
            # إضافة الحل إذا تم تقديمه
            if serializer.validated_data.get('resolution'):
                complaint.resolution = serializer.validated_data['resolution']
                complaint.status = 'resolved'
                complaint.resolved_at = timezone.now()
                
                # منح النقاط للنائب إذا طُلب ذلك
                if serializer.validated_data.get('award_points') and not complaint.points_awarded:
                    complaint.points_awarded = True
                    complaint.thank_you_message = serializer.validated_data.get('thank_you_message', '')
                    
                    # إرسال طلب لخدمة الإحصائيات لزيادة نقاط النائب
                    self.award_points_to_representative(
                        complaint.assigned_representative_id,
                        complaint.thank_you_message
                    )
            
            complaint.save()
            
            # إضافة سجل في التاريخ
            ComplaintHistory.objects.create(
                complaint=complaint,
                action='response_added',
                description=f'تم إضافة رد من {response_type}',
                performed_by_id=request.user.id,
                performed_by_name=request.user.username
            )
            
            return Response({'message': 'تم إضافة الرد بنجاح'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def award_points_to_representative(self, representative_id, thank_you_message):
        """منح النقاط للنائب عبر خدمة الإحصائيات"""
        # TODO: تكامل مع خدمة الإحصائيات
        pass
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """قبول الشكوى (للنائب)"""
        complaint = self.get_object()
        
        if complaint.assigned_representative_id != request.user.id:
            return Response(
                {'error': 'غير مسموح لك بقبول هذه الشكوى'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        complaint.status = 'accepted'
        complaint.save()
        
        ComplaintHistory.objects.create(
            complaint=complaint,
            action='accepted',
            description='تم قبول الشكوى من قبل النائب',
            performed_by_id=request.user.id,
            performed_by_name=request.user.username
        )
        
        return Response({'message': 'تم قبول الشكوى بنجاح'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رفض الشكوى (للنائب)"""
        complaint = self.get_object()
        reason = request.data.get('reason', '')
        
        if complaint.assigned_representative_id != request.user.id:
            return Response(
                {'error': 'غير مسموح لك برفض هذه الشكوى'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        complaint.status = 'rejected'
        complaint.representative_response = reason
        complaint.save()
        
        ComplaintHistory.objects.create(
            complaint=complaint,
            action='rejected',
            description=f'تم رفض الشكوى من قبل النائب. السبب: {reason}',
            performed_by_id=request.user.id,
            performed_by_name=request.user.username
        )
        
        return Response({'message': 'تم رفض الشكوى'})
    
    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        """تعليق الشكوى لمدة 3 أيام (للنائب)"""
        complaint = self.get_object()
        reason = request.data.get('reason', '')
        
        if complaint.assigned_representative_id != request.user.id:
            return Response(
                {'error': 'غير مسموح لك بتعليق هذه الشكوى'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        complaint.status = 'on_hold'
        complaint.hold_until = timezone.now() + timedelta(days=3)
        complaint.representative_response = reason
        complaint.save()
        
        ComplaintHistory.objects.create(
            complaint=complaint,
            action='on_hold',
            description=f'تم تعليق الشكوى لمدة 3 أيام. السبب: {reason}',
            performed_by_id=request.user.id,
            performed_by_name=request.user.username
        )
        
        return Response({'message': 'تم تعليق الشكوى لمدة 3 أيام'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """إحصائيات الشكاوى"""
        queryset = self.get_queryset()
        
        stats = {
            'total_complaints': queryset.count(),
            'pending_complaints': queryset.filter(status='pending').count(),
            'assigned_complaints': queryset.filter(status='assigned').count(),
            'resolved_complaints': queryset.filter(status='resolved').count(),
            'rejected_complaints': queryset.filter(status='rejected').count(),
            'overdue_complaints': queryset.filter(
                status='on_hold',
                hold_until__lt=timezone.now()
            ).count(),
            'complaints_by_category': dict(
                queryset.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
            ),
            'complaints_by_priority': dict(
                queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
            ),
            'recent_complaints': ComplaintListSerializer(
                queryset.order_by('-created_at')[:10], many=True
            ).data
        }
        
        serializer = ComplaintStatsSerializer(stats)
        return Response(serializer.data)


class ComplaintAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة مرفقات الشكاوى"""
    
    queryset = ComplaintAttachment.objects.all()
    serializer_class = ComplaintAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """تصفية المرفقات حسب الشكوى"""
        complaint_id = self.request.query_params.get('complaint_id')
        if complaint_id:
            return self.queryset.filter(complaint_id=complaint_id)
        return self.queryset


class ComplaintCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة تصنيفات الشكاوى"""
    
    queryset = ComplaintCategory.objects.filter(is_active=True)
    serializer_class = ComplaintCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ComplaintTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة قوالب الشكاوى"""
    
    queryset = ComplaintTemplate.objects.filter(is_active=True)
    serializer_class = ComplaintTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """استخدام قالب الشكوى"""
        template = self.get_object()
        template.usage_count += 1
        template.save()
        
        return Response({
            'title': template.title,
            'content': template.content,
            'category': template.category.id
        })


class ComplaintHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet لعرض تاريخ الشكاوى"""
    
    queryset = ComplaintHistory.objects.all()
    serializer_class = ComplaintHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """تصفية التاريخ حسب الشكوى"""
        complaint_id = self.request.query_params.get('complaint_id')
        if complaint_id:
            return self.queryset.filter(complaint_id=complaint_id)
        return self.queryset


class HealthCheckView(APIView):
    """فحص صحة الخدمة"""
    
    permission_classes = []
    
    def get(self, request):
        """فحص صحة الخدمة"""
        return Response({
            'status': 'healthy',
            'service': 'naebak-complaints-service',
            'timestamp': timezone.now(),
            'version': '1.0.0'
        })
