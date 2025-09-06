/**
 * Utilities Module
 * Common utility functions and helpers used across the application
 */

class Utils {
    constructor() {
        this.init();
    }

    init() {
        this.setupGlobalHelpers();
        this.setupEventHelpers();
        this.setupFormHelpers();
    }

    setupGlobalHelpers() {
        // Add utility methods to window for global access
        window.utils = {
            formatDate: this.formatDate.bind(this),
            formatNumber: this.formatNumber.bind(this),
            debounce: this.debounce.bind(this),
            throttle: this.throttle.bind(this),
            generateId: this.generateId.bind(this),
            showToast: this.showToast.bind(this),
            showAlert: this.showAlert.bind(this),
            confirmAction: this.confirmAction.bind(this),
            sanitizeHtml: this.sanitizeHtml.bind(this),
            validateEmail: this.validateEmail.bind(this),
            copyToClipboard: this.copyToClipboard.bind(this),
            downloadFile: this.downloadFile.bind(this),
            formatFileSize: this.formatFileSize.bind(this),
            truncateText: this.truncateText.bind(this),
            slugify: this.slugify.bind(this),
            getTimeSince: this.getTimeSince.bind(this),
            getMaturityLevel: this.getMaturityLevel.bind(this),
            calculateProgress: this.calculateProgress.bind(this),
            // Loading utilities
            showLoading: this.showLoading.bind(this),
            hideLoading: this.hideLoading.bind(this),
            // Form utilities
            restoreFormData: this.restoreFormData.bind(this),
            clearFormAutoSave: this.clearFormAutoSave.bind(this),
            autoSaveForm: this.autoSaveForm.bind(this)
        };
    }

    setupEventHelpers() {
        // Delegate common events
        document.addEventListener('click', (e) => {
            // Copy to clipboard
            if (e.target.matches('[data-copy]')) {
                e.preventDefault();
                const text = e.target.dataset.copy || e.target.textContent;
                this.copyToClipboard(text);
            }

            // Confirm actions
            if (e.target.matches('[data-confirm]')) {
                e.preventDefault();
                const message = e.target.dataset.confirm;
                this.confirmAction(message).then(confirmed => {
                    if (confirmed) {
                        // Trigger the original action
                        if (e.target.href) {
                            window.location.href = e.target.href;
                        } else if (e.target.form) {
                            e.target.form.submit();
                        }
                    }
                });
            }

            // Tooltip triggers
            if (e.target.matches('[data-bs-toggle="tooltip"]')) {
                this.initializeTooltip(e.target);
            }
        });

        // Auto-dismiss alerts
        document.addEventListener('DOMContentLoaded', () => {
            this.setupAutoDismissAlerts();
        });
    }

    setupFormHelpers() {
        // Form validation helpers
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.needs-validation')) {
                if (!e.target.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                e.target.classList.add('was-validated');
            }
        });

        // Auto-save functionality
        document.addEventListener('input', this.debounce((e) => {
            if (e.target.matches('[data-auto-save]')) {
                this.autoSaveForm(e.target.form);
            }
        }, 1000));
    }

    // Date and Time Utilities
    formatDate(date, format = 'short') {
        if (!date) return '';
        
        const d = new Date(date);
        const options = {
            short: { year: 'numeric', month: 'short', day: 'numeric' },
            long: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' },
            time: { hour: '2-digit', minute: '2-digit' },
            datetime: { 
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            },
            relative: null // Special case for relative time
        };

        if (format === 'relative') {
            return this.getTimeSince(d);
        }

        return d.toLocaleDateString('en-US', options[format] || options.short);
    }

    getTimeSince(date) {
        const now = new Date();
        const diffMs = now - new Date(date);
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        
        return this.formatDate(date, 'short');
    }

    // Number and Text Formatting
    formatNumber(number, type = 'default') {
        if (number === null || number === undefined) return '';
        
        const num = parseFloat(number);
        if (isNaN(num)) return number;

        switch (type) {
            case 'percent':
                return `${num.toFixed(1)}%`;
            case 'decimal':
                return num.toFixed(2);
            case 'integer':
                return Math.round(num).toLocaleString();
            case 'currency':
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD'
                }).format(num);
            default:
                return num.toLocaleString();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    truncateText(text, maxLength = 100, suffix = '...') {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength - suffix.length) + suffix;
    }

    slugify(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // Function Utilities
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ID Generation
    generateId(prefix = 'id') {
        return `${prefix}_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
    }

    // UI Helpers
    showToast(message, type = 'info', duration = 5000) {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${this.sanitizeHtml(message)}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        const toast = toastElement.firstElementChild;
        toastContainer.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, { 
            autohide: duration > 0,
            delay: duration 
        });
        bsToast.show();

        // Remove from DOM after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        return bsToast;
    }

    showAlert(message, type = 'info', title = null, dismissible = true) {
        const alertId = this.generateId('alert');
        const alertHtml = `
            <div class="alert alert-${type} ${dismissible ? 'alert-dismissible' : ''} fade show" role="alert" id="${alertId}">
                ${title ? `<h4 class="alert-heading">${this.sanitizeHtml(title)}</h4>` : ''}
                ${this.sanitizeHtml(message)}
                ${dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}
            </div>
        `;

        let alertContainer = document.querySelector('.alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.className = 'alert-container';
            const main = document.querySelector('main') || document.body;
            main.insertAdjacentElement('afterbegin', alertContainer);
        }

        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        return document.getElementById(alertId);
    }

    async confirmAction(message, title = 'Confirm Action') {
        return new Promise((resolve) => {
            const modalId = this.generateId('confirm-modal');
            const modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${this.sanitizeHtml(title)}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                ${this.sanitizeHtml(message)}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary confirm-action">Confirm</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = document.getElementById(modalId);
            const bsModal = new bootstrap.Modal(modal);

            modal.querySelector('.confirm-action').addEventListener('click', () => {
                resolve(true);
                bsModal.hide();
            });

            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });

            bsModal.show();
        });
    }

    // Validation Utilities
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    // Clipboard Utilities
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                textArea.remove();
            }
            this.showToast('Copied to clipboard!', 'success', 2000);
            return true;
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            this.showToast('Failed to copy to clipboard', 'danger', 3000);
            return false;
        }
    }

    // File Utilities
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        if (filename) {
            link.download = filename;
        }
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Assessment-specific Utilities
    getMaturityLevel(score) {
        if (score < 20) return { level: 'Initial', class: 'danger', description: 'Ad-hoc and unpredictable processes' };
        if (score < 40) return { level: 'Developing', class: 'warning', description: 'Some processes defined but not consistently followed' };
        if (score < 60) return { level: 'Defined', class: 'info', description: 'Processes are well-defined and documented' };
        if (score < 80) return { level: 'Managed', class: 'primary', description: 'Processes are measured and controlled' };
        return { level: 'Optimizing', class: 'success', description: 'Focus on continuous process improvement' };
    }

    calculateProgress(current, total) {
        if (!total || total === 0) return 0;
        return Math.round((current / total) * 100);
    }

    // Form Utilities
    autoSaveForm(form) {
        if (!form) return;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const key = `autosave_${form.id || 'form'}`;
        
        try {
            localStorage.setItem(key, JSON.stringify({
                data: data,
                timestamp: Date.now()
            }));
        } catch (error) {
            console.warn('Auto-save failed:', error);
        }
    }

    restoreFormData(form) {
        if (!form) return false;

        const key = `autosave_${form.id || 'form'}`;
        try {
            const saved = localStorage.getItem(key);
            if (!saved) return false;

            const { data, timestamp } = JSON.parse(saved);
            
            // Only restore if less than 24 hours old
            if (Date.now() - timestamp > 24 * 60 * 60 * 1000) {
                localStorage.removeItem(key);
                return false;
            }

            Object.entries(data).forEach(([name, value]) => {
                const field = form.querySelector(`[name="${name}"]`);
                if (field) {
                    if (field.type === 'checkbox' || field.type === 'radio') {
                        field.checked = field.value === value;
                    } else {
                        field.value = value;
                    }
                }
            });

            return true;
        } catch (error) {
            console.warn('Form restore failed:', error);
            return false;
        }
    }

    clearFormAutoSave(form) {
        if (!form) return;
        const key = `autosave_${form.id || 'form'}`;
        localStorage.removeItem(key);
    }

    // Bootstrap Component Helpers
    initializeTooltip(element) {
        if (element.hasAttribute('data-tooltip-initialized')) return;
        
        // Dispose any existing tooltip instance
        const existingTooltip = bootstrap.Tooltip.getInstance(element);
        if (existingTooltip) {
            existingTooltip.dispose();
        }
        
        new bootstrap.Tooltip(element);
        element.setAttribute('data-tooltip-initialized', 'true');
    }

    initializeTooltips() {
        if (typeof bootstrap === 'undefined') return;
        
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            this.initializeTooltip(element);
        });
    }

    initializePopovers() {
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(element => {
            if (!element.hasAttribute('data-popover-initialized')) {
                new bootstrap.Popover(element);
                element.setAttribute('data-popover-initialized', 'true');
            }
        });
    }

    setupAutoDismissAlerts() {
        document.querySelectorAll('.alert[data-auto-dismiss]').forEach(alert => {
            const delay = parseInt(alert.dataset.autoDismiss) || 5000;
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }, delay);
        });
    }

    // Loading States
    showLoading(element, text = 'Loading...') {
        if (!element) return;

        // Clear any existing loading overlays first to prevent duplicates
        this.hideLoading(element);

        const spinner = document.createElement('div');
        spinner.className = 'loading-overlay d-flex align-items-center justify-content-center';
        spinner.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.8);
            z-index: 9999;
        `;
        spinner.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="small text-muted">${this.sanitizeHtml(text)}</div>
            </div>
        `;

        const container = element.querySelector('.loading-container') || element;
        container.style.position = 'relative';
        container.appendChild(spinner);

        return spinner;
    }

    hideLoading(element) {
        if (!element) return;
        
        const container = element.querySelector('.loading-container') || element;
        const overlays = container.querySelectorAll('.loading-overlay');
        
        if (overlays.length > 0) {
            overlays.forEach(overlay => overlay.remove());
        }
        
        // Also remove any orphaned loading overlays from the entire document if element is body
        if (element === document.body) {
            const orphanedOverlays = document.querySelectorAll('.loading-overlay');
            orphanedOverlays.forEach(overlay => overlay.remove());
        }
    }

    // Local Storage Utilities
    setStorageItem(key, value, expirationHours = null) {
        const item = {
            value: value,
            timestamp: Date.now()
        };

        if (expirationHours) {
            item.expiry = Date.now() + (expirationHours * 60 * 60 * 1000);
        }

        try {
            localStorage.setItem(key, JSON.stringify(item));
            return true;
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
            return false;
        }
    }

    getStorageItem(key) {
        try {
            const item = localStorage.getItem(key);
            if (!item) return null;

            const parsed = JSON.parse(item);
            
            // Check expiration
            if (parsed.expiry && Date.now() > parsed.expiry) {
                localStorage.removeItem(key);
                return null;
            }

            return parsed.value;
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
            return null;
        }
    }

    removeStorageItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Failed to remove from localStorage:', error);
            return false;
        }
    }

    // URL Utilities
    updateUrlParams(params) {
        const url = new URL(window.location);
        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined || value === '') {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        window.history.replaceState({}, '', url);
    }

    getUrlParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    }

    // Device Detection
    isMobile() {
        return window.innerWidth <= 768;
    }

    isTablet() {
        return window.innerWidth > 768 && window.innerWidth <= 1024;
    }

    isDesktop() {
        return window.innerWidth > 1024;
    }

    // Performance Utilities
    measurePerformance(name, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    }

    async measureAsyncPerformance(name, fn) {
        const start = performance.now();
        const result = await fn();
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    }
}

// Auto-initialize utilities
document.addEventListener('DOMContentLoaded', function() {
    window.utilsInstance = new Utils();
    
    // Initialize popovers
    window.utilsInstance.initializePopovers();
    
    // Setup keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S for save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            const activeForm = document.querySelector('form:focus-within');
            if (activeForm && activeForm.dataset.autoSave !== 'false') {
                e.preventDefault();
                window.utilsInstance.autoSaveForm(activeForm);
                window.utils.showToast('Form auto-saved', 'success', 2000);
            }
        }
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
