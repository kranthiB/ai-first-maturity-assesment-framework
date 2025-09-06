"""
Questions API Routes - RESTful endpoints for question operations

Task 4.1: Questions API Endpoints
Provides access to questions by section, area, and individual question operations.
"""

from flask import request, current_app
from flask_restful import Resource
from sqlalchemy.orm import sessionmaker

from app.models import Question, Section, Area, Response
from app.models.database import DatabaseManager
from app.core.logging import get_logger


logger = get_logger(__name__)


class QuestionListResource(Resource):
    """Resource for handling question collection operations."""
    
    def get(self):
        """
        Get list of questions with optional filtering.
        
        Query Parameters:
            section_id: Filter by section ID
            area_id: Filter by area ID
            difficulty: Filter by difficulty level
            limit: Limit number of results (default: 100)
            offset: Offset for pagination (default: 0)
            
        Returns:
            JSON response with question list and metadata
        """
        try:
            # Get query parameters
            section_id = request.args.get('section_id', type=int)
            area_id = request.args.get('area_id', type=int)
            difficulty = request.args.get('difficulty')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            # Validate parameters
            if limit > 200:
                limit = 200
            if offset < 0:
                offset = 0
                
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                # Build query
                query = session.query(Question)
                
                # Apply filters
                if section_id:
                    query = query.join(Area).join(Section).filter(
                        Section.id == section_id
                    )
                
                if area_id:
                    query = query.filter(Question.area_id == area_id)
                
                if difficulty:
                    query = query.filter(Question.difficulty == difficulty)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and get results
                questions = query.offset(offset).limit(limit).all()
                
                # Serialize questions
                question_data = []
                for question in questions:
                    question_dict = question.to_dict()
                    
                    # Add area and section information
                    if question.area:
                        question_dict['area'] = {
                            'id': question.area.id,
                            'name': question.area.name,
                            'section_id': question.area.section_id
                        }
                        
                        if question.area.section:
                            question_dict['section'] = {
                                'id': question.area.section.id,
                                'name': question.area.section.name
                            }
                    
                    question_data.append(question_dict)
                
                response_data = {
                    'questions': question_data,
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_next': offset + limit < total_count,
                        'has_prev': offset > 0
                    },
                    'filters': {
                        'section_id': section_id,
                        'area_id': area_id,
                        'difficulty': difficulty
                    }
                }
                
                logger.info(
                    f"Retrieved {len(question_data)} questions "
                    f"(total: {total_count})"
                )
                
                return response_data, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error retrieving questions: {e}")
            return {
                'error': 'Failed to retrieve questions',
                'message': str(e)
            }, 500


class QuestionResource(Resource):
    """Resource for handling individual question operations."""
    
    def get(self, question_id):
        """
        Get specific question by ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            JSON response with question data
        """
        try:
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                # Get question
                question = session.query(Question).filter(
                    Question.id == question_id
                ).first()
                
                if not question:
                    return {
                        'error': 'Question not found',
                        'message': f'Question {question_id} does not exist'
                    }, 404
                
                # Serialize question
                question_dict = question.to_dict()
                
                # Add area and section information
                if question.area:
                    question_dict['area'] = {
                        'id': question.area.id,
                        'name': question.area.name,
                        'description': question.area.description,
                        'section_id': question.area.section_id
                    }
                    
                    if question.area.section:
                        question_dict['section'] = {
                            'id': question.area.section.id,
                            'name': question.area.section.name,
                            'description': question.area.section.description
                        }
                
                logger.info(f"Retrieved question: {question_id}")
                
                return question_dict, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error retrieving question {question_id}: {e}")
            return {
                'error': 'Failed to retrieve question',
                'message': str(e)
            }, 500


class SectionQuestionsResource(Resource):
    """Resource for handling section-specific question operations."""
    
    def get(self, section_id):
        """
        Get all questions for a specific section.
        
        Args:
            section_id: Section ID
            
        Query Parameters:
            area_id: Filter by specific area within section
            difficulty: Filter by difficulty level
            include_responses: Include response data if assessment_id provided
            assessment_id: Assessment ID for response data
            
        Returns:
            JSON response with section questions organized by area
        """
        try:
            # Get query parameters
            area_id = request.args.get('area_id', type=int)
            difficulty = request.args.get('difficulty')
            include_responses = request.args.get('include_responses', 
                                               'false').lower() == 'true'
            assessment_id = request.args.get('assessment_id', type=int)
            
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                # Check if section exists
                section = session.query(Section).filter(
                    Section.id == section_id
                ).first()
                
                if not section:
                    return {
                        'error': 'Section not found',
                        'message': f'Section {section_id} does not exist'
                    }, 404
                
                # Build query for areas in section
                areas_query = session.query(Area).filter(
                    Area.section_id == section_id
                )
                
                if area_id:
                    areas_query = areas_query.filter(Area.id == area_id)
                
                areas = areas_query.all()
                
                # Get questions for each area
                section_data = {
                    'section': section.to_dict(),
                    'areas': []
                }
                
                for area in areas:
                    # Build questions query
                    questions_query = session.query(Question).filter(
                        Question.area_id == area.id
                    )
                    
                    if difficulty:
                        questions_query = questions_query.filter(
                            Question.difficulty == difficulty
                        )
                    
                    questions = questions_query.all()
                    
                    # Serialize questions
                    question_data = []
                    for question in questions:
                        question_dict = question.to_dict()
                        
                        # Add response data if requested
                        if include_responses and assessment_id:
                            response = session.query(Response).filter(
                                Response.assessment_id == assessment_id,
                                Response.question_id == question.id
                            ).first()
                            
                            if response:
                                question_dict['response'] = response.to_dict()
                        
                        question_data.append(question_dict)
                    
                    area_data = area.to_dict()
                    area_data['questions'] = question_data
                    area_data['question_count'] = len(question_data)
                    
                    section_data['areas'].append(area_data)
                
                # Add summary statistics
                total_questions = sum(len(area['questions']) 
                                    for area in section_data['areas'])
                section_data['summary'] = {
                    'total_areas': len(section_data['areas']),
                    'total_questions': total_questions
                }
                
                logger.info(
                    f"Retrieved {total_questions} questions "
                    f"for section {section_id}"
                )
                
                return section_data, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error retrieving questions for section {section_id}: {e}"
            )
            return {
                'error': 'Failed to retrieve section questions',
                'message': str(e)
            }, 500


class AreaQuestionsResource(Resource):
    """Resource for handling area-specific question operations."""
    
    def get(self, area_id):
        """
        Get all questions for a specific area.
        
        Args:
            area_id: Area ID
            
        Query Parameters:
            difficulty: Filter by difficulty level
            include_responses: Include response data if assessment_id provided
            assessment_id: Assessment ID for response data
            
        Returns:
            JSON response with area questions and metadata
        """
        try:
            # Get query parameters
            difficulty = request.args.get('difficulty')
            include_responses = request.args.get('include_responses', 
                                               'false').lower() == 'true'
            assessment_id = request.args.get('assessment_id', type=int)
            
            # Get database session
            db_manager = DatabaseManager(current_app)
            Session = sessionmaker(bind=db_manager.get_adapter().get_engine())
            session = Session()
            
            try:
                # Check if area exists
                area = session.query(Area).filter(Area.id == area_id).first()
                
                if not area:
                    return {
                        'error': 'Area not found',
                        'message': f'Area {area_id} does not exist'
                    }, 404
                
                # Build questions query
                questions_query = session.query(Question).filter(
                    Question.area_id == area_id
                )
                
                if difficulty:
                    questions_query = questions_query.filter(
                        Question.difficulty == difficulty
                    )
                
                questions = questions_query.all()
                
                # Serialize questions
                question_data = []
                for question in questions:
                    question_dict = question.to_dict()
                    
                    # Add response data if requested
                    if include_responses and assessment_id:
                        response = session.query(Response).filter(
                            Response.assessment_id == assessment_id,
                            Response.question_id == question.id
                        ).first()
                        
                        if response:
                            question_dict['response'] = response.to_dict()
                    
                    question_data.append(question_dict)
                
                # Build response
                area_data = area.to_dict()
                
                # Add section information
                if area.section:
                    area_data['section'] = {
                        'id': area.section.id,
                        'name': area.section.name,
                        'description': area.section.description
                    }
                
                response_data = {
                    'area': area_data,
                    'questions': question_data,
                    'summary': {
                        'total_questions': len(question_data),
                        'difficulty_distribution': {}
                    }
                }
                
                # Calculate difficulty distribution
                for question in questions:
                    difficulty_level = question.difficulty or 'unspecified'
                    response_data['summary']['difficulty_distribution'][
                        difficulty_level
                    ] = response_data['summary']['difficulty_distribution'].get(
                        difficulty_level, 0
                    ) + 1
                
                logger.info(
                    f"Retrieved {len(question_data)} questions for area {area_id}"
                )
                
                return response_data, 200
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(
                f"Error retrieving questions for area {area_id}: {e}"
            )
            return {
                'error': 'Failed to retrieve area questions',
                'message': str(e)
            }, 500
