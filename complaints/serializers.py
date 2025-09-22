"""
Serializers لخدمة الشكاوى - منصة نائبك.كوم
"""

from rest_framework import serializers
from django.conf import settings
from .models import (
    Complaint, ComplaintAttachment, ComplaintHistory, 
    ComplaintCategory, ComplaintTemplate
)


class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    """Serializer لمرفقات الشكوى"""
    
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = ComplaintAttachment
        fields = [
            'id', 'file', 'file_type', 'original_name', 
            'file_size', 'file_size_mb', 'uploaded_at', 'description'
        ]
        read_only_fields = ['id', 'file_type', 'file_size', 'uploaded_at']
    
    def validate_file(self, value):
        """التحقق من صحة الملف المرفوع"""
        # التحقق من حجم الملف
        if value.size > settings.MAX_ATTACHMENT_SIZE:
            raise serializers.ValidationError(
                f'حجم الملف كبير جداً. الحد الأقصى هو {settings.MAX_ATTACHMENT_SIZE / (1024*1024):.1f} ميجابايت.'
            )
        
        # التحقق من نوع الملف
        content_type = value.content_type
        if content_type not in settings.ALLOWED_ATTACHMENT_TYPES:
            raise serializers.ValidationError(
                'نوع الملف غير مدعوم. الأنواع المدعومة: صور (JPG, PNG, GIF), PDF, Word (DOC, DOCX)'
            )
        
        return value


class ComplaintHistorySerializer(serializers.ModelSerializer):
    """Serializer لتاريخ الشكوى"""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ComplaintHistory
        fields = [
            'id', 'action', 'action_display', 'description', 
            'performed_by_id', 'performed_by_name', 'performed_at', 'additional_data'
        ]
        read_only_fields = ['id', 'performed_at']


class ComplaintCategorySerializer(serializers.ModelSerializer):
    """Serializer لتصنيفات الشكاوى"""
    
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ComplaintTemplateSerializer(serializers.ModelSerializer):
    """Serializer لقوالب الشكاوى"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ComplaintTemplate
        fields = [
            'id', 'title', 'content', 'category', 'category_name', 
            'is_active', 'usage_count', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']


class ComplaintListSerializer(serializers.ModelSerializer):
    """Serializer لقائمة الشكاوى (عرض مختصر)"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    attachments_count = serializers.ReadOnlyField()
    days_since_created = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'status', 'status_display', 'priority', 'priority_display',
            'citizen_id', 'citizen_name', 'assigned_representative_id', 
            'assigned_representative_name', 'reference_number', 'category_name',
            'attachments_count', 'days_since_created', 'is_overdue',
            'created_at', 'updated_at', 'resolved_at'
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Serializer لتفاصيل الشكوى الكاملة"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    history = ComplaintHistorySerializer(many=True, read_only=True)
    attachments_count = serializers.ReadOnlyField()
    days_since_created = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'content', 'youtube_link', 'status', 'status_display',
            'priority', 'priority_display', 'citizen_id', 'citizen_name', 'citizen_email',
            'assigned_representative_id', 'assigned_representative_name', 'assigned_at',
            'assigned_by_admin_id', 'admin_response', 'representative_response',
            'resolution', 'resolved_at', 'created_at', 'updated_at', 'hold_until',
            'is_public', 'reference_number', 'points_awarded', 'thank_you_message',
            'category', 'category_name', 'attachments', 'history', 'attachments_count',
            'days_since_created', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'reference_number', 'created_at', 'updated_at', 'attachments',
            'history', 'attachments_count', 'days_since_created', 'is_overdue'
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء شكوى جديدة"""
    
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
        max_length=settings.MAX_ATTACHMENTS_PER_COMPLAINT
    )
    
    class Meta:
        model = Complaint
        fields = [
            'title', 'content', 'youtube_link', 'priority', 'category', 'attachments'
        ]
    
    def validate_content(self, value):
        """التحقق من طول محتوى الشكوى"""
        if len(value) > settings.MAX_COMPLAINT_LENGTH:
            raise serializers.ValidationError(
                f'محتوى الشكوى طويل جداً. الحد الأقصى هو {settings.MAX_COMPLAINT_LENGTH} حرف.'
            )
        return value
    
    def validate_attachments(self, value):
        """التحقق من المرفقات"""
        if len(value) > settings.MAX_ATTACHMENTS_PER_COMPLAINT:
            raise serializers.ValidationError(
                f'عدد المرفقات كبير جداً. الحد الأقصى هو {settings.MAX_ATTACHMENTS_PER_COMPLAINT} ملفات.'
            )
        
        for attachment in value:
            # التحقق من حجم الملف
            if attachment.size > settings.MAX_ATTACHMENT_SIZE:
                raise serializers.ValidationError(
                    f'حجم الملف "{attachment.name}" كبير جداً. الحد الأقصى هو {settings.MAX_ATTACHMENT_SIZE / (1024*1024):.1f} ميجابايت.'
                )
            
            # التحقق من نوع الملف
            content_type = attachment.content_type
            if content_type not in settings.ALLOWED_ATTACHMENT_TYPES:
                raise serializers.ValidationError(
                    f'نوع الملف "{attachment.name}" غير مدعوم. الأنواع المدعومة: صور (JPG, PNG, GIF), PDF, Word (DOC, DOCX)'
                )
        
        return value
    
    def create(self, validated_data):
        """إنشاء شكوى جديدة مع المرفقات"""
        attachments_data = validated_data.pop('attachments', [])
        
        # إنشاء الشكوى
        complaint = Complaint.objects.create(**validated_data)
        
        # إنشاء المرفقات
        for attachment_file in attachments_data:
            ComplaintAttachment.objects.create(
                complaint=complaint,
                file=attachment_file,
                original_name=attachment_file.name,
                file_size=attachment_file.size
            )
        
        # إنشاء سجل في التاريخ
        ComplaintHistory.objects.create(
            complaint=complaint,
            action='created',
            description=f'تم إنشاء الشكوى: {complaint.title}',
            performed_by_id=complaint.citizen_id,
            performed_by_name=complaint.citizen_name
        )
        
        return complaint


class ComplaintUpdateSerializer(serializers.ModelSerializer):
    """Serializer لتحديث الشكوى (للأدمن والنائب)"""
    
    class Meta:
        model = Complaint
        fields = [
            'status', 'priority', 'assigned_representative_id', 'assigned_representative_name',
            'admin_response', 'representative_response', 'resolution', 'thank_you_message'
        ]
    
    def update(self, instance, validated_data):
        """تحديث الشكوى مع تسجيل التغييرات في التاريخ"""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # تحديث الشكوى
        complaint = super().update(instance, validated_data)
        
        # تسجيل التغيير في التاريخ إذا تغيرت الحالة
        if old_status != new_status:
            action_map = {
                'assigned': 'assigned',
                'accepted': 'accepted',
                'rejected': 'rejected',
                'on_hold': 'on_hold',
                'resolved': 'resolved',
                'closed': 'closed'
            }
            
            action = action_map.get(new_status, 'status_changed')
            
            ComplaintHistory.objects.create(
                complaint=complaint,
                action=action,
                description=f'تم تغيير حالة الشكوى من "{complaint.get_status_display()}" إلى "{complaint.get_status_display()}"',
                performed_by_id=self.context['request'].user.id if 'request' in self.context else 0,
                performed_by_name=self.context['request'].user.username if 'request' in self.context else 'النظام'
            )
        
        return complaint


class ComplaintAssignSerializer(serializers.Serializer):
    """Serializer لإسناد الشكوى لنائب"""
    
    representative_id = serializers.IntegerField()
    representative_name = serializers.CharField(max_length=255)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_representative_id(self, value):
        """التحقق من صحة معرف النائب"""
        if value <= 0:
            raise serializers.ValidationError('معرف النائب غير صحيح.')
        return value


class ComplaintResponseSerializer(serializers.Serializer):
    """Serializer للرد على الشكوى"""
    
    response_type = serializers.ChoiceField(choices=['admin', 'representative'])
    response_text = serializers.CharField(max_length=2000)
    resolution = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    thank_you_message = serializers.CharField(max_length=500, required=False, allow_blank=True)
    award_points = serializers.BooleanField(default=False)
    
    def validate_response_text(self, value):
        """التحقق من نص الرد"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError('نص الرد قصير جداً. يجب أن يكون على الأقل 10 أحرف.')
        return value


class ComplaintStatsSerializer(serializers.Serializer):
    """Serializer لإحصائيات الشكاوى"""
    
    total_complaints = serializers.IntegerField()
    pending_complaints = serializers.IntegerField()
    assigned_complaints = serializers.IntegerField()
    resolved_complaints = serializers.IntegerField()
    rejected_complaints = serializers.IntegerField()
    overdue_complaints = serializers.IntegerField()
    complaints_by_category = serializers.DictField()
    complaints_by_priority = serializers.DictField()
    recent_complaints = ComplaintListSerializer(many=True)


class ComplaintExportSerializer(serializers.Serializer):
    """Serializer لتصدير الشكاوى"""
    
    format = serializers.ChoiceField(choices=['zip', 'excel', 'pdf'], default='zip')
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    status = serializers.MultipleChoiceField(
        choices=Complaint.COMPLAINT_STATUS,
        required=False,
        allow_empty=True
    )
    category = serializers.IntegerField(required=False)
    include_attachments = serializers.BooleanField(default=True)
