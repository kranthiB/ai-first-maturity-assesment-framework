"""
Assessment API Routes - RESTful endpoints for assessment operations

Task 4.1: Assessment API Endpoints
Provides CRUD operations and management for assessments.
"""

from flask import request, current_app
from flask_restful import Resource
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.services.assessment_service import AssessmentService
from app.utils.exceptions import ValidationError, AssessmentError
from app.core.logging import get_logger
from app.api.db_helper import get_db_session, close_db_session


logger = get_logger(__name__)


class AssessmentListResource(Resource):
    """Resource for handling assessment collection operations."""
    
    def get(self):
        """
        Get list of assessments with optional filtering.
        
        Query Parameters:
            status: Filter by assessment status
            organization: Filter by organization
            limit: Limit number of results (default: 50)
            offset: Offset for pagination (default: 0)
            
        Returns:
            JSON response with assessment list and metadata
        """
        try:
            # Get query parameters
            status = request.args.get('status')
            organization = request.args.get('organization')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            # Validate parameters
            if limit > 100:
                limit = 100
            if offset < 0:
                offset = 0
                
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Get assessments with filtering
                assessments = assessment_service.get_assessments(
                    status=status,
                    organization=organization,
                    limit=limit,
                    offset=offset
                )
                
                # Get total count for pagination
                total_count = assessment_service.get_assessments_count(
                    status=status,
                    organization=organization
                )
                
                # Serialize assessments
                assessment_data = []
                for assessment in assessments:
                    assessment_dict = assessment.to_dict()
                    
                    # Add progress information
                    progress = assessment_service.get_assessment_progress(
                        assessment.id
                    )
                    assessment_dict['progress'] = progress
                    
                    assessment_data.append(assessment_dict)
                
                response_data = {
                    'assessments': assessment_data,
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_next': offset + limit < total_count,
                        'has_prev': offset > 0
                    },
                    'filters': {
                        'status': status,
                        'organization': organization
                    }
                }
                
                logger.info(
                    f"Retrieved {len(assessment_data)} assessments "
                    f"(total: {total_count})"
                )
                
                return response_data, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error retrieving assessments: {e}")
            return {
                'error': 'Failed to retrieve assessments',
                'message': str(e)
            }, 500
    
    def post(self):
        """
        Create a new assessment.
        
        Request Body:
            name: Assessment name (required)
            description: Assessment description (required)
            organization: Organization name (required)
            assessor_name: Assessor name (required)
            assessor_email: Assessor email (required)
            metadata: Additional metadata (optional)
            
        Returns:
            JSON response with created assessment data
        """
        try:
            # Get request data
            data = request.get_json()
            if not data:
                raise ValidationError("Request body is required")
            
            # Extract required fields
            required_fields = [
                'name', 'description', 'organization',
                'assessor_name', 'assessor_email'
            ]
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"'{field}' is required")
            
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Create assessment
                assessment = assessment_service.create_assessment(
                    name=data['name'],
                    description=data['description'],
                    organization=data['organization'],
                    assessor_name=data['assessor_name'],
                    assessor_email=data['assessor_email'],
                    metadata=data.get('metadata', {})
                )
                
                # Serialize response
                assessment_dict = assessment.to_dict()
                
                # Add initial progress
                progress = assessment_service.get_assessment_progress(
                    assessment.id
                )
                assessment_dict['progress'] = progress
                
                logger.info(
                    f"Created new assessment: {assessment.id} "
                    f"for {assessment.organization}"
                )
                
                return assessment_dict, 201
                
            finally:
                session.close()
                
        except ValidationError as e:
            logger.warning(f"Validation error creating assessment: {e}")
            return {
                'error': 'Validation Error',
                'message': str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error creating assessment: {e}")
            return {
                'error': 'Failed to create assessment',
                'message': str(e)
            }, 500


class AssessmentResource(Resource):
    """Resource for handling individual assessment operations."""
    
    def get(self, assessment_id):
        """
        Get specific assessment by ID.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            JSON response with assessment data
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Get assessment
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                # Serialize assessment
                assessment_dict = assessment.to_dict()
                
                # Add progress information
                progress = assessment_service.get_assessment_progress(
                    assessment.id
                )
                assessment_dict['progress'] = progress
                
                # Add responses if requested
                include_responses = request.args.get('include_responses', 
                                                   'false').lower() == 'true'
                if include_responses:
                    responses = assessment_service.get_assessment_responses(
                        assessment.id
                    )
                    assessment_dict['responses'] = [
                        response.to_dict() for response in responses
                    ]
                
                logger.info(f"Retrieved assessment: {assessment_id}")
                
                return assessment_dict, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error retrieving assessment {assessment_id}: {e}")
            return {
                'error': 'Failed to retrieve assessment',
                'message': str(e)
            }, 500
    
    def put(self, assessment_id):
        """
        Update specific assessment.
        
        Args:
            assessment_id: Assessment ID
            
        Request Body:
            Fields to update (name, description, metadata, etc.)
            
        Returns:
            JSON response with updated assessment data
        """
        try:
            # Get request data
            data = request.get_json()
            if not data:
                raise ValidationError("Request body is required")
            
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Check if assessment exists
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                # Update assessment
                updated_assessment = assessment_service.update_assessment(
                    assessment_id, data
                )
                
                # Serialize response
                assessment_dict = updated_assessment.to_dict()
                
                # Add progress information
                progress = assessment_service.get_assessment_progress(
                    assessment.id
                )
                assessment_dict['progress'] = progress
                
                logger.info(f"Updated assessment: {assessment_id}")
                
                return assessment_dict, 200
                
            finally:
                session.close()
                
        except ValidationError as e:
            logger.warning(
                f"Validation error updating assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Validation Error',
                'message': str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error updating assessment {assessment_id}: {e}")
            return {
                'error': 'Failed to update assessment',
                'message': str(e)
            }, 500
    
    def delete(self, assessment_id):
        """
        Delete specific assessment.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            JSON response confirming deletion
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Check if assessment exists
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                # Delete assessment
                assessment_service.delete_assessment(assessment_id)
                
                logger.info(f"Deleted assessment: {assessment_id}")
                
                return {
                    'message': f'Assessment {assessment_id} deleted successfully'
                }, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error deleting assessment {assessment_id}: {e}")
            return {
                'error': 'Failed to delete assessment',
                'message': str(e)
            }, 500


class AssessmentProgressResource(Resource):
    """Resource for handling assessment progress operations."""
    
    def get(self, assessment_id):
        """
        Get assessment progress details.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            JSON response with detailed progress information
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Check if assessment exists
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                # Get detailed progress
                progress = assessment_service.get_assessment_progress(
                    assessment_id
                )
                
                # Add next question if available
                if assessment.status in ['draft', 'in_progress']:
                    next_question = assessment_service.get_next_question(
                        assessment_id
                    )
                    if next_question:
                        progress['next_question'] = next_question.to_dict()
                
                logger.info(f"Retrieved progress for assessment: {assessment_id}")
                
                return progress, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error retrieving progress for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Failed to retrieve progress',
                'message': str(e)
            }, 500


class AssessmentCompletionResource(Resource):
    """Resource for handling assessment completion operations."""
    
    def post(self, assessment_id):
        """
        Complete an assessment and generate final report.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            JSON response with completion status and report data
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Check if assessment exists
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                # Complete assessment
                completed_assessment = assessment_service.complete_assessment(
                    assessment_id
                )
                
                # Get final report data
                progress = assessment_service.get_assessment_progress(
                    assessment_id
                )
                
                response_data = {
                    'assessment': completed_assessment.to_dict(),
                    'progress': progress,
                    'completion_timestamp': datetime.utcnow().isoformat(),
                    'message': 'Assessment completed successfully'
                }
                
                logger.info(f"Completed assessment: {assessment_id}")
                
                return response_data, 200
                
            finally:
                session.close()
                
        except AssessmentError as e:
            logger.warning(
                f"Assessment error completing {assessment_id}: {e}"
            )
            return {
                'error': 'Assessment Error',
                'message': str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error completing assessment {assessment_id}: {e}")
            return {
                'error': 'Failed to complete assessment',
                'message': str(e)
            }, 500
