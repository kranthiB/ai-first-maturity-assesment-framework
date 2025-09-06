"""
Base Model for AFS Assessment Framework

This module provides the base model class with common functionality
for all SQLAlchemy models in the application.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, Integer, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from sqlalchemy.inspection import inspect


Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common functionality
    
    Provides common fields and methods for all models including:
    - Primary key
    - Timestamps (created_at, updated_at)
    - Serialization methods
    - Validation helpers
    """
    
    __abstract__ = True
    
    # Common fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    def __init__(self, **kwargs):
        """Initialize model with provided attributes"""
        super().__init__(**kwargs)
        
    def __repr__(self) -> str:
        """String representation of the model"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
        """
        result = {}
        
        # Get all columns
        mapper = inspect(self.__class__)
        
        for column in mapper.columns:
            value = getattr(self, column.name)
            
            # Handle datetime serialization
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        
        # Include relationships if requested
        if include_relationships:
            for relationship in mapper.relationships:
                rel_value = getattr(self, relationship.key)
                
                if rel_value is None:
                    result[relationship.key] = None
                elif hasattr(rel_value, '__iter__') and not isinstance(rel_value, str):
                    # Collection relationship
                    result[relationship.key] = [
                        item.to_dict() if hasattr(item, 'to_dict') else str(item)
                        for item in rel_value
                    ]
                else:
                    # Single relationship
                    result[relationship.key] = (
                        rel_value.to_dict() if hasattr(rel_value, 'to_dict') 
                        else str(rel_value)
                    )
        
        return result
    
    def to_json(self, include_relationships: bool = False) -> str:
        """
        Convert model to JSON string
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(include_relationships), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create model instance from dictionary
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            Model instance
        """
        # Filter out fields that don't exist in the model
        mapper = inspect(cls)
        valid_columns = {column.name for column in mapper.columns}
        
        filtered_data = {
            key: value for key, value in data.items() 
            if key in valid_columns and key not in ('id', 'created_at', 'updated_at')
        }
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary
        
        Args:
            data: Dictionary containing updated data
        """
        mapper = inspect(self.__class__)
        valid_columns = {column.name for column in mapper.columns}
        
        for key, value in data.items():
            if key in valid_columns and key not in ('id', 'created_at'):
                setattr(self, key, value)
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
    
    def validate(self) -> List[str]:
        """
        Validate model instance
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Subclasses should override this method to add specific validations
        
        return errors
    
    def is_valid(self) -> bool:
        """
        Check if model instance is valid
        
        Returns:
            True if model is valid, False otherwise
        """
        return len(self.validate()) == 0
    
    def save(self, session) -> bool:
        """
        Save model to database
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.is_valid():
                return False
            
            session.add(self)
            session.flush()  # Get ID without committing
            return True
        except Exception:
            session.rollback()
            return False
    
    def delete(self, session) -> bool:
        """
        Delete model from database
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            session.delete(self)
            session.flush()
            return True
        except Exception:
            session.rollback()
            return False
    
    @validates('*')
    def validate_fields(self, key: str, value: Any) -> Any:
        """
        General field validation
        
        Args:
            key: Field name
            value: Field value
            
        Returns:
            Validated value
        """
        # Trim string values
        if isinstance(value, str):
            value = value.strip()
            
            # Convert empty strings to None for nullable fields
            if not value:
                mapper = inspect(self.__class__)
                column = mapper.columns.get(key)
                if column and column.nullable:
                    return None
        
        return value


class TimestampMixin:
    """
    Mixin for models that need timestamp fields
    """
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )


class SoftDeleteMixin:
    """
    Mixin for models that support soft deletion
    """
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(String(1), default='N', nullable=False)
    
    def soft_delete(self) -> None:
        """Mark record as deleted"""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = 'Y'
    
    def restore(self) -> None:
        """Restore soft-deleted record"""
        self.deleted_at = None
        self.is_deleted = 'N'
    
    @property
    def is_soft_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.is_deleted == 'Y'


__all__ = ['Base', 'BaseModel', 'TimestampMixin', 'SoftDeleteMixin']
