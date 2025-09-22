/**
 * ملف JavaScript الرئيسي لخدمة الشكاوى - نائبك.كوم
 */

// إعدادات عامة
const CONFIG = {
    API_BASE_URL: '/api/v1',
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    MAX_ATTACHMENTS: 10,
    ALLOWED_FILE_TYPES: [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ],
    YOUTUBE_REGEX: /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
};

// وظائف مساعدة عامة
const Utils = {
    /**
     * استخراج معرف فيديو يوتيوب من الرابط
     */
    extractYouTubeId: function(url) {
        if (!url) return null;
        const match = url.match(CONFIG.YOUTUBE_REGEX);
        return (match && match[2].length === 11) ? match[2] : null;
    },

    /**
     * تنسيق حجم الملف
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * التحقق من نوع الملف
     */
    isValidFileType: function(fileType) {
        return CONFIG.ALLOWED_FILE_TYPES.includes(fileType);
    },

    /**
     * التحقق من حجم الملف
     */
    isValidFileSize: function(fileSize) {
        return fileSize <= CONFIG.MAX_FILE_SIZE;
    },

    /**
     * تنسيق التاريخ
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ar-EG', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * إظهار رسالة تنبيه
     */
    showAlert: function(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // إضافة التنبيه في أعلى الصفحة
        const container = $('.container').first();
        container.prepend(alertHtml);

        // إزالة التنبيه تلقائياً بعد 5 ثوان
        setTimeout(() => {
            $('.alert').fadeOut();
        }, 5000);
    },

    /**
     * تأخير تنفيذ الدالة (debounce)
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * الحصول على CSRF token
     */
    getCSRFToken: function() {
        return $('[name=csrfmiddlewaretoken]').val() || 
               $('meta[name=csrf-token]').attr('content');
    }
};

// إدارة الملفات المرفقة
const FileManager = {
    selectedFiles: [],
    maxFiles: CONFIG.MAX_ATTACHMENTS,

    /**
     * إضافة ملفات جديدة
     */
    addFiles: function(files) {
        for (let i = 0; i < files.length && this.selectedFiles.length < this.maxFiles; i++) {
            const file = files[i];
            
            if (!this.validateFile(file)) {
                continue;
            }

            this.selectedFiles.push(file);
            this.renderFilePreview(file);
        }

        this.updateFileCounter();
    },

    /**
     * التحقق من صحة الملف
     */
    validateFile: function(file) {
        if (!Utils.isValidFileType(file.type)) {
            Utils.showAlert(`نوع الملف غير مدعوم: ${file.name}`, 'error');
            return false;
        }

        if (!Utils.isValidFileSize(file.size)) {
            Utils.showAlert(`حجم الملف كبير جداً: ${file.name}`, 'error');
            return false;
        }

        // التحقق من عدم وجود ملف بنفس الاسم
        if (this.selectedFiles.some(f => f.name === file.name)) {
            Utils.showAlert(`الملف موجود بالفعل: ${file.name}`, 'warning');
            return false;
        }

        return true;
    },

    /**
     * عرض معاينة الملف
     */
    renderFilePreview: function(file) {
        const fileId = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const fileIcon = this.getFileIcon(file.type);
        
        const previewHtml = `
            <div class="attachment-item" data-file-id="${fileId}" data-file-name="${file.name}">
                <button type="button" class="attachment-remove" onclick="FileManager.removeFile('${fileId}')">×</button>
                <i class="${fileIcon} fa-2x mb-2"></i>
                <p class="small mb-0 text-truncate" title="${file.name}">${file.name}</p>
                <small class="text-muted">${Utils.formatFileSize(file.size)}</small>
            </div>
        `;

        $('#attachment-preview').append(previewHtml);
    },

    /**
     * الحصول على أيقونة الملف
     */
    getFileIcon: function(fileType) {
        if (fileType.startsWith('image/')) {
            return 'fas fa-image text-primary';
        } else if (fileType === 'application/pdf') {
            return 'fas fa-file-pdf text-danger';
        } else if (fileType.includes('word')) {
            return 'fas fa-file-word text-primary';
        } else {
            return 'fas fa-file text-secondary';
        }
    },

    /**
     * إزالة ملف
     */
    removeFile: function(fileId) {
        const fileElement = $(`.attachment-item[data-file-id="${fileId}"]`);
        const fileName = fileElement.data('file-name');
        
        // إزالة الملف من القائمة
        this.selectedFiles = this.selectedFiles.filter(f => f.name !== fileName);
        
        // إزالة العنصر من الواجهة
        fileElement.remove();
        
        this.updateFileCounter();
    },

    /**
     * تحديث عداد الملفات
     */
    updateFileCounter: function() {
        const count = this.selectedFiles.length;
        const counterText = `${count} / ${this.maxFiles} ملف`;
        
        $('#file-counter').text(counterText);
        
        // تغيير لون العداد حسب العدد
        if (count >= this.maxFiles) {
            $('#file-counter').addClass('text-danger').removeClass('text-warning text-success');
        } else if (count >= this.maxFiles * 0.8) {
            $('#file-counter').addClass('text-warning').removeClass('text-danger text-success');
        } else {
            $('#file-counter').addClass('text-success').removeClass('text-danger text-warning');
        }
    },

    /**
     * مسح جميع الملفات
     */
    clearAll: function() {
        this.selectedFiles = [];
        $('#attachment-preview').empty();
        this.updateFileCounter();
    },

    /**
     * الحصول على الملفات المحددة
     */
    getFiles: function() {
        return this.selectedFiles;
    }
};

// إدارة معاينة يوتيوب
const YouTubeManager = {
    /**
     * معاينة فيديو يوتيوب
     */
    previewVideo: function(url) {
        const videoId = Utils.extractYouTubeId(url);
        const previewContainer = $('#youtube-preview');
        
        if (videoId) {
            const embedUrl = `https://www.youtube.com/embed/${videoId}`;
            const embedHtml = `
                <iframe width="100%" height="200" src="${embedUrl}" 
                        frameborder="0" allowfullscreen></iframe>
            `;
            previewContainer.html(embedHtml).show();
            return true;
        } else {
            previewContainer.hide();
            return false;
        }
    },

    /**
     * مسح المعاينة
     */
    clearPreview: function() {
        $('#youtube-preview').hide().empty();
    }
};

// إدارة النماذج
const FormManager = {
    /**
     * إرسال نموذج الشكوى
     */
    submitComplaint: function(formData, files) {
        const data = new FormData();
        
        // إضافة بيانات النموذج
        for (const [key, value] of Object.entries(formData)) {
            if (value !== null && value !== undefined && value !== '') {
                data.append(key, value);
            }
        }
        
        // إضافة الملفات
        files.forEach(file => {
            data.append('attachments', file);
        });
        
        // إضافة CSRF token
        data.append('csrfmiddlewaretoken', Utils.getCSRFToken());
        
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/`,
            type: 'POST',
            data: data,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * تحديث الشكوى
     */
    updateComplaint: function(complaintId, formData) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/`,
            type: 'PATCH',
            data: formData,
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * إسناد الشكوى
     */
    assignComplaint: function(complaintId, representativeData) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/assign/`,
            type: 'POST',
            data: representativeData,
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * قبول الشكوى
     */
    acceptComplaint: function(complaintId) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/accept/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * رفض الشكوى
     */
    rejectComplaint: function(complaintId, reason) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/reject/`,
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * تعليق الشكوى
     */
    holdComplaint: function(complaintId, reason) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/hold/`,
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    },

    /**
     * الرد على الشكوى
     */
    respondToComplaint: function(complaintId, responseData) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/respond/`,
            type: 'POST',
            data: responseData,
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    }
};

// إدارة البيانات
const DataManager = {
    /**
     * تحميل الشكاوى
     */
    loadComplaints: function(filters = {}) {
        const params = new URLSearchParams();
        
        for (const [key, value] of Object.entries(filters)) {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        }
        
        const url = `${CONFIG.API_BASE_URL}/complaints/?${params.toString()}`;
        
        return $.ajax({
            url: url,
            type: 'GET'
        });
    },

    /**
     * تحميل تفاصيل الشكوى
     */
    loadComplaintDetails: function(complaintId) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/${complaintId}/`,
            type: 'GET'
        });
    },

    /**
     * تحميل الإحصائيات
     */
    loadStatistics: function() {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/statistics/`,
            type: 'GET'
        });
    },

    /**
     * تحميل التصنيفات
     */
    loadCategories: function() {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/categories/`,
            type: 'GET'
        });
    },

    /**
     * تصدير الشكاوى
     */
    exportComplaints: function(exportData) {
        return $.ajax({
            url: `${CONFIG.API_BASE_URL}/complaints/export/`,
            type: 'POST',
            data: exportData,
            headers: {
                'X-CSRFToken': Utils.getCSRFToken()
            }
        });
    }
};

// إدارة الواجهة
const UIManager = {
    /**
     * إظهار مؤشر التحميل
     */
    showLoading: function(element) {
        const loadingHtml = `
            <div class="text-center py-4 loading-container">
                <div class="loading-spinner"></div>
                <p class="mt-2">جاري التحميل...</p>
            </div>
        `;
        $(element).html(loadingHtml);
    },

    /**
     * إخفاء مؤشر التحميل
     */
    hideLoading: function(element) {
        $(element).find('.loading-container').remove();
    },

    /**
     * إظهار رسالة فارغة
     */
    showEmptyMessage: function(element, message, icon = 'fas fa-inbox') {
        const emptyHtml = `
            <div class="text-center py-4">
                <i class="${icon} fa-3x text-muted mb-3"></i>
                <p>${message}</p>
            </div>
        `;
        $(element).html(emptyHtml);
    },

    /**
     * إظهار رسالة خطأ
     */
    showErrorMessage: function(element, message) {
        const errorHtml = `
            <div class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">إعادة المحاولة</button>
            </div>
        `;
        $(element).html(errorHtml);
    },

    /**
     * تحديث الإحصائيات
     */
    updateStatistics: function(stats) {
        for (const [key, value] of Object.entries(stats)) {
            $(`.stat-number[data-stat="${key}"]`).text(value);
        }
    },

    /**
     * تحديث عداد الزوار
     */
    updateVisitorCounter: function() {
        // محاكاة تحديث عداد الزوار
        const currentCount = parseInt($('#visitor-count').text().replace(/,/g, '')) || 0;
        const newCount = currentCount + Math.floor(Math.random() * 10) + 1;
        $('#visitor-count').text(newCount.toLocaleString());
    }
};

// إعدادات الصفحة عند التحميل
$(document).ready(function() {
    // تحديث عداد الزوار كل 30 ثانية
    setInterval(UIManager.updateVisitorCounter, 30000);
    
    // إعداد معالجات الأحداث العامة
    setupGlobalEventHandlers();
    
    // تحميل البيانات الأولية
    loadInitialData();
});

/**
 * إعداد معالجات الأحداث العامة
 */
function setupGlobalEventHandlers() {
    // إعداد رفع الملفات بالسحب والإفلات
    $(document).on('dragover', '.file-upload-area', function(e) {
        e.preventDefault();
        $(this).addClass('dragover');
    });
    
    $(document).on('dragleave', '.file-upload-area', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
    });
    
    $(document).on('drop', '.file-upload-area', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        FileManager.addFiles(files);
    });
    
    // إعداد النقر على منطقة رفع الملفات
    $(document).on('click', '.file-upload-area', function() {
        $(this).find('input[type="file"]').click();
    });
    
    // إعداد تغيير ملف الإدخال
    $(document).on('change', 'input[type="file"]', function() {
        FileManager.addFiles(this.files);
    });
    
    // إعداد معاينة يوتيوب
    $(document).on('input', 'input[name="youtube_link"]', function() {
        const url = $(this).val();
        if (url) {
            YouTubeManager.previewVideo(url);
        } else {
            YouTubeManager.clearPreview();
        }
    });
    
    // إعداد عداد الأحرف
    $(document).on('input', 'textarea[maxlength]', function() {
        const maxLength = parseInt($(this).attr('maxlength'));
        const currentLength = $(this).val().length;
        const counterId = $(this).data('counter') || $(this).attr('id') + '-count';
        
        $(`#${counterId}`).text(currentLength);
        
        if (currentLength > maxLength * 0.9) {
            $(`#${counterId}`).addClass('text-danger').removeClass('text-warning');
        } else if (currentLength > maxLength * 0.8) {
            $(`#${counterId}`).addClass('text-warning').removeClass('text-danger');
        } else {
            $(`#${counterId}`).removeClass('text-danger text-warning');
        }
    });
    
    // إعداد تأكيد الحذف
    $(document).on('click', '[data-confirm]', function(e) {
        const message = $(this).data('confirm');
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });
    
    // إعداد التحديث التلقائي للصفحة
    $(document).on('click', '[data-refresh]', function() {
        const target = $(this).data('refresh');
        if (target === 'page') {
            location.reload();
        } else {
            // تحديث عنصر محدد
            $(target).trigger('refresh');
        }
    });
}

/**
 * تحميل البيانات الأولية
 */
function loadInitialData() {
    // تحميل التصنيفات إذا كان هناك عنصر لها
    if ($('#category').length > 0) {
        DataManager.loadCategories()
            .done(function(categories) {
                const categorySelect = $('#category');
                categorySelect.empty().append('<option value="">اختر التصنيف</option>');
                
                categories.forEach(category => {
                    categorySelect.append(`<option value="${category.id}">${category.name}</option>`);
                });
            })
            .fail(function() {
                console.error('فشل في تحميل التصنيفات');
            });
    }
    
    // تحميل الإحصائيات إذا كان هناك عناصر لها
    if ($('.stat-number').length > 0) {
        DataManager.loadStatistics()
            .done(function(stats) {
                UIManager.updateStatistics(stats);
            })
            .fail(function() {
                console.error('فشل في تحميل الإحصائيات');
            });
    }
}

// تصدير الوظائف للاستخدام العام
window.Utils = Utils;
window.FileManager = FileManager;
window.YouTubeManager = YouTubeManager;
window.FormManager = FormManager;
window.DataManager = DataManager;
window.UIManager = UIManager;
