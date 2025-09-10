"""
Assessment blueprint routes for AFS Assessment Framework
"""

import json
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    jsonify, session, current_app, make_response
)
from sqlalchemy.orm import joinedload
from datetime import datetime

from app.models import Assessment, Section, Area, Question, Response
from app.services.assessment_service import AssessmentService
from app.services.scoring_service import ScoringService
from app.services.recommendation_service import RecommendationService
from app.utils.exceptions import AssessmentError, ValidationError
from app.utils.helpers import get_maturity_level, format_score_display
from app.core.logging import get_logger

logger = get_logger(__name__)

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')


def get_assessment_service():
    """Get assessment service instance with current database session"""
    from app.extensions import db
    return AssessmentService(db.session)


def get_scoring_service():
    """Get scoring service instance with current database session"""
    from app.extensions import db
    return ScoringService(db.session)


def get_recommendation_service():
    """Get recommendation service instance with current database session"""
    from app.extensions import db
    return RecommendationService(db.session)


def format_industry(industry_code):
    """Format industry code to human readable name"""
    industry_mapping = {
        'automotive': 'Automotive',
        'bfsi': 'Banking, Financial Services & Insurance',
        'energy_utilities': 'Energy & Utilities',
        'government': 'Government & Public Sector',
        'travel_transport_tourism': 'Travel, Transport & Tourism',
        'healthcare': 'Healthcare',
        'media_communications': 'Media & Communications',
        'retail_commerce': 'Retail & Commerce',
        'technology': 'Technology',
        'other': 'Other'
    }
    return industry_mapping.get(industry_code, industry_code.title())


def manage_assessment_session(assessment_id):
    """
    Manage assessment session state for user navigation
    
    Args:
        assessment_id: Assessment ID to track in session
    """
    session['current_assessment_id'] = assessment_id
    session['assessment_start_time'] = datetime.utcnow().isoformat()
    session.permanent = True  # Keep session across browser restarts


def get_current_assessment():
    """
    Get current assessment from session if available
    
    Returns:
        Assessment ID or None
    """
    return session.get('current_assessment_id')


def clear_assessment_session():
    """Clear assessment-related session data"""
    session.pop('current_assessment_id', None)
    session.pop('assessment_start_time', None)
    session.pop('assessment_responses', None)
    session.pop('assessment_metadata', None)


def validate_assessment_session(assessment_id):
    """
    Validate that the session assessment matches the requested assessment
    
    Args:
        assessment_id: Assessment ID to validate against session
    
    Returns:
        bool: True if session is valid, False otherwise
    """
    current_assessment = get_current_assessment()
    if current_assessment and current_assessment != assessment_id:
        return False
    return True


def update_session_activity():
    """Update session activity timestamp"""
    session['last_activity'] = datetime.utcnow().isoformat()


@assessment_bp.before_request
def before_assessment_request():
    """
    Pre-request processing for assessment routes
    """
    # Update session activity for assessment routes
    update_session_activity()
    
    # Set session timeout (optional - extend session for active users)
    session.permanent = True


@assessment_bp.errorhandler(404)
def assessment_not_found(error):
    """Handle 404 errors in assessment blueprint"""
    flash('The requested assessment or page was not found.', 'error')
    return redirect(url_for('assessment.index'))


@assessment_bp.errorhandler(500)
def assessment_server_error(error):
    """Handle 500 errors in assessment blueprint"""
    logger.error(f"Server error in assessment blueprint: {error}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('assessment.index'))


@assessment_bp.route('/')
def index():
    """
    Enhanced assessment overview page with search, filtering, and grid view
    """
    try:
        from app.extensions import db
        from sqlalchemy import or_, and_
        
        # Get search and filter parameters
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        # Build query with filters
        query = db.session.query(Assessment).filter(
            Assessment.status.isnot(None)
        )
        
        # Apply search filter
        if search_query:
            query = query.filter(
                or_(
                    Assessment.team_name.ilike(f'%{search_query}%'),
                    Assessment.id.like(f'%{search_query}%')
                )
            )
        
        # Apply status filter
        if status_filter and status_filter != 'all':
            query = query.filter(Assessment.status == status_filter)
        
        # Apply date filters
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Assessment.created_at >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Assessment.created_at <= date_to_obj)
            except ValueError:
                pass
        
        # Order by most recent
        query = query.order_by(Assessment.updated_at.desc())
        
        # Paginate results
        assessments_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        assessments = assessments_pagination.items
        
        # Add maturity levels to assessments
        for assessment in assessments:
            maturity = get_maturity_level(assessment.overall_score)
            assessment.maturity_level = maturity
        
        # Get framework statistics
        total_questions = db.session.query(Question).count()
        sections = db.session.query(Section).order_by(
            Section.display_order
        ).all()
        
        # Get assessment statistics
        total_assessments = db.session.query(Assessment).filter(
            Assessment.status.isnot(None)
        ).count()
        completed_assessments = db.session.query(Assessment).filter(
            Assessment.status == 'COMPLETED'
        ).count()
        in_progress_assessments = db.session.query(Assessment).filter(
            Assessment.status == 'IN_PROGRESS'
        ).count()
        
        # Get unique statuses for filter dropdown
        status_options = db.session.query(Assessment.status).filter(
            Assessment.status.isnot(None)
        ).distinct().all()
        status_options = [status[0] for status in status_options if status[0]]
        
        context = {
            'assessments': assessments,
            'pagination': assessments_pagination,
            'total_questions': total_questions,
            'sections': sections or [],
            'total_sections': len(sections) if sections else 4,
            'total_assessments': total_assessments,
            'completed_assessments': completed_assessments,
            'in_progress_assessments': in_progress_assessments,
            'status_options': status_options,
            'search_query': search_query,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'current_page': page,
            'per_page': per_page
        }
        
        return render_template('pages/assessment/index.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading assessment index: {e}")
        flash('Error loading assessments', 'error')
        # Provide safe defaults
        return render_template('pages/assessment/index.html', 
                               assessments=[], 
                               sections=[], 
                               total_questions=24,
                               total_sections=4)


@assessment_bp.route('/start')
def start():
    """
    Assessment start page with basic information collection
    """
    try:
        from app.extensions import db
        
        # Get framework overview for display
        sections = db.session.query(Section).options(
            joinedload(Section.areas)
        ).order_by(Section.display_order).all()
        
        total_questions = db.session.query(Question).count()
        estimated_time = max(15, (total_questions * 1.5))  # 1.5 min per question
        
        context = {
            'sections': sections,
            'total_questions': total_questions,
            'estimated_time': int(estimated_time)
        }
        
        return render_template('pages/assessment/start.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading assessment start page: {e}")
        return render_template('pages/assessment/start.html')


@assessment_bp.route('/create', methods=['GET', 'POST'])
def create():
    """
    Simplified Linear Assessment Creation Flow
    Step 1: Collect organization + candidate details, then proceed directly to first section
    """
    if request.method == 'GET':
        # Show the organization and candidate information form
        return render_template('pages/assessment/org_information.html')
    
    # POST method - from form submission
    try:
        # Get form data for organization and candidate
        organization_name = request.form.get('organization_name', '').strip()
        account_name = request.form.get('account_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        industry = request.form.get('industry', '').strip()
        
        # Get optional assessor information
        assessor_name = request.form.get('assessor_name', '').strip()
        assessor_email = request.form.get('assessor_email', '').strip()
        
        # Validate required fields
        if not organization_name:
            flash('Organization name is required', 'error')
            return render_template('pages/assessment/org_information.html')
        
        if not account_name:
            flash('Account name is required', 'error')
            return render_template('pages/assessment/org_information.html')
        
        if not first_name or not last_name:
            flash('First name and last name are required', 'error')
            return render_template('pages/assessment/org_information.html')
        
        if not email:
            flash('Email address is required', 'error')
            return render_template('pages/assessment/org_information.html')
        
        if not industry:
            flash('Please select an industry', 'error')
            return render_template('pages/assessment/org_information.html')
        
        # Create assessment using the existing database schema
        from app.extensions import db
        from app.models import Assessment
        from app.models.question import Section
        
        # Get the first section before creating assessment to avoid session issues
        first_section = db.session.query(Section).order_by(Section.display_order).first()
        if not first_section:
            flash('No assessment sections found. Please contact support.', 'error')
            return render_template('pages/assessment/org_information.html')
        
        assessment = Assessment()
        assessment.team_name = account_name
        assessment.organization_name = organization_name
        assessment.account_name = account_name
        assessment.first_name = first_name
        assessment.last_name = last_name
        assessment.email = email
        assessment.industry = industry
        assessment.assessor_name = assessor_name if assessor_name else None
        assessment.assessor_email = assessor_email if assessor_email else None
        assessment.status = 'IN_PROGRESS'
        assessment.created_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()
        
        db.session.add(assessment)
        db.session.flush()  # Get the ID without committing yet
        
        # Store the assessment ID before commit
        assessment_id = assessment.id
        
        # Set up comprehensive session management with candidate details BEFORE commit
        manage_assessment_session(assessment_id)
        
        # Initialize response tracking and metadata in session BEFORE commit
        session['assessment_responses'] = {}
        session['assessment_metadata'] = {
            'organization_name': organization_name,
            'account_name': account_name,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'industry': industry,
            'assessor_name': assessor_name,
            'assessor_email': assessor_email,
            'created_at': datetime.utcnow().isoformat(),
            'current_section_index': 0,
            'assessment_id': assessment_id  # Store ID in session for reliability
        }
        
        # Now commit the transaction - everything is set up
        db.session.commit()
        
        # Log successful creation
        logger.info(f"Assessment {assessment_id} successfully created and committed")
        
        logger.info(f"Found first section: {first_section.id} - {first_section.name}")
        flash(f'Assessment created for {first_name} {last_name}. Starting with {first_section.name}!', 'success')
        logger.info(f"Assessment created: {assessment_id} for {organization_name}, proceeding to section {first_section.id}")
        
        # Redirect directly to the first section's questions
        return redirect(url_for('assessment.section_questions', 
                                assessment_id=assessment_id,
                                section_id=first_section.id))
        
    except ValidationError as e:
        flash(f'Validation error: {str(e)}', 'error')
        logger.warning(f"Assessment validation error: {str(e)}")
        return render_template('pages/assessment/org_information.html')
    except AssessmentError as e:
        flash(f'Assessment error: {str(e)}', 'error')
        logger.error(f"Assessment creation error: {str(e)}")
        return render_template('pages/assessment/org_information.html')
    except Exception as e:
        flash('An unexpected error occurred while creating the assessment. Please try again.', 'error')
        logger.error(f"Unexpected error in assessment creation: {str(e)}")
        return render_template('pages/assessment/org_information.html')


@assessment_bp.route('/<int:assessment_id>/section-overview')
def section_overview(assessment_id):
    """
    Step 2: Overview of assessment sections before starting questions
    """
    try:
        from app.extensions import db
        
        # Get assessment
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Validate session consistency
        current_assessment = get_current_assessment()
        if current_assessment != assessment_id:
            flash('Session mismatch. Please restart the assessment.', 'warning')
            clear_assessment_session()
            return redirect(url_for('assessment.index'))
        
        # Get all sections with their areas for overview
        sections = db.session.query(Section).options(
            joinedload(Section.areas)
        ).order_by(Section.display_order).all()
        
        # Get metadata from session
        metadata = session.get('assessment_metadata', {})
        
        context = {
            'assessment': assessment,
            'sections': sections,
            'metadata': metadata,
            'total_questions': sum(len(section.areas) for section in sections)
        }
        
        return render_template('pages/assessment/section_overview.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading section overview: {e}")
        flash('Error loading assessment overview', 'error')
        return redirect(url_for('assessment.index'))


@assessment_bp.route('/<int:assessment_id>/section/<section_id>')
def section_questions(assessment_id, section_id):
    """
    Step 3: Questions for a specific section
    """
    try:
        from app.extensions import db
        
        # Check session first to verify this is a valid request
        if 'assessment_metadata' not in session:
            logger.error(f"No session data for assessment {assessment_id}")
            flash('Assessment session expired. Please start a new assessment.', 'error')
            return redirect(url_for('assessment.create'))
            
        session_assessment_id = session['assessment_metadata'].get('assessment_id')
        if session_assessment_id != assessment_id:
            logger.error(f"Session assessment ID {session_assessment_id} doesn't match URL {assessment_id}")
            flash('Assessment session mismatch. Please start a new assessment.', 'error')
            return redirect(url_for('assessment.create'))
        
        # Now try to get the assessment from database
        assessment = db.session.get(Assessment, assessment_id)
        
        # If not found in DB but session is valid, create a temporary assessment object
        if not assessment:
            logger.warning(f"Assessment {assessment_id} not in DB yet, using session data")
            # Create a minimal assessment object for the template
            assessment = type('Assessment', (), {
                'id': assessment_id,
                'team_name': session['assessment_metadata'].get('organization_name'),
                'status': 'IN_PROGRESS'
            })()
        
        # Get section with areas and questions
        section = db.session.query(Section).options(
            joinedload(Section.areas).joinedload(Area.questions)
        ).filter(Section.id == section_id).first()
        
        if not section:
            logger.error(f"Section {section_id} not found")
            flash('Section not found', 'error')
            return redirect(url_for('assessment.create'))
        
        # Get progression data for each area in the section
        from app.models.progression import get_all_progressions_for_area
        area_progressions = {}
        for area in section.areas:
            progressions = get_all_progressions_for_area(area.id)
            # Convert MaturityProgression objects to dictionaries for JSON serialization
            area_progressions[area.id] = {
                level: progression.to_dict() 
                for level, progression in progressions.items()
            }
        
        # Get all sections for navigation
        all_sections = db.session.query(Section).order_by(
            Section.display_order).all()
        
        # Find current section index
        current_section_index = next(
            (i for i, s in enumerate(all_sections) if s.id == section_id), 0
        )
        
        # Update session metadata
        session['assessment_metadata']['current_section_index'] = current_section_index
        session['assessment_metadata']['assessment_id'] = assessment.id
        question_ids = []
        for area in section.areas:
            question_ids.extend([q.id for q in area.questions])
        
        existing_responses = {}
        if question_ids:
            responses = db.session.query(Response).filter(
                Response.assessment_id == assessment_id,
                Response.question_id.in_(question_ids)
            ).all()
            existing_responses = {r.question_id: r for r in responses}
        
        context = {
            'assessment': assessment,
            'section': section,
            'all_sections': all_sections,
            'current_section_index': current_section_index,
            'total_sections': len(all_sections),
            'existing_responses': existing_responses,
            'is_last_section': current_section_index == len(all_sections) - 1,
            'area_progressions': area_progressions
        }
        
        return render_template('pages/assessment/section_questions.html', 
                               **context)
        
    except Exception as e:
        logger.error(f"Error loading section questions: {e}")
        flash('Error loading section questions', 'error')
        return redirect(url_for('assessment.section_overview',
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/section/<section_id>/submit', 
                     methods=['POST'])
def submit_section_responses(assessment_id, section_id):
    """
    Submit all responses for a section
    """
    print(f"DEBUG: Function called with assessment_id={assessment_id}, section_id={section_id}")
    logger.info(f"=== SUBMIT FUNCTION CALLED: assessment_id={assessment_id}, section_id={section_id} ===")
    
    try:
        from app.extensions import db
        
        logger.info(f"Submitting section {section_id} for assessment {assessment_id}")
        
        # Try different approaches to get the assessment
        try:
            # First try: commit and refresh session
            db.session.commit()
            assessment = db.session.query(Assessment).get(assessment_id)
        except:
            # Second try: create new session
            db.session.rollback()
            assessment = db.session.query(Assessment).filter(Assessment.id == assessment_id).first()
        
        if not assessment:
            # Third try: get from session data if it exists
            if 'current_assessment_id' in session and session['current_assessment_id'] == assessment_id:
                # Create a mock assessment object with the data we need
                from app.models.assessment import Assessment as AssessmentModel
                assessment = AssessmentModel()
                assessment.id = assessment_id
                # Get team name from session metadata
                if 'assessment_metadata' in session:
                    assessment.team_name = session['assessment_metadata'].get('organization_name', 'Unknown')
                else:
                    assessment.team_name = 'Unknown'
                assessment.status = 'IN_PROGRESS'
                logger.info(f"Using session data for assessment {assessment_id}")
            else:
                logger.error(f"Assessment {assessment_id} not found anywhere")
                flash('Assessment not found', 'error')
                return redirect(url_for('assessment.index'))
        
        section = db.session.query(Section).get(section_id)
        
        logger.info(f"Assessment query result: {assessment}")
        logger.info(f"Section query result: {section}")
        
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found in database")
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
            
        if not section:
            logger.error(f"Section {section_id} not found in database")
            flash('Section not found', 'error')
            return redirect(url_for('assessment.index'))
        
        logger.info(f"Found assessment: {assessment.team_name}, section: {section.name}")
        
        # Process all responses for this section
        responses_data = {}
        notes_data = {}
        
        # Extract response data from form
        for key, value in request.form.items():
            if key.startswith('response_'):
                question_id = key.replace('response_', '')
                responses_data[question_id] = value
                logger.info(f"Response for {question_id}: {value}")
            elif key.startswith('notes_'):
                question_id = key.replace('notes_', '')
                notes_data[question_id] = value
        
        logger.info(f"Collected {len(responses_data)} responses")
        
        # Save or update responses directly to avoid transaction isolation issues
        for question_id, answer_value in responses_data.items():
            if answer_value:  # Only save if response provided
                # Check if response already exists
                existing_response = db.session.query(Response).filter(
                    Response.assessment_id == assessment_id,
                    Response.question_id == question_id
                ).first()
                
                if existing_response:
                    # Update existing response
                    existing_response.score = int(answer_value)
                    existing_response.timestamp = datetime.utcnow()
                    logger.info(f"Updated response for {question_id}: {answer_value}")
                else:
                    # Create new response
                    new_response = Response(
                        assessment_id=assessment_id,
                        question_id=question_id,
                        score=int(answer_value),
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(new_response)
                    logger.info(f"Created new response for {question_id}: {answer_value}")
        
        # Commit the responses
        db.session.commit()
        logger.info("All responses committed successfully")
        
        # Update session tracking - ensure session dict exists
        if 'assessment_responses' not in session:
            session['assessment_responses'] = {}
        session['assessment_responses'].update(responses_data)
        
        # Determine next action
        all_sections = db.session.query(Section).order_by(
            Section.display_order).all()
        current_index = next(
            (i for i, s in enumerate(all_sections) if s.id == section_id), 0
        )
        
        if current_index < len(all_sections) - 1:
            # Go to next section
            next_section = all_sections[current_index + 1]
            flash(f'Section "{section.name}" completed successfully!', 'success')
            return redirect(url_for('assessment.section_questions',
                                    assessment_id=assessment_id,
                                    section_id=next_section.id))
        else:
            # All sections completed, go to final review
            flash('All sections completed! Ready for final review.', 'success')
            return redirect(url_for('assessment.final_review',
                                    assessment_id=assessment_id))
        
    except Exception as e:
        print(f"DEBUG: Exception in submit_section_responses: {e}")
        logger.error(f"Error submitting section responses: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        flash('Error saving responses. Please try again.', 'error')
        return redirect(url_for('assessment.section_questions',
                                assessment_id=assessment_id,
                                section_id=section_id))


@assessment_bp.route('/<int:assessment_id>/final-review')
def final_review(assessment_id):
    """
    Step 4: Final review before generating report
    """
    try:
        from app.extensions import db
        
        # Get assessment with responses
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            # Try session fallback for transaction isolation issues
            assessment_metadata = session.get('assessment_metadata', {})
            if assessment_metadata.get('assessment_id') == assessment_id:
                # Create temporary assessment object for review
                class TempAssessment:
                    def __init__(self, id, team_name, status='IN_PROGRESS'):
                        self.id = id
                        self.team_name = team_name
                        self.status = status
                        self.overall_score = None
                        self.created_at = None
                        self.completion_date = None
                
                assessment = TempAssessment(
                    assessment_id, 
                    assessment_metadata.get('team_name', 'Unknown Organization')
                )
                logger.info(f"Using session data for final review of assessment {assessment_id}")
            else:
                flash('Assessment not found', 'error')
                return redirect(url_for('assessment.index'))
        
        # Get all sections with responses
        sections = db.session.query(Section).options(
            joinedload(Section.areas).joinedload(Area.questions)
        ).order_by(Section.display_order).all()
        
        # Get all responses for this assessment
        responses = db.session.query(Response).filter(
            Response.assessment_id == assessment_id
        ).all()
        responses_dict = {r.question_id: r for r in responses}
        
        # Calculate completion statistics
        total_questions = 0
        answered_questions = 0
        
        for section in sections:
            for area in section.areas:
                for question in area.questions:
                    total_questions += 1
                    if question.id in responses_dict:
                        answered_questions += 1
        
        completion_percentage = (
            (answered_questions / total_questions * 100) 
            if total_questions > 0 else 0
        )
        
        # Get metadata from session or create basic metadata
        metadata = session.get('assessment_metadata', {})
        if not metadata:
            metadata = {
                'team_name': getattr(assessment, 'team_name', 'Organization'),
                'assessment_id': assessment_id,
                'created_at': str(getattr(assessment, 'created_at', '')),
            }
        
        context = {
            'assessment': assessment,
            'sections': sections,
            'responses': responses_dict,
            'metadata': metadata,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_percentage': completion_percentage,
            'can_generate_report': completion_percentage >= 80
        }
        
        logger.info(f"Final review loaded for assessment {assessment_id}, completion: {completion_percentage:.1f}%")
        return render_template('pages/assessment/final_review.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading final review: {e}")
        flash('Error loading final review', 'error')
        return redirect(url_for('assessment.section_questions',
                                assessment_id=assessment_id, section_id='SG'))


@assessment_bp.route('/<int:assessment_id>/generate-report', methods=['POST'])
def generate_report(assessment_id):
    """
    Generate the final assessment report
    """
    try:
        from app.extensions import db
        from sqlalchemy import text
        
        logger.info(f"Starting report generation for assessment {assessment_id}")
        
        # Get assessment using id (schema has been fixed)
        result = db.session.execute(
            text('SELECT * FROM assessments WHERE id = :assessment_id'),
            {'assessment_id': assessment_id}
        )
        assessment_row = result.fetchone()
        
        if not assessment_row:
            logger.error(f"Assessment {assessment_id} not found")
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        logger.info(f"Found assessment {assessment_id}, status: {assessment_row.status}")
        
        # Check if assessment is already completed
        if assessment_row.status == 'COMPLETED':
            flash('Assessment is already completed', 'info')
            return redirect(url_for('assessment.report', 
                                    assessment_id=assessment_id))
        
        # Get responses to check completion
        responses = db.session.query(Response).filter_by(
            assessment_id=assessment_id
        ).all()
        logger.info(f"Found {len(responses)} responses for assessment {assessment_id}")
        
        # Get all questions for completion calculation
        from sqlalchemy import func
        total_questions = db.session.query(func.count(Question.id)).scalar()
        answered_questions = len(responses) if responses else 0
        completion_percentage = (
            (answered_questions / total_questions * 100) 
            if total_questions > 0 else 0
        )
        
        logger.info(
            f"Completion: {answered_questions}/{total_questions} "
            f"({completion_percentage:.1f}%)"
        )
        
        # Check completion requirements
        force_complete = request.form.get('force_complete', 'false') == 'true'
        if not force_complete and completion_percentage < 80:
            flash(
                'Assessment must be at least 80% complete before finalization. '
                'Please answer more questions or use force completion.', 
                'warning'
            )
            return redirect(url_for('assessment.final_review', 
                                    assessment_id=assessment_id))
        
        # Mark assessment as completed and calculate basic scores
        try:
            logger.info(f"Starting completion process for assessment {assessment_id}")
            
            # Get responses by section for scoring
            responses_by_section = {}
            for response in responses:
                question = db.session.get(Question, response.question_id)
                if question and question.area:
                    section_id = question.area.section_id
                    if section_id not in responses_by_section:
                        responses_by_section[section_id] = []
                    responses_by_section[section_id].append(response)
            
            # Calculate section scores (average of responses in each section)
            section_scores = {}
            for section_id, section_responses in responses_by_section.items():
                if section_responses:
                    scores = [
                        r.score for r in section_responses 
                        if r.score
                    ]
                    section_scores[section_id] = (
                        sum(scores) / len(scores) if scores else 0
                    )
            
            logger.info(f"Section scores calculated: {section_scores}")
            
            # Calculate overall score
            scores = [score for score in section_scores.values() if score > 0]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Set DevIQ classification based on overall score
            if overall_score >= 3.5:
                deviq_classification = 'Optimized'
            elif overall_score >= 2.5:
                deviq_classification = 'Advanced'
            elif overall_score >= 1.5:
                deviq_classification = 'Evolving'
            else:
                deviq_classification = 'Basic'
            
            logger.info(
                f"Assessment completion data: "
                f"overall_score={overall_score}, "
                f"classification={deviq_classification}"
            )
            
            # Prepare metadata for storage in results_json
            metadata = session.get('assessment_metadata', {})
            assessment_results = {
                'scores': section_scores,
                'overall_score': overall_score,
                'deviq_classification': deviq_classification,
                'metadata': {
                    'organization_name': metadata.get('organization_name'),
                    'account_name': metadata.get('account_name'),
                    'first_name': metadata.get('first_name'),
                    'last_name': metadata.get('last_name'),
                    'email': metadata.get('email'),
                    'industry': metadata.get('industry'),
                    'created_at': metadata.get('created_at'),
                    'completion_date': datetime.utcnow().isoformat()
                }
            }
            
            # Update assessment using raw SQL (since SQLAlchemy model has schema mismatch)
            db.session.execute(text('''
                UPDATE assessments SET 
                    status = 'COMPLETED',
                    completion_date = CURRENT_TIMESTAMP,
                    overall_score = :overall_score,
                    deviq_classification = :deviq_classification,
                    foundational_score = :foundational_score,
                    transformation_score = :transformation_score,
                    enterprise_score = :enterprise_score,
                    governance_score = :governance_score,
                    results_json = :results_json,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :assessment_id
            '''), {
                'overall_score': overall_score,
                'deviq_classification': deviq_classification,
                'foundational_score': section_scores.get('FC', 0),
                'transformation_score': section_scores.get('TC', 0),
                'enterprise_score': section_scores.get('EI', 0),
                'governance_score': section_scores.get('SG', 0),
                'results_json': json.dumps(assessment_results),
                'assessment_id': assessment_id
            })
            
            # Commit the changes
            db.session.commit()
            logger.info(f"Assessment {assessment_id} committed to database")
            
            # Clear session data as assessment is complete
            clear_assessment_session()
            
            logger.info(f"Assessment {assessment_id} completed successfully")
            flash('Assessment completed successfully! Your report is now available.', 'success')
            return redirect(url_for('assessment.report', 
                                    assessment_id=assessment_id))
            
        except Exception as scoring_error:
            logger.error(f"Error during assessment completion: {scoring_error}")
            db.session.rollback()
            flash('Error occurred during completion. Please try again.', 'warning')
            return redirect(url_for('assessment.final_review', 
                                    assessment_id=assessment_id))
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        flash('Error generating report. Please try again.', 'error')
        return redirect(url_for('assessment.final_review', 
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>')
def detail(assessment_id):
    """
    Assessment detail view - redirects to read-only assessment view
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        # Get assessment to verify it exists
        assessment = assessment_service.get_assessment(assessment_id)
        
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Redirect to read-only organization information view
        return redirect(url_for('assessment.view_readonly',
                                assessment_id=assessment_id))
        
    except Exception as e:
        logger.error(f"Error loading assessment detail: {e}")
        flash('Error loading assessment', 'error')
        return redirect(url_for('assessment.index'))


@assessment_bp.route('/<int:assessment_id>/view')
def view_readonly(assessment_id):
    """
    Read-only view of assessment - organization information page
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        # Get assessment with responses
        assessment = assessment_service.get_assessment(
            assessment_id, include_responses=True
        )
        
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Get progress information
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        context = {
            'assessment': assessment,
            'progress': progress,
            'readonly': True
        }
        
        return render_template('pages/assessment/readonly_org_info.html',
                               **context)
        
    except Exception as e:
        logger.error(f"Error loading assessment readonly view: {e}")
        flash('Error loading assessment', 'error')
        return redirect(url_for('assessment.index'))


@assessment_bp.route('/<int:assessment_id>/view/sections')
def view_readonly_sections(assessment_id):
    """
    Read-only view of assessment - sections overview
    """
    try:
        from app.extensions import db
        
        # Get assessment
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Get all sections with their areas
        sections = db.session.query(Section).options(
            joinedload(Section.areas)
        ).order_by(Section.display_order).all()
        
        # Get progress information
        assessment_service = AssessmentService(db.session)
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        context = {
            'assessment': assessment,
            'sections': sections,
            'progress': progress,
            'readonly': True,
            'total_questions': sum(len(section.areas) for section in sections)
        }
        
        return render_template(
            'pages/assessment/readonly_section_overview.html',
            **context)
        
    except Exception as e:
        logger.error(f"Error loading readonly sections overview: {e}")
        flash('Error loading assessment', 'error')
        return redirect(url_for('assessment.index'))


@assessment_bp.route('/<int:assessment_id>/view/section/<section_id>')
def view_readonly_section(assessment_id, section_id):
    """
    Read-only view of assessment - specific section with responses
    """
    try:
        from app.extensions import db
        
        # Get assessment
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Get section with areas and questions
        section = db.session.query(Section).options(
            joinedload(Section.areas).joinedload(Area.questions)
        ).filter(Section.id == section_id).first()
        
        if not section:
            flash('Section not found', 'error')
            return redirect(url_for('assessment.view_readonly_sections',
                                    assessment_id=assessment_id))
        
        # Get all responses for this assessment
        responses = db.session.query(Response).filter(
            Response.assessment_id == assessment_id
        ).all()
        
        # Create responses dictionary for easy lookup
        responses_dict = {resp.question_id: resp for resp in responses}
        
        # Get all sections for navigation
        all_sections = db.session.query(Section).order_by(
            Section.display_order).all()
        
        # Find current section index
        current_section_index = 0
        for i, s in enumerate(all_sections):
            if s.id == section.id:
                current_section_index = i
                break
        
        # Get progress information
        assessment_service = AssessmentService(db.session)
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        context = {
            'assessment': assessment,
            'section': section,
            'responses': responses_dict,
            'all_sections': all_sections,
            'current_section_index': current_section_index,
            'progress': progress,
            'readonly': True
        }
        
        return render_template(
            'pages/assessment/readonly_section_questions.html',
            **context)
        
    except Exception as e:
        logger.error(f"Error loading readonly section view: {e}")
        flash('Error loading section', 'error')
        return redirect(url_for('assessment.view_readonly_sections',
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/question')
@assessment_bp.route('/<int:assessment_id>/question/<int:question_id>')
def question(assessment_id, question_id=None):
    """
    Assessment question page
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        # Get assessment
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Check if assessment is completed
        if assessment.status == 'COMPLETED':
            return redirect(url_for('assessment.report', 
                                    assessment_id=assessment_id))
        
        # Get specific question or next question
        if question_id:
            question_obj = db.session.query(Question).filter(
                Question.id == question_id
            ).first()
        else:
            question_obj = assessment_service.get_next_question(assessment_id)
        
        if not question_obj:
            # No more questions, redirect to completion
            return redirect(url_for('assessment.complete', 
                                    assessment_id=assessment_id))
        
        # Get existing response if any
        existing_response = db.session.query(Response).filter(
            Response.assessment_id == assessment_id,
            Response.question_id == question_obj.id
        ).first()
        
        # Get progress
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        # Get question navigation context
        all_questions = db.session.query(Question).join(Area).join(
            Section
        ).order_by(
            Section.display_order, Area.display_order, Question.display_order
        ).all()
        
        current_index = next(
            (i for i, q in enumerate(all_questions) if q.id == question_obj.id),
            0
        )
        
        prev_question = all_questions[current_index - 1] if current_index > 0 else None
        next_question_obj = (
            all_questions[current_index + 1] 
            if current_index < len(all_questions) - 1 else None
        )
        
        context = {
            'assessment': assessment,
            'question': question_obj,
            'existing_response': existing_response,
            'progress': progress,
            'current_index': current_index + 1,
            'total_questions': len(all_questions),
            'prev_question': prev_question,
            'next_question': next_question_obj
        }
        
        return render_template('pages/assessment/question.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading question: {e}")
        flash('Error loading question', 'error')
        return redirect(url_for('assessment.detail', 
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/submit', methods=['POST'])
def submit_response(assessment_id):
    """
    Submit a response to an assessment question with enhanced validation 
    and session management
    """
    try:
        # Validate session consistency
        current_assessment = get_current_assessment()
        if current_assessment and current_assessment != assessment_id:
            flash('Session mismatch. Please restart the assessment.', 'warning')
            clear_assessment_session()
            return redirect(url_for('assessment.index'))
        
        assessment_service = get_assessment_service()
        
        # Get form data with validation
        question_id = request.form.get('question_id', type=int)
        answer_value = request.form.get('answer_value', '').strip()
        notes = request.form.get('notes', '').strip()
        next_action = request.form.get('next_action', 'next')
        
        # Validate required fields
        if not question_id:
            flash('Question ID is required', 'error')
            return redirect(url_for('assessment.question', 
                                    assessment_id=assessment_id))
        
        if not answer_value:
            flash('Please select an answer before proceeding', 'error')
            return redirect(url_for('assessment.question', 
                                    assessment_id=assessment_id,
                                    question_id=question_id))
        
        # Validate answer value range
        try:
            answer_int = int(answer_value)
            if answer_int < 1 or answer_int > 5:
                flash('Answer must be between 1 and 5', 'error')
                return redirect(url_for('assessment.question',
                                        assessment_id=assessment_id,
                                        question_id=question_id))
        except ValueError:
            flash('Invalid answer format', 'error')
            return redirect(url_for('assessment.question',
                                    assessment_id=assessment_id,
                                    question_id=question_id))
        
        # Submit response with notes
        response_data = {
            'assessment_id': assessment_id,
            'question_id': question_id,
            'answer_value': answer_value,
            'notes': notes if notes else None
        }
        
        response = assessment_service.submit_response(**response_data)
        
        # Update session tracking
        if 'assessment_responses' not in session:
            session['assessment_responses'] = {}
        session['assessment_responses'][str(question_id)] = {
            'answer_value': answer_value,
            'notes': notes,
            'submitted_at': datetime.utcnow().isoformat()
        }
        
        # Log response submission
        logger.info(f"Response submitted for assessment {assessment_id}, "
                   f"question {question_id}: {answer_value}")
        
        # Handle navigation based on next_action
        return handle_navigation(assessment_id, question_id, next_action)
        
    except ValidationError as e:
        flash(f'Validation error: {str(e)}', 'error')
        logger.warning(f"Response validation error: {str(e)}")
        return redirect(url_for('assessment.question',
                                assessment_id=assessment_id,
                                question_id=question_id))
    except AssessmentError as e:
        flash(f'Assessment error: {str(e)}', 'error')
        logger.error(f"Assessment submission error: {str(e)}")
        return redirect(url_for('assessment.question',
                                assessment_id=assessment_id,
                                question_id=question_id))
    except Exception as e:
        flash('An unexpected error occurred while submitting your response.', 'error')
        logger.error(f"Unexpected error submitting response: {str(e)}")
        return redirect(url_for('assessment.question',
                                assessment_id=assessment_id))


def handle_navigation(assessment_id, current_question_id, next_action):
    """
    Handle assessment navigation after response submission
    
    Args:
        assessment_id: ID of current assessment
        current_question_id: ID of question just answered
        next_action: Navigation action ('next', 'prev', 'complete')
    
    Returns:
        Flask redirect response
    """
    try:
        from app.extensions import db
        assessment_service = get_assessment_service()
        
        if next_action == 'prev':
            # Navigate to previous question
            all_questions = db.session.query(Question).join(Area).join(
                Section
            ).order_by(
                Section.display_order, Area.display_order, Question.display_order
            ).all()
            
            current_index = next(
                (i for i, q in enumerate(all_questions) 
                 if q.id == current_question_id), 0
            )
            
            if current_index > 0:
                prev_question_id = all_questions[current_index - 1].id
                return redirect(url_for('assessment.question',
                                        assessment_id=assessment_id,
                                        question_id=prev_question_id))
            else:
                return redirect(url_for('assessment.question',
                                        assessment_id=assessment_id))
        
        elif next_action == 'complete':
            # Complete assessment
            return redirect(url_for('assessment.complete',
                                    assessment_id=assessment_id))
        
        else:
            # Next question (default)
            next_question = assessment_service.get_next_question(assessment_id)
            if next_question:
                return redirect(url_for('assessment.question',
                                        assessment_id=assessment_id,
                                        question_id=next_question.id))
            else:
                # No more questions, redirect to completion
                return redirect(url_for('assessment.complete',
                                        assessment_id=assessment_id))
    
    except Exception as e:
        logger.error(f"Navigation error: {str(e)}")
        return redirect(url_for('assessment.question',
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/complete')
def complete(assessment_id):
    """
    Complete assessment and show completion page
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        # Get assessment
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        # Check if already completed
        if assessment.status == 'COMPLETED':
            return redirect(url_for('assessment.report',
                                    assessment_id=assessment_id))
        
        # Get progress to check if ready for completion
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        context = {
            'assessment': assessment,
            'progress': progress,
            'can_complete': progress['progress_percentage'] >= 80
        }
        
        return render_template('pages/assessment/complete.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading completion page: {e}")
        flash('Error loading completion page', 'error')
        return redirect(url_for('assessment.detail',
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/finalize', methods=['POST'])
def finalize(assessment_id):
    """
    Finalize assessment with complete scoring and recommendation integration
    """
    try:
        # Validate session consistency
        current_assessment = get_current_assessment()
        if current_assessment and current_assessment != assessment_id:
            flash('Session mismatch. Please restart the assessment.', 'warning')
            clear_assessment_session()
            return redirect(url_for('assessment.index'))
        
        assessment_service = get_assessment_service()
        scoring_service = get_scoring_service()
        recommendation_service = get_recommendation_service()
        
        # Get assessment and validate status
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        if assessment.status == 'COMPLETED':
            flash('Assessment is already completed', 'info')
            return redirect(url_for('assessment.report',
                                    assessment_id=assessment_id))
        
        # Check completion requirements
        force_complete = request.form.get('force_complete', 'false') == 'true'
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        # Validate completion criteria
        if not force_complete and progress['progress_percentage'] < 80:
            flash('Assessment must be at least 80% complete before finalization. '
                  'Please answer more questions or use force completion.', 'warning')
            return redirect(url_for('assessment.complete',
                                    assessment_id=assessment_id))
        
        # Complete assessment with scoring
        try:
            # Step 1: Mark assessment as completed
            completed_assessment = assessment_service.complete_assessment(
                assessment_id, force=force_complete
            )
            
            # Step 2: Calculate comprehensive scores
            scoring_results = scoring_service.calculate_assessment_score(
                assessment_id
            )
            
            # Step 3: Generate recommendations
            recommendations = recommendation_service.generate_recommendations(
                assessment_id, scoring_results
            )
            
            # Step 4: Update assessment with final results
            assessment_service.update_assessment_results(
                assessment_id,
                scores=scoring_results,
                recommendations=recommendations
            )
            
            # Clear session data as assessment is complete
            clear_assessment_session()
            
            # Log completion
            metadata = session.get('assessment_metadata', {})
            organization = metadata.get('organization', 'Unknown')
            assessor = metadata.get('assessor_name', 'Unknown')
            
            logger.info(f"Assessment {assessment_id} completed successfully "
                       f"for {organization} by {assessor}")
            
            flash('Assessment completed successfully! Your report is now available.', 'success')
            return redirect(url_for('assessment.report',
                                    assessment_id=assessment_id))
            
        except Exception as scoring_error:
            logger.error(f"Error during assessment scoring/completion: {scoring_error}")
            flash('Error occurred during scoring. Assessment saved but may need manual review.', 'warning')
            return redirect(url_for('assessment.report',
                                    assessment_id=assessment_id))
        
    except ValidationError as e:
        flash(f'Validation error: {str(e)}', 'error')
        logger.warning(f"Assessment finalization validation error: {str(e)}")
        return redirect(url_for('assessment.complete',
                                assessment_id=assessment_id))
    except AssessmentError as e:
        flash(f'Assessment error: {str(e)}', 'error')
        logger.error(f"Assessment finalization error: {str(e)}")
        return redirect(url_for('assessment.complete',
                                assessment_id=assessment_id))
    except Exception as e:
        flash('An unexpected error occurred during assessment finalization.', 'error')
        logger.error(f"Unexpected error in assessment finalization: {str(e)}")
        return redirect(url_for('assessment.complete',
                                assessment_id=assessment_id))
        
    except AssessmentError as e:
        flash(f'Error completing assessment: {str(e)}', 'error')
        return redirect(url_for('assessment.complete',
                                assessment_id=assessment_id))
    except Exception as e:
        logger.error(f"Error finalizing assessment: {e}")
        flash('Error finalizing assessment', 'error')
        return redirect(url_for('assessment.complete',
                                assessment_id=assessment_id))





def _calculate_assessment_duration(assessment):
    """
    Calculate assessment duration in human-readable format
    
    Args:
        assessment: Assessment object with created_at and completion_date timestamps
    
    Returns:
        str: Human-readable duration
    """
    try:
        if assessment.completion_date and assessment.created_at:
            duration = assessment.completion_date - assessment.created_at
            total_minutes = int(duration.total_seconds() / 60)
            
            if total_minutes < 60:
                return f"{total_minutes} minutes"
            else:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                if minutes > 0:
                    return f"{hours} hours {minutes} minutes"
                else:
                    return f"{hours} hours"
        
        return "Duration not available"
    except Exception:
        return "Duration not available"


@assessment_bp.route('/<int:assessment_id>/report')
def report(assessment_id):
    """
    Modern, interactive assessment report with charts and roadmap
    """
    try:
        from app.extensions import db
        from sqlalchemy.orm import joinedload
        from app.models.progression import get_all_progressions_for_area
        
        # Get assessment
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        if assessment.status != 'COMPLETED':
            flash('Assessment not completed yet', 'warning')
            return redirect(url_for('assessment.detail',
                                    assessment_id=assessment_id))
        
        # Get all sections with areas and questions
        sections = db.session.query(Section).options(
            joinedload(Section.areas).joinedload(Area.questions)
        ).order_by(Section.display_order).all()
        
        # Get all responses for this assessment
        responses = db.session.query(Response).filter(
            Response.assessment_id == assessment_id
        ).all()
        responses_dict = {r.question_id: r for r in responses}
        
        # Calculate detailed scores
        section_scores = []
        area_scores = {}
        all_scores = []
        
        for section in sections:
            section_responses = []
            section_areas = []
            
            for area in section.areas:
                area_responses = []
                for question in area.questions:
                    if question.id in responses_dict:
                        response_score = responses_dict[question.id].score
                        area_responses.append(response_score)
                
                if area_responses:
                    area_score = sum(area_responses) / len(area_responses)
                    area_scores[area.id] = {
                        'score': area_score,
                        'name': area.name,
                        'responses_count': len(area_responses),
                        'max_possible': len(area.questions) * 4
                    }
                    section_responses.extend(area_responses)
                    section_areas.append({
                        'id': area.id,
                        'name': area.name,
                        'score': area_score,
                        'level': _get_maturity_level_from_score(area_score),
                        'responses_count': len(area_responses)
                    })
            
            if section_responses:
                section_score = sum(section_responses) / len(section_responses)
                all_scores.extend(section_responses)
                
                section_scores.append({
                    'id': section.id,
                    'name': section.name,
                    'score': section_score,
                    'level': _get_maturity_level_from_score(section_score),
                    'color': _get_section_color(section.id),
                    'areas': section_areas,
                    'responses_count': len(section_responses),
                    'percentage': round((section_score / 4.0) * 100, 1)
                })
        
        # Calculate overall metrics
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        overall_level = _get_maturity_level_from_score(overall_score)
        
        # Generate roadmap data for each answered question
        roadmap_data = {}
        for question_id, response in responses_dict.items():
            question = db.session.query(Question).get(question_id)
            if question and question.area:
                area_id = question.area.id
                current_level = response.score
                
                # Get progression data for next levels
                progressions = get_all_progressions_for_area(area_id)
                next_levels = []
                
                # Up to level 4
                for target_level in range(current_level + 1, 5):
                    if target_level in progressions:
                        prog = progressions[target_level]
                        next_levels.append({
                            'level': target_level,
                            'prerequisites': _parse_progression_text(
                                prog.prerequisites
                            ),
                            'action_items': _parse_progression_text(
                                prog.action_items
                            ),
                            'success_metrics': _parse_progression_text(
                                prog.success_metrics
                            ),
                            'timeline': prog.timeline,
                            'common_pitfalls': _parse_progression_text(
                                prog.common_pitfall
                            )
                        })
                
                if next_levels:
                    roadmap_data[question_id] = {
                        'question': question.question,
                        'area_name': question.area.name,
                        'current_level': current_level,
                        'current_description': _get_level_description(
                            question, current_level
                        ),
                        'next_levels': next_levels
                    }
        
        # Prepare chart data
        chart_data = {
            'section_scores': [
                {'name': s['name'], 'score': s['score'], 'color': s['color']}
                for s in section_scores
            ],
            'maturity_distribution': _calculate_maturity_distribution(
                section_scores
            ),
            'area_comparison': [
                {
                    'name': area['name'],
                    'score': area['score'],
                    'section': section['name']
                }
                for section in section_scores
                for area in section['areas']
            ]
        }
        
        # Generate insights and recommendations
        insights = _generate_insights(section_scores, overall_score)
        priority_areas = _identify_priority_areas(section_scores)
        
        context = {
            'assessment': assessment,
            'overall_score': overall_score,
            'overall_level': overall_level,
            'section_scores': section_scores,
            'area_scores': area_scores,
            'chart_data': chart_data,
            'roadmap_data': roadmap_data,
            'insights': insights,
            'priority_areas': priority_areas,
            'responses_count': len(responses_dict),
            'total_questions': sum(
                len(area.questions)
                for section in sections
                for area in section.areas
            ),
            'completion_date': assessment.completion_date,
            'organization_name': (
                assessment.organization_name or assessment.team_name
            )
        }
        
        return render_template('pages/assessment/report.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading report: {e}")
        flash('Error loading report', 'error')
        return redirect(url_for('assessment.detail',
                                assessment_id=assessment_id))


def _get_maturity_level_from_score(score):
    """Convert numeric score to maturity level name"""
    if score >= 3.5:
        return 'AI-First'
    elif score >= 2.5:
        return 'AI-Augmented'
    elif score >= 1.5:
        return 'AI-Assisted'
    else:
        return 'Traditional'


def _get_section_color(section_id):
    """Get color for section based on ID"""
    colors = {
        'FC': '#3b82f6',  # Blue
        'TC': '#10b981',  # Green
        'EI': '#f59e0b',  # Yellow
        'SG': '#ef4444'   # Red
    }
    return colors.get(section_id, '#6b7280')


def _parse_progression_text(text):
    """Parse progression text into list items"""
    if not text:
        return []
    return [item.strip() for item in text.split('|') if item.strip()]


def _get_level_description(question, level):
    """Get description for specific level of a question"""
    level_descriptions = {
        1: question.level_1_desc,
        2: question.level_2_desc,
        3: question.level_3_desc,
        4: question.level_4_desc
    }
    return level_descriptions.get(level, '')


def _calculate_maturity_distribution(section_scores):
    """Calculate distribution of maturity levels across sections"""
    distribution = {
        'Traditional': 0,
        'AI-Assisted': 0,
        'AI-Augmented': 0,
        'AI-First': 0
    }
    
    for section in section_scores:
        level = section['level']
        if level in distribution:
            distribution[level] += 1
    
    return distribution


def _generate_insights(section_scores, overall_score):
    """Generate key insights from the assessment results"""
    insights = []
    
    if not section_scores:
        return insights
    
    # Find strongest and weakest sections
    strongest = max(section_scores, key=lambda x: x['score'])
    weakest = min(section_scores, key=lambda x: x['score'])
    
    insights.append({
        'type': 'strength',
        'title': f"Strongest Area: {strongest['name']}",
        'description': (
            f"Your organization excels in {strongest['name']} "
            f"with a score of {strongest['score']:.1f}"
        ),
        'icon': 'trophy'
    })
    
    insights.append({
        'type': 'improvement',
        'title': f"Priority for Improvement: {weakest['name']}",
        'description': (
            f"{weakest['name']} scored {weakest['score']:.1f} and offers "
            f"the greatest opportunity for advancement"
        ),
        'icon': 'target'
    })
    
    # Score variance insight
    scores = [s['score'] for s in section_scores]
    variance = max(scores) - min(scores)
    
    if variance > 1.5:
        insights.append({
            'type': 'warning',
            'title': 'Uneven Maturity Distribution',
            'description': (
                f'Large gap ({variance:.1f} points) between highest and '
                f'lowest scoring areas suggests focused improvement needed'
            ),
            'icon': 'exclamation-triangle'
        })
    elif variance < 0.5:
        insights.append({
            'type': 'success',
            'title': 'Consistent Maturity Levels',
            'description': (
                'Your organization shows consistent maturity across '
                'all assessment areas'
            ),
            'icon': 'check-circle'
        })
    
    return insights


def _identify_priority_areas(section_scores):
    """Identify priority areas for improvement"""
    if not section_scores:
        return []
    
    # Sort by score ascending to get lowest scores first
    sorted_sections = sorted(section_scores, key=lambda x: x['score'])
    
    priority_areas = []
    for i, section in enumerate(sorted_sections[:3]):  # Top 3 priority areas
        priority_areas.append({
            'rank': i + 1,
            'name': section['name'],
            'score': section['score'],
            'level': section['level'],
            'color': section['color'],
            'areas': section['areas'][:2],  # Top 2 areas within section
            'improvement_potential': round((4.0 - section['score']), 1)
        })
    
    return priority_areas


@assessment_bp.route('/<int:assessment_id>/progress')
def progress(assessment_id):
    """
    Assessment progress page for tracking completion
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        # Get assessment and progress
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))
        
        progress_data = assessment_service.get_assessment_progress(
            assessment_id
        )
        
        context = {
            'assessment': assessment,
            'progress': progress_data
        }
        
        return render_template('pages/assessment/progress.html', **context)
        
    except Exception as e:
        logger.error(f"Error loading progress: {e}")
        flash('Error loading progress', 'error')
        return redirect(url_for('assessment.detail',
                                assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/download-pdf')
def download_pdf(assessment_id):
    """
    Generate and download PDF report
    """
    try:
        from playwright.sync_api import sync_playwright
        from app.extensions import db
        from sqlalchemy.orm import joinedload
        from app.models.progression import get_all_progressions_for_area
        import tempfile
        import os
        
        # Get assessment data (reuse the same logic as report route)
        assessment = db.session.query(Assessment).get(assessment_id)
        if not assessment:
            flash('Assessment not found', 'error')
            return redirect(url_for('assessment.index'))

        if assessment.status != 'COMPLETED':
            flash('Assessment not completed yet', 'warning')
            return redirect(url_for('assessment.detail',
                                    assessment_id=assessment_id))

        # Get all sections with areas and questions
        sections = db.session.query(Section).options(
            joinedload(Section.areas).joinedload(Area.questions)
        ).order_by(Section.display_order).all()

        # Get all responses for this assessment
        responses = db.session.query(Response).filter(
            Response.assessment_id == assessment_id
        ).all()
        responses_dict = {r.question_id: r for r in responses}

        # Calculate detailed scores (same logic as report route)
        section_scores = []
        area_scores = {}
        all_scores = []

        for section in sections:
            section_responses = []
            section_areas = []

            for area in section.areas:
                area_responses = []
                for question in area.questions:
                    if question.id in responses_dict:
                        response_score = responses_dict[question.id].score
                        area_responses.append(response_score)

                if area_responses:
                    area_score = sum(area_responses) / len(area_responses)
                    area_scores[area.id] = {
                        'score': area_score,
                        'name': area.name,
                        'responses_count': len(area_responses),
                        'max_possible': len(area.questions) * 4
                    }
                    section_responses.extend(area_responses)
                    section_areas.append({
                        'id': area.id,
                        'name': area.name,
                        'score': area_score,
                        'level': _get_maturity_level_from_score(area_score),
                        'responses_count': len(area_responses)
                    })

            if section_responses:
                section_score = sum(section_responses) / len(section_responses)
                all_scores.extend(section_responses)

                section_scores.append({
                    'id': section.id,
                    'name': section.name,
                    'score': section_score,
                    'level': _get_maturity_level_from_score(section_score),
                    'color': _get_section_color(section.id),
                    'areas': section_areas,
                    'responses_count': len(section_responses),
                    'percentage': round((section_score / 4.0) * 100, 1)
                })

        # Calculate overall metrics
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        overall_level = _get_maturity_level_from_score(overall_score)

        # Generate chart data
        chart_data = {
            'section_scores': section_scores,
            'maturity_distribution': _calculate_maturity_distribution(section_scores)
        }

        # Generate roadmap data for each answered question
        roadmap_data = {}
        for question_id, response in responses_dict.items():
            question = db.session.query(Question).get(question_id)
            if question and question.area:
                area_id = question.area.id
                current_level = response.score

                # Get progression data for next levels
                progressions = get_all_progressions_for_area(area_id)
                next_levels = []

                # Up to level 4
                for target_level in range(current_level + 1, 5):
                    if target_level in progressions:
                        prog = progressions[target_level]
                        next_levels.append({
                            'level': target_level,
                            'level_name': _get_maturity_level_from_score(target_level),
                            'prerequisites': _parse_progression_text(prog.prerequisites),
                            'action_items': _parse_progression_text(prog.action_items),
                            'success_metrics': _parse_progression_text(prog.success_metrics),
                            'timeline': prog.timeline,
                            'common_pitfalls': _parse_progression_text(prog.common_pitfall),
                            'description': prog.prerequisites  # Fallback
                        })

                if next_levels:
                    roadmap_data[question_id] = {
                        'question': question.question,
                        'area': question.area.name,
                        'area_name': question.area.name,  # For template compatibility
                        'current_level': current_level,
                        'current_level_name': _get_maturity_level_from_score(current_level),
                        'current_description': _get_level_description(question, current_level),
                        'next_levels': next_levels
                    }

        # Generate insights and recommendations
        insights = _generate_insights(section_scores, overall_score)
        priority_areas = _identify_priority_areas(section_scores)

        context = {
            'assessment': assessment,
            'overall_score': overall_score,
            'overall_level': overall_level,
            'section_scores': section_scores,
            'area_scores': area_scores,
            'chart_data': chart_data,
            'roadmap_data': roadmap_data,
            'insights': insights,
            'priority_areas': priority_areas,
            'responses_count': len(responses_dict),
            'total_questions': sum(
                len(area.questions)
                for section in sections
                for area in section.areas
            ),
            'completion_date': assessment.completion_date,
            'organization_name': (
                assessment.organization_name or assessment.team_name
            ),
            'is_pdf': True  # Flag to indicate PDF generation
        }

        # Render the same template with PDF-specific styling
        html_content = render_template('pages/assessment/report_pdf.html', **context)
        
        # Generate PDF using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Set HTML content
            page.set_content(html_content, wait_until='networkidle')
            
            # Generate PDF with options
            pdf_bytes = page.pdf(
                format='A4',
                margin={
                    'top': '0.75in',
                    'right': '0.75in', 
                    'bottom': '0.75in',
                    'left': '0.75in'
                },
                print_background=True,
                prefer_css_page_size=True
            )
            
            browser.close()
        
        # Create response with team name in filename
        team_name = assessment.team_name or assessment.organization_name or "Unknown_Team"
        # Clean team name for filename (remove special characters)
        clean_team_name = "".join(c for c in team_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_team_name = clean_team_name.replace(' ', '_')
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="AI_Maturity_Assessment_Report_{clean_team_name}.pdf"'
        
        return response
        
    except ImportError as e:
        flash('PDF generation not available. Please install Playwright.', 'error')
        return redirect(url_for('assessment.report', assessment_id=assessment_id))
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        flash('Error generating PDF report', 'error')
        return redirect(url_for('assessment.report', assessment_id=assessment_id))


@assessment_bp.route('/api/<int:assessment_id>/progress')
def api_progress(assessment_id):
    """
    API endpoint for assessment progress
    """
    try:
        from app.extensions import db
        assessment_service = AssessmentService(db.session)
        
        progress = assessment_service.get_assessment_progress(assessment_id)
        
        return jsonify({
            'status': 'success',
            'data': progress,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching progress: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch progress',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
