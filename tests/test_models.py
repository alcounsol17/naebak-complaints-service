"""
اختبارات نماذج خدمة الشكاوى
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from complaints.models import (
    ComplaintCategory, Complaint, ComplaintAttachment, 
    ComplaintHistory, ComplaintResponse
)

User = get_user_model()


class ComplaintCategoryModelTest(TestCase):
    """اختبارات نموذج تصنيف الشكاوى"""
    
    def setUp(self):
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة",
            is_active=True
        )
    
    def test_category_creation(self):
        """اختبار إنشاء تصنيف جديد"""
        self.assertEqual(self.category.name, "خدمات عامة")
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.created_at)
    
    def test_category_str_representation(self):
        """اختبار تمثيل التصنيف كنص"""
        self.assertEqual(str(self.category), "خدمات عامة")
    
    def test_category_slug_generation(self):
        """اختبار توليد slug تلقائياً"""
        self.assertEqual(self.category.slug, "خدمات-عامة")


class ComplaintModelTest(TestCase):
    """اختبارات نموذج الشكوى"""
    
    def setUp(self):
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة"
        )
        
        # إنشاء مستخدمين وهميين
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
        
        self.complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي في شارع النيل",
            citizen=self.citizen,
            category=self.category,
            priority="medium"
        )
    
    def test_complaint_creation(self):
        """اختبار إنشاء شكوى جديدة"""
        self.assertEqual(self.complaint.title, "مشكلة في الصرف الصحي")
        self.assertEqual(self.complaint.status, "pending")
        self.assertEqual(self.complaint.priority, "medium")
        self.assertIsNotNone(self.complaint.reference_number)
    
    def test_complaint_str_representation(self):
        """اختبار تمثيل الشكوى كنص"""
        expected = f"{self.complaint.reference_number} - مشكلة في الصرف الصحي"
        self.assertEqual(str(self.complaint), expected)
    
    def test_reference_number_generation(self):
        """اختبار توليد رقم المرجع"""
        self.assertTrue(self.complaint.reference_number.startswith('CMP'))
        self.assertEqual(len(self.complaint.reference_number), 13)  # CMP + 10 digits
    
    def test_content_max_length_validation(self):
        """اختبار التحقق من الحد الأقصى لطول المحتوى"""
        long_content = "ا" * 1501  # أكثر من 1500 حرف
        
        with self.assertRaises(ValidationError):
            complaint = Complaint(
                title="عنوان",
                content=long_content,
                citizen=self.citizen,
                category=self.category
            )
            complaint.full_clean()
    
    def test_youtube_link_validation(self):
        """اختبار التحقق من صحة رابط يوتيوب"""
        # رابط صحيح
        self.complaint.youtube_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.complaint.full_clean()  # يجب ألا يثير خطأ
        
        # رابط خاطئ
        with self.assertRaises(ValidationError):
            self.complaint.youtube_link = "https://example.com/video"
            self.complaint.full_clean()
    
    def test_complaint_assignment(self):
        """اختبار إسناد الشكوى لنائب"""
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen,  # في الواقع سيكون أدمن
            notes="شكوى مهمة تحتاج متابعة"
        )
        
        self.assertEqual(self.complaint.status, "assigned")
        self.assertEqual(self.complaint.assigned_representative, self.representative)
        self.assertIsNotNone(self.complaint.assigned_at)
        self.assertEqual(self.complaint.assignment_notes, "شكوى مهمة تحتاج متابعة")
    
    def test_complaint_acceptance(self):
        """اختبار قبول الشكوى من النائب"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        
        # قبول الشكوى
        self.complaint.accept_by_representative()
        
        self.assertEqual(self.complaint.status, "accepted")
        self.assertIsNotNone(self.complaint.accepted_at)
    
    def test_complaint_rejection(self):
        """اختبار رفض الشكوى من النائب"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        
        # رفض الشكوى
        self.complaint.reject_by_representative("خارج نطاق اختصاصي")
        
        self.assertEqual(self.complaint.status, "rejected")
        self.assertEqual(self.complaint.rejection_reason, "خارج نطاق اختصاصي")
        self.assertIsNotNone(self.complaint.rejected_at)
    
    def test_complaint_hold(self):
        """اختبار تعليق الشكوى"""
        # إسناد الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        
        # تعليق الشكوى
        self.complaint.put_on_hold("تحتاج دراسة إضافية")
        
        self.assertEqual(self.complaint.status, "on_hold")
        self.assertEqual(self.complaint.hold_reason, "تحتاج دراسة إضافية")
        self.assertIsNotNone(self.complaint.hold_until)
    
    def test_complaint_resolution(self):
        """اختبار حل الشكوى"""
        # إسناد وقبول الشكوى أولاً
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        self.complaint.accept_by_representative()
        
        # حل الشكوى
        self.complaint.resolve("تم إصلاح مشكلة الصرف الصحي")
        
        self.assertEqual(self.complaint.status, "resolved")
        self.assertEqual(self.complaint.resolution, "تم إصلاح مشكلة الصرف الصحي")
        self.assertIsNotNone(self.complaint.resolved_at)
    
    def test_is_overdue_property(self):
        """اختبار خاصية التأخير"""
        # إسناد الشكوى وتعليقها
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        self.complaint.put_on_hold("تحتاج دراسة")
        
        # تعديل تاريخ التعليق ليكون في الماضي
        past_date = timezone.now() - timedelta(days=4)
        self.complaint.hold_until = past_date
        self.complaint.save()
        
        self.assertTrue(self.complaint.is_overdue)
    
    def test_days_since_assignment_property(self):
        """اختبار خاصية عدد الأيام منذ الإسناد"""
        # إسناد الشكوى
        past_date = timezone.now() - timedelta(days=2)
        self.complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        self.complaint.assigned_at = past_date
        self.complaint.save()
        
        self.assertEqual(self.complaint.days_since_assignment, 2)


class ComplaintAttachmentModelTest(TestCase):
    """اختبارات نموذج مرفقات الشكوى"""
    
    def setUp(self):
        self.citizen = User.objects.create_user(
            username="citizen1",
            email="citizen@example.com",
            user_type="citizen"
        )
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        self.complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي",
            citizen=self.citizen,
            category=self.category
        )
    
    def test_attachment_creation(self):
        """اختبار إنشاء مرفق جديد"""
        attachment = ComplaintAttachment.objects.create(
            complaint=self.complaint,
            file="attachments/test.pdf",
            original_name="تقرير.pdf",
            file_type="application/pdf",
            file_size=1024
        )
        
        self.assertEqual(attachment.complaint, self.complaint)
        self.assertEqual(attachment.original_name, "تقرير.pdf")
        self.assertEqual(attachment.file_type, "application/pdf")
        self.assertEqual(attachment.file_size, 1024)
    
    def test_attachment_str_representation(self):
        """اختبار تمثيل المرفق كنص"""
        attachment = ComplaintAttachment.objects.create(
            complaint=self.complaint,
            file="attachments/test.pdf",
            original_name="تقرير.pdf"
        )
        
        expected = f"{self.complaint.reference_number} - تقرير.pdf"
        self.assertEqual(str(attachment), expected)
    
    def test_file_size_validation(self):
        """اختبار التحقق من حجم الملف"""
        max_size = 10 * 1024 * 1024  # 10MB
        
        with self.assertRaises(ValidationError):
            attachment = ComplaintAttachment(
                complaint=self.complaint,
                file="attachments/large.pdf",
                file_size=max_size + 1
            )
            attachment.full_clean()


class ComplaintHistoryModelTest(TestCase):
    """اختبارات نموذج تاريخ الشكوى"""
    
    def setUp(self):
        self.citizen = User.objects.create_user(
            username="citizen1",
            email="citizen@example.com",
            user_type="citizen"
        )
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        self.complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي",
            citizen=self.citizen,
            category=self.category
        )
    
    def test_history_creation(self):
        """اختبار إنشاء سجل تاريخي"""
        history = ComplaintHistory.objects.create(
            complaint=self.complaint,
            action="created",
            description="تم إنشاء الشكوى",
            performed_by=self.citizen
        )
        
        self.assertEqual(history.complaint, self.complaint)
        self.assertEqual(history.action, "created")
        self.assertEqual(history.performed_by, self.citizen)
        self.assertIsNotNone(history.performed_at)
    
    def test_history_str_representation(self):
        """اختبار تمثيل السجل التاريخي كنص"""
        history = ComplaintHistory.objects.create(
            complaint=self.complaint,
            action="created",
            description="تم إنشاء الشكوى",
            performed_by=self.citizen
        )
        
        expected = f"{self.complaint.reference_number} - created"
        self.assertEqual(str(history), expected)


class ComplaintResponseModelTest(TestCase):
    """اختبارات نموذج ردود الشكوى"""
    
    def setUp(self):
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
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        self.complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي",
            citizen=self.citizen,
            category=self.category
        )
    
    def test_response_creation(self):
        """اختبار إنشاء رد جديد"""
        response = ComplaintResponse.objects.create(
            complaint=self.complaint,
            response_type="representative",
            response_text="سيتم حل المشكلة خلال أسبوع",
            responded_by=self.representative
        )
        
        self.assertEqual(response.complaint, self.complaint)
        self.assertEqual(response.response_type, "representative")
        self.assertEqual(response.responded_by, self.representative)
        self.assertIsNotNone(response.responded_at)
    
    def test_response_str_representation(self):
        """اختبار تمثيل الرد كنص"""
        response = ComplaintResponse.objects.create(
            complaint=self.complaint,
            response_type="representative",
            response_text="سيتم حل المشكلة خلال أسبوع",
            responded_by=self.representative
        )
        
        expected = f"{self.complaint.reference_number} - representative response"
        self.assertEqual(str(response), expected)
    
    def test_response_text_max_length(self):
        """اختبار الحد الأقصى لطول نص الرد"""
        long_text = "ا" * 2001  # أكثر من 2000 حرف
        
        with self.assertRaises(ValidationError):
            response = ComplaintResponse(
                complaint=self.complaint,
                response_type="representative",
                response_text=long_text,
                responded_by=self.representative
            )
            response.full_clean()


class ComplaintManagerTest(TestCase):
    """اختبارات مدير نموذج الشكوى"""
    
    def setUp(self):
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
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        # إنشاء شكاوى مختلفة
        self.pending_complaint = Complaint.objects.create(
            title="شكوى معلقة",
            content="محتوى الشكوى المعلقة",
            citizen=self.citizen,
            category=self.category,
            status="pending"
        )
        
        self.resolved_complaint = Complaint.objects.create(
            title="شكوى محلولة",
            content="محتوى الشكوى المحلولة",
            citizen=self.citizen,
            category=self.category,
            status="resolved"
        )
        
        # شكوى متأخرة
        self.overdue_complaint = Complaint.objects.create(
            title="شكوى متأخرة",
            content="محتوى الشكوى المتأخرة",
            citizen=self.citizen,
            category=self.category,
            status="on_hold"
        )
        self.overdue_complaint.assign_to_representative(
            representative=self.representative,
            assigned_by=self.citizen
        )
        self.overdue_complaint.put_on_hold("تحتاج دراسة")
        # تعديل تاريخ التعليق ليكون في الماضي
        past_date = timezone.now() - timedelta(days=4)
        self.overdue_complaint.hold_until = past_date
        self.overdue_complaint.save()
    
    def test_pending_complaints_queryset(self):
        """اختبار استعلام الشكاوى المعلقة"""
        pending_complaints = Complaint.objects.pending()
        self.assertIn(self.pending_complaint, pending_complaints)
        self.assertNotIn(self.resolved_complaint, pending_complaints)
    
    def test_resolved_complaints_queryset(self):
        """اختبار استعلام الشكاوى المحلولة"""
        resolved_complaints = Complaint.objects.resolved()
        self.assertIn(self.resolved_complaint, resolved_complaints)
        self.assertNotIn(self.pending_complaint, resolved_complaints)
    
    def test_overdue_complaints_queryset(self):
        """اختبار استعلام الشكاوى المتأخرة"""
        overdue_complaints = Complaint.objects.overdue()
        self.assertIn(self.overdue_complaint, overdue_complaints)
        self.assertNotIn(self.pending_complaint, overdue_complaints)
    
    def test_by_representative_queryset(self):
        """اختبار استعلام الشكاوى حسب النائب"""
        rep_complaints = Complaint.objects.by_representative(self.representative)
        self.assertIn(self.overdue_complaint, rep_complaints)
        self.assertNotIn(self.pending_complaint, rep_complaints)
    
    def test_by_citizen_queryset(self):
        """اختبار استعلام الشكاوى حسب المواطن"""
        citizen_complaints = Complaint.objects.by_citizen(self.citizen)
        self.assertEqual(citizen_complaints.count(), 3)  # جميع الشكاوى للمواطن نفسه
    
    def test_by_priority_queryset(self):
        """اختبار استعلام الشكاوى حسب الأولوية"""
        # إنشاء شكوى عاجلة
        urgent_complaint = Complaint.objects.create(
            title="شكوى عاجلة",
            content="محتوى الشكوى العاجلة",
            citizen=self.citizen,
            category=self.category,
            priority="urgent"
        )
        
        urgent_complaints = Complaint.objects.by_priority("urgent")
        self.assertIn(urgent_complaint, urgent_complaints)
        self.assertNotIn(self.pending_complaint, urgent_complaints)  # أولوية متوسطة
