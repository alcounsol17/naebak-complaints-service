"""
اختبارات تعمل مع التصميم الفعلي لخدمة الشكاوى
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from complaints.models import ComplaintCategory, Complaint, ComplaintAttachment


class WorkingComplaintTest(TestCase):
    """اختبارات تعمل مع النماذج الفعلية"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة"
        )
    
    def test_create_complaint_category(self):
        """اختبار إنشاء تصنيف الشكوى"""
        self.assertEqual(self.category.name, "خدمات عامة")
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.created_at)
        self.assertEqual(str(self.category), "خدمات عامة")
    
    def test_create_complaint(self):
        """اختبار إنشاء شكوى جديدة"""
        complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي في الشارع",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category,
            priority="medium"
        )
        
        self.assertEqual(complaint.title, "مشكلة في الصرف الصحي")
        self.assertEqual(complaint.status, "pending")
        self.assertEqual(complaint.priority, "medium")
        self.assertEqual(complaint.citizen_id, 123)
        self.assertEqual(complaint.citizen_name, "أحمد محمد")
        self.assertEqual(complaint.citizen_email, "ahmed@example.com")
        self.assertEqual(complaint.category, self.category)
        self.assertIsNotNone(complaint.reference_number)
        self.assertTrue(complaint.reference_number.startswith('CMP'))
    
    def test_complaint_content_max_length(self):
        """اختبار الحد الأقصى لطول محتوى الشكوى (1500 حرف)"""
        # محتوى بطول 1500 حرف (الحد الأقصى)
        max_content = "ا" * 1500
        
        complaint = Complaint.objects.create(
            title="شكوى بحد أقصى",
            content=max_content,
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category
        )
        
        self.assertEqual(len(complaint.content), 1500)
        
        # اختبار تجاوز الحد الأقصى
        long_content = "ا" * 1501
        
        with self.assertRaises(ValidationError):
            complaint = Complaint(
                title="شكوى طويلة جداً",
                content=long_content,
                citizen_id=123,
                citizen_name="أحمد محمد",
                citizen_email="ahmed@example.com",
                category=self.category
            )
            complaint.full_clean()
    
    def test_complaint_str_representation(self):
        """اختبار تمثيل الشكوى كنص"""
        complaint = Complaint.objects.create(
            title="شكوى اختبار",
            content="محتوى الشكوى",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category
        )
        
        expected = f"{complaint.reference_number} - شكوى اختبار"
        self.assertEqual(str(complaint), expected)
    
    def test_complaint_youtube_link(self):
        """اختبار إضافة رابط يوتيوب للشكوى"""
        complaint = Complaint.objects.create(
            title="شكوى مع فيديو",
            content="شكوى تحتوي على رابط يوتيوب",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category,
            youtube_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        
        self.assertEqual(complaint.youtube_link, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    def test_complaint_priority_choices(self):
        """اختبار خيارات أولوية الشكوى"""
        priorities = ["low", "medium", "high", "urgent"]
        
        for priority in priorities:
            complaint = Complaint.objects.create(
                title=f"شكوى {priority}",
                content=f"شكوى بأولوية {priority}",
                citizen_id=123,
                citizen_name="أحمد محمد",
                citizen_email="ahmed@example.com",
                category=self.category,
                priority=priority
            )
            self.assertEqual(complaint.priority, priority)
    
    def test_complaint_status_choices(self):
        """اختبار خيارات حالة الشكوى"""
        statuses = ["pending", "assigned", "accepted", "rejected", "on_hold", "resolved", "closed"]
        
        for status in statuses:
            complaint = Complaint.objects.create(
                title=f"شكوى {status}",
                content=f"شكوى بحالة {status}",
                citizen_id=123,
                citizen_name="أحمد محمد",
                citizen_email="ahmed@example.com",
                category=self.category,
                status=status
            )
            self.assertEqual(complaint.status, status)
    
    def test_complaint_status_default(self):
        """اختبار الحالة الافتراضية للشكوى"""
        complaint = Complaint.objects.create(
            title="شكوى جديدة",
            content="محتوى الشكوى الجديدة",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category
        )
        
        self.assertEqual(complaint.status, "pending")
    
    def test_category_slug_generation(self):
        """اختبار توليد slug للتصنيف"""
        category = ComplaintCategory.objects.create(
            name="خدمات صحية",
            description="شكاوى متعلقة بالخدمات الصحية"
        )
        
        self.assertEqual(category.slug, "خدمات-صحية")
    
    def test_category_active_by_default(self):
        """اختبار أن التصنيف نشط افتراضياً"""
        category = ComplaintCategory.objects.create(
            name="تصنيف جديد",
            description="وصف التصنيف الجديد"
        )
        
        self.assertTrue(category.is_active)
    
    def test_complaint_assignment(self):
        """اختبار إسناد الشكوى لنائب"""
        complaint = Complaint.objects.create(
            title="شكوى للإسناد",
            content="شكوى تحتاج إسناد لنائب",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category
        )
        
        # إسناد الشكوى
        complaint.status = "assigned"
        complaint.assigned_representative_id = 456
        complaint.assigned_representative_name = "النائب محمد علي"
        complaint.assignment_notes = "شكوى مهمة تحتاج متابعة"
        complaint.save()
        
        self.assertEqual(complaint.status, "assigned")
        self.assertEqual(complaint.assigned_representative_id, 456)
        self.assertEqual(complaint.assigned_representative_name, "النائب محمد علي")
        self.assertEqual(complaint.assignment_notes, "شكوى مهمة تحتاج متابعة")
    
    def test_complaint_resolution(self):
        """اختبار حل الشكوى"""
        complaint = Complaint.objects.create(
            title="شكوى للحل",
            content="شكوى تحتاج حل",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category,
            status="accepted"
        )
        
        # حل الشكوى
        complaint.status = "resolved"
        complaint.resolution = "تم حل المشكلة بنجاح"
        complaint.save()
        
        self.assertEqual(complaint.status, "resolved")
        self.assertEqual(complaint.resolution, "تم حل المشكلة بنجاح")


class ComplaintAttachmentTest(TestCase):
    """اختبارات مرفقات الشكوى"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        self.complaint = Complaint.objects.create(
            title="شكوى مع مرفقات",
            content="شكوى تحتوي على مرفقات",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category
        )
    
    def test_create_attachment(self):
        """اختبار إنشاء مرفق للشكوى"""
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
        
        expected_str = f"{self.complaint.reference_number} - تقرير.pdf"
        self.assertEqual(str(attachment), expected_str)


class ComplaintQueryTest(TestCase):
    """اختبارات استعلامات الشكاوى"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        # إنشاء شكاوى بحالات مختلفة
        self.pending_complaint = Complaint.objects.create(
            title="شكوى معلقة",
            content="محتوى الشكوى المعلقة",
            citizen_id=123,
            citizen_name="أحمد محمد",
            citizen_email="ahmed@example.com",
            category=self.category,
            status="pending"
        )
        
        self.resolved_complaint = Complaint.objects.create(
            title="شكوى محلولة",
            content="محتوى الشكوى المحلولة",
            citizen_id=124,
            citizen_name="فاطمة أحمد",
            citizen_email="fatima@example.com",
            category=self.category,
            status="resolved"
        )
        
        self.urgent_complaint = Complaint.objects.create(
            title="شكوى عاجلة",
            content="محتوى الشكوى العاجلة",
            citizen_id=125,
            citizen_name="محمد سالم",
            citizen_email="mohamed@example.com",
            category=self.category,
            priority="urgent"
        )
    
    def test_filter_by_status(self):
        """اختبار التصفية حسب الحالة"""
        pending_complaints = Complaint.objects.filter(status="pending")
        self.assertIn(self.pending_complaint, pending_complaints)
        self.assertNotIn(self.resolved_complaint, pending_complaints)
        
        resolved_complaints = Complaint.objects.filter(status="resolved")
        self.assertIn(self.resolved_complaint, resolved_complaints)
        self.assertNotIn(self.pending_complaint, resolved_complaints)
    
    def test_filter_by_priority(self):
        """اختبار التصفية حسب الأولوية"""
        urgent_complaints = Complaint.objects.filter(priority="urgent")
        self.assertIn(self.urgent_complaint, urgent_complaints)
        self.assertNotIn(self.pending_complaint, urgent_complaints)
    
    def test_filter_by_citizen(self):
        """اختبار التصفية حسب المواطن"""
        citizen_complaints = Complaint.objects.filter(citizen_id=123)
        self.assertIn(self.pending_complaint, citizen_complaints)
        self.assertNotIn(self.resolved_complaint, citizen_complaints)
    
    def test_complaints_count(self):
        """اختبار عد الشكاوى"""
        total_complaints = Complaint.objects.count()
        self.assertEqual(total_complaints, 3)
        
        pending_count = Complaint.objects.filter(status="pending").count()
        self.assertEqual(pending_count, 2)  # pending + urgent (default status)
        
        resolved_count = Complaint.objects.filter(status="resolved").count()
        self.assertEqual(resolved_count, 1)
