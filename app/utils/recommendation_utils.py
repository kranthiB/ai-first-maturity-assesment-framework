"""
Recommendation utility functions for AFS Assessment Framework
Provides recommendation generation and prioritization logic
"""

from typing import Dict, List
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of recommendations"""
    QUICK_WIN = "quick_win"
    FOUNDATIONAL = "foundational"
    STRATEGIC = "strategic"
    TRANSFORMATIONAL = "transformational"


class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactLevel(Enum):
    """Impact levels for recommendations"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeasibilityLevel(Enum):
    """Feasibility levels for recommendations"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def load_recommendation_templates() -> Dict:
    """
    Load recommendation templates from seed data
    
    Returns:
        Dictionary with recommendation templates
    """
    try:
        # Get the project root directory
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        recommendations_file = project_root / "data" / "seeds" / "recommendations.json"
        
        if recommendations_file.exists():
            with open(recommendations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Recommendations file not found: {recommendations_file}")
            return get_default_recommendations()
    
    except Exception as e:
        logger.error(f"Error loading recommendation templates: {e}")
        return get_default_recommendations()


def get_default_recommendations() -> Dict:
    """
    Get default recommendation templates if file loading fails
    
    Returns:
        Dictionary with default recommendations
    """
    return {
        "recommendations": {
            "level_transitions": {
                "1_to_2": {
                    "foundational_capabilities": [
                        "Deploy basic AI assistants like GitHub Copilot for individual developers",
                        "Conduct AI literacy training with prompt engineering basics",
                        "Begin using AI for code completion and documentation",
                        "Establish AI tool usage guidelines and best practices"
                    ],
                    "transformation_capabilities": [
                        "Experiment with AI-assisted requirement analysis",
                        "Begin AI-assisted test case generation for unit tests",
                        "Add AI insights to CI/CD pipelines for build analysis",
                        "Use AI for legacy system documentation"
                    ],
                    "enterprise_integration": [
                        "Assess current AI tool costs and usage patterns",
                        "Standardize AI tools across small teams",
                        "Create inventory of systems for AI integration",
                        "Establish data classification for AI usage"
                    ],
                    "strategic_governance": [
                        "Create initial AI ethics awareness and guidelines",
                        "Track AI tool usage and developer satisfaction",
                        "Develop policies for AI-generated code IP concerns",
                        "Monitor AI-related risks with basic oversight"
                    ]
                },
                "2_to_3": {
                    "foundational_capabilities": [
                        "Scale to team-wide adoption with standardized toolchain",
                        "Implement structured AI training programs",
                        "Establish systematic AI code review processes",
                        "Deploy automated documentation generation"
                    ],
                    "transformation_capabilities": [
                        "Build AI systems for architecture proposal generation",
                        "Implement comprehensive AI-driven testing (50-85%)",
                        "Create intelligent CI/CD pipelines with optimization",
                        "Develop AI-powered migration planning"
                    ],
                    "enterprise_integration": [
                        "Implement enterprise-wide AI tool standards",
                        "Deploy automated enterprise system integration",
                        "Establish automated cost tracking and optimization",
                        "Create systematic data governance framework"
                    ],
                    "strategic_governance": [
                        "Establish comprehensive AI ethics framework",
                        "Implement comprehensive productivity metrics",
                        "Create structured change management programs",
                        "Develop systematic compliance management"
                    ]
                },
                "3_to_4": {
                    "foundational_capabilities": [
                        "Achieve enterprise-grade AI platform integration",
                        "Develop advanced AI expertise across teams",
                        "Implement AI-first development workflows",
                        "Create intelligent knowledge systems"
                    ],
                    "transformation_capabilities": [
                        "Deploy automated intent-to-architecture pipelines",
                        "Achieve fully autonomous testing (85%+)",
                        "Implement autonomous CI/CD with self-healing",
                        "Complete autonomous legacy transformation"
                    ],
                    "enterprise_integration": [
                        "Establish strategic AI vendor partnerships",
                        "Achieve seamless AI-powered integrations",
                        "Implement advanced cost optimization models",
                        "Deploy advanced resilience systems"
                    ],
                    "strategic_governance": [
                        "Implement automated ethics compliance monitoring",
                        "Deploy advanced analytics with predictive modeling",
                        "Achieve seamless multi-agent collaboration",
                        "Lead strategic innovation programs"
                    ]
                }
            }
        }
    }


def get_maturity_transition_key(current_level: int, target_level: int) -> str:
    """
    Get the key for maturity level transition
    
    Args:
        current_level: Current maturity level (1-4)
        target_level: Target maturity level (1-4)
        
    Returns:
        Transition key string
    """
    return f"{current_level}_to_{target_level}"


def calculate_recommendation_priority(impact: ImpactLevel, 
                                    feasibility: FeasibilityLevel,
                                    current_score: float,
                                    section_weight: float = 1.0) -> RecommendationPriority:
    """
    Calculate recommendation priority based on impact and feasibility
    
    Args:
        impact: Impact level of the recommendation
        feasibility: Feasibility level of implementation
        current_score: Current score in the area
        section_weight: Weight/importance of the section
        
    Returns:
        Calculated priority level
    """
    # Create scoring matrix
    impact_scores = {
        ImpactLevel.HIGH: 3,
        ImpactLevel.MEDIUM: 2,
        ImpactLevel.LOW: 1
    }
    
    feasibility_scores = {
        FeasibilityLevel.HIGH: 3,
        FeasibilityLevel.MEDIUM: 2,
        FeasibilityLevel.LOW: 1
    }
    
    # Calculate base score
    impact_score = impact_scores[impact]
    feasibility_score = feasibility_scores[feasibility]
    
    # Lower current scores get higher priority
    score_urgency = (4.0 - current_score) / 3.0  # Normalize to 0-1
    
    # Combine factors
    priority_score = (impact_score * 0.4 + 
                     feasibility_score * 0.4 + 
                     score_urgency * 0.2) * section_weight
    
    # Map to priority levels
    if priority_score >= 2.5:
        return RecommendationPriority.HIGH
    elif priority_score >= 1.5:
        return RecommendationPriority.MEDIUM
    else:
        return RecommendationPriority.LOW


def classify_recommendation_type(recommendation_text: str, 
                               impact: ImpactLevel,
                               feasibility: FeasibilityLevel,
                               implementation_time: str = None) -> RecommendationType:
    """
    Classify recommendation type based on content and characteristics
    
    Args:
        recommendation_text: The recommendation text
        impact: Impact level
        feasibility: Feasibility level
        implementation_time: Optional implementation timeframe
        
    Returns:
        Recommendation type classification
    """
    text_lower = recommendation_text.lower()
    
    # Quick win indicators
    quick_win_keywords = [
        "basic", "simple", "start", "begin", "deploy", "use", "add",
        "experiment", "introduce", "initial", "2-hour", "workshop"
    ]
    
    # Foundational indicators
    foundational_keywords = [
        "establish", "create", "implement", "systematic", "framework",
        "training", "standardize", "governance", "policy", "process"
    ]
    
    # Strategic indicators
    strategic_keywords = [
        "enterprise", "organization", "strategic", "comprehensive", 
        "roadmap", "transformation", "culture", "leadership"
    ]
    
    # Transformational indicators
    transformational_keywords = [
        "autonomous", "automated", "ai-first", "intelligent", "advanced",
        "revolutionary", "paradigm", "reimagine", "reinvent"
    ]
    
    # Count keyword matches
    quick_win_count = sum(1 for keyword in quick_win_keywords 
                         if keyword in text_lower)
    foundational_count = sum(1 for keyword in foundational_keywords 
                           if keyword in text_lower)
    strategic_count = sum(1 for keyword in strategic_keywords 
                         if keyword in text_lower)
    transformational_count = sum(1 for keyword in transformational_keywords 
                               if keyword in text_lower)
    
    # Consider impact and feasibility
    if (feasibility == FeasibilityLevel.HIGH and 
        impact in [ImpactLevel.LOW, ImpactLevel.MEDIUM] and
        quick_win_count > 0):
        return RecommendationType.QUICK_WIN
    
    if transformational_count > 0 or impact == ImpactLevel.HIGH:
        return RecommendationType.TRANSFORMATIONAL
    
    if strategic_count > 0 or "enterprise" in text_lower:
        return RecommendationType.STRATEGIC
    
    if foundational_count > 0:
        return RecommendationType.FOUNDATIONAL
    
    # Default based on feasibility and impact
    if feasibility == FeasibilityLevel.HIGH:
        return RecommendationType.QUICK_WIN
    elif impact == ImpactLevel.HIGH:
        return RecommendationType.TRANSFORMATIONAL
    else:
        return RecommendationType.FOUNDATIONAL


def estimate_implementation_effort(recommendation_type: RecommendationType,
                                 section_complexity: float = 1.0) -> Dict:
    """
    Estimate implementation effort for a recommendation
    
    Args:
        recommendation_type: Type of recommendation
        section_complexity: Complexity factor for the section (0.5-2.0)
        
    Returns:
        Dictionary with effort estimates
    """
    base_efforts = {
        RecommendationType.QUICK_WIN: {
            "time_weeks": 2,
            "resources_needed": 1,
            "complexity": "Low",
            "risk": "Low"
        },
        RecommendationType.FOUNDATIONAL: {
            "time_weeks": 8,
            "resources_needed": 3,
            "complexity": "Medium", 
            "risk": "Medium"
        },
        RecommendationType.STRATEGIC: {
            "time_weeks": 16,
            "resources_needed": 5,
            "complexity": "High",
            "risk": "Medium"
        },
        RecommendationType.TRANSFORMATIONAL: {
            "time_weeks": 24,
            "resources_needed": 8,
            "complexity": "Very High",
            "risk": "High"
        }
    }
    
    base_effort = base_efforts[recommendation_type]
    
    # Apply complexity factor
    adjusted_effort = {
        "time_weeks": int(base_effort["time_weeks"] * section_complexity),
        "resources_needed": int(base_effort["resources_needed"] * section_complexity),
        "complexity": base_effort["complexity"],
        "risk": base_effort["risk"],
        "section_complexity_factor": section_complexity
    }
    
    return adjusted_effort


def generate_recommendation_metadata(recommendation_text: str,
                                   section_name: str,
                                   current_score: float,
                                   target_score: float) -> Dict:
    """
    Generate metadata for a recommendation
    
    Args:
        recommendation_text: The recommendation text
        section_name: Section this recommendation applies to
        current_score: Current score in the section
        target_score: Target score for the section
        
    Returns:
        Dictionary with recommendation metadata
    """
    # Estimate impact and feasibility based on content
    impact = ImpactLevel.MEDIUM
    feasibility = FeasibilityLevel.MEDIUM
    
    # Simple heuristics for impact/feasibility
    if "comprehensive" in recommendation_text.lower():
        impact = ImpactLevel.HIGH
    if "autonomous" in recommendation_text.lower():
        impact = ImpactLevel.HIGH
        feasibility = FeasibilityLevel.LOW
    if "basic" in recommendation_text.lower():
        feasibility = FeasibilityLevel.HIGH
    if "experiment" in recommendation_text.lower():
        feasibility = FeasibilityLevel.HIGH
        impact = ImpactLevel.LOW
    
    # Calculate recommendation type and priority
    rec_type = classify_recommendation_type(recommendation_text, impact, feasibility)
    priority = calculate_recommendation_priority(impact, feasibility, current_score)
    
    # Generate effort estimate
    section_complexity = max(0.5, min(2.0, (4.0 - current_score) / 2.0))
    effort = estimate_implementation_effort(rec_type, section_complexity)
    
    return {
        "type": rec_type.value,
        "priority": priority.value,
        "impact": impact.value,
        "feasibility": feasibility.value,
        "section": section_name,
        "current_score": current_score,
        "target_score": target_score,
        "score_improvement": target_score - current_score,
        "effort_estimate": effort,
        "tags": extract_recommendation_tags(recommendation_text)
    }


def extract_recommendation_tags(recommendation_text: str) -> List[str]:
    """
    Extract relevant tags from recommendation text
    
    Args:
        recommendation_text: The recommendation text
        
    Returns:
        List of relevant tags
    """
    tags = []
    text_lower = recommendation_text.lower()
    
    # Technology tags
    tech_tags = {
        "ai": ["ai", "artificial intelligence"],
        "automation": ["automat", "autonomous"],
        "testing": ["test", "qa", "quality"],
        "ci/cd": ["ci/cd", "pipeline", "deployment"],
        "tools": ["tool", "platform", "infrastructure"],
        "training": ["training", "education", "literacy"],
        "governance": ["governance", "policy", "compliance"],
        "integration": ["integration", "enterprise", "system"]
    }
    
    for tag, keywords in tech_tags.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(tag)
    
    # Add scope tags
    if "team" in text_lower:
        tags.append("team-level")
    if "enterprise" in text_lower:
        tags.append("enterprise-level")
    if "individual" in text_lower:
        tags.append("individual-level")
    
    return list(set(tags))  # Remove duplicates


def rank_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """
    Rank recommendations by priority and other factors
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Sorted list of recommendations
    """
    def priority_score(rec):
        # Priority scoring
        priority_scores = {
            "high": 3,
            "medium": 2, 
            "low": 1
        }
        
        # Impact scoring
        impact_scores = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        # Feasibility scoring (higher is better)
        feasibility_scores = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        priority = priority_scores.get(rec.get("priority", "medium"), 2)
        impact = impact_scores.get(rec.get("impact", "medium"), 2)
        feasibility = feasibility_scores.get(rec.get("feasibility", "medium"), 2)
        score_improvement = rec.get("score_improvement", 0)
        
        # Calculate composite score
        return (priority * 0.4 + 
                impact * 0.3 + 
                feasibility * 0.2 + 
                score_improvement * 0.1)
    
    return sorted(recommendations, key=priority_score, reverse=True)


def filter_recommendations_by_type(recommendations: List[Dict], 
                                 rec_type: RecommendationType) -> List[Dict]:
    """
    Filter recommendations by type
    
    Args:
        recommendations: List of recommendation dictionaries
        rec_type: Recommendation type to filter by
        
    Returns:
        Filtered list of recommendations
    """
    return [rec for rec in recommendations 
            if rec.get("type") == rec_type.value]


def get_next_level_recommendations(current_level: int) -> int:
    """
    Get the next maturity level for recommendations
    
    Args:
        current_level: Current maturity level (1-4)
        
    Returns:
        Next maturity level
    """
    return min(4, current_level + 1)
