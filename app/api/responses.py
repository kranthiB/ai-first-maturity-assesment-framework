"""
Responses API Routes - RESTful endpoints for response operations

Task 4.1: Response API Endpoints
Provides endpoints for submitting and managing assessment responses.
"""

from flask import request, current_app
from flask_restful import Resource
from sqlalchemy.orm import sessionmaker

from app.services.assessment_service import AssessmentService
from app.models.database import DatabaseManager
from app.utils.exceptions import ValidationError, AssessmentError
from app.core.logging import get_logger
from app.api.assessments.schemas import ResponseSubmitSchema


logger = get_logger(__name__)


class ResponseSubmissionResource(Resource):
    """Resource for submitting assessment responses."""
    
    def post(self, assessment_id):
        """
        Submit a response to an assessment question.
        
        Args:
            assessment_id: Assessment ID
            
        Request Body:
            question_id: Question ID (required)
            score: Response score 1-5 (required)
            justification: Response justification (optional)
            evidence: Supporting evidence (optional)
            confidence_level: Confidence level (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            JSON response with submitted response data
        """
        try:
            # Get request data
            data = request.get_json()
            if not data:
                raise ValidationError("Request body is required")
            
            # Validate request data
            schema = ResponseSubmitSchema()
            validated_data = schema.load(data)
            
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Check if assessment exists and is in valid state
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                if assessment.status not in ['draft', 'in_progress']:
                    return {
                        'error': 'Invalid assessment status',
                        'message': (
                            f'Cannot submit responses to assessment '
                            f'with status: {assessment.status}'
                        )
                    }, 400
                
                # Submit response
                response = assessment_service.submit_response(
                    assessment_id=assessment_id,
                    question_id=validated_data['question_id'],
                    score=validated_data['score'],
                    justification=validated_data.get('justification'),
                    evidence=validated_data.get('evidence'),
                    confidence_level=validated_data.get('confidence_level'),
                    metadata=validated_data.get('metadata', {})
                )
                
                # Get updated progress
                progress = assessment_service.get_assessment_progress(
                    assessment_id
                )
                
                # Serialize response
                response_data = {
                    'response': response.to_dict(),
                    'assessment_progress': progress,
                    'next_question': None
                }
                
                # Get next question if available
                if assessment.status in ['draft', 'in_progress']:
                    next_question = assessment_service.get_next_question(
                        assessment_id
                    )
                    if next_question:
                        response_data['next_question'] = (
                            next_question.to_dict()
                        )
                
                logger.info(
                    f"Submitted response for assessment {assessment_id}, "
                    f"question {validated_data['question_id']}"
                )
                
                return response_data, 201
                
            finally:
                session.close()
                
        except ValidationError as e:
            logger.warning(
                f"Validation error submitting response "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Validation Error',
                'message': str(e)
            }, 400
        except AssessmentError as e:
            logger.warning(
                f"Assessment error submitting response "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Assessment Error',
                'message': str(e)
            }, 400
        except Exception as e:
            logger.error(
                f"Error submitting response for assessment "
                f"{assessment_id}: {e}"
            )
            return {
                'error': 'Failed to submit response',
                'message': str(e)
            }, 500


class ResponseListResource(Resource):
    """Resource for managing assessment responses."""
    
    def get(self, assessment_id):
        """
        Get all responses for an assessment.
        
        Args:
            assessment_id: Assessment ID
            
        Query Parameters:
            question_id: Filter by specific question
            section_id: Filter by section
            area_id: Filter by area
            include_details: Include question and area details
            
        Returns:
            JSON response with assessment responses
        """
        try:
            # Get query parameters
            question_id = request.args.get('question_id', type=int)
            section_id = request.args.get('section_id', type=int)
            area_id = request.args.get('area_id', type=int)
            include_details = request.args.get(
                'include_details', 'false'
            ).lower() == 'true'
            
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
                
                # Get responses with filtering
                responses = assessment_service.get_assessment_responses(
                    assessment_id=assessment_id,
                    question_id=question_id,
                    section_id=section_id,
                    area_id=area_id
                )
                
                # Serialize responses
                response_data = []
                for response in responses:
                    response_dict = response.to_dict()
                    
                    # Add question details if requested
                    if include_details and response.question:
                        response_dict['question'] = response.question.to_dict()
                        
                        if response.question.area:
                            response_dict['area'] = {
                                'id': response.question.area.id,
                                'name': response.question.area.name,
                                'section_id': response.question.area.section_id
                            }
                            
                            if response.question.area.section:
                                response_dict['section'] = {
                                    'id': response.question.area.section.id,
                                    'name': response.question.area.section.name
                                }
                    
                    response_data.append(response_dict)
                
                # Get response statistics
                stats = assessment_service.get_response_statistics(
                    assessment_id
                )
                
                result = {
                    'assessment_id': assessment_id,
                    'responses': response_data,
                    'statistics': stats,
                    'filters': {
                        'question_id': question_id,
                        'section_id': section_id,
                        'area_id': area_id
                    }
                }
                
                logger.info(
                    f"Retrieved {len(response_data)} responses "
                    f"for assessment {assessment_id}"
                )
                
                return result, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error retrieving responses for assessment "
                f"{assessment_id}: {e}"
            )
            return {
                'error': 'Failed to retrieve responses',
                'message': str(e)
            }, 500


class ResponseResource(Resource):
    """Resource for managing individual responses."""
    
    def get(self, assessment_id, response_id):
        """
        Get specific response by ID.
        
        Args:
            assessment_id: Assessment ID
            response_id: Response ID
            
        Returns:
            JSON response with response data
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                assessment_service = AssessmentService(session)
                
                # Get response
                response = assessment_service.get_response(
                    assessment_id, response_id
                )
                
                if not response:
                    return {
                        'error': 'Response not found',
                        'message': (
                            f'Response {response_id} not found '
                            f'in assessment {assessment_id}'
                        )
                    }, 404
                
                # Serialize response with full details
                response_dict = response.to_dict()
                
                if response.question:
                    response_dict['question'] = response.question.to_dict()
                    
                    if response.question.area:
                        response_dict['area'] = (
                            response.question.area.to_dict()
                        )
                        
                        if response.question.area.section:
                            response_dict['section'] = (
                                response.question.area.section.to_dict()
                            )
                
                logger.info(
                    f"Retrieved response {response_id} "
                    f"for assessment {assessment_id}"
                )
                
                return response_dict, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error retrieving response {response_id} "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Failed to retrieve response',
                'message': str(e)
            }, 500
    
    def put(self, assessment_id, response_id):
        """
        Update specific response.
        
        Args:
            assessment_id: Assessment ID
            response_id: Response ID
            
        Request Body:
            Fields to update (score, justification, evidence, etc.)
            
        Returns:
            JSON response with updated response data
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
                
                # Check if assessment is in valid state for updates
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                if assessment.status not in ['draft', 'in_progress']:
                    return {
                        'error': 'Invalid assessment status',
                        'message': (
                            f'Cannot update responses for assessment '
                            f'with status: {assessment.status}'
                        )
                    }, 400
                
                # Update response
                updated_response = assessment_service.update_response(
                    assessment_id, response_id, data
                )
                
                if not updated_response:
                    return {
                        'error': 'Response not found',
                        'message': (
                            f'Response {response_id} not found '
                            f'in assessment {assessment_id}'
                        )
                    }, 404
                
                # Get updated progress
                progress = assessment_service.get_assessment_progress(
                    assessment_id
                )
                
                response_data = {
                    'response': updated_response.to_dict(),
                    'assessment_progress': progress
                }
                
                logger.info(
                    f"Updated response {response_id} "
                    f"for assessment {assessment_id}"
                )
                
                return response_data, 200
                
            finally:
                session.close()
                
        except ValidationError as e:
            logger.warning(
                f"Validation error updating response {response_id} "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Validation Error',
                'message': str(e)
            }, 400
        except AssessmentError as e:
            logger.warning(
                f"Assessment error updating response {response_id} "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Assessment Error',
                'message': str(e)
            }, 400
        except Exception as e:
            logger.error(
                f"Error updating response {response_id} "
                f"for assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Failed to update response',
                'message': str(e)
            }, 500
    
    def delete(self, assessment_id, response_id):
        """
        Delete specific response.
        
        Args:
            assessment_id: Assessment ID
            response_id: Response ID
            
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
                
                # Check if assessment is in valid state for deletions
                assessment = assessment_service.get_assessment(assessment_id)
                if not assessment:
                    return {
                        'error': 'Assessment not found',
                        'message': f'Assessment {assessment_id} does not exist'
                    }, 404
                
                if assessment.status not in ['draft', 'in_progress']:
                    return {
                        'error': 'Invalid assessment status',
                        'message': (
                            f'Cannot delete responses from assessment '
                            f'with status: {assessment.status}'
                        )
                    }, 400
                
                # Delete response
                deleted = assessment_service.delete_response(
                    assessment_id, response_id
                )
                
                if not deleted:
                    return {
                        'error': 'Response not found',
                        'message': (
                            f'Response {response_id} not found '
                            f'in assessment {assessment_id}'
                        )
                    }, 404
                
                # Get updated progress
                progress = assessment_service.get_assessment_progress(
                    assessment_id
                )
                
                response_data = {
                    'message': (
                        f'Response {response_id} deleted successfully '
                        f'from assessment {assessment_id}'
                    ),
                    'assessment_progress': progress
                }
                
                logger.info(
                    f"Deleted response {response_id} "
                    f"from assessment {assessment_id}"
                )
                
                return response_data, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error deleting response {response_id} "
                f"from assessment {assessment_id}: {e}"
            )
            return {
                'error': 'Failed to delete response',
                'message': str(e)
            }, 500
