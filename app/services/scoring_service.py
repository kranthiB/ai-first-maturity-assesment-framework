"""
Scoring Service for AFS Assessment Framework
Calculates AFS scores and maturity classifications
"""

from typing import Dict, List
from sqlalchemy.orm import Session
import logging

from app.models.assessment import Assessment
from app.models.response import Response
from app.models.question import Question, Section, Area
from app.utils.scoring_utils import (
    ScoringConstants,
    calculate_weighted_average,
    classify_maturity_level, get_maturity_level_details,
    calculate_section_coverage, validate_score_inputs,
    format_score_display, calculate_improvement_potential
)

logger = logging.getLogger(__name__)


class ScoringService:
    """
    Main service for calculating AFS scores and maturity classifications
    """

    def __init__(self, session: Session):
        """
        Initialize scoring service with database session

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def calculate_assessment_score(self, assessment_id: int) -> Dict:
        """
        Calculate complete assessment score including DevIQ and maturity level

        Args:
            assessment_id: Assessment ID to score

        Returns:
            Dictionary with complete scoring results

        Raises:
            ValueError: If assessment not found or invalid
        """
        try:
            # Get assessment
            assessment = self.session.query(Assessment).filter_by(
                id=assessment_id
            ).first()

            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")

            logger.info(f"Calculating score for assessment {assessment_id}")

            # Calculate section scores
            section_scores = self._calculate_section_scores(assessment_id)

            # Calculate overall AFS score
            deviq_score = self._calculate_deviq_score(section_scores)

            # Classify maturity level
            maturity_level, level_name = classify_maturity_level(deviq_score)

            # Get detailed results
            results = {
                'assessment_id': assessment_id,
                'assessment_name': (assessment.team_name or 
                                  f"Assessment {assessment_id}"),
                'deviq_score': deviq_score,
                'deviq_score_display': format_score_display(deviq_score),
                'maturity_level': maturity_level.name,
                'maturity_level_display': level_name,
                'maturity_details': get_maturity_level_details(maturity_level),
                'section_scores': section_scores,
                'improvement_potential': calculate_improvement_potential(
                    deviq_score
                ),
                'completion_status': self._calculate_completion_status(
                    assessment_id
                ),
                'scoring_metadata': {
                    'calculation_timestamp': assessment.updated_at,
                    'total_responses': len(assessment.responses),
                    'scoring_version': '1.0'
                }
            }

            logger.info(f"Assessment {assessment_id} scored: "
                       f"DevIQ {deviq_score}, Level: {level_name}")

            return results

        except Exception as e:
            logger.error(f"Error calculating assessment score: {e}")
            raise

    def _calculate_section_scores(self, assessment_id: int) -> Dict:
        """
        Calculate scores for each section in the assessment

        Args:
            assessment_id: Assessment ID

        Returns:
            Dictionary with section scores and details
        """
        section_scores = {}

        # Get all sections
        sections = self.session.query(Section).order_by(
            Section.display_order
        ).all()

        for section in sections:
            try:
                score_data = self._calculate_single_section_score(
                    assessment_id, section.id
                )
                section_scores[section.name.lower().replace(' ', '_')] = {
                    'section_id': section.id,
                    'section_name': section.name,
                    'score': score_data['score'],
                    'score_display': format_score_display(score_data['score']),
                    'area_scores': score_data['area_scores'],
                    'coverage': score_data['coverage'],
                    'responses_count': score_data['responses_count'],
                    'total_questions': score_data['total_questions']
                }

            except Exception as e:
                logger.warning(f"Error calculating section {section.id}: {e}")
                # Set default values for failed section
                section_scores[section.name.lower().replace(' ', '_')] = {
                    'section_id': section.id,
                    'section_name': section.name,
                    'score': ScoringConstants.MIN_SCORE,
                    'score_display': format_score_display(
                        ScoringConstants.MIN_SCORE
                    ),
                    'area_scores': {},
                    'coverage': 0.0,
                    'responses_count': 0,
                    'total_questions': 0,
                    'error': str(e)
                }

        return section_scores

    def _calculate_single_section_score(self, assessment_id: int,
                                       section_id: int) -> Dict:
        """
        Calculate score for a single section

        Args:
            assessment_id: Assessment ID
            section_id: Section ID

        Returns:
            Dictionary with section score details
        """
        # Get all areas in this section
        areas = self.session.query(Area).filter_by(
            section_id=section_id
        ).order_by(Area.display_order).all()

        if not areas:
            return {
                'score': ScoringConstants.MIN_SCORE,
                'area_scores': {},
                'coverage': 0.0,
                'responses_count': 0,
                'total_questions': 0
            }

        area_scores = []
        area_weights = []
        area_details = {}
        total_responses = 0
        total_questions = 0

        for area in areas:
            area_data = self._calculate_area_score(assessment_id, area.id)
            area_scores.append(area_data['score'])
            area_weights.append(area_data['weight'])

            area_details[area.name.lower().replace(' ', '_')] = {
                'area_id': area.id,
                'area_name': area.name,
                'score': area_data['score'],
                'score_display': format_score_display(area_data['score']),
                'weight': area_data['weight'],
                'responses_count': area_data['responses_count'],
                'total_questions': area_data['total_questions'],
                'coverage': area_data['coverage']
            }

            total_responses += area_data['responses_count']
            total_questions += area_data['total_questions']

        # Calculate section score as weighted average of area scores
        if area_scores:
            validate_score_inputs(area_scores, area_weights)
            section_score = calculate_weighted_average(area_scores,
                                                      area_weights)
        else:
            section_score = ScoringConstants.MIN_SCORE

        # Calculate overall coverage
        coverage = calculate_section_coverage(total_responses, total_questions)

        return {
            'score': section_score,
            'area_scores': area_details,
            'coverage': coverage,
            'responses_count': total_responses,
            'total_questions': total_questions
        }

    def _calculate_area_score(self, assessment_id: int, area_id: int) -> Dict:
        """
        Calculate score for a single area

        Args:
            assessment_id: Assessment ID
            area_id: Area ID

        Returns:
            Dictionary with area score details
        """
        # Get all questions in this area with their responses
        questions = self.session.query(Question).filter_by(
            area_id=area_id
        ).order_by(Question.display_order).all()

        if not questions:
            return {
                'score': ScoringConstants.MIN_SCORE,
                'weight': 1.0,
                'responses_count': 0,
                'total_questions': 0,
                'coverage': 0.0
            }

        question_scores = []
        question_weights = []
        responses_count = 0

        for question in questions:
            # Get response for this question in this assessment
            response = self.session.query(Response).filter_by(
                assessment_id=assessment_id,
                question_id=question.id
            ).first()

            if response and response.score is not None:
                # Questions use 1-4 scale directly based on level selection
                # Normalize to ensure score is within expected range
                normalized_score = max(1.0, min(4.0, float(response.score)))
                question_scores.append(normalized_score)
                question_weights.append(1.0)  # Equal weight for all questions
                responses_count += 1
            else:
                # No response - don't include in average calculation
                # This maintains scoring integrity for incomplete assessments
                pass

        # Calculate area score
        if question_scores:
            validate_score_inputs(question_scores, question_weights)
            area_score = calculate_weighted_average(question_scores,
                                                   question_weights)
        else:
            area_score = ScoringConstants.MIN_SCORE

        # Calculate coverage
        coverage = calculate_section_coverage(responses_count, len(questions))

        return {
            'score': area_score,
            'weight': 1.0,  # Equal weighting for areas within sections
            'responses_count': responses_count,
            'total_questions': len(questions),
            'coverage': coverage
        }

    def _calculate_deviq_score(self, section_scores: Dict) -> float:
        """
        Calculate overall AFS score from section scores

        Args:
            section_scores: Dictionary of section scores

        Returns:
            Overall AFS score (1.0-4.0)
        """
        if not section_scores:
            return ScoringConstants.MIN_SCORE

        scores = []
        weights = []

        # Extract scores and weights for each section
        for section_key, section_data in section_scores.items():
            if 'score' in section_data and section_data['score'] is not None:
                scores.append(section_data['score'])
                # Use predefined weights or default to equal weighting
                weight = ScoringConstants.SECTION_WEIGHTS.get(
                    section_key, 0.25
                )
                weights.append(weight)

        if not scores:
            return ScoringConstants.MIN_SCORE

        # Validate and calculate weighted average
        validate_score_inputs(scores, weights)
        deviq_score = calculate_weighted_average(scores, weights)

        # Ensure score is within valid range
        deviq_score = max(ScoringConstants.MIN_SCORE,
                         min(ScoringConstants.MAX_SCORE, deviq_score))

        return round(deviq_score, 2)

    def _calculate_completion_status(self, assessment_id: int) -> Dict:
        """
        Calculate assessment completion status

        Args:
            assessment_id: Assessment ID

        Returns:
            Dictionary with completion statistics
        """
        # Get answered questions count
        answered_questions = self.session.query(Response).filter_by(
            assessment_id=assessment_id
        ).filter(
            Response.score.isnot(None)
        ).count()

        # Get total questions count
        total_questions = self.session.query(Question).count()

        # Calculate percentages
        completion_percentage = (answered_questions / total_questions * 100
                               if total_questions > 0 else 0)

        return {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'skipped_questions': 0,  # Not tracked in current schema
            'unanswered_questions': total_questions - answered_questions,
            'completion_percentage': round(completion_percentage, 1),
            'is_complete': completion_percentage >= 100.0,
            'is_substantial': completion_percentage >= 80.0  # 80% threshold
        }

    def get_section_benchmark(self, section_name: str) -> Dict:
        """
        Get benchmark data for a specific section

        Args:
            section_name: Name of the section

        Returns:
            Dictionary with benchmark information
        """
        # Industry benchmark data (would typically come from database)
        benchmarks = {
            'foundational_capabilities': {
                'industry_average': 2.1,
                'top_quartile': 2.8,
                'best_in_class': 3.5
            },
            'transformation_capabilities': {
                'industry_average': 1.9,
                'top_quartile': 2.6,
                'best_in_class': 3.3
            },
            'enterprise_integration': {
                'industry_average': 1.7,
                'top_quartile': 2.4,
                'best_in_class': 3.1
            },
            'strategic_governance': {
                'industry_average': 1.6,
                'top_quartile': 2.3,
                'best_in_class': 3.0
            }
        }

        section_key = section_name.lower().replace(' ', '_')
        return benchmarks.get(section_key, {
            'industry_average': 2.0,
            'top_quartile': 2.5,
            'best_in_class': 3.2
        })

    def calculate_score_trends(self, assessment_ids: List[int]) -> Dict:
        """
        Calculate scoring trends across multiple assessments

        Args:
            assessment_ids: List of assessment IDs to analyze

        Returns:
            Dictionary with trend analysis
        """
        if not assessment_ids:
            return {}

        trends = {
            'assessment_count': len(assessment_ids),
            'deviq_scores': [],
            'maturity_levels': [],
            'section_trends': {}
        }

        for assessment_id in assessment_ids:
            try:
                score_data = self.calculate_assessment_score(assessment_id)
                trends['deviq_scores'].append(score_data['deviq_score'])
                trends['maturity_levels'].append(
                    score_data['maturity_level']
                )

                # Track section trends
                for section_key, section_data in score_data[
                    'section_scores'
                ].items():
                    if section_key not in trends['section_trends']:
                        trends['section_trends'][section_key] = []
                    trends['section_trends'][section_key].append(
                        section_data['score']
                    )

            except Exception as e:
                logger.warning(f"Error processing assessment {assessment_id} "
                              f"for trends: {e}")

        return trends
