"""
Validation utilities for assessment data and responses.
"""

import re
from typing import Dict, Any, List, Optional

from app.models import Question
from app.utils.exceptions import ValidationError


def validate_email_format(email: str) -> bool:
    """Simple email validation using regex."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


class AssessmentValidator:
    """
    Validator for assessment data and business rules.
    """
    
    # Validation constraints
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 1000
    MIN_ORGANIZATION_LENGTH = 2
    MAX_ORGANIZATION_LENGTH = 100
    MIN_ASSESSOR_NAME_LENGTH = 2
    MAX_ASSESSOR_NAME_LENGTH = 100
    
    # Valid assessment statuses
    VALID_STATUSES = {'draft', 'in_progress', 'completed', 'cancelled'}
    
    def validate_assessment_data(self, data: Dict[str, Any]) -> None:
        """
        Validate assessment creation/update data.
        
        Args:
            data: Dictionary containing assessment data
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Validate name
        if 'name' in data:
            name_errors = self._validate_name(data['name'])
            errors.extend(name_errors)
        
        # Validate description
        if 'description' in data:
            desc_errors = self._validate_description(data['description'])
            errors.extend(desc_errors)
        
        # Validate organization
        if 'organization' in data:
            org_errors = self._validate_organization(data['organization'])
            errors.extend(org_errors)
        
        # Validate assessor name
        if 'assessor_name' in data:
            assessor_errors = self._validate_assessor_name(
                data['assessor_name']
            )
            errors.extend(assessor_errors)
        
        # Validate assessor email
        if 'assessor_email' in data:
            email_errors = self._validate_assessor_email(
                data['assessor_email']
            )
            errors.extend(email_errors)
        
        # Validate status
        if 'status' in data:
            status_errors = self._validate_status(data['status'])
            errors.extend(status_errors)
        
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
    
    def _validate_name(self, name: Any) -> List[str]:
        """Validate assessment name."""
        errors = []
        
        if not name:
            errors.append("Name is required")
            return errors
        
        if not isinstance(name, str):
            errors.append("Name must be a string")
            return errors
        
        name = name.strip()
        
        if len(name) < self.MIN_NAME_LENGTH:
            errors.append(
                f"Name must be at least {self.MIN_NAME_LENGTH} characters"
            )
        
        if len(name) > self.MAX_NAME_LENGTH:
            errors.append(
                f"Name cannot exceed {self.MAX_NAME_LENGTH} characters"
            )
        
        # Check for valid characters (alphanumeric, spaces, basic punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-_.,()]+$', name):
            errors.append("Name contains invalid characters")
        
        return errors
    
    def _validate_description(self, description: Any) -> List[str]:
        """Validate assessment description."""
        errors = []
        
        if not description:
            errors.append("Description is required")
            return errors
        
        if not isinstance(description, str):
            errors.append("Description must be a string")
            return errors
        
        description = description.strip()
        
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            errors.append(
                f"Description must be at least "
                f"{self.MIN_DESCRIPTION_LENGTH} characters"
            )
        
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"Description cannot exceed "
                f"{self.MAX_DESCRIPTION_LENGTH} characters"
            )
        
        return errors
    
    def _validate_organization(self, organization: Any) -> List[str]:
        """Validate organization name."""
        errors = []
        
        if not organization:
            errors.append("Organization is required")
            return errors
        
        if not isinstance(organization, str):
            errors.append("Organization must be a string")
            return errors
        
        organization = organization.strip()
        
        if len(organization) < self.MIN_ORGANIZATION_LENGTH:
            errors.append(
                f"Organization must be at least "
                f"{self.MIN_ORGANIZATION_LENGTH} characters"
            )
        
        if len(organization) > self.MAX_ORGANIZATION_LENGTH:
            errors.append(
                f"Organization cannot exceed "
                f"{self.MAX_ORGANIZATION_LENGTH} characters"
            )
        
        return errors
    
    def _validate_assessor_name(self, assessor_name: Any) -> List[str]:
        """Validate assessor name."""
        errors = []
        
        if not assessor_name:
            errors.append("Assessor name is required")
            return errors
        
        if not isinstance(assessor_name, str):
            errors.append("Assessor name must be a string")
            return errors
        
        assessor_name = assessor_name.strip()
        
        if len(assessor_name) < self.MIN_ASSESSOR_NAME_LENGTH:
            errors.append(
                f"Assessor name must be at least "
                f"{self.MIN_ASSESSOR_NAME_LENGTH} characters"
            )
        
        if len(assessor_name) > self.MAX_ASSESSOR_NAME_LENGTH:
            errors.append(
                f"Assessor name cannot exceed "
                f"{self.MAX_ASSESSOR_NAME_LENGTH} characters"
            )
        
        # Basic name validation (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", assessor_name):
            errors.append("Assessor name contains invalid characters")
        
        return errors
    
    def _validate_assessor_email(self, assessor_email: Any) -> List[str]:
        """Validate assessor email address."""
        errors = []
        
        if not assessor_email:
            errors.append("Assessor email is required")
            return errors
        
        if not isinstance(assessor_email, str):
            errors.append("Assessor email must be a string")
            return errors
        
        assessor_email = assessor_email.strip()
        
        if not validate_email_format(assessor_email):
            errors.append("Invalid email format")
        
        return errors
    
    def _validate_status(self, status: Any) -> List[str]:
        """Validate assessment status."""
        errors = []
        
        if not status:
            errors.append("Status is required")
            return errors
        
        if not isinstance(status, str):
            errors.append("Status must be a string")
            return errors
        
        if status not in self.VALID_STATUSES:
            errors.append(
                f"Invalid status. Must be one of: "
                f"{', '.join(self.VALID_STATUSES)}"
            )
        
        return errors


class ResponseValidator:
    """
    Validator for assessment response data.
    """
    
    def validate_response(self, question: Question, answer_value: str) -> None:
        """
        Validate a response against a question's answer options.
        
        Args:
            question: Question instance
            answer_value: Answer value to validate
            
        Raises:
            ValidationError: If response validation fails
        """
        errors = []
        
        # Basic validation
        if not answer_value:
            errors.append("Answer value is required")
        
        if not isinstance(answer_value, str):
            errors.append("Answer value must be a string")
        
        if errors:
            raise ValidationError(
                f"Response validation failed: {'; '.join(errors)}"
            )
        
        # Validate against question's answer options
        answer_options = question.get_answer_options()
        
        if not answer_options:
            # If no answer options defined, accept any non-empty string
            return
        
        # Check if answer_value matches any of the valid options
        valid_values = [option.get('value') for option in answer_options
                        if 'value' in option]
        
        if answer_value not in valid_values:
            raise ValidationError(
                f"Invalid answer value '{answer_value}'. "
                f"Valid options: {', '.join(valid_values)}"
            )
    
    def validate_response_batch(self, responses: List[Dict[str, Any]],
                                questions: Dict[int, Question]) -> List[str]:
        """
        Validate a batch of responses.
        
        Args:
            responses: List of response dictionaries
            questions: Dictionary mapping question IDs to Question instances
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for i, response_data in enumerate(responses):
            try:
                # Validate required fields
                if 'question_id' not in response_data:
                    errors.append(f"Response {i}: Missing question_id")
                    continue
                
                if 'answer_value' not in response_data:
                    errors.append(f"Response {i}: Missing answer_value")
                    continue
                
                question_id = response_data['question_id']
                answer_value = response_data['answer_value']
                
                # Validate question exists
                if question_id not in questions:
                    errors.append(
                        f"Response {i}: Invalid question_id {question_id}"
                    )
                    continue
                
                # Validate response
                question = questions[question_id]
                self.validate_response(question, answer_value)
                
            except ValidationError as e:
                errors.append(f"Response {i}: {str(e)}")
            except Exception as e:
                errors.append(f"Response {i}: Unexpected error - {str(e)}")
        
        return errors


class ProgressValidator:
    """
    Validator for assessment progress and completion rules.
    """
    
    def __init__(self, min_completion_percentage: float = 80.0):
        """
        Initialize progress validator.
        
        Args:
            min_completion_percentage: Minimum completion required (0-100)
        """
        self.min_completion_percentage = min_completion_percentage
    
    def validate_completion_eligibility(self,
                                        total_questions: int,
                                        answered_questions: int,
                                        force: bool = False) -> None:
        """
        Validate if assessment is eligible for completion.
        
        Args:
            total_questions: Total number of questions
            answered_questions: Number of answered questions
            force: Whether to force completion
            
        Raises:
            ValidationError: If assessment not eligible for completion
        """
        if force:
            return
        
        if total_questions == 0:
            raise ValidationError("Cannot complete assessment with no questions")
        
        completion_percentage = (answered_questions / total_questions) * 100
        
        if completion_percentage < self.min_completion_percentage:
            raise ValidationError(
                f"Assessment completion requires at least "
                f"{self.min_completion_percentage}% of questions answered. "
                f"Current: {completion_percentage:.1f}% "
                f"({answered_questions}/{total_questions})"
            )
    
    def validate_section_completion(self,
                                    section_progress: Dict[str, Any],
                                    required_sections: Optional[List[str]] = None
                                    ) -> List[str]:
        """
        Validate section-level completion requirements.
        
        Args:
            section_progress: Section progress data
            required_sections: List of section names that must be complete
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not required_sections:
            return errors
        
        for section_name in required_sections:
            if section_name not in section_progress:
                errors.append(f"Required section '{section_name}' not found")
                continue
            
            section_data = section_progress[section_name]
            if not section_data.get('is_complete', False):
                progress = section_data.get('progress_percentage', 0)
                errors.append(
                    f"Required section '{section_name}' not complete "
                    f"({progress:.1f}%)"
                )
        
        return errors


class BusinessRuleValidator:
    """
    Validator for business rules and constraints.
    """
    
    @staticmethod
    def validate_assessment_uniqueness(session, name: str, organization: str,
                                       exclude_id: Optional[int] = None) -> None:
        """
        Validate assessment name uniqueness within organization.
        
        Args:
            session: Database session
            name: Assessment name
            organization: Organization name
            exclude_id: Assessment ID to exclude from check (for updates)
            
        Raises:
            ValidationError: If assessment name already exists
        """
        from app.models import Assessment
        
        query = session.query(Assessment).filter(
            Assessment.name == name.strip(),
            Assessment.organization == organization.strip()
        )
        
        if exclude_id:
            query = query.filter(Assessment.id != exclude_id)
        
        existing = query.first()
        
        if existing:
            raise ValidationError(
                f"Assessment '{name}' already exists for organization "
                f"'{organization}'"
            )
    
    @staticmethod
    def validate_response_modification(assessment_status: str) -> None:
        """
        Validate if responses can be modified based on assessment status.
        
        Args:
            assessment_status: Current assessment status
            
        Raises:
            ValidationError: If responses cannot be modified
        """
        read_only_statuses = {'completed', 'cancelled'}
        
        if assessment_status in read_only_statuses:
            raise ValidationError(
                f"Cannot modify responses for assessment with status "
                f"'{assessment_status}'"
            )
