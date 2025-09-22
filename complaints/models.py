"""
نماذج قاعدة البيانات لخدمة الشكاوى - منصة نائبك.كوم
مايكروسيرفيس مستقلة للشكاوى
"""

import uuid
import os
from django.db import models
from django.core.validators import MaxLengthValidator, FileExtensionValidator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def complaint_attachment_path(instance, filename):
    """تحديد مسار تخزين مرفقات الشكاوى"""
    return f'complaints/{instance.complaint.id}/attachments/{filename}'


class Complaint(models.Model):
    """نموذج الشكوى الأساسي"""
    
    COMPLAINT_STATUS = [
        ('pending', 'في الانتظار'),
        ('assigned', 'مُوجهة لنائب'),
        ('accepted', 'مقبولة'),
        ('rejected', 'مرفوضة'),
        ('on_hold', 'معلقة للدراسة'),
        ('resolved', 'محلولة'),
        ('closed', 'مغلقة'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    ]
    
    # المعرف الفريد
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name='معرف الشكوى'
    )
    
    # بيانات المواطن (معرف من خدمة المصادقة)
    citizen_id = models.PositiveIntegerField(
        verbose_name='معرف المواطن',
        help_text='معرف المواطن من خدمة المصادقة'
    )
    
    citizen_name = models.CharField(
        max_length=255,
        verbose_name='اسم المواطن',
        help_text='اسم المواطن (مخزن محلياً للأداء)'
    )
    
    citizen_email = models.EmailField(
        verbose_name='بريد المواطن الإلكتروني'
    )
    
    # محتوى الشكوى
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الشكوى',
        help_text='عنوان مختصر للشكوى'
    )
    
    content = models.TextField(
        validators=[MaxLengthValidator(settings.MAX_COMPLAINT_LENGTH)],
        verbose_name='محتوى الشكوى',
        help_text=f'وصف تفصيلي للشكوى (حد أقصى {settings.MAX_COMPLAINT_LENGTH} حرف)'
    )
    
    youtube_link = models.URLField(
        blank=True, 
        null=True,
        verbose_name='رابط يوتيوب',
        help_text='رابط فيديو يوتيوب اختياري لتوضيح الشكوى'
    )
    
    # حالة الشكوى
    status = models.CharField(
        max_length=20, 
        choices=COMPLAINT_STATUS, 
        default='pending',
        verbose_name='حالة الشكوى'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='أولوية الشكوى'
    )
    
    # إسناد للنائب (معرف من خدمة المحتوى)
    assigned_representative_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='معرف النائب المُكلف'
    )
    
    assigned_representative_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم النائب المُكلف'
    )
    
    assigned_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الإسناد'
    )
    
    assigned_by_admin_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='معرف الأدمن المُسند'
    )
    
    # الرد والحل
    admin_response = models.TextField(
        blank=True,
        verbose_name='رد الإدارة',
        help_text='رد الإدارة على الشكوى'
    )
    
    representative_response = models.TextField(
        blank=True,
        verbose_name='رد النائب',
        help_text='رد النائب على الشكوى'
    )
    
    resolution = models.TextField(
        blank=True,
        verbose_name='الحل المقترح',
        help_text='الحل النهائي للشكوى'
    )
    
    resolved_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='تاريخ الحل'
    )
    
    # تواريخ مهمة
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث'
    )
    
    # للشكاوى المعلقة (3 أيام كما هو محدد في البرومبت)
    hold_until = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='معلقة حتى',
        help_text='تاريخ انتهاء فترة التعليق (3 أيام)'
    )
    
    # معلومات إضافية
    is_public = models.BooleanField(
        default=False,
        verbose_name='شكوى عامة',
        help_text='هل يمكن عرض هذه الشكوى للعامة؟'
    )
    
    reference_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='رقم المرجع',
        help_text='رقم مرجعي فريد للشكوى'
    )
    
    # معلومات التكامل مع الخدمات الأخرى
    points_awarded = models.BooleanField(
        default=False,
        verbose_name='تم منح النقاط',
        help_text='هل تم منح النقاط للنائب عند حل هذه الشكوى؟'
    )
    
    thank_you_message = models.TextField(
        blank=True,
        verbose_name='رسالة الشكر للنائب',
        help_text='رسالة الشكر التي ستظهر في قسم الإنجازات'
    )
    
    class Meta:
        verbose_name = 'شكوى'
        verbose_name_plural = 'الشكاوى'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['citizen_id']),
            models.Index(fields=['assigned_representative_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.citizen_name}'
    
    def save(self, *args, **kwargs):
        # إنشاء رقم مرجعي تلقائي
        if not self.reference_number:
            self.reference_number = f'COMP-{timezone.now().strftime("%Y%m%d")}-{str(self.id)[:8].upper()}'
        
        # تحديث تاريخ الحل عند تغيير الحالة إلى محلولة
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        # تحديث تاريخ التعليق عند تغيير الحالة إلى معلقة (3 أيام)
        if self.status == 'on_hold' and not self.hold_until:
            self.hold_until = timezone.now() + timedelta(days=3)
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """التحقق من انتهاء فترة التعليق"""
        if self.status == 'on_hold' and self.hold_until:
            return timezone.now() > self.hold_until
        return False
    
    @property
    def days_since_created(self):
        """عدد الأيام منذ إنشاء الشكوى"""
        return (timezone.now() - self.created_at).days
    
    @property
    def attachments_count(self):
        """عدد المرفقات"""
        return self.attachments.count()


class ComplaintAttachment(models.Model):
    """نموذج مرفقات الشكوى - حتى 10 ملفات كما هو محدد في البرومبت"""
    
    ATTACHMENT_TYPES = [
        ('image', 'صورة'),
        ('pdf', 'مستند PDF'),
        ('word', 'مستند Word'),
        ('other', 'أخرى'),
    ]
    
    complaint = models.ForeignKey(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name='الشكوى'
    )
    
    file = models.FileField(
        upload_to=complaint_attachment_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx']
            )
        ],
        verbose_name='الملف'
    )
    
    file_type = models.CharField(
        max_length=10, 
        choices=ATTACHMENT_TYPES,
        verbose_name='نوع الملف'
    )
    
    original_name = models.CharField(
        max_length=255,
        verbose_name='الاسم الأصلي للملف'
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name='حجم الملف (بايت)'
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع'
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='وصف الملف'
    )
    
    class Meta:
        verbose_name = 'مرفق شكوى'
        verbose_name_plural = 'مرفقات الشكاوى'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f'{self.original_name} - {self.complaint.title}'
    
    def save(self, *args, **kwargs):
        if self.file:
            # تحديد نوع الملف تلقائياً
            file_extension = os.path.splitext(self.file.name)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                self.file_type = 'image'
            elif file_extension == '.pdf':
                self.file_type = 'pdf'
            elif file_extension in ['.doc', '.docx']:
                self.file_type = 'word'
            else:
                self.file_type = 'other'
            
            # حفظ الاسم الأصلي وحجم الملف
            if not self.original_name:
                self.original_name = self.file.name
            if not self.file_size:
                self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """حجم الملف بالميجابايت"""
        return round(self.file_size / (1024 * 1024), 2)


class ComplaintHistory(models.Model):
    """نموذج تاريخ الشكوى - تتبع جميع الإجراءات"""
    
    ACTION_TYPES = [
        ('created', 'تم إنشاء الشكوى'),
        ('assigned', 'تم إسناد الشكوى'),
        ('accepted', 'تم قبول الشكوى'),
        ('rejected', 'تم رفض الشكوى'),
        ('on_hold', 'تم تعليق الشكوى'),
        ('resolved', 'تم حل الشكوى'),
        ('closed', 'تم إغلاق الشكوى'),
        ('response_added', 'تم إضافة رد'),
        ('attachment_added', 'تم إضافة مرفق'),
        ('status_changed', 'تم تغيير الحالة'),
        ('priority_changed', 'تم تغيير الأولوية'),
        ('points_awarded', 'تم منح النقاط للنائب'),
    ]
    
    complaint = models.ForeignKey(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='history',
        verbose_name='الشكوى'
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        verbose_name='نوع الإجراء'
    )
    
    description = models.TextField(
        verbose_name='وصف الإجراء'
    )
    
    performed_by_id = models.PositiveIntegerField(
        verbose_name='معرف المنفذ'
    )
    
    performed_by_name = models.CharField(
        max_length=255,
        verbose_name='اسم المنفذ'
    )
    
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التنفيذ'
    )
    
    additional_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name='بيانات إضافية',
        help_text='بيانات إضافية مرتبطة بالإجراء'
    )
    
    class Meta:
        verbose_name = 'سجل الشكوى'
        verbose_name_plural = 'سجلات الشكاوى'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f'{self.get_action_display()} - {self.complaint.title}'


class ComplaintCategory(models.Model):
    """نموذج تصنيفات الشكاوى"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='اسم التصنيف'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='وصف التصنيف'
    )
    
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name='لون التصنيف',
        help_text='كود اللون بصيغة HEX'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'تصنيف الشكوى'
        verbose_name_plural = 'تصنيفات الشكاوى'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ComplaintTemplate(models.Model):
    """نموذج قوالب الشكاوى الجاهزة"""
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان القالب'
    )
    
    content = models.TextField(
        verbose_name='محتوى القالب'
    )
    
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.CASCADE,
        verbose_name='التصنيف'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد مرات الاستخدام'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'قالب شكوى'
        verbose_name_plural = 'قوالب الشكاوى'
        ordering = ['-usage_count', 'title']
    
    def __str__(self):
        return self.title


# إضافة تصنيف للشكوى
Complaint.add_to_class(
    'category',
    models.ForeignKey(
        ComplaintCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='التصنيف'
    )
)
