"""
URLs الرئيسية لخدمة الشكاوى - منصة نائبك.كوم
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # تطبيق الشكاوى
    path('', include('complaints.urls')),
]

# إضافة URLs للملفات الثابتة والمرفوعة في بيئة التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
