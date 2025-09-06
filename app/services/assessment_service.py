"""
Assessment Service Layer
Implements business logic for assessment creation, management, and completion.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from app.models import (
    Assessment, Section, Area, Question, Response
)
from app.services.scoring_service import ScoringService
from app.services.recommendation_service import RecommendationService
from app.utils.validators import AssessmentValidator, ResponseValidator
from app.utils.exceptions import (
    AssessmentError, ValidationError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AssessmentService:
    """
    Service class for managing assessment lifecycle and operations.
    
    Handles:
    - Assessment creation and initialization
    - Response validation and storage
    - Progress tracking
    - Assessment completion and finalization
    - Integration with scoring and recommendation services
    """
    
    def __init__(self, db_session: Session):
        """Initialize assessment service with database session."""
        self.session = db_session
        self.scoring_service = ScoringService(db_session)
        self.recommendation_service = RecommendationService(db_session)
        self.assessment_validator = AssessmentValidator()
        self.response_validator = ResponseValidator()
        logger.debug("AssessmentService initialized")
    
    def create_assessment(self, name: str, description: str,
                          organization: str, assessor_name: str,
                          assessor_email: str,
                          metadata: Optional[Dict] = None) -> Assessment:
        """
        Create a new assessment with validation.
        
        Args:
            name: Assessment name
            description: Assessment description
            organization: Organization name
            assessor_name: Name of person conducting assessment
            assessor_email: Email of assessor
            metadata: Optional additional metadata
            
        Returns:
            Created Assessment instance
            
        Raises:
            ValidationError: If input validation fails
            AssessmentError: If assessment creation fails
        """
        try:
            # Validate input data
            assessment_data = {
                'name': name,
                'description': description,
                'organization': organization,
                'assessor_name': assessor_name,
                'assessor_email': assessor_email
            }
            
            self.assessment_validator.validate_assessment_data(assessment_data)
            
            # Create assessment instance
            assessment = Assessment(
                name=name.strip(),
                description=description.strip(),
                organization=organization.strip(),
                assessor_name=assessor_name.strip(),
                assessor_email=assessor_email.strip().lower(),
                status='draft',
                metadata=metadata or {}
            )
            
            # Save to database
            self.session.add(assessment)
            self.session.commit()
            
            logger.info(f"Created assessment '{name}' for {organization}")
            return assessment
            
        except ValidationError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create assessment: {e}")
            raise AssessmentError(f"Assessment creation failed: {str(e)}")
    
    def get_assessment(self, assessment_id: int,
                       include_responses: bool = False
                       ) -> Optional[Assessment]:
        """
        Retrieve assessment by ID with optional response data.
        
        Args:
            assessment_id: Assessment ID
            include_responses: Whether to include response data
            
        Returns:
            Assessment instance or None if not found
        """
        try:
            query = self.session.query(Assessment).filter(
                Assessment.id == assessment_id
            )
            
            if include_responses:
                query = query.options(
                    joinedload(Assessment.responses)
                    .joinedload(Response.question)
                    .joinedload(Question.area)
                    .joinedload(Area.section)
                )
            
            assessment = query.first()
            
            if assessment:
                logger.debug(f"Retrieved assessment {assessment_id}")
            else:
                logger.warning(f"Assessment {assessment_id} not found")
                
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to retrieve assessment {assessment_id}: {e}")
            raise AssessmentError(f"Failed to retrieve assessment: {str(e)}")
    
    def submit_response(self, assessment_id: int, question_id: int,
                        answer_value: str,
                        validate_answer: bool = True) -> Response:
        """
        Submit and validate a response to an assessment question.
        
        Args:
            assessment_id: Assessment ID
            question_id: Question ID
            answer_value: Answer value to submit
            validate_answer: Whether to validate answer against question options
            
        Returns:
            Created or updated Response instance
            
        Raises:
            ValidationError: If response validation fails
            AssessmentError: If submission fails
        """
        try:
            # Get assessment and question
            assessment = self.get_assessment(assessment_id)
            if not assessment:
                raise AssessmentError(f"Assessment {assessment_id} not found")
            
            # Check assessment status
            if assessment.status == 'completed':
                raise AssessmentError("Cannot modify completed assessment")
            
            question = self.session.query(Question).filter(
                Question.id == question_id
            ).first()
            if not question:
                raise AssessmentError(f"Question {question_id} not found")
            
            # Validate response
            if validate_answer:
                self.response_validator.validate_response(
                    question, answer_value
                )
            
            # Check for existing response
            existing_response = self.session.query(Response).filter(
                and_(
                    Response.assessment_id == assessment_id,
                    Response.question_id == question_id
                )
            ).first()
            
            if existing_response:
                # Update existing response
                existing_response.set_answer(answer_value)
                response = existing_response
                logger.debug(f"Updated response for question {question_id}")
            else:
                # Create new response
                response = Response(
                    assessment_id=assessment_id,
                    question_id=question_id,
                    answer_value=answer_value
                )
                self.session.add(response)
                self.session.flush()  # Get ID
                response.set_answer(answer_value)
                logger.debug(f"Created response for question {question_id}")
            
            # Update assessment status if needed
            if assessment.status == 'draft':
                assessment.status = 'in_progress'
                assessment.updated_at = datetime.now(timezone.utc)
            
            self.session.commit()
            return response
            
        except (ValidationError, AssessmentError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to submit response: {e}")
            raise AssessmentError(f"Response submission failed: {str(e)}")
    
    def get_assessment_progress(self, assessment_id: int) -> Dict[str, Any]:
        """
        Calculate and return assessment completion progress.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            Dictionary with progress information
        """
        try:
            assessment = self.get_assessment(assessment_id,
                                             include_responses=True)
            if not assessment:
                raise AssessmentError(f"Assessment {assessment_id} not found")
            
            # Get total questions count
            total_questions = self.session.query(func.count(Question.id)).scalar()
            
            # Get responded questions count
            responded_questions = len(assessment.responses)
            
            # Calculate progress percentage
            progress_percentage = (
                (responded_questions / total_questions * 100)
                if total_questions > 0 else 0
            )
            
            # Get progress by section
            section_progress = self._calculate_section_progress(assessment)
            
            # Determine if assessment is complete
            is_complete = responded_questions >= total_questions
            
            progress_data = {
                'assessment_id': assessment_id,
                'total_questions': total_questions,
                'responded_questions': responded_questions,
                'progress_percentage': round(progress_percentage, 1),
                'is_complete': is_complete,
                'section_progress': section_progress,
                'status': assessment.status,
                'last_response_date': max(
                    (r.timestamp for r in assessment.responses),
                    default=None
                )
            }
            
            logger.debug(f"Calculated progress for assessment {assessment_id}")
            return progress_data
            
        except AssessmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate progress: {e}")
            raise AssessmentError(f"Progress calculation failed: {str(e)}")
    
    def complete_assessment(self, assessment_id: int,
                            force: bool = False) -> Dict[str, Any]:
        """
        Complete an assessment and generate final scores and recommendations.
        
        Args:
            assessment_id: Assessment ID to complete
            force: Whether to force completion even if not all questions answered
            
        Returns:
            Dictionary with completion results including scores and
            recommendations
            
        Raises:
            AssessmentError: If completion fails or assessment incomplete
        """
        try:
            assessment = self.get_assessment(assessment_id,
                                             include_responses=True)
            if not assessment:
                raise AssessmentError(f"Assessment {assessment_id} not found")
            
            if assessment.status == 'completed':
                logger.info(f"Assessment {assessment_id} already completed")
                return self._get_completion_results(assessment)
            
            # Check completion status
            progress = self.get_assessment_progress(assessment_id)
            
            if not force and not progress['is_complete']:
                raise AssessmentError(
                    f"Assessment incomplete: {progress['responded_questions']}"
                    f"/{progress['total_questions']} questions answered"
                )
            
            # Calculate final scores
            scoring_results = self.scoring_service.calculate_assessment_score(
                assessment_id
            )
            
            # Generate recommendations
            recommendations = (
                self.recommendation_service.generate_assessment_recommendations(
                    assessment_id
                )
            )
            
            # Update assessment status and metadata
            completion_data = {
                'deviq_score': scoring_results['deviq_score'],
                'maturity_level': scoring_results['maturity_level'],
                'section_scores': scoring_results['section_scores'],
                'completion_date': datetime.now(timezone.utc).isoformat(),
                'total_recommendations': recommendations['total_recommendations']
            }
            
            assessment.status = 'completed'
            assessment.completed_at = datetime.now(timezone.utc)
            assessment.deviq_score = scoring_results['deviq_score']
            
            # Update metadata with completion data
            existing_metadata = assessment.metadata or {}
            existing_metadata.update(completion_data)
            assessment.metadata = existing_metadata
            
            self.session.commit()
            
            # Prepare completion results
            completion_results = {
                'assessment_id': assessment_id,
                'status': 'completed',
                'completion_date': assessment.completed_at,
                'scores': scoring_results,
                'recommendations': recommendations,
                'progress': progress
            }
            
            logger.info(f"Completed assessment {assessment_id} with DevIQ "
                        f"score {scoring_results['deviq_score']}")
            
            return completion_results
            
        except AssessmentError:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to complete assessment {assessment_id}: {e}")
            raise AssessmentError(f"Assessment completion failed: {str(e)}")
    
    def get_next_question(self, assessment_id: int) -> Optional[Question]:
        """
        Get the next unanswered question for an assessment.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            Next Question instance or None if all complete
        """
        try:
            assessment = self.get_assessment(assessment_id,
                                             include_responses=True)
            if not assessment:
                raise AssessmentError(f"Assessment {assessment_id} not found")
            
            # Get answered question IDs
            answered_question_ids = {r.question_id for r in assessment.responses}
            
            # Find first unanswered question (by display order)
            next_question = (
                self.session.query(Question)
                .join(Area)
                .join(Section)
                .filter(Question.id.notin_(answered_question_ids))
                .order_by(Section.display_order, Area.display_order,
                          Question.display_order)
                .first()
            )
            
            return next_question
            
        except Exception as e:
            logger.error(f"Failed to get next question: {e}")
            raise AssessmentError(f"Failed to get next question: {str(e)}")
    
    def _calculate_section_progress(self,
                                    assessment: Assessment) -> Dict[str, Any]:
        """Calculate progress by section."""
        try:
            # Get all sections with question counts
            sections_data = (
                self.session.query(
                    Section.id,
                    Section.name,
                    func.count(Question.id).label('total_questions')
                )
                .join(Area, Section.id == Area.section_id)
                .join(Question, Area.id == Question.area_id)
                .group_by(Section.id, Section.name)
                .all()
            )
            
            # Get responses grouped by section
            responded_by_section = {}
            for response in assessment.responses:
                question = response.question
                section_id = question.area.section_id
                
                if section_id not in responded_by_section:
                    responded_by_section[section_id] = 0
                responded_by_section[section_id] += 1
            
            # Calculate progress for each section
            section_progress = {}
            for section_id, section_name, total_questions in sections_data:
                responded = responded_by_section.get(section_id, 0)
                progress = ((responded / total_questions * 100)
                            if total_questions > 0 else 0)
                
                section_progress[section_name] = {
                    'section_id': section_id,
                    'total_questions': total_questions,
                    'responded_questions': responded,
                    'progress_percentage': round(progress, 1),
                    'is_complete': responded >= total_questions
                }
            
            return section_progress
            
        except Exception as e:
            logger.error(f"Failed to calculate section progress: {e}")
            return {}
    
    def _get_completion_results(self,
                                assessment: Assessment) -> Dict[str, Any]:
        """Get results for already completed assessment."""
        try:
            # Get cached results from metadata
            metadata = assessment.metadata or {}
            
            # If no cached results, recalculate
            if 'deviq_score' not in metadata:
                return self.complete_assessment(assessment.id, force=True)
            
            return {
                'assessment_id': assessment.id,
                'status': 'completed',
                'completion_date': assessment.completed_at,
                'deviq_score': metadata.get('deviq_score'),
                'maturity_level': metadata.get('maturity_level'),
                'section_scores': metadata.get('section_scores', {}),
                'total_recommendations': metadata.get(
                    'total_recommendations', 0
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get completion results: {e}")
            raise AssessmentError("Failed to retrieve completion results")
