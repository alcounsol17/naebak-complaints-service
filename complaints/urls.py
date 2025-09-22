"""
URLs لخدمة الشكاوى - منصة نائبك.كوم
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# إنشاء router لـ ViewSets
router = DefaultRouter()
router.register(r'complaints', views.ComplaintViewSet, basename='complaint')
router.register(r'attachments', views.ComplaintAttachmentViewSet, basename='attachment')
router.register(r'categories', views.ComplaintCategoryViewSet, basename='category')
router.register(r'templates', views.ComplaintTemplateViewSet, basename='template')
router.register(r'history', views.ComplaintHistoryViewSet, basename='history')

# URLs الأساسية
urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
    
    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    
    # Authentication URLs (DRF)
    path('api-auth/', include('rest_framework.urls')),
]

# إضافة URLs للواجهات الأمامية (سيتم إضافتها لاحقاً)
# urlpatterns += [
#     path('', views.ComplaintDashboardView.as_view(), name='dashboard'),
#     path('citizen/', views.CitizenComplaintView.as_view(), name='citizen_complaints'),
#     path('representative/', views.RepresentativeComplaintView.as_view(), name='representative_complaints'),
#     path('admin/', views.AdminComplaintView.as_view(), name='admin_complaints'),
# ]
