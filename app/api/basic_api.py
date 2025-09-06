"""
Basic API Implementation for Task 4.1

Simple RESTful API endpoints that demonstrate the core functionality
without complex dependencies.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime


def create_basic_api_blueprint():
    """Create a basic API blueprint for testing."""
    api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
    
    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    
    @api_bp.route('/config', methods=['GET'])
    def get_config():
        """Get application configuration for frontend."""
        return jsonify({
            'debug': False,
            'apiTimeout': 30000,
            'autoSaveInterval': 30000,
            'chartRefreshInterval': 300000,
            'maxRetries': 3,
            'retryDelay': 1000,
            'version': '2.0.0',
            'features': {
                'darkMode': True,
                'analytics': True,
                'export': True,
                'comparison': True
            },
            'widgets': {
                'assessmentStats': {
                    'endpoint': '/api/v1/analytics/overview',
                    'refreshInterval': 300000
                },
                'recentActivity': {
                    'endpoint': '/api/v1/analytics/trends',
                    'refreshInterval': 60000
                }
            }
        }), 200
    
    @api_bp.route('/assessments', methods=['GET', 'POST'])
    def assessments():
        """Handle assessment collection operations."""
        if request.method == 'GET':
            # Mock response for GET /assessments
            return jsonify({
                'assessments': [
                    {
                        'id': 1,
                        'name': 'Sample Assessment',
                        'organization': 'Test Org',
                        'status': 'draft',
                        'created_at': datetime.utcnow().isoformat()
                    }
                ],
                'pagination': {
                    'total': 1,
                    'limit': 50,
                    'offset': 0
                }
            }), 200
        
        elif request.method == 'POST':
            # Mock response for POST /assessments
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Request body required'
                }), 400
            
            # Basic validation
            required_fields = [
                'name', 'description', 'organization',
                'assessor_name', 'assessor_email'
            ]
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'error': f'Field {field} is required'
                    }), 400
            
            # Mock created assessment
            assessment = {
                'id': 1,
                'name': data['name'],
                'description': data['description'],
                'organization': data['organization'],
                'assessor_name': data['assessor_name'],
                'assessor_email': data['assessor_email'],
                'status': 'draft',
                'created_at': datetime.utcnow().isoformat(),
                'progress': {
                    'progress_percentage': 0.0,
                    'total_questions': 50,
                    'responded_questions': 0
                }
            }
            
            return jsonify(assessment), 201
    
    @api_bp.route(
        '/assessments/<int:assessment_id>',
        methods=['GET', 'PUT', 'DELETE']
    )
    def assessment_detail(assessment_id):
        """Handle individual assessment operations."""
        if request.method == 'GET':
            # Mock response for GET /assessments/{id}
            return jsonify({
                'id': assessment_id,
                'name': 'Sample Assessment',
                'description': 'Sample assessment description',
                'organization': 'Test Organization',
                'assessor_name': 'John Doe',
                'assessor_email': 'john@test.com',
                'status': 'draft',
                'created_at': datetime.utcnow().isoformat(),
                'progress': {
                    'progress_percentage': 25.0,
                    'total_questions': 50,
                    'responded_questions': 12
                }
            }), 200
        
        elif request.method == 'PUT':
            # Mock response for PUT /assessments/{id}
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Request body required'
                }), 400
            
            return jsonify({
                'id': assessment_id,
                'message': 'Assessment updated successfully',
                'updated_fields': list(data.keys())
            }), 200
        
        elif request.method == 'DELETE':
            # Mock response for DELETE /assessments/{id}
            return jsonify({
                'message': f'Assessment {assessment_id} deleted successfully'
            }), 200
    
    @api_bp.route('/assessments/<int:assessment_id>/progress', methods=['GET'])
    def assessment_progress(assessment_id):
        """Get assessment progress."""
        return jsonify({
            'assessment_id': assessment_id,
            'progress_percentage': 35.0,
            'total_questions': 50,
            'responded_questions': 17,
            'remaining_questions': 33,
            'sections_progress': [
                {
                    'section_id': 1,
                    'section_name': 'Development Practices',
                    'progress_percentage': 60.0,
                    'questions_completed': 6,
                    'total_questions': 10
                },
                {
                    'section_id': 2,
                    'section_name': 'Testing & Quality',
                    'progress_percentage': 20.0,
                    'questions_completed': 2,
                    'total_questions': 10
                }
            ],
            'estimated_completion_time': '45 minutes',
            'last_activity': datetime.utcnow().isoformat()
        }), 200
    
    @api_bp.route('/assessments/<int:assessment_id>/complete', methods=['POST'])
    def assessment_completion(assessment_id):
        """Complete an assessment."""
        return jsonify({
            'assessment_id': assessment_id,
            'status': 'completed',
            'completion_timestamp': datetime.utcnow().isoformat(),
            'final_score': 3.2,
            'maturity_level': 'Developing',
            'message': 'Assessment completed successfully'
        }), 200
    
    @api_bp.route('/assessments/<int:assessment_id>/responses', methods=['GET', 'POST'])
    def assessment_responses(assessment_id):
        """Handle assessment responses."""
        if request.method == 'GET':
            # Mock response list
            return jsonify({
                'assessment_id': assessment_id,
                'responses': [
                    {
                        'id': 1,
                        'question_id': 1,
                        'score': 4,
                        'justification': 'We have implemented CI/CD pipeline',
                        'confidence_level': 'high',
                        'created_at': datetime.utcnow().isoformat()
                    }
                ],
                'statistics': {
                    'total_responses': 1,
                    'average_score': 4.0,
                    'average_confidence': 'high'
                }
            }), 200
        
        elif request.method == 'POST':
            # Mock response submission
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            required_fields = ['question_id', 'score']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'error': f'Field {field} is required'
                    }), 400
            
            return jsonify({
                'response': {
                    'id': 1,
                    'assessment_id': assessment_id,
                    'question_id': data['question_id'],
                    'score': data['score'],
                    'justification': data.get('justification'),
                    'confidence_level': data.get('confidence_level', 'medium'),
                    'created_at': datetime.utcnow().isoformat()
                },
                'assessment_progress': {
                    'progress_percentage': 36.0,
                    'responded_questions': 18,
                    'total_questions': 50
                }
            }), 201
    
    @api_bp.route('/questions', methods=['GET'])
    def questions():
        """Get questions list."""
        return jsonify({
            'questions': [
                {
                    'id': 1,
                    'text': 'How mature is your CI/CD pipeline?',
                    'description': 'Assess the maturity of continuous integration...',
                    'area_id': 1,
                    'difficulty': 'medium',
                    'area': {
                        'id': 1,
                        'name': 'Continuous Integration',
                        'section_id': 1
                    },
                    'section': {
                        'id': 1,
                        'name': 'Development Practices'
                    }
                }
            ],
            'pagination': {
                'total': 1,
                'limit': 100,
                'offset': 0
            }
        }), 200
    
    @api_bp.route('/analytics/overview', methods=['GET'])
    def analytics_overview():
        """Get analytics overview."""
        return jsonify({
            'overview': {
                'total_assessments': 42,
                'completed_assessments': 38,
                'average_score': 3.4,
                'average_completion_time': '67 minutes'
            },
            'recent_activity': [
                {
                    'assessment_id': 1,
                    'organization': 'Test Org',
                    'status': 'completed',
                    'score': 3.2,
                    'completed_at': datetime.utcnow().isoformat()
                }
            ],
            'maturity_distribution': {
                'Initial': 5,
                'Developing': 15,
                'Defined': 12,
                'Managed': 8,
                'Optimizing': 2
            }
        }), 200
    
    @api_bp.route('/analytics/trends', methods=['GET'])
    def analytics_trends():
        """Get analytics trends."""
        return jsonify({
            'trends': [
                {
                    'date': '2024-01-01',
                    'assessments_count': 5,
                    'average_score': 3.1
                },
                {
                    'date': '2024-01-02',
                    'assessments_count': 8,
                    'average_score': 3.3
                }
            ],
            'summary': {
                'period': 'daily',
                'metric': 'assessments',
                'trend_direction': 'increasing'
            }
        }), 200
    
    # Error handlers
    @api_bp.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @api_bp.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood'
        }), 400
    
    @api_bp.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return api_bp
