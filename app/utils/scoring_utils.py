"""
Scoring utility functions for AFS Assessment Framework
Provides core scoring calculations and DevIQ classification logic
"""

from typing import Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MaturityLevel(Enum):
    """DevIQ Maturity Level Classifications"""
    TRADITIONAL = "Traditional Development"
    ASSISTED = "AI-Assisted Development"
    AUGMENTED = "AI-Augmented Development"
    FIRST = "AI-First Development"


class ScoringConstants:
    """Constants for scoring calculations"""

    # Score ranges (1.0-4.0 scale)
    MIN_SCORE = 1.0
    MAX_SCORE = 4.0

    # Maturity level thresholds
    MATURITY_THRESHOLDS = {
        MaturityLevel.TRADITIONAL: (1.0, 1.8),
        MaturityLevel.ASSISTED: (1.8, 2.5),
        MaturityLevel.AUGMENTED: (2.5, 3.3),
        MaturityLevel.FIRST: (3.3, 4.0)
    }

    # Section weights (equal weighting for now)
    SECTION_WEIGHTS = {
        'foundational_capabilities': 0.25,
        'transformation_capabilities': 0.25,
        'enterprise_integration': 0.25,
        'strategic_governance': 0.25
    }


def calculate_weighted_average(scores: List[float],
                               weights: List[float] = None) -> float:
    """Calculate weighted average of scores"""
    if not scores:
        raise ValueError("Cannot calculate average of empty scores list")

    if weights is None:
        weights = [1.0] * len(scores)

    if len(scores) != len(weights):
        raise ValueError("Scores and weights must have the same length")

    # Calculate weighted sum
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)

    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    return weighted_sum / total_weight


def normalize_score(score: float, min_val: float = None,
                   max_val: float = None) -> float:
    """Normalize score to 1.0-4.0 scale"""
    if min_val is None:
        min_val = ScoringConstants.MIN_SCORE
    if max_val is None:
        max_val = ScoringConstants.MAX_SCORE

    # Clamp score to valid range
    score = max(min_val, min(max_val, score))

    # Normalize to 1.0-4.0 scale
    if max_val == min_val:
        return ScoringConstants.MIN_SCORE

    range_size = ScoringConstants.MAX_SCORE - ScoringConstants.MIN_SCORE
    normalized = ((score - min_val) / (max_val - min_val)) * range_size
    normalized += ScoringConstants.MIN_SCORE

    return round(normalized, 2)


def classify_maturity_level(deviq_score: float) -> Tuple[MaturityLevel, str]:
    """Classify AFS score into maturity level"""
    if not isinstance(deviq_score, (int, float)):
        raise ValueError("AFS score must be numeric")

    # Clamp score to valid range
    min_score = ScoringConstants.MIN_SCORE
    max_score = ScoringConstants.MAX_SCORE
    deviq_score = max(min_score, min(max_score, deviq_score))

    thresholds = ScoringConstants.MATURITY_THRESHOLDS
    
    # Check each level in order (highest to lowest for proper boundary handling)
    if deviq_score >= thresholds[MaturityLevel.FIRST][0]:
        return MaturityLevel.FIRST, MaturityLevel.FIRST.value
    elif deviq_score >= thresholds[MaturityLevel.AUGMENTED][0]:
        return MaturityLevel.AUGMENTED, MaturityLevel.AUGMENTED.value
    elif deviq_score >= thresholds[MaturityLevel.ASSISTED][0]:
        return MaturityLevel.ASSISTED, MaturityLevel.ASSISTED.value
    else:
        return MaturityLevel.TRADITIONAL, MaturityLevel.TRADITIONAL.value


def get_maturity_level_details(level: MaturityLevel) -> Dict:
    """Get detailed information about a maturity level"""
    details = {
        MaturityLevel.TRADITIONAL: {
            "name": "Traditional Development",
            "short_name": "Basic",
            "description": "Manual development with limited AI integration",
            "characteristics": [
                "No AI tools in regular use",
                "Manual coding and review processes",
                "Traditional project management",
                "Limited automation"
            ]
        },
        MaturityLevel.ASSISTED: {
            "name": "AI-Assisted Development",
            "short_name": "Developing",
            "description": "Basic AI tools support individual developers",
            "characteristics": [
                "Individual use of AI assistants",
                "Basic code completion and suggestions",
                "Some automated documentation",
                "Limited team-wide adoption"
            ]
        },
        MaturityLevel.AUGMENTED: {
            "name": "AI-Augmented Development",
            "short_name": "Advanced",
            "description": "Systematic AI integration across lifecycle",
            "characteristics": [
                "Team-wide AI tool adoption",
                "AI-generated code with human review",
                "Automated testing and quality assurance",
                "Intelligent CI/CD pipelines"
            ]
        },
        MaturityLevel.FIRST: {
            "name": "AI-First Development",
            "short_name": "Optimized",
            "description": "AI-native development with autonomous systems",
            "characteristics": [
                "AI-first development mindset",
                "Autonomous code generation and review",
                "Self-healing systems",
                "Predictive and proactive automation"
            ]
        }
    }

    return details.get(level, {})


def calculate_section_coverage(responses_count: int,
                              total_questions: int) -> float:
    """Calculate completion percentage for a section"""
    if total_questions <= 0:
        return 0.0

    coverage = responses_count / total_questions
    return min(1.0, max(0.0, coverage))


def validate_score_inputs(scores: List[float],
                         weights: List[float] = None) -> bool:
    """Validate scoring inputs for common issues"""
    if not scores:
        raise ValueError("Scores list cannot be empty")

    if not all(isinstance(score, (int, float)) for score in scores):
        raise ValueError("All scores must be numeric")

    min_score = ScoringConstants.MIN_SCORE
    max_score = ScoringConstants.MAX_SCORE
    if not all(min_score <= score <= max_score for score in scores):
        msg = f"All scores must be between {min_score} and {max_score}"
        raise ValueError(msg)

    if weights is not None:
        if len(weights) != len(scores):
            raise ValueError("Weights list must match scores list length")

        if not all(isinstance(weight, (int, float)) for weight in weights):
            raise ValueError("All weights must be numeric")

        if not all(weight >= 0 for weight in weights):
            raise ValueError("All weights must be non-negative")

        if sum(weights) == 0:
            raise ValueError("Sum of weights cannot be zero")

    return True


def format_score_display(score: float, precision: int = 1) -> str:
    """Format score for display with appropriate precision"""
    if not isinstance(score, (int, float)):
        return "N/A"

    return f"{score:.{precision}f}"


def calculate_improvement_potential(current_score: float,
                                   target_level: MaturityLevel = None) -> Dict:
    """Calculate improvement potential to reach next or target level"""
    current_level, _ = classify_maturity_level(current_score)

    if target_level is None:
        # Default to next level
        levels = list(MaturityLevel)
        current_idx = levels.index(current_level)
        if current_idx < len(levels) - 1:
            target_level = levels[current_idx + 1]
        else:
            target_level = current_level  # Already at highest level

    thresholds = ScoringConstants.MATURITY_THRESHOLDS
    target_min, target_max = thresholds[target_level]

    improvement = {
        'current_score': current_score,
        'current_level': current_level.value,
        'target_level': target_level.value,
        'target_min_score': target_min,
        'target_max_score': target_max,
        'gap_to_target': max(0, target_min - current_score),
        'potential_improvement': target_max - current_score,
        'is_achievable': current_score < target_max
    }

    return improvement
