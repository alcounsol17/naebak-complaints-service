"""
المهام غير المتزامنة لخدمة الشكاوى - منصة نائبك.كوم
"""

import os
import zipfile
import tempfile
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from celery import shared_task
import requests

from .models import Complaint, ComplaintAttachment


@shared_task
def create_complaints_export(user_id, filters):
    """إنشاء ملف مضغوط يحتوي على الشكاوى والمرفقات"""
    
    try:
        # تصفية الشكاوى حسب المعايير المحددة
        queryset = Complaint.objects.all()
        
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        if filters.get('status'):
            queryset = queryset.filter(status__in=filters['status'])
        
        if filters.get('category'):
            queryset = queryset.filter(category_id=filters['category'])
        
        # إنشاء مجلد مؤقت
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f'complaints_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                # إضافة ملف CSV بتفاصيل الشكاوى
                csv_content = generate_complaints_csv(queryset)
                zip_file.writestr('complaints_list.csv', csv_content)
                
                # إضافة المرفقات إذا طُلب ذلك
                if filters.get('include_attachments', True):
                    for complaint in queryset:
                        complaint_folder = f'complaint_{complaint.reference_number}_{complaint.citizen_name}'
                        
                        # إضافة تفاصيل الشكوى كملف نصي
                        complaint_details = generate_complaint_details(complaint)
                        zip_file.writestr(f'{complaint_folder}/details.txt', complaint_details)
                        
                        # إضافة المرفقات
                        for attachment in complaint.attachments.all():
                            if os.path.exists(attachment.file.path):
                                zip_file.write(
                                    attachment.file.path,
                                    f'{complaint_folder}/attachments/{attachment.original_name}'
                                )
            
            # رفع الملف المضغوط إلى التخزين السحابي
            # TODO: رفع إلى Google Cloud Storage
            
            # إرسال إشعار للمستخدم بجاهزية الملف
            send_export_notification(user_id, zip_path)
            
            return {'status': 'success', 'file_path': zip_path}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def generate_complaints_csv(queryset):
    """إنشاء ملف CSV بتفاصيل الشكاوى"""
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # كتابة العناوين
    writer.writerow([
        'رقم المرجع', 'العنوان', 'المحتوى', 'الحالة', 'الأولوية',
        'اسم المواطن', 'البريد الإلكتروني', 'النائب المُسند',
        'تاريخ الإنشاء', 'تاريخ التحديث', 'تاريخ الحل'
    ])
    
    # كتابة البيانات
    for complaint in queryset:
        writer.writerow([
            complaint.reference_number,
            complaint.title,
            complaint.content,
            complaint.get_status_display(),
            complaint.get_priority_display(),
            complaint.citizen_name,
            complaint.citizen_email,
            complaint.assigned_representative_name or 'غير مُسند',
            complaint.created_at.strftime('%Y-%m-%d %H:%M'),
            complaint.updated_at.strftime('%Y-%m-%d %H:%M'),
            complaint.resolved_at.strftime('%Y-%m-%d %H:%M') if complaint.resolved_at else 'لم يتم الحل'
        ])
    
    return output.getvalue()


def generate_complaint_details(complaint):
    """إنشاء ملف نصي بتفاصيل الشكوى"""
    
    details = f"""
تفاصيل الشكوى - {complaint.reference_number}
=====================================

العنوان: {complaint.title}
الحالة: {complaint.get_status_display()}
الأولوية: {complaint.get_priority_display()}

بيانات المواطن:
- الاسم: {complaint.citizen_name}
- البريد الإلكتروني: {complaint.citizen_email}

المحتوى:
{complaint.content}

رابط يوتيوب: {complaint.youtube_link or 'لا يوجد'}

النائب المُسند: {complaint.assigned_representative_name or 'غير مُسند'}
تاريخ الإسناد: {complaint.assigned_at.strftime('%Y-%m-%d %H:%M') if complaint.assigned_at else 'لم يتم الإسناد'}

رد الأدمن:
{complaint.admin_response or 'لا يوجد رد'}

رد النائب:
{complaint.representative_response or 'لا يوجد رد'}

الحل:
{complaint.resolution or 'لم يتم تقديم حل'}

تاريخ الإنشاء: {complaint.created_at.strftime('%Y-%m-%d %H:%M')}
تاريخ آخر تحديث: {complaint.updated_at.strftime('%Y-%m-%d %H:%M')}
تاريخ الحل: {complaint.resolved_at.strftime('%Y-%m-%d %H:%M') if complaint.resolved_at else 'لم يتم الحل'}

عدد المرفقات: {complaint.attachments.count()}
"""
    
    return details


def send_export_notification(user_id, file_path):
    """إرسال إشعار للمستخدم بجاهزية ملف التصدير"""
    
    # TODO: إرسال إشعار عبر خدمة الإشعارات
    # TODO: إرسال بريد إلكتروني للمستخدم
    pass


@shared_task
def notify_complaint_update(complaint_id, action, user_id):
    """إرسال إشعار عند تحديث الشكوى"""
    
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        
        # تحديد نوع الإشعار ومحتواه
        notification_data = {
            'user_id': user_id,
            'title': get_notification_title(action, complaint),
            'message': get_notification_message(action, complaint),
            'type': 'complaint_update',
            'data': {
                'complaint_id': complaint_id,
                'action': action,
                'reference_number': complaint.reference_number
            }
        }
        
        # إرسال الإشعار عبر خدمة الإشعارات
        send_notification_to_service(notification_data)
        
        return {'status': 'success'}
    
    except Complaint.DoesNotExist:
        return {'status': 'error', 'message': 'الشكوى غير موجودة'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_notification_title(action, complaint):
    """الحصول على عنوان الإشعار"""
    
    titles = {
        'assigned': 'تم إسناد شكوى جديدة إليك',
        'accepted': 'تم قبول شكواك',
        'rejected': 'تم رفض شكواك',
        'on_hold': 'تم تعليق شكواك مؤقتاً',
        'resolved': 'تم حل شكواك',
        'response_added': 'تم إضافة رد على شكواك'
    }
    
    return titles.get(action, 'تحديث على شكواك')


def get_notification_message(action, complaint):
    """الحصول على محتوى الإشعار"""
    
    messages = {
        'assigned': f'تم إسناد الشكوى "{complaint.title}" إليك للمراجعة والرد عليها.',
        'accepted': f'تم قبول شكواك "{complaint.title}" وسيتم العمل على حلها قريباً.',
        'rejected': f'تم رفض شكواك "{complaint.title}". يمكنك مراجعة السبب في تفاصيل الشكوى.',
        'on_hold': f'تم تعليق شكواك "{complaint.title}" مؤقتاً لمدة 3 أيام للدراسة.',
        'resolved': f'تم حل شكواك "{complaint.title}". يمكنك مراجعة الحل في تفاصيل الشكوى.',
        'response_added': f'تم إضافة رد جديد على شكواك "{complaint.title}".'
    }
    
    return messages.get(action, f'تم تحديث شكواك "{complaint.title}".')


def send_notification_to_service(notification_data):
    """إرسال الإشعار إلى خدمة الإشعارات"""
    
    try:
        # TODO: تكامل مع خدمة الإشعارات
        # notifications_service_url = settings.NOTIFICATIONS_SERVICE_URL
        # response = requests.post(f'{notifications_service_url}/api/v1/send/', json=notification_data)
        # return response.json()
        pass
    except Exception as e:
        # تسجيل الخطأ
        print(f'خطأ في إرسال الإشعار: {e}')


@shared_task
def update_representative_score(representative_id, points, thank_you_message):
    """تحديث نقاط النائب في خدمة الإحصائيات"""
    
    try:
        # TODO: تكامل مع خدمة الإحصائيات
        # statistics_service_url = settings.STATISTICS_SERVICE_URL
        # 
        # data = {
        #     'representative_id': representative_id,
        #     'points': points,
        #     'reason': 'complaint_resolved',
        #     'thank_you_message': thank_you_message
        # }
        # 
        # response = requests.post(f'{statistics_service_url}/api/v1/update-score/', json=data)
        # return response.json()
        
        return {'status': 'success', 'message': 'تم تحديث النقاط بنجاح'}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_attachments():
    """تنظيف المرفقات القديمة (مهمة دورية)"""
    
    try:
        # حذف المرفقات الأقدم من 6 أشهر للشكاوى المحلولة
        old_date = timezone.now() - timezone.timedelta(days=180)
        
        old_attachments = ComplaintAttachment.objects.filter(
            complaint__status='resolved',
            complaint__resolved_at__lt=old_date
        )
        
        deleted_count = 0
        for attachment in old_attachments:
            if os.path.exists(attachment.file.path):
                os.remove(attachment.file.path)
            attachment.delete()
            deleted_count += 1
        
        return {'status': 'success', 'deleted_count': deleted_count}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_overdue_reminders():
    """إرسال تذكيرات للشكاوى المتأخرة"""
    
    try:
        # البحث عن الشكاوى المعلقة التي انتهت مدة التعليق
        overdue_complaints = Complaint.objects.filter(
            status='on_hold',
            hold_until__lt=timezone.now()
        )
        
        for complaint in overdue_complaints:
            # إرسال تذكير للنائب
            notify_complaint_update.delay(
                complaint.id,
                'overdue_reminder',
                complaint.assigned_representative_id
            )
            
            # تحديث حالة الشكوى إلى "متأخرة"
            complaint.status = 'overdue'
            complaint.save()
        
        return {'status': 'success', 'processed_count': overdue_complaints.count()}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
