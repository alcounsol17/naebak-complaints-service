"""
اختبارات مبسطة لخدمة الشكاوى
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from complaints.models import ComplaintCategory, Complaint

User = get_user_model()


class SimpleComplaintTest(TestCase):
    """اختبارات أساسية للشكاوى"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة",
            description="شكاوى متعلقة بالخدمات العامة"
        )
    
    def test_create_complaint_category(self):
        """اختبار إنشاء تصنيف الشكوى"""
        self.assertEqual(self.category.name, "خدمات عامة")
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.created_at)
    
    def test_create_complaint(self):
        """اختبار إنشاء شكوى جديدة"""
        complaint = Complaint.objects.create(
            title="مشكلة في الصرف الصحي",
            content="يوجد مشكلة في الصرف الصحي في الشارع",
            citizen=self.user,
            category=self.category,
            priority="medium"
        )
        
        self.assertEqual(complaint.title, "مشكلة في الصرف الصحي")
        self.assertEqual(complaint.status, "pending")
        self.assertEqual(complaint.priority, "medium")
        self.assertEqual(complaint.citizen, self.user)
        self.assertEqual(complaint.category, self.category)
        self.assertIsNotNone(complaint.reference_number)
        self.assertTrue(complaint.reference_number.startswith('CMP'))
    
    def test_complaint_content_max_length(self):
        """اختبار الحد الأقصى لطول محتوى الشكوى"""
        # محتوى بطول 1500 حرف (الحد الأقصى)
        max_content = "ا" * 1500
        
        complaint = Complaint.objects.create(
            title="شكوى بحد أقصى",
            content=max_content,
            citizen=self.user,
            category=self.category
        )
        
        self.assertEqual(len(complaint.content), 1500)
    
    def test_complaint_str_representation(self):
        """اختبار تمثيل الشكوى كنص"""
        complaint = Complaint.objects.create(
            title="شكوى اختبار",
            content="محتوى الشكوى",
            citizen=self.user,
            category=self.category
        )
        
        expected = f"{complaint.reference_number} - شكوى اختبار"
        self.assertEqual(str(complaint), expected)
    
    def test_complaint_youtube_link(self):
        """اختبار إضافة رابط يوتيوب للشكوى"""
        complaint = Complaint.objects.create(
            title="شكوى مع فيديو",
            content="شكوى تحتوي على رابط يوتيوب",
            citizen=self.user,
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
                citizen=self.user,
                category=self.category,
                priority=priority
            )
            self.assertEqual(complaint.priority, priority)
    
    def test_complaint_status_default(self):
        """اختبار الحالة الافتراضية للشكوى"""
        complaint = Complaint.objects.create(
            title="شكوى جديدة",
            content="محتوى الشكوى الجديدة",
            citizen=self.user,
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


class ComplaintManagerTest(TestCase):
    """اختبارات مدير نموذج الشكوى"""
    
    def setUp(self):
        """إعداد البيانات للاختبارات"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = ComplaintCategory.objects.create(
            name="خدمات عامة"
        )
        
        # إنشاء شكاوى بحالات مختلفة
        self.pending_complaint = Complaint.objects.create(
            title="شكوى معلقة",
            content="محتوى الشكوى المعلقة",
            citizen=self.user,
            category=self.category,
            status="pending"
        )
        
        self.resolved_complaint = Complaint.objects.create(
            title="شكوى محلولة",
            content="محتوى الشكوى المحلولة",
            citizen=self.user,
            category=self.category,
            status="resolved"
        )
    
    def test_pending_complaints_queryset(self):
        """اختبار استعلام الشكاوى المعلقة"""
        pending_complaints = Complaint.objects.filter(status="pending")
        self.assertIn(self.pending_complaint, pending_complaints)
        self.assertNotIn(self.resolved_complaint, pending_complaints)
    
    def test_resolved_complaints_queryset(self):
        """اختبار استعلام الشكاوى المحلولة"""
        resolved_complaints = Complaint.objects.filter(status="resolved")
        self.assertIn(self.resolved_complaint, resolved_complaints)
        self.assertNotIn(self.pending_complaint, resolved_complaints)
    
    def test_complaints_count(self):
        """اختبار عد الشكاوى"""
        total_complaints = Complaint.objects.count()
        self.assertEqual(total_complaints, 2)
        
        pending_count = Complaint.objects.filter(status="pending").count()
        self.assertEqual(pending_count, 1)
        
        resolved_count = Complaint.objects.filter(status="resolved").count()
        self.assertEqual(resolved_count, 1)
