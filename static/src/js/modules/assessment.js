/**
 * Assessment Module
 * Handles assessment form interactions, validation, progress tracking, and submission
 */

class AssessmentManager {
    constructor(options = {}) {
        this.assessmentId = options.assessmentId || null;
        this.currentQuestion = options.currentQuestion || 1;
        this.totalQuestions = options.totalQuestions || 24;
        this.autoSaveEnabled = options.autoSave !== false;
        this.autoSaveInterval = options.autoSaveInterval || 30000; // 30 seconds
        this.responses = new Map();
        this.validationRules = new Map();
        this.callbacks = {
            onQuestionChange: [],
            onProgressUpdate: [],
            onValidationError: [],
            onSaveSuccess: [],
            onSaveError: []
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedResponses();
        this.setupAutoSave();
        this.updateProgress();
        this.setupKeyboardNavigation();
        this.setupFormValidation();
    }

    bindEvents() {
        // Response input handling
        document.addEventListener('change', (e) => {
            if (e.target.matches('[name^="response_"]')) {
                this.handleResponseChange(e.target);
            }
        });

        // Navigation buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-next-question')) {
                this.nextQuestion();
            } else if (e.target.matches('.btn-prev-question')) {
                this.previousQuestion();
            } else if (e.target.matches('.btn-save-draft')) {
                this.saveDraft();
            } else if (e.target.matches('.btn-submit-assessment')) {
                this.submitAssessment();
            }
        });

        // Form submission
        const assessmentForm = document.getElementById('assessmentForm');
        if (assessmentForm) {
            assessmentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(e);
            });
        }

        // Page visibility change (for auto-save on tab switch)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.hasUnsavedChanges()) {
                this.saveDraft(true); // Silent save
            }
        });

        // Before unload warning
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    handleResponseChange(input) {
        const questionId = this.extractQuestionId(input.name);
        const value = this.getInputValue(input);
        
        // Store response
        this.responses.set(questionId, {
            value: value,
            timestamp: new Date().toISOString(),
            element: input
        });

        // Validate response
        this.validateResponse(questionId, value);

        // Update progress
        this.updateProgress();

        // Mark as having unsaved changes
        this.markUnsavedChanges();

        // Trigger callbacks
        this.triggerCallbacks('onResponseChange', { questionId, value });
    }

    extractQuestionId(inputName) {
        // Extract question ID from input name (e.g., "response_1_2" -> "1_2")
        const match = inputName.match(/response_(.+)/);
        return match ? match[1] : null;
    }

    getInputValue(input) {
        switch (input.type) {
            case 'radio':
                return input.checked ? input.value : null;
            case 'checkbox':
                const checkboxes = document.querySelectorAll(`[name="${input.name}"]`);
                return Array.from(checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);
            case 'range':
                return parseInt(input.value);
            case 'number':
                return parseFloat(input.value);
            default:
                return input.value;
        }
    }

    validateResponse(questionId, value) {
        const rules = this.validationRules.get(questionId);
        if (!rules) return true;

        const errors = [];

        // Required validation
        if (rules.required && (!value || (Array.isArray(value) && value.length === 0))) {
            errors.push('This question is required');
        }

        // Range validation for numeric inputs
        if (rules.min !== undefined && value < rules.min) {
            errors.push(`Value must be at least ${rules.min}`);
        }

        if (rules.max !== undefined && value > rules.max) {
            errors.push(`Value must be no more than ${rules.max}`);
        }

        // Custom validation
        if (rules.custom && typeof rules.custom === 'function') {
            const customError = rules.custom(value);
            if (customError) {
                errors.push(customError);
            }
        }

        // Display validation errors
        this.displayValidationErrors(questionId, errors);

        return errors.length === 0;
    }

    displayValidationErrors(questionId, errors) {
        const errorContainer = document.getElementById(`errors_${questionId}`);
        if (!errorContainer) return;

        if (errors.length > 0) {
            errorContainer.innerHTML = errors
                .map(error => `<div class="alert alert-danger alert-sm">${error}</div>`)
                .join('');
            errorContainer.style.display = 'block';
            this.triggerCallbacks('onValidationError', { questionId, errors });
        } else {
            errorContainer.style.display = 'none';
        }
    }

    updateProgress() {
        const answeredQuestions = this.getAnsweredQuestionCount();
        const progressPercentage = Math.round((answeredQuestions / this.totalQuestions) * 100);

        // Update progress bars
        document.querySelectorAll('.progress-bar[data-target="assessment"]').forEach(bar => {
            bar.style.width = `${progressPercentage}%`;
            bar.setAttribute('aria-valuenow', progressPercentage);
            bar.textContent = `${progressPercentage}%`;
        });

        // Update progress text
        document.querySelectorAll('[data-progress-text]').forEach(element => {
            element.textContent = `${answeredQuestions} of ${this.totalQuestions} questions completed`;
        });

        // Update question counter
        const questionCounter = document.querySelector('.question-counter');
        if (questionCounter) {
            questionCounter.textContent = `Question ${this.currentQuestion} of ${this.totalQuestions}`;
        }

        this.triggerCallbacks('onProgressUpdate', { 
            answered: answeredQuestions, 
            total: this.totalQuestions, 
            percentage: progressPercentage 
        });
    }

    getAnsweredQuestionCount() {
        return Array.from(this.responses.values())
            .filter(response => response.value !== null && response.value !== undefined && response.value !== '')
            .length;
    }

    nextQuestion() {
        if (this.currentQuestion < this.totalQuestions) {
            const currentValid = this.validateCurrentQuestion();
            if (currentValid) {
                this.navigateToQuestion(this.currentQuestion + 1);
            }
        } else {
            this.showCompletionPrompt();
        }
    }

    previousQuestion() {
        if (this.currentQuestion > 1) {
            this.navigateToQuestion(this.currentQuestion - 1);
        }
    }

    validateCurrentQuestion() {
        const questionElements = document.querySelectorAll(`[name^="response_${this.currentQuestion}"]`);
        let isValid = true;

        questionElements.forEach(element => {
            const questionId = this.extractQuestionId(element.name);
            const value = this.getInputValue(element);
            if (!this.validateResponse(questionId, value)) {
                isValid = false;
            }
        });

        return isValid;
    }

    navigateToQuestion(questionNumber) {
        this.currentQuestion = questionNumber;
        
        // Auto-save before navigation
        if (this.hasUnsavedChanges()) {
            this.saveDraft(true);
        }

        // Update URL or trigger page change
        if (typeof window.navigateToQuestion === 'function') {
            window.navigateToQuestion(questionNumber);
        } else {
            // Fallback: update URL hash
            window.location.hash = `question-${questionNumber}`;
        }

        this.triggerCallbacks('onQuestionChange', { 
            previous: this.currentQuestion - 1, 
            current: questionNumber 
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Only handle keyboard navigation if not in an input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            switch (e.key) {
                case 'ArrowRight':
                case 'n':
                case 'N':
                    e.preventDefault();
                    this.nextQuestion();
                    break;
                case 'ArrowLeft':
                case 'p':
                case 'P':
                    e.preventDefault();
                    this.previousQuestion();
                    break;
                case 's':
                case 'S':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.saveDraft();
                    }
                    break;
            }
        });
    }

    setupFormValidation() {
        // Set up validation rules for different question types
        document.querySelectorAll('[data-validation]').forEach(element => {
            const questionId = this.extractQuestionId(element.name);
            const validationData = JSON.parse(element.dataset.validation);
            this.validationRules.set(questionId, validationData);
        });
    }

    setupAutoSave() {
        if (!this.autoSaveEnabled) return;

        setInterval(() => {
            if (this.hasUnsavedChanges()) {
                this.saveDraft(true);
            }
        }, this.autoSaveInterval);
    }

    saveDraft(silent = false) {
        const data = this.prepareSubmissionData();
        data.status = 'draft';

        if (!silent) {
            this.showSaveIndicator('Saving...');
        }

        return fetch(`/api/v1/assessments/${this.assessmentId}/responses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            this.markSaved();
            if (!silent) {
                this.showSaveIndicator('Saved', 'success');
            }
            this.triggerCallbacks('onSaveSuccess', result);
            return result;
        })
        .catch(error => {
            console.error('Save failed:', error);
            if (!silent) {
                this.showSaveIndicator('Save failed', 'error');
            }
            this.triggerCallbacks('onSaveError', error);
            throw error;
        });
    }

    submitAssessment() {
        // Validate all responses
        const isValid = this.validateAllResponses();
        if (!isValid) {
            this.showAlert('Please complete all required questions before submitting.', 'error');
            return;
        }

        // Show confirmation dialog
        if (!confirm('Are you sure you want to submit your assessment? This action cannot be undone.')) {
            return;
        }

        const data = this.prepareSubmissionData();
        data.status = 'completed';

        this.showSubmitIndicator('Submitting...');

        return fetch(`/api/v1/assessments/${this.assessmentId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            this.showSubmitIndicator('Submitted successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/assessment/${this.assessmentId}/results`;
            }, 1500);
            return result;
        })
        .catch(error => {
            console.error('Submission failed:', error);
            this.showSubmitIndicator('Submission failed. Please try again.', 'error');
            throw error;
        });
    }

    validateAllResponses() {
        let isValid = true;
        
        this.validationRules.forEach((rules, questionId) => {
            const response = this.responses.get(questionId);
            if (!this.validateResponse(questionId, response?.value)) {
                isValid = false;
            }
        });

        return isValid;
    }

    prepareSubmissionData() {
        const responses = {};
        
        this.responses.forEach((responseData, questionId) => {
            responses[questionId] = {
                value: responseData.value,
                timestamp: responseData.timestamp
            };
        });

        return {
            assessment_id: this.assessmentId,
            responses: responses,
            metadata: {
                user_agent: navigator.userAgent,
                timestamp: new Date().toISOString(),
                session_duration: this.getSessionDuration()
            }
        };
    }

    loadSavedResponses() {
        if (!this.assessmentId) return;

        fetch(`/api/v1/assessments/${this.assessmentId}/responses`)
            .then(response => response.json())
            .then(data => {
                if (data.responses) {
                    Object.entries(data.responses).forEach(([questionId, responseData]) => {
                        this.responses.set(questionId, responseData);
                        this.populateFormField(questionId, responseData.value);
                    });
                    this.updateProgress();
                }
            })
            .catch(error => {
                console.warn('Failed to load saved responses:', error);
            });
    }

    populateFormField(questionId, value) {
        const elements = document.querySelectorAll(`[name="response_${questionId}"]`);
        
        elements.forEach(element => {
            switch (element.type) {
                case 'radio':
                    element.checked = element.value === value;
                    break;
                case 'checkbox':
                    element.checked = Array.isArray(value) && value.includes(element.value);
                    break;
                default:
                    element.value = value;
            }
        });
    }

    hasUnsavedChanges() {
        return this.unsavedChanges === true;
    }

    markUnsavedChanges() {
        this.unsavedChanges = true;
        document.querySelectorAll('.save-indicator').forEach(indicator => {
            indicator.textContent = 'Unsaved changes';
            indicator.className = 'save-indicator text-warning';
        });
    }

    markSaved() {
        this.unsavedChanges = false;
    }

    showSaveIndicator(message, type = 'info') {
        document.querySelectorAll('.save-indicator').forEach(indicator => {
            indicator.textContent = message;
            indicator.className = `save-indicator text-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'}`;
        });
    }

    showSubmitIndicator(message, type = 'info') {
        const submitButton = document.querySelector('.btn-submit-assessment');
        if (submitButton) {
            submitButton.innerHTML = type === 'info' ? 
                `<span class="spinner-border spinner-border-sm me-2"></span>${message}` : 
                message;
            submitButton.disabled = type === 'info';
        }
    }

    showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const alertContainer = document.querySelector('.alert-container') || document.body;
        alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
    }

    getSessionDuration() {
        if (!this.sessionStart) {
            this.sessionStart = new Date();
        }
        return new Date() - this.sessionStart;
    }

    showCompletionPrompt() {
        const completionRate = (this.getAnsweredQuestionCount() / this.totalQuestions) * 100;
        
        if (completionRate >= 80) {
            const modal = this.createCompletionModal();
            modal.show();
        } else {
            this.showAlert(`You have completed ${completionRate.toFixed(1)}% of the assessment. Please answer more questions before submitting.`, 'warning');
        }
    }

    createCompletionModal() {
        const modalHtml = `
            <div class="modal fade" id="completionModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Complete Assessment</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>You have completed ${this.getAnsweredQuestionCount()} of ${this.totalQuestions} questions.</p>
                            <p>Are you ready to submit your assessment and view your results?</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Continue Editing</button>
                            <button type="button" class="btn btn-primary" onclick="assessmentManager.submitAssessment()">Submit Assessment</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        return new bootstrap.Modal(document.getElementById('completionModal'));
    }

    // Event callback system
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }

    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }

    triggerCallbacks(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} callback:`, error);
                }
            });
        }
    }

    // Public API methods
    getCurrentProgress() {
        return {
            current: this.currentQuestion,
            total: this.totalQuestions,
            answered: this.getAnsweredQuestionCount(),
            percentage: Math.round((this.getAnsweredQuestionCount() / this.totalQuestions) * 100)
        };
    }

    getResponse(questionId) {
        return this.responses.get(questionId);
    }

    setResponse(questionId, value) {
        this.responses.set(questionId, {
            value: value,
            timestamp: new Date().toISOString()
        });
        this.updateProgress();
        this.markUnsavedChanges();
    }

    clearResponse(questionId) {
        this.responses.delete(questionId);
        this.updateProgress();
        this.markUnsavedChanges();
    }

    reset() {
        this.responses.clear();
        this.currentQuestion = 1;
        this.updateProgress();
        this.markSaved();
    }
}

// Auto-initialize if assessment container exists
document.addEventListener('DOMContentLoaded', function() {
    const assessmentContainer = document.querySelector('[data-assessment-id]');
    if (assessmentContainer) {
        const options = {
            assessmentId: assessmentContainer.dataset.assessmentId,
            currentQuestion: parseInt(assessmentContainer.dataset.currentQuestion) || 1,
            totalQuestions: parseInt(assessmentContainer.dataset.totalQuestions) || 24,
            autoSave: assessmentContainer.dataset.autoSave !== 'false'
        };
        
        window.assessmentManager = new AssessmentManager(options);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AssessmentManager;
}