/**
 * Main Application Entry Point
 * Initializes all modules and provides global application management
 */

class MaturityAssessmentApp {
    constructor() {
        this.modules = new Map();
        this.config = {
            debug: false,
            apiTimeout: 30000,
            autoSaveInterval: 30000,
            chartRefreshInterval: 300000, // 5 minutes
            maxRetries: 3,
            retryDelay: 1000
        };
        this.isInitialized = false;
        
        this.init();
    }

    async init() {
        try {
            // Initialize core utilities first
            await this.initializeUtilities();
            
            // Load configuration
            await this.loadConfiguration();
            
            // Initialize modules
            await this.initializeModules();
            
            // Setup global event handlers
            this.setupGlobalEvents();
            
            // Setup error handling
            this.setupErrorHandling();
            
            // Initialize page-specific functionality
            this.initializePageSpecific();
            
            // Mark as initialized
            this.isInitialized = true;
            
            // Dispatch ready event
            this.dispatchEvent('app:ready');
            
            this.log('Application initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.handleInitializationError(error);
        }
    }

    async initializeUtilities() {
        // Wait for utilities to be available
        let retries = 0;
        const maxRetries = 10;
        
        while (typeof window.utils === 'undefined' && retries < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms
            retries++;
        }
        
        if (typeof window.utils === 'undefined') {
            throw new Error('Utilities module not loaded after waiting');
        }
        
        this.utils = window.utils;
        this.log('Utilities initialized');
    }

    async loadConfiguration() {
        try {
            // Try to load configuration from server
            const response = await fetch('/api/config', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const serverConfig = await response.json();
                this.config = { ...this.config, ...serverConfig };
            }
        } catch (error) {
            this.log('Failed to load server configuration, using defaults');
        }

        // Load configuration from meta tags
        const metaConfig = this.loadMetaConfiguration();
        this.config = { ...this.config, ...metaConfig };
        
        this.log('Configuration loaded', this.config);
    }

    loadMetaConfiguration() {
        const config = {};
        const metaTags = document.querySelectorAll('meta[name^="app-"]');
        
        metaTags.forEach(tag => {
            const key = tag.name.replace('app-', '').replace(/-/g, '_');
            let value = tag.content;
            
            // Try to parse as JSON for complex values
            try {
                if (value.startsWith('{') || value.startsWith('[') || value === 'true' || value === 'false') {
                    value = JSON.parse(value);
                } else if (!isNaN(value) && value !== '') {
                    value = Number(value);
                }
            } catch (e) {
                // Keep as string
            }
            
            config[key] = value;
        });
        
        return config;
    }

    async initializeModules() {
        const modulesToLoad = [];

        // Assessment module
        if (this.isPageType('assessment')) {
            modulesToLoad.push(this.initializeAssessmentModule());
        }

        // Charts module (if Chart.js is available and needed for results page)
        if (typeof Chart !== 'undefined' && this.isPageType('assessment')) {
            modulesToLoad.push(this.initializeChartsModule());
        }

        // Wait for all modules to initialize
        await Promise.all(modulesToLoad);
        
        this.log(`Initialized ${modulesToLoad.length} modules`);
    }

    async initializeAssessmentModule() {
        if (typeof AssessmentManager !== 'undefined') {
            const assessmentManager = new AssessmentManager();
            this.modules.set('assessment', assessmentManager);
            this.log('Assessment module initialized');
        }
    }

    async initializeChartsModule() {
        if (typeof window.chartManager !== 'undefined') {
            this.modules.set('charts', window.chartManager);
            this.log('Charts module initialized');
        }
    }

    setupGlobalEvents() {
        // Handle AJAX errors globally
        document.addEventListener('ajaxError', (e) => {
            this.handleAjaxError(e.detail);
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });

        // Handle navigation
        document.addEventListener('click', (e) => {
            // Exclude dropdown toggles and other non-navigation elements
            if (e.target.matches('.nav-link, .btn-nav') && 
                !e.target.matches('[data-bs-toggle="dropdown"]') &&
                !e.target.closest('[data-bs-toggle="dropdown"]') &&
                !e.target.matches('.dropdown-toggle')) {
                this.handleNavigation(e);
            }
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            this.handleOnlineStatus(true);
        });

        window.addEventListener('offline', () => {
            this.handleOnlineStatus(false);
        });

        // Handle window resize
        const resizeHandler = this.safeUtils('debounce', 
            () => this.handleWindowResize(), 
            250
        ) || (() => this.handleWindowResize());
        
        window.addEventListener('resize', resizeHandler);

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        this.log('Global events setup complete');
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (e) => {
            this.handleError('JavaScript Error', e.error, {
                filename: e.filename,
                lineno: e.lineno,
                colno: e.colno
            });
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (e) => {
            this.handleError('Unhandled Promise Rejection', e.reason);
        });

        this.log('Error handling setup complete');
    }

    initializePageSpecific() {
        const pageType = this.getPageType();
        const pageMethod = `initialize${pageType}Page`;
        
        if (typeof this[pageMethod] === 'function') {
            this[pageMethod]();
            this.log(`Page-specific initialization for ${pageType} complete`);
        }
    }

    // Page-specific initializers
    initializeAssessmentPage() {
        // Restore auto-saved data
        const assessmentForm = document.querySelector('#assessment-form');
        if (assessmentForm) {
            const restored = this.safeUtils('restoreFormData', assessmentForm);
            if (restored) {
                this.safeUtils('showToast', 'Previous session data restored', 'info');
            }
        }

        // Setup progress tracking
        this.setupAssessmentProgress();
    }

    initializeHomePage() {
        // Initialize home page functionality
        this.log('Home page initialized');
    }

    initializeDefaultPage() {
        // Default page initialization
        this.log('Default page initialized');
    }

    // Utility methods
    isPageType(type) {
        return document.body.classList.contains(`page-${type}`) || 
               document.querySelector(`[data-page="${type}"]`) !== null;
    }

    getPageType() {
        const bodyClasses = Array.from(document.body.classList);
        const pageClass = bodyClasses.find(cls => cls.startsWith('page-'));
        
        if (pageClass) {
            return pageClass.replace('page-', '').split('-').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join('');
        }
        
        return 'Default';
    }

    // Safe utility methods
    safeUtils(method, ...args) {
        if (this.utils && typeof this.utils[method] === 'function') {
            return this.utils[method](...args);
        }
        console.warn(`Utils method '${method}' not available`);
        return null;
    }

    // Event handlers
    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';

        try {
            this.safeUtils('showLoading', form);
            
            const response = await this.fetch(url, {
                method: method,
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.handleAjaxFormSuccess(form, result);
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.handleAjaxFormError(form, error);
        } finally {
            this.safeUtils('hideLoading', form);
        }
    }

    handleAjaxFormSuccess(form, result) {
        if (result.message) {
            this.safeUtils('showToast', result.message, result.type || 'success');
        }

        if (result.redirect) {
            window.location.href = result.redirect;
        } else if (result.reload) {
            window.location.reload();
        }

        // Clear auto-save data
        this.safeUtils('clearFormAutoSave', form);

        this.dispatchEvent('form:success', { form, result });
    }

    handleAjaxFormError(form, error) {
        this.handleError('Form Submission Error', error, { form: form.id });
        this.safeUtils('showToast', 'Form submission failed. Please try again.', 'danger');
        this.dispatchEvent('form:error', { form, error });
    }

    handleNavigation(e) {
        // Add loading state for navigation only for actual page changes
        if (!e.target.dataset.noLoading && (e.target.href || e.target.form)) {
            // Clear any existing loading overlays first
            this.safeUtils('hideLoading', document.body);
            // Add new loading overlay
            this.safeUtils('showLoading', document.body, 'Loading page...');
        }
    }

    handlePageHidden() {
        // Pause auto-refresh timers
        this.modules.forEach(module => {
            if (module.pauseAutoRefresh) {
                module.pauseAutoRefresh();
            }
        });
        
        this.log('Page hidden - paused auto-refresh');
    }

    handlePageVisible() {
        // Resume auto-refresh timers
        this.modules.forEach(module => {
            if (module.resumeAutoRefresh) {
                module.resumeAutoRefresh();
            }
        });
        
        this.log('Page visible - resumed auto-refresh');
    }

    handleOnlineStatus(online) {
        if (online) {
            this.safeUtils('showToast', 'Connection restored', 'success', 3000);
            // Retry failed requests
            this.retryFailedRequests();
        } else {
            this.safeUtils('showToast', 'Connection lost - working offline', 'warning', 5000);
        }
        
        this.dispatchEvent('network:status', { online });
    }

    handleWindowResize() {
        // Notify modules about resize
        this.modules.forEach(module => {
            if (module.handleResize) {
                module.handleResize();
            }
        });
        
        this.dispatchEvent('window:resize');
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#global-search, .search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals/dropdowns
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const bsModal = bootstrap.Modal.getInstance(openModal);
                if (bsModal) bsModal.hide();
            }
        }
    }

    handleAjaxError(error) {
        this.handleError('AJAX Error', error);
    }

    handleError(type, error, context = {}) {
        const errorInfo = {
            type,
            message: error?.message || error,
            stack: error?.stack,
            context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // Log to console
        console.error(`${type}:`, errorInfo);

        // Send to error reporting service if configured
        if (this.config.errorReporting) {
            this.reportError(errorInfo);
        }

        // Store locally for debugging
        this.storeError(errorInfo);

        this.dispatchEvent('app:error', errorInfo);
    }

    handleInitializationError(error) {
        // Show critical error message
        const errorHtml = `
            <div class="alert alert-danger m-3" role="alert">
                <h4 class="alert-heading">Application Failed to Initialize</h4>
                <p>The application encountered an error during startup. Please refresh the page to try again.</p>
                <hr>
                <p class="mb-0">
                    <small>Error: ${this.safeUtils('sanitizeHtml', error.message) || error.message}</small>
                </p>
                <button class="btn btn-outline-danger btn-sm mt-2" onclick="window.location.reload()">
                    Refresh Page
                </button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', errorHtml);
    }

    // Helper methods
    setupAssessmentProgress() {
        const progressBar = document.querySelector('.assessment-progress');
        if (progressBar) {
            // Update progress based on completed questions
            this.updateAssessmentProgress();
        }
    }

    updateAssessmentProgress() {
        const form = document.querySelector('#assessment-form');
        if (!form) return;

        const questions = form.querySelectorAll('.question');
        const answered = form.querySelectorAll('.question.answered').length;
        const progress = this.safeUtils('calculateProgress', answered, questions.length) || Math.round((answered / questions.length) * 100);

        const progressBar = document.querySelector('.assessment-progress .progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${progress}%`;
        }
    }

    // Network utilities
    async fetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': this.getCSRFToken()
            },
            timeout: this.config.apiTimeout
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        // Merge headers
        if (options.headers) {
            finalOptions.headers = { ...defaultOptions.headers, ...options.headers };
        }

        return await this.fetchWithRetry(url, finalOptions);
    }

    async fetchWithRetry(url, options, retryCount = 0) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), options.timeout);

            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;

        } catch (error) {
            if (retryCount < this.config.maxRetries && !error.name === 'AbortError') {
                await this.delay(this.config.retryDelay * (retryCount + 1));
                return this.fetchWithRetry(url, options, retryCount + 1);
            }
            throw error;
        }
    }

    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    retryFailedRequests() {
        // Implementation would depend on how failed requests are stored
        this.log('Retrying failed requests...');
    }

    // Error reporting
    async reportError(errorInfo) {
        try {
            await this.fetch('/api/errors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorInfo)
            });
        } catch (error) {
            console.warn('Failed to report error:', error);
        }
    }

    storeError(errorInfo) {
        try {
            const errors = JSON.parse(localStorage.getItem('app_errors') || '[]');
            errors.push(errorInfo);
            
            // Keep only last 10 errors
            if (errors.length > 10) {
                errors.splice(0, errors.length - 10);
            }
            
            localStorage.setItem('app_errors', JSON.stringify(errors));
        } catch (error) {
            console.warn('Failed to store error locally:', error);
        }
    }

    // Template engine (basic)
    templateEngine(template, data) {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] || '';
        });
    }

    // Event system
    dispatchEvent(eventName, detail = null) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    addEventListener(eventName, handler) {
        document.addEventListener(eventName, handler);
    }

    removeEventListener(eventName, handler) {
        document.removeEventListener(eventName, handler);
    }

    // Public API
    getModule(name) {
        return this.modules.get(name);
    }

    getConfig() {
        return { ...this.config };
    }

    log(...args) {
        if (this.config.debug) {
            console.log('[App]', ...args);
        }
    }

    // Cleanup
    destroy() {
        // Clean up modules
        this.modules.forEach(module => {
            if (module.destroy) {
                module.destroy();
            }
        });

        // Clear intervals
        if (this.refreshIntervals) {
            this.refreshIntervals.forEach(intervalId => {
                clearInterval(intervalId);
            });
        }

        this.isInitialized = false;
        this.log('Application destroyed');
    }
}

// Auto-initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Clear any existing loading overlays that might be left over
    const existingOverlays = document.querySelectorAll('.loading-overlay');
    existingOverlays.forEach(overlay => overlay.remove());
    
    // Initialize application
    window.app = new MaturityAssessmentApp();
    
    // Development helpers
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.app.config.debug = true;
        
        // Add development tools to console
        console.log('Development mode enabled');
        console.log('Available globals: app, utils, chartManager');
        console.log('Type app.getConfig() to see configuration');
        console.log('Type app.getModule("moduleName") to access modules');
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (window.app) {
        // Auto-save any active forms
        document.querySelectorAll('form[data-auto-save]:not([data-auto-save="false"])').forEach(form => {
            window.app.safeUtils('autoSaveForm', form);
        });
    }
});

// Handle page load completion - clean up any remaining loading overlays
window.addEventListener('load', function() {
    // Give a small delay to ensure all scripts have executed
    setTimeout(() => {
        const remainingOverlays = document.querySelectorAll('.loading-overlay');
        remainingOverlays.forEach(overlay => {
            overlay.remove();
        });
    }, 100);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MaturityAssessmentApp;
}
