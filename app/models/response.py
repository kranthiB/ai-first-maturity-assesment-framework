"""
Response Model for AFS Assessment Framework

This module defines the Response model for storing assessment answers
and related metadata.
"""

from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .base import Base


class Response(Base):
    """
    Assessment response model
    
    Represents an answer to a specific question within an assessment
    """
    
    __tablename__ = 'responses'
    
    # Primary key - matching actual database schema
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic fields - matching actual database schema
    score = Column(Integer, nullable=False)  # Score for this response (1-4)
    notes = Column(Text, nullable=True)  # Additional notes
    response_time_seconds = Column(Integer, nullable=True)  # Time spent
    timestamp = Column(DateTime, default=datetime.utcnow)  # Using timestamp
    
    # Foreign keys - using TEXT to match database schema
    assessment_id = Column(String, ForeignKey('assessments.id'), nullable=False)
    question_id = Column(String, ForeignKey('questions.id'), nullable=False)
    
    # Relationships
    assessment = relationship('Assessment', back_populates='responses')
    question = relationship('Question', back_populates='responses')
    
    # Constraints - matching actual database schema
    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 4", name='check_score_range'),
        CheckConstraint("response_time_seconds >= 0", 
                       name='check_response_time_positive'),
        Index('idx_responses_assessment', 'assessment_id', 'question_id'),
        Index('idx_responses_question', 'question_id', 'score'),
        Index('idx_responses_timestamp', 'timestamp'),
        Index('idx_responses_score_analysis', 'question_id', 'score', 'timestamp'),
        UniqueConstraint(
            'assessment_id', 'question_id',
            name='uq_response_assessment_question'
        ),
    )
    
    def __repr__(self) -> str:
        return (f"<Response(id={self.id}, assessment_id={self.assessment_id}, "
                f"question_id={self.question_id}, score={self.score})>")
    
    def validate(self) -> List[str]:
        """Validate response data"""
        errors = []
        
        if not self.assessment_id:
            errors.append("Assessment ID is required")
        
        if not self.question_id:
            errors.append("Question ID is required")
        
        if self.score is None:
            errors.append("Score is required")
        elif not (1 <= self.score <= 4):
            errors.append("Score must be between 1 and 4")
        
        if (self.response_time_seconds is not None and 
                self.response_time_seconds < 0):
            errors.append("Response time must be non-negative")
        
        return errors
    
    def set_answer(self, score: int, notes: str = None) -> None:
        """
        Set answer score and optional notes
        
        Args:
            score: Answer score (1-4)
            notes: Optional notes
        """
        if not (1 <= score <= 4):
            raise ValueError("Score must be between 1 and 4")
        
        self.score = score
        if notes:
            self.notes = notes
    
    def get_score_text(self) -> str:
        """
        Get human-readable score text
        
        Returns:
            Score description
        """
        score_map = {
            1: "Initial",
            2: "Developing", 
            3: "Defined",
            4: "Optimizing"
        }
        return score_map.get(self.score, "Unknown")
    
    def calculate_weighted_score(self) -> float:
        """
        Calculate weighted score based on question weight
        
        Returns:
            Weighted score
        """
        if self.score is None:
            return 0.0
        
        # Assuming equal weighting for now
        return float(self.score)
    
    def get_response_metadata(self) -> Dict[str, Any]:
        """
        Get response metadata
        
        Returns:
            Metadata dictionary
        """
        return {
            'response_time_seconds': self.response_time_seconds,
            'has_notes': bool(self.notes),
            'score': self.score,
            'score_text': self.get_score_text(),
            'weighted_score': self.calculate_weighted_score(),
            'max_possible_score': 4,
            'timestamp': self.timestamp
        }
    
    @property
    def is_answered(self) -> bool:
        """Check if response has been answered"""
        return self.score is not None
    
    @property
    def percentage_score(self) -> float:
        """Get percentage score for this response"""
        if self.score is None:
            return 0.0
        
        return (self.score / 4.0) * 100.0
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with additional computed fields"""
        result = {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question_id': self.question_id,
            'score': self.score,
            'notes': self.notes,
            'response_time_seconds': self.response_time_seconds,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
        
        # Add computed fields
        result['is_answered'] = self.is_answered
        result['percentage_score'] = self.percentage_score
        result['score_text'] = self.get_score_text()
        result['weighted_score'] = self.calculate_weighted_score()
        result['metadata'] = self.get_response_metadata()
        
        if include_relationships:
            if hasattr(self, 'assessment') and self.assessment:
                result['assessment'] = {
                    'id': self.assessment.id,
                    'team_name': self.assessment.team_name
                }
            if hasattr(self, 'question') and self.question:
                result['question'] = {
                    'id': self.question.id,
                    'question': self.question.question
                }
        
        return result


__all__ = ['Response']
