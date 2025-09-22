"""
اختبارات واجهات برمجة التطبيقات لخدمة الشكاوى
"""

import json
import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from complaints.models import (
    ComplaintCategory, Complaint, ComplaintAttachment
)

User = get_user_model()


class ComplaintAPITestCase(APITestCase):
    """اختبارات واجهات برمجة التطبيقات للشكاوى"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.client = APIClient()
        
        # إنشاء المستخدمين
        self.citizen = User.objects.create_user(
            username="citizen1",
            email="citizen@example.com",
            user_type="citizen"
        )
        
        self.representative = User.objects.create_user(
            username="representative1",
            email="rep@example.com",
            user_type="representative"
        )
        
        self.admin_user = User.objects.create_user(
            username="admin1",
            email="admin@example.com",
            is_staff=True
        )
        
        # إنشاء تصنيف
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة"
        )
        
        # إنشاء شكوى للاختبارات
        self.complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي في شارع النيل",
            citizen=self.citizen,
            category=self.category,
            priority="medium"
        )
    
    def test_create_complaint_success(self):
        """اختبار إنشاء شكوى بنجاح"""
        self.client.force_authenticate(user=self.citizen)
        
        data = {
            'title': 'مشكلة في الإنارة',
            'content': 'لا توجد إنارة في الشارع',
            'category': self.category.id,
            'priority': 'high'
        }
        
        response = self.client.post('/api/v1/complaints/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'مشكلة في الإنارة')
        self.assertEqual(response.data['status'], 'pending')
        self.assertIsNotNone(response.data['reference_number'])
    
    def test_create_complaint_with_attachments(self):
        """اختبار إنشاء شكوى مع مرفقات"""
        self.client.force_authenticate(user=self.citizen)
        
        # إنشاء ملف وهمي
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        data = {
            'title': 'مشكلة مع مرفق',
            'content': 'شكوى مع ملف مرفق',
            'category': self.category.id,
            'attachments': [test_file]
        }
        
        response = self.client.post('/api/v1/complaints/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # التحقق من وجود المرفق
        complaint_id = response.data['id']
        attachments = ComplaintAttachment.objects.filter(complaint_id=complaint_id)
        self.assertEqual(attachments.count(), 1)
    
    def test_create_complaint_invalid_content_length(self):
        """اختبار إنشاء شكوى بمحتوى طويل جداً"""
        self.client.force_authenticate(user=self.citizen)
        
        long_content = "ا" * 1501  # أكثر من 1500 حرف
        
        data = {
            'title': 'شكوى بمحتوى طويل',
            'content': long_content,
            'category': self.category.id
        }
        
        response = self.client.post('/api/v1/complaints/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)
    
    def test_create_complaint_too_many_attachments(self):
        """اختبار إنشاء شكوى بأكثر من 10 مرفقات"""
        self.client.force_authenticate(user=self.citizen)
        
        # إنشاء 11 ملف
        attachments = []
        for i in range(11):
            file = SimpleUploadedFile(
                f"test{i}.pdf",
                b"file_content",
                content_type="application/pdf"
            )
            attachments.append(file)
        
        data = {
            'title': 'شكوى بمرفقات كثيرة',
            'content': 'شكوى مع مرفقات كثيرة',
            'category': self.category.id,
            'attachments': attachments
        }
        
        response = self.client.post('/api/v1/complaints/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('attachments', response.data)
    
    def test_create_complaint_invalid_youtube_link(self):
        """اختبار إنشاء شكوى برابط يوتيوب خاطئ"""
        self.client.force_authenticate(user=self.citizen)
        
        data = {
            'title': 'شكوى برابط خاطئ',
            'content': 'شكوى مع رابط يوتيوب خاطئ',
            'category': self.category.id,
            'youtube_link': 'https://example.com/video'
        }
        
        response = self.client.post('/api/v1/complaints/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('youtube_link', response.data)
    
    def test_list_complaints_citizen(self):
        """اختبار عرض قائمة الشكاوى للمواطن"""
        self.client.force_authenticate(user=self.citizen)
        
        response = self.client.get('/api/v1/complaints/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.complaint.id)
    
    def test_list_complaints_representative(self):
        """اختبار عرض قائمة الشكاوى للنائب"""
        # إسناد الشكوى للنائب
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.representative)
        
        response = self.client.get('/api/v1/complaints/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_complaints_admin(self):
        """اختبار عرض قائمة الشكاوى للأدمن"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/v1/complaints/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_complaint_details(self):
        """اختبار عرض تفاصيل شكوى محددة"""
        self.client.force_authenticate(user=self.citizen)
        
        response = self.client.get(f'/api/v1/complaints/{self.complaint.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.complaint.id)
        self.assertEqual(response.data['title'], self.complaint.title)
    
    def test_update_complaint_citizen(self):
        """اختبار تعديل الشكوى من المواطن"""
        self.client.force_authenticate(user=self.citizen)
        
        data = {
            'title': 'عنوان محدث',
            'content': 'محتوى محدث'
        }
        
        response = self.client.patch(f'/api/v1/complaints/{self.complaint.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'عنوان محدث')
    
    def test_update_complaint_after_assignment(self):
        """اختبار منع تعديل الشكوى بعد الإسناد"""
        # إسناد الشكوى
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.citizen)
        
        data = {
            'title': 'عنوان محدث'
        }
        
        response = self.client.patch(f'/api/v1/complaints/{self.complaint.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_assign_complaint_admin(self):
        """اختبار إسناد الشكوى من الأدمن"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'representative_id': self.representative.id,
            'representative_name': self.representative.username,
            'notes': 'شكوى مهمة'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/assign/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # التحقق من الإسناد
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'assigned')
        self.assertEqual(self.complaint.assigned_representative, self.representative)
    
    def test_assign_complaint_non_admin(self):
        """اختبار منع إسناد الشكوى من غير الأدمن"""
        self.client.force_authenticate(user=self.citizen)
        
        data = {
            'representative_id': self.representative.id,
            'representative_name': self.representative.username
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/assign/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_accept_complaint_representative(self):
        """اختبار قبول الشكوى من النائب"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.representative)
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # التحقق من القبول
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'accepted')
    
    def test_reject_complaint_representative(self):
        """اختبار رفض الشكوى من النائب"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.representative)
        
        data = {
            'reason': 'خارج نطاق اختصاصي'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/reject/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # التحقق من الرفض
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'rejected')
        self.assertEqual(self.complaint.rejection_reason, 'خارج نطاق اختصاصي')
    
    def test_hold_complaint_representative(self):
        """اختبار تعليق الشكوى من النائب"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.representative)
        
        data = {
            'reason': 'تحتاج دراسة إضافية'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/hold/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # التحقق من التعليق
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'on_hold')
        self.assertEqual(self.complaint.hold_reason, 'تحتاج دراسة إضافية')
    
    def test_respond_to_complaint_representative(self):
        """اختبار الرد على الشكوى من النائب"""
        # إسناد وقبول الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        self.complaint.accept_by_representative()
        
        self.client.force_authenticate(user=self.representative)
        
        data = {
            'response_type': 'representative',
            'response_text': 'سيتم حل المشكلة خلال أسبوع'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/respond/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # التحقق من الرد
        self.assertEqual(self.complaint.responses.count(), 1)
        response_obj = self.complaint.responses.first()
        self.assertEqual(response_obj.response_text, 'سيتم حل المشكلة خلال أسبوع')
    
    def test_respond_to_complaint_admin(self):
        """اختبار الرد الإداري على الشكوى"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'response_type': 'admin',
            'response_text': 'تم استلام شكواكم وسيتم التعامل معها'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/respond/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_resolve_complaint_with_points(self):
        """اختبار حل الشكوى مع منح نقاط للنائب"""
        # إسناد وقبول الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.admin_user
        )
        self.complaint.accept_by_representative()
        
        self.client.force_authenticate(user=self.representative)
        
        data = {
            'response_type': 'representative',
            'response_text': 'تم حل المشكلة',
            'resolution': 'تم إصلاح الصرف الصحي',
            'award_points': True,
            'thank_you_message': 'شكراً للنائب على حل المشكلة'
        }
        
        response = self.client.post(f'/api/v1/complaints/{self.complaint.id}/respond/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # التحقق من الحل
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')
        self.assertEqual(self.complaint.resolution, 'تم إصلاح الصرف الصحي')
    
    def test_get_complaint_statistics(self):
        """اختبار الحصول على إحصائيات الشكاوى"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/v1/complaints/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_complaints', response.data)
        self.assertIn('pending_complaints', response.data)
        self.assertIn('resolved_complaints', response.data)
    
    def test_export_complaints(self):
        """اختبار تصدير الشكاوى"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'format': 'zip',
            'include_attachments': True
        }
        
        response = self.client.post('/api/v1/complaints/export/', data)
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
    
    def test_filter_complaints_by_status(self):
        """اختبار تصفية الشكاوى حسب الحالة"""
        # إنشاء شكوى محلولة
        resolved_complaint = Complaint.objects.create(
            title="شكوى محلولة",
            content="محتوى الشكوى المحلولة",
            citizen=self.citizen,
            category=self.category,
            status="resolved"
        )
        
        self.client.force_authenticate(user=self.citizen)
        
        # تصفية الشكاوى المعلقة
        response = self.client.get('/api/v1/complaints/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')
        
        # تصفية الشكاوى المحلولة
        response = self.client.get('/api/v1/complaints/?status=resolved')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'resolved')
    
    def test_filter_complaints_by_priority(self):
        """اختبار تصفية الشكاوى حسب الأولوية"""
        # إنشاء شكوى عاجلة
        urgent_complaint = Complaint.objects.create(
            title="شكوى عاجلة",
            content="محتوى الشكوى العاجلة",
            citizen=self.citizen,
            category=self.category,
            priority="urgent"
        )
        
        self.client.force_authenticate(user=self.citizen)
        
        # تصفية الشكاوى العاجلة
        response = self.client.get('/api/v1/complaints/?priority=urgent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['priority'], 'urgent')
    
    def test_search_complaints(self):
        """اختبار البحث في الشكاوى"""
        self.client.force_authenticate(user=self.citizen)
        
        # البحث بالعنوان
        response = self.client.get('/api/v1/complaints/?search=صرف')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # البحث بمصطلح غير موجود
        response = self.client.get('/api/v1/complaints/?search=كهرباء')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_unauthorized_access(self):
        """اختبار منع الوصول غير المصرح به"""
        # محاولة الوصول بدون تسجيل دخول
        response = self.client.get('/api/v1/complaints/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # محاولة إنشاء شكوى بدون تسجيل دخول
        data = {
            'title': 'شكوى جديدة',
            'content': 'محتوى الشكوى',
            'category': self.category.id
        }
        response = self.client.post('/api/v1/complaints/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_other_user_complaint(self):
        """اختبار منع الوصول لشكاوى المستخدمين الآخرين"""
        # إنشاء مستخدم آخر
        other_citizen = User.objects.create_user(
            username="citizen2",
            email="citizen2@example.com",
            user_type="citizen"
        )
        
        # إنشاء شكوى للمستخدم الآخر
        other_complaint = Complaint.objects.create(
            title="شكوى المستخدم الآخر",
            content="محتوى شكوى المستخدم الآخر",
            citizen=other_citizen,
            category=self.category
        )
        
        # محاولة الوصول للشكوى من مستخدم مختلف
        self.client.force_authenticate(user=self.citizen)
        response = self.client.get(f'/api/v1/complaints/{other_complaint.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ComplaintCategoryAPITestCase(APITestCase):
    """اختبارات واجهات برمجة التطبيقات لتصنيفات الشكاوى"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.citizen = User.objects.create_user(
            username="citizen1",
            email="citizen@example.com",
            user_type="citizen"
        )
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة",
            is_active=True
        )
    
    def test_list_categories(self):
        """اختبار عرض قائمة التصنيفات"""
        self.client.force_authenticate(user=self.citizen)
        
        response = self.client.get('/api/v1/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'خدمات عامة')
    
    def test_list_only_active_categories(self):
        """اختبار عرض التصنيفات النشطة فقط"""
        # إنشاء تصنيف غير نشط
        inactive_category = ComplaintCategory.objects.create(
            name="تصنيف غير نشط",
            description="تصنيف معطل",
            is_active=False
        )
        
        self.client.force_authenticate(user=self.citizen)
        
        response = self.client.get('/api/v1/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # فقط التصنيف النشط
        self.assertEqual(response.data[0]['name'], 'خدمات عامة')
