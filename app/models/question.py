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

    def __repr__(self) -> str:
        return f"<Section(id={self.id}, name='{self.name}')>"


class Area(BaseModel):
    """
    Assessment area model
    
    Represents assessment areas within sections
    """
    
    __tablename__ = 'areas'
    
    # Override the id to match database schema (TEXT instead of Integer)
    id = Column(String, primary_key=True)
    
    # Basic fields - matching actual database schema
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    
    # Timeline fields specific to this schema
    timeline_l1_l2 = Column(Text, nullable=True)
    timeline_l2_l3 = Column(Text, nullable=True)
    timeline_l3_l4 = Column(Text, nullable=True)
    
    # Foreign keys - matching database schema (TEXT not Integer)
    section_id = Column(String, ForeignKey('sections.id'), nullable=False)
    
    # Relationships
    section = relationship('Section', back_populates='areas')
    questions = relationship(
        'Question',
        back_populates='area',
        cascade='all, delete-orphan',
        order_by='Question.display_order'
    )

    def __repr__(self) -> str:
        return f"<Area(id={self.id}, name='{self.name}')>"


class Question(BaseModel):
    """
    Assessment question model
    
    Represents individual questions within areas
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

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, question='{self.question[:50]}...')>"
    
    def get_level_descriptions(self) -> List[Dict[str, Any]]:
        """Get level descriptions as a list of dictionaries"""
        levels = []
        for i in range(1, 5):
            level_desc = getattr(self, f'level_{i}_desc', None)
            if level_desc:
                levels.append({
                    'level': i,
                    'description': level_desc,
                    'score': i
                })
        return levels


__all__ = ['Section', 'Area', 'Question']
