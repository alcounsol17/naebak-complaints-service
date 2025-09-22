# خدمة الشكاوى - نائبك.كوم

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Django](https://img.shields.io/badge/django-4.2-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue.svg)
![Redis](https://img.shields.io/badge/redis-7-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

خدمة مايكروسيرفيس مخصصة لإدارة الشكاوى في منصة نائبك.كوم - منصة التواصل بين المواطنين والنواب في مصر.

## 📋 المحتويات

- [نظرة عامة](#نظرة-عامة)
- [المميزات](#المميزات)
- [المتطلبات التقنية](#المتطلبات-التقنية)
- [التثبيت والتشغيل](#التثبيت-والتشغيل)
- [واجهات برمجة التطبيقات](#واجهات-برمجة-التطبيقات)
- [الاختبارات](#الاختبارات)
- [النشر](#النشر)
- [المساهمة](#المساهمة)
- [الترخيص](#الترخيص)

## 🎯 نظرة عامة

خدمة الشكاوى هي جزء من منظومة نائبك.كوم المتكاملة، وهي مصممة كخدمة مايكروسيرفيس مستقلة لإدارة الشكاوى بين المواطنين والنواب والإدارة.

### الهدف
تمكين المواطنين من تقديم شكاواهم ومتابعة حلولها، وتمكين النواب من استقبال الشكاوى والرد عليها، وتمكين الإدارة من إدارة العملية بكفاءة.

## ✨ المميزات

### للمواطنين
- ✅ إرسال شكوى بحد أقصى 1500 حرف
- ✅ إرفاق حتى 10 ملفات (صور، PDF، Word)
- ✅ إضافة رابط يوتيوب اختياري
- ✅ متابعة حالة الشكوى في الوقت الفعلي
- ✅ استقبال الردود والحلول
- ✅ صفحة إدارة شخصية للشكاوى

### للنواب
- ✅ استقبال الشكاوى المُسندة إليهم
- ✅ قبول أو رفض أو تعليق الشكوى (3 أيام للدراسة)
- ✅ تقديم الردود والحلول
- ✅ كسب نقاط عند حل الشكاوى
- ✅ صفحة إدارة متخصصة للشكاوى

### للإدارة
- ✅ مراجعة وإدارة جميع الشكاوى
- ✅ إسناد الشكاوى للنواب المناسبين
- ✅ تحميل الشكاوى في ملف مضغوط
- ✅ إحصائيات شاملة ومفصلة
- ✅ لوحة تحكم متقدمة

### المميزات التقنية
- 🔄 **مايكروسيرفيس مستقل** مع قاعدة بيانات منفصلة
- 🚀 **أداء عالي** مع Redis للتخزين المؤقت
- 📊 **مهام غير متزامنة** مع Celery
- 🔒 **أمان متقدم** مع JWT والصلاحيات
- 📱 **تصميم متجاوب** يعمل على جميع الأجهزة
- 🌐 **واجهات برمجة تطبيقات RESTful** شاملة
- 🧪 **اختبارات شاملة** مع تغطية عالية
- 🐳 **Docker** جاهز للنشر
- ☁️ **Google Cloud Run** للنشر السحابي

## 🛠 المتطلبات التقنية

### البرمجيات المطلوبة
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (للتطوير)

### المكتبات الأساسية
- Django 4.2
- Django REST Framework
- Celery
- PostgreSQL Adapter (psycopg2)
- Redis Client
- Pillow (معالجة الصور)
- Google Cloud Storage

## 🚀 التثبيت والتشغيل

### 1. استنساخ المشروع
```bash
git clone https://github.com/alcounsol17/naebak-complaints-service.git
cd naebak-complaints-service
```

### 2. التشغيل باستخدام Docker (الطريقة المفضلة)
```bash
# تشغيل جميع الخدمات
docker-compose up -d

# تطبيق migrations
docker-compose exec web python manage.py migrate

# إنشاء superuser
docker-compose exec web python manage.py createsuperuser

# تحميل البيانات الأولية
docker-compose exec web python manage.py loaddata initial_data.json
```

### 3. التشغيل المحلي (للتطوير)
```bash
# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد متغيرات البيئة
cp .env.example .env
# قم بتعديل .env حسب إعداداتك

# تطبيق migrations
python manage.py migrate

# تشغيل الخادم
python manage.py runserver

# تشغيل Celery (في terminal منفصل)
celery -A complaints_service worker --loglevel=info

# تشغيل Celery Beat (في terminal منفصل)
celery -A complaints_service beat --loglevel=info
```

### 4. الوصول للتطبيق
- **التطبيق الرئيسي**: http://localhost:8000
- **واجهات برمجة التطبيقات**: http://localhost:8000/api/v1/
- **لوحة الإدارة**: http://localhost:8000/admin/
- **التوثيق التفاعلي**: http://localhost:8000/api/docs/

## 📡 واجهات برمجة التطبيقات

### نقاط النهاية الأساسية

#### الشكاوى
```
GET    /api/v1/complaints/              # قائمة الشكاوى
POST   /api/v1/complaints/              # إنشاء شكوى جديدة
GET    /api/v1/complaints/{id}/         # تفاصيل شكوى
PATCH  /api/v1/complaints/{id}/         # تحديث شكوى
DELETE /api/v1/complaints/{id}/         # حذف شكوى
```

#### إجراءات الشكاوى
```
POST   /api/v1/complaints/{id}/assign/  # إسناد الشكوى
POST   /api/v1/complaints/{id}/accept/  # قبول الشكوى
POST   /api/v1/complaints/{id}/reject/  # رفض الشكوى
POST   /api/v1/complaints/{id}/hold/    # تعليق الشكوى
POST   /api/v1/complaints/{id}/respond/ # الرد على الشكوى
```

#### الإحصائيات والتقارير
```
GET    /api/v1/complaints/statistics/   # إحصائيات الشكاوى
POST   /api/v1/complaints/export/       # تصدير الشكاوى
```

#### التصنيفات
```
GET    /api/v1/categories/              # قائمة التصنيفات
```

### أمثلة على الاستخدام

#### إنشاء شكوى جديدة
```bash
curl -X POST http://localhost:8000/api/v1/complaints/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "مشكلة في الصرف الصحي",
    "content": "يوجد مشكلة في الصرف الصحي في شارع النيل",
    "category": 1,
    "priority": "high"
  }'
```

#### إسناد شكوى لنائب
```bash
curl -X POST http://localhost:8000/api/v1/complaints/1/assign/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "representative_id": 123,
    "representative_name": "أحمد محمد",
    "notes": "شكوى مهمة تحتاج متابعة"
  }'
```

## 🧪 الاختبارات

### تشغيل جميع الاختبارات
```bash
python manage.py test
```

### تشغيل اختبارات محددة
```bash
# اختبارات النماذج
python manage.py test tests.test_models

# اختبارات واجهات برمجة التطبيقات
python manage.py test tests.test_views

# اختبارات مع تقرير التغطية
coverage run --source='.' manage.py test
coverage report
coverage html
```

### اختبارات الأداء
```bash
# اختبار الحمولة
python manage.py test tests.test_performance
```

## 🚀 النشر

### النشر على Google Cloud Run

#### 1. إعداد Google Cloud
```bash
# تسجيل الدخول
gcloud auth login

# تعيين المشروع
gcloud config set project YOUR_PROJECT_ID

# تفعيل الخدمات المطلوبة
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sql-component.googleapis.com
```

#### 2. إعداد قاعدة البيانات
```bash
# إنشاء Cloud SQL instance
gcloud sql instances create naebak-complaints-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# إنشاء قاعدة البيانات
gcloud sql databases create naebak_complaints \
  --instance=naebak-complaints-db
```

#### 3. النشر
```bash
# بناء ونشر التطبيق
gcloud run deploy naebak-complaints-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### النشر التلقائي مع GitHub Actions

المشروع مُعد للنشر التلقائي عند push إلى branch main. تأكد من إعداد المتغيرات التالية في GitHub Secrets:

```
GCP_SA_KEY              # مفتاح حساب الخدمة
DATABASE_URL            # رابط قاعدة البيانات
REDIS_URL              # رابط Redis
SECRET_KEY             # مفتاح Django السري
ALLOWED_HOSTS          # المضيفين المسموحين
CORS_ALLOWED_ORIGINS   # أصول CORS المسموحة
GCS_BUCKET_NAME        # اسم bucket للملفات
```

## 🏗 البنية المعمارية

```
naebak-complaints-service/
├── complaints/                 # التطبيق الرئيسي
│   ├── models.py              # نماذج قاعدة البيانات
│   ├── views.py               # واجهات برمجة التطبيقات
│   ├── serializers.py         # مسلسلات البيانات
│   ├── urls.py                # توجيه URLs
│   ├── tasks.py               # مهام Celery
│   └── admin.py               # لوحة الإدارة
├── complaints_service/         # إعدادات المشروع
│   ├── settings.py            # إعدادات Django
│   ├── urls.py                # URLs الرئيسية
│   ├── wsgi.py                # WSGI للنشر
│   └── celery.py              # إعدادات Celery
├── templates/                  # قوالب HTML
│   ├── shared/                # قوالب مشتركة
│   └── complaints/            # قوالب الشكاوى
├── static/                     # الملفات الثابتة
│   ├── css/                   # ملفات CSS
│   ├── js/                    # ملفات JavaScript
│   └── images/                # الصور
├── tests/                      # الاختبارات
│   ├── test_models.py         # اختبارات النماذج
│   └── test_views.py          # اختبارات APIs
├── .github/workflows/          # GitHub Actions
├── docker-compose.yml          # Docker Compose
├── Dockerfile                  # Docker image
├── requirements.txt            # متطلبات Python
└── README.md                   # هذا الملف
```

## 🔧 التكوين

### متغيرات البيئة

إنشئ ملف `.env` في جذر المشروع:

```env
# إعدادات Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# قاعدة البيانات
DATABASE_URL=postgresql://user:password@localhost:5432/naebak_complaints

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Cloud Storage
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# خدمات أخرى
AUTH_SERVICE_URL=http://localhost:8001
CONTENT_SERVICE_URL=http://localhost:8002
STATISTICS_SERVICE_URL=http://localhost:8003
```

## 🤝 المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. **Fork** المشروع
2. إنشاء branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

### إرشادات المساهمة

- اتبع معايير PEP 8 للكود
- اكتب اختبارات للمميزات الجديدة
- حدث التوثيق عند الحاجة
- استخدم رسائل commit واضحة

### تشغيل اختبارات الجودة

```bash
# فحص جودة الكود
flake8 .
black --check .
isort --check-only .

# فحص الأمان
bandit -r .
safety check
```

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 التواصل والدعم

- **البريد الإلكتروني**: support@naebak.com
- **الموقع الرسمي**: https://naebak.com
- **التوثيق**: https://docs.naebak.com
- **المشاكل**: [GitHub Issues](https://github.com/alcounsol17/naebak-complaints-service/issues)

## 🙏 شكر وتقدير

- فريق تطوير نائبك.كوم
- مجتمع Django و Python
- جميع المساهمين في المشروع

---

**نائبك.كوم** - منصة التواصل بين المواطنين والنواب 🇪🇬
