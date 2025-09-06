"""
API Schemas - Request and response schemas for API validation

Task 4.1: API Request/Response Schemas
Provides data validation schemas for API endpoints.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime


class AssessmentCreateSchema(Schema):
    """Schema for creating new assessments."""
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=100),
        error_messages={'required': 'Assessment name is required'}
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=500),
        error_messages={'required': 'Assessment description is required'}
    )
    organization = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'Organization name is required'}
    )
    assessor_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'Assessor name is required'}
    )
    assessor_email = fields.Email(
        required=True,
        error_messages={'required': 'Valid assessor email is required'}
    )
    metadata = fields.Dict(missing=dict)
    
    @validates('name')
    def validate_name(self, value):
        """Validate assessment name."""
        if not value or value.isspace():
            raise ValidationError(
                'Assessment name cannot be empty or whitespace'
            )
        
        # Check for prohibited characters
        prohibited_chars = ['<', '>', '&', '"', "'"]
        if any(char in value for char in prohibited_chars):
            raise ValidationError(
                'Assessment name contains prohibited characters'
            )


class AssessmentUpdateSchema(Schema):
    """Schema for updating assessments."""
    
    name = fields.Str(
        validate=validate.Length(min=3, max=100),
        allow_none=True
    )
    description = fields.Str(
        validate=validate.Length(min=10, max=500),
        allow_none=True
    )
    organization = fields.Str(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    assessor_name = fields.Str(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    assessor_email = fields.Email(allow_none=True)
    metadata = fields.Dict(allow_none=True)
    status = fields.Str(
        validate=validate.OneOf([
            'draft', 'in_progress', 'completed', 'archived'
        ]),
        allow_none=True
    )


class ResponseSubmitSchema(Schema):
    """Schema for submitting question responses."""
    
    question_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'Question ID is required'}
    )
    score = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5),
        error_messages={
            'required': 'Response score is required',
            'invalid': 'Score must be between 1 and 5'
        }
    )
    justification = fields.Str(
        validate=validate.Length(max=1000),
        allow_none=True
    )
    evidence = fields.Str(
        validate=validate.Length(max=2000),
        allow_none=True
    )
    confidence_level = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high']),
        missing='medium'
    )
    metadata = fields.Dict(missing=dict)
    
    @validates('justification')
    def validate_justification(self, value):
        """Validate response justification."""
        if value and len(value.strip()) < 10:
            raise ValidationError(
                'Justification must be at least 10 characters when provided'
            )


class AnalyticsQuerySchema(Schema):
    """Schema for analytics query parameters."""
    
    date_from = fields.DateTime(
        format='iso',
        allow_none=True
    )
    date_to = fields.DateTime(
        format='iso',
        allow_none=True
    )
    organization = fields.Str(
        validate=validate.Length(min=1, max=100),
        allow_none=True
    )
    metric = fields.Str(
        validate=validate.OneOf([
            'assessments', 'completions', 'scores', 'responses'
        ]),
        missing='assessments'
    )
    period = fields.Str(
        validate=validate.OneOf(['daily', 'weekly', 'monthly']),
        missing='daily'
    )
    
    @validates('date_from')
    def validate_date_from(self, value):
        """Validate start date."""
        if value and value > datetime.utcnow():
            raise ValidationError('Start date cannot be in the future')
    
    @validates('date_to')
    def validate_date_to(self, value):
        """Validate end date."""
        if value and value > datetime.utcnow():
            raise ValidationError('End date cannot be in the future')


class ExportQuerySchema(Schema):
    """Schema for export query parameters."""
    
    format = fields.Str(
        validate=validate.OneOf(['csv', 'json', 'xlsx']),
        missing='csv'
    )
    data_type = fields.Str(
        validate=validate.OneOf([
            'assessments', 'responses', 'analytics', 'scores'
        ]),
        missing='assessments'
    )
    date_from = fields.DateTime(
        format='iso',
        allow_none=True
    )
    date_to = fields.DateTime(
        format='iso',
        allow_none=True
    )
    organization = fields.Str(
        validate=validate.Length(min=1, max=100),
        allow_none=True
    )


class PaginationSchema(Schema):
    """Schema for pagination parameters."""
    
    limit = fields.Int(
        validate=validate.Range(min=1, max=200),
        missing=50
    )
    offset = fields.Int(
        validate=validate.Range(min=0),
        missing=0
    )


class QuestionFilterSchema(Schema):
    """Schema for question filtering parameters."""
    
    section_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True
    )
    area_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True
    )
    difficulty = fields.Str(
        validate=validate.OneOf(['easy', 'medium', 'hard']),
        allow_none=True
    )
    assessment_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True
    )
    include_responses = fields.Bool(missing=False)


class AssessmentFilterSchema(Schema):
    """Schema for assessment filtering parameters."""
    
    status = fields.Str(
        validate=validate.OneOf([
            'draft', 'in_progress', 'completed', 'archived'
        ]),
        allow_none=True
    )
    organization = fields.Str(
        validate=validate.Length(min=1, max=100),
        allow_none=True
    )
    assessor_email = fields.Email(allow_none=True)
    date_from = fields.DateTime(
        format='iso',
        allow_none=True
    )
    date_to = fields.DateTime(
        format='iso',
        allow_none=True
    )


# Response Schemas for API Documentation

class AssessmentResponseSchema(Schema):
    """Schema for assessment response data."""
    
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    organization = fields.Str()
    assessor_name = fields.Str()
    assessor_email = fields.Email()
    status = fields.Str()
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')
    completed_at = fields.DateTime(format='iso', allow_none=True)
    metadata = fields.Dict()
    progress = fields.Dict()


class QuestionResponseSchema(Schema):
    """Schema for question response data."""
    
    id = fields.Int()
    text = fields.Str()
    description = fields.Str()
    area_id = fields.Int()
    weight = fields.Float()
    difficulty = fields.Str()
    metadata = fields.Dict()
    area = fields.Dict()
    section = fields.Dict()


class ProgressResponseSchema(Schema):
    """Schema for progress response data."""
    
    assessment_id = fields.Int()
    progress_percentage = fields.Float()
    total_questions = fields.Int()
    responded_questions = fields.Int()
    remaining_questions = fields.Int()
    sections_progress = fields.List(fields.Dict())
    estimated_completion_time = fields.Str()
    last_activity = fields.DateTime(format='iso')


class AnalyticsResponseSchema(Schema):
    """Schema for analytics response data."""
    
    overview = fields.Dict()
    trends = fields.List(fields.Dict())
    comparisons = fields.List(fields.Dict())
    summary = fields.Dict()
    metadata = fields.Dict()


class ErrorResponseSchema(Schema):
    """Schema for error response data."""
    
    error = fields.Str()
    message = fields.Str()
    type = fields.Str()
    details = fields.Dict(allow_none=True)
    timestamp = fields.DateTime(format='iso')


class SuccessResponseSchema(Schema):
    """Schema for success response data."""
    
    message = fields.Str()
    data = fields.Raw(allow_none=True)
    metadata = fields.Dict(allow_none=True)
    timestamp = fields.DateTime(format='iso')
