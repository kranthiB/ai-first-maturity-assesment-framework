"""
Utility functions for the AI First Maturity Assessment Framework
"""


def get_maturity_level(overall_score):
    """
    Determine the maturity level based on overall score
    
    Args:
        overall_score (float): The overall assessment score (1.0-4.0)
        
    Returns:
        dict: Contains level name, description, and score range
    """
    if overall_score is None:
        return {
            'name': 'Not Assessed',
            'description': 'Assessment not yet completed',
            'range': 'N/A',
            'color': 'secondary'
        }
    
    if 1.0 <= overall_score < 1.8:
        return {
            'name': 'Traditional Development',
            'description': 'Minimal AI integration in development processes',
            'range': '1.0-1.8',
            'color': 'danger'
        }
    elif 1.8 <= overall_score < 2.5:
        return {
            'name': 'AI-Assisted Development',
            'description': 'Basic AI tools supporting development activities',
            'range': '1.8-2.5',
            'color': 'warning'
        }
    elif 2.5 <= overall_score < 3.3:
        return {
            'name': 'AI-Augmented Development',
            'description': 'Significant AI integration across development',
            'range': '2.5-3.3',
            'color': 'info'
        }
    elif 3.3 <= overall_score <= 4.0:
        return {
            'name': 'AI-First Development',
            'description': 'AI-native approach with comprehensive integration',
            'range': '3.3-4.0',
            'color': 'success'
        }
    else:
        return {
            'name': 'Invalid Score',
            'description': 'Score outside expected range',
            'range': 'Invalid',
            'color': 'secondary'
        }


def format_score_display(overall_score):
    """
    Format the overall score for display with appropriate precision
    
    Args:
        overall_score (float): The overall assessment score
        
    Returns:
        str: Formatted score string
    """
    if overall_score is None:
        return 'N/A'
    
    return f"{overall_score:.1f}"
