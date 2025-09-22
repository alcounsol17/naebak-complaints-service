# Dockerfile لخدمة الشكاوى - نائبك.كوم

FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=complaints_service.settings

# تعيين مجلد العمل
WORKDIR /app

# تثبيت متطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع
COPY . .

# إنشاء مجلدات للملفات الثابتة والمرفقات
RUN mkdir -p /app/staticfiles /app/media/attachments

# تجميع الملفات الثابتة
RUN python manage.py collectstatic --noinput

# إنشاء مستخدم غير جذر
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# فتح المنفذ
EXPOSE 8000

# إعداد فحص الصحة
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# تشغيل الخادم
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "complaints_service.wsgi:application"]
