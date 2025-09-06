"""
Question Model for AFS Assessment Framework

This module defines the Question model and related entities for
the assessment framework.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Boolean, 
    CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates

from .base import BaseModel


class Section(BaseModel):
    """
    Assessment section model
    
    Represents major sections of the assessment framework
    (e.g., "Development Practices", "Testing", "Deployment")
    """
    
    __tablename__ = 'sections'
    
    # Override the id to match database schema (TEXT instead of Integer)
    id = Column(String, primary_key=True)
    
    # Basic fields - matching actual database schema
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    color = Column(Text, default='#3b82f6', nullable=True)
    icon = Column(Text, default='fas fa-cog', nullable=True)
    
    # Relationships
    areas = relationship(
        'Area', 
        back_populates='section',
        cascade='all, delete-orphan',
        order_by='Area.display_order'
    )
    
    # Constraints
    __table_args__ = (
        # No additional constraints needed for now
    )
        Index('idx_section_active', 'is_active'),
        UniqueConstraint('name', name='uq_section_name'),
    )
    
    def __repr__(self) -> str:
        return f"<Section(id={self.id}, name='{self.name}')>"
    
    def validate(self) -> List[str]:
        """Validate section data"""
        errors = super().validate()
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Section name is required")
        
        if len(self.name) > 100:
            errors.append("Section name must be 100 characters or less")
        
        if self.display_order < 0:
            errors.append("Display order must be non-negative")
        
        return errors
    
    @property
    def question_count(self) -> int:
        """Get total number of questions in this section"""
        return sum(area.question_count for area in self.areas)
    
    @property
    def active_areas(self):
        """Get active areas in this section"""
        return [area for area in self.areas if area.is_active == 'Y']


class Area(BaseModel):
    """
    Assessment area model
    
    Represents specific areas within sections
    (e.g., "Code Quality", "Automated Testing", "CI/CD Pipeline")
    """
    
    __tablename__ = 'areas'
    
    # Basic fields
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(String(1), default='Y', nullable=False)
    
    # Foreign keys
    section_id = Column(Integer, ForeignKey('sections.id'), nullable=False)
    
    # Relationships
    section = relationship('Section', back_populates='areas')
    questions = relationship(
        'Question',
        back_populates='area',
        cascade='all, delete-orphan',
        order_by='Question.display_order'
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("is_active IN ('Y', 'N')", name='check_area_active'),
        CheckConstraint("is_deleted IN ('Y', 'N')", name='check_area_deleted'),
        Index('idx_area_section', 'section_id'),
        Index('idx_area_order', 'display_order'),
        Index('idx_area_active', 'is_active'),
        UniqueConstraint('section_id', 'name', name='uq_area_name_section'),
    )
    
    def __repr__(self) -> str:
        return f"<Area(id={self.id}, name='{self.name}')>"
    
    def validate(self) -> List[str]:
        """Validate area data"""
        errors = super().validate()
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Area name is required")
        
        if len(self.name) > 100:
            errors.append("Area name must be 100 characters or less")
        
        if not self.section_id:
            errors.append("Section ID is required")
        
        if self.display_order < 0:
            errors.append("Display order must be non-negative")
        
        return errors
    
    @property
    def question_count(self) -> int:
        """Get number of questions in this area"""
        return len([q for q in self.questions if q.is_active == 'Y'])
    
    @property
    def active_questions(self):
        """Get active questions in this area"""
        return [q for q in self.questions if q.is_active == 'Y']


class Question(BaseModel):
    """
    Assessment question model
    
    Represents individual questions within areas with multiple choice answers
    """
    
    __tablename__ = 'questions'
    
    # Override the id to match database schema (TEXT instead of Integer)
    id = Column(String, primary_key=True)
    
    # Basic fields - matching actual database schema
    question = Column(Text, nullable=False)  # This is 'question' not 'text'
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, default=1, nullable=False)  # INTEGER not String
    
    # Level descriptions instead of answer_options
    level_1_desc = Column(Text, nullable=True)
    level_2_desc = Column(Text, nullable=True)
    level_3_desc = Column(Text, nullable=True)
    level_4_desc = Column(Text, nullable=True)
    
    # Foreign keys - matching database schema (TEXT not Integer)
    area_id = Column(String, ForeignKey('areas.id'), nullable=False)
    
    # Relationships
    area = relationship('Area', back_populates='questions')
    responses = relationship(
        'Response',
        back_populates='question',
        cascade='all, delete-orphan'
    )
    
    # Constraints
    __table_args__ = (
        Index('idx_questions_area', 'area_id', 'display_order'),
        Index('idx_questions_active', 'is_active', 'display_order'),
    )
    
    def __repr__(self) -> str:
        return f"<Question(id={self.id}, text='{self.text[:50]}...')>"
    
    def validate(self) -> List[str]:
        """Validate question data"""
        errors = super().validate()
        
        if not self.text or len(self.text.strip()) == 0:
            errors.append("Question text is required")
        
        if not self.area_id:
            errors.append("Area ID is required")
        
        if self.max_score <= 0:
            errors.append("Max score must be positive")
        
        if self.weight <= 0:
            errors.append("Weight must be positive")
        
        if self.display_order < 0:
            errors.append("Display order must be non-negative")
        
        # Validate answer options
        if not self.answer_options:
            errors.append("Answer options are required")
        else:
            try:
                options = self.get_answer_options()
                if not options or len(options) == 0:
                    errors.append("At least one answer option is required")
                
                # Validate each option has required fields
                for i, option in enumerate(options):
                    if not isinstance(option, dict):
                        errors.append(f"Answer option {i+1} must be an object")
                        continue
                    
                    if 'value' not in option:
                        errors.append(f"Answer option {i+1} missing 'value' field")
                    
                    if 'text' not in option:
                        errors.append(f"Answer option {i+1} missing 'text' field")
                    
                    if 'score' not in option:
                        errors.append(f"Answer option {i+1} missing 'score' field")
                    
                    if option.get('score', 0) > self.max_score:
                        errors.append(f"Answer option {i+1} score exceeds max_score")
                        
            except (json.JSONDecodeError, TypeError):
                errors.append("Answer options must be valid JSON")
        
        return errors
    
    def get_answer_options(self) -> List[Dict[str, Any]]:
        """
        Parse answer options from JSON string
        
        Returns:
            List of answer option dictionaries
        """
        try:
            if isinstance(self.answer_options, str):
                return json.loads(self.answer_options)
            else:
                return self.answer_options or []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_answer_options(self, options: List[Dict[str, Any]]) -> None:
        """
        Set answer options as JSON string
        
        Args:
            options: List of answer option dictionaries
        """
        self.answer_options = json.dumps(options)
    
    def get_option_by_value(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Get answer option by value
        
        Args:
            value: Option value to find
            
        Returns:
            Answer option dictionary or None if not found
        """
        options = self.get_answer_options()
        return next((opt for opt in options if opt.get('value') == value), None)
    
    def get_score_for_value(self, value: str) -> int:
        """
        Get score for an answer value
        
        Args:
            value: Answer value
            
        Returns:
            Score for the answer value
        """
        option = self.get_option_by_value(value)
        return option.get('score', 0) if option else 0
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with parsed answer options"""
        result = super().to_dict(include_relationships)
        
        # Parse answer options for easier consumption
        result['answer_options'] = self.get_answer_options()
        
        return result


@validates('answer_options')
def validate_answer_options(self, key: str, value: Any) -> str:
    """Validate answer options format"""
    if isinstance(value, list):
        # Convert list to JSON string
        return json.dumps(value)
    elif isinstance(value, str):
        # Validate JSON string
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for answer options")
    else:
        raise ValueError("Answer options must be a list or JSON string")


__all__ = ['Section', 'Area', 'Question']
