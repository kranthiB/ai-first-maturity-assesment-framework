"""
Response Model for AFS Assessment Framework

This module defines the Response model for storing assessment answers
and related metadata.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Float,
    CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates

from .base import BaseModel


class Response(BaseModel):
    """
    Assessment response model
    
    Represents an answer to a specific question within an assessment
    """
    
    __tablename__ = 'responses'
    
    # Override id to match database schema (INTEGER PRIMARY KEY AUTOINCREMENT)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic fields - matching actual database schema
    score = Column(Integer, nullable=False)  # Score for this response (1-4)
    notes = Column(Text, nullable=True)  # Additional notes
    response_time_seconds = Column(Integer, nullable=True)  # Time spent
    timestamp = Column(DateTime, default=datetime.utcnow)  # Using timestamp not created_at
    
    # Foreign keys - using TEXT to match database schema
    assessment_id = Column(String, ForeignKey('assessments.id'), 
                          nullable=False)
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
        UniqueConstraint('assessment_id', 'question_id',
                        name='uq_response_assessment_question'),
    )
    
    # Override BaseModel timestamp behavior
    def __init__(self, **kwargs):
        # Don't call BaseModel.__init__ to avoid created_at/updated_at
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self) -> str:
        return (f"<Response(id={self.id}, assessment_id={self.assessment_id}, "
                f"question_id={self.question_id}, score={self.score})>")
    
    def validate(self) -> List[str]:
        """Validate response data"""
        errors = super().validate()
        
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
        if not self.question or self.score is None:
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
            'max_possible_score': 4
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
        result = super().to_dict(include_relationships)
        
        # Add computed fields
        result['is_answered'] = self.is_answered
        result['percentage_score'] = self.percentage_score
        result['score_text'] = self.get_score_text()
        result['weighted_score'] = self.calculate_weighted_score()
        result['metadata'] = self.get_response_metadata()
        
        return result


class ResponseAnalytics(BaseModel):
    """
    Response analytics model for storing aggregated response data
    
    This model stores analytics data for responses to help with
    reporting and insights.
    """
    
    __tablename__ = 'response_analytics'
    
    # Reference fields
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    answer_value = Column(String(500), nullable=False)
    
    # Analytics data
    response_count = Column(Integer, default=0, nullable=False)
    total_score = Column(Float, default=0.0, nullable=False)
    average_score = Column(Float, default=0.0, nullable=False)
    min_score = Column(Float, default=0.0, nullable=False)
    max_score = Column(Float, default=0.0, nullable=False)
    
    # Time-based analytics
    average_response_time = Column(Float, nullable=True)  # In seconds
    
    # Last updated
    last_calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    question = relationship('Question')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("response_count >= 0", name='check_analytics_count_positive'),
        CheckConstraint("total_score >= 0", name='check_analytics_total_positive'),
        CheckConstraint("average_score >= 0", name='check_analytics_avg_positive'),
        CheckConstraint("min_score >= 0", name='check_analytics_min_positive'),
        CheckConstraint("max_score >= 0", name='check_analytics_max_positive'),
        Index('idx_analytics_question', 'question_id'),
        Index('idx_analytics_answer', 'answer_value'),
        Index('idx_analytics_calculated', 'last_calculated_at'),
        UniqueConstraint(
            'question_id', 'answer_value',
            name='uq_analytics_question_answer'
        ),
    )
    
    def __repr__(self) -> str:
        return (f"<ResponseAnalytics(question_id={self.question_id}, "
                f"answer='{self.answer_value}', count={self.response_count})>")
    
    def update_analytics(self, responses: List[Response]) -> None:
        """
        Update analytics data from list of responses
        
        Args:
            responses: List of responses for this question/answer combination
        """
        if not responses:
            self.response_count = 0
            self.total_score = 0.0
            self.average_score = 0.0
            self.min_score = 0.0
            self.max_score = 0.0
            self.average_response_time = None
        else:
            scores = [r.score for r in responses if r.score is not None]
            times = [r.response_time_seconds for r in responses 
                    if r.response_time_seconds is not None]
            
            self.response_count = len(responses)
            self.total_score = sum(scores)
            self.average_score = sum(scores) / len(scores) if scores else 0.0
            self.min_score = min(scores) if scores else 0.0
            self.max_score = max(scores) if scores else 0.0
            self.average_response_time = sum(times) / len(times) if times else None
        
        self.last_calculated_at = datetime.utcnow()


__all__ = ['Response', 'ResponseAnalytics']
