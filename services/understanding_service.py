"""
services/understanding_service.py — Understanding and clarity analysis service.

Handles all business logic related to calculating understanding levels,
clarity percentages, and providing appropriate feedback messages and styling.
"""

from typing import Dict, Tuple


class UnderstandingService:
    """
    Service class for understanding and clarity analysis.
    
    Centralizes all understanding-related operations including percentage calculation,
    message generation, and styling recommendations.
    """
    
    @staticmethod
    def get_understanding_message(score: float) -> Dict[str, str]:
        """
        Return a title and description based on understanding percentage.
        Expected score range: 0 to 100.
        """
        score = max(0, min(100, score))

        if score == 100:
            return {
                "title": "Perfect understanding",
                "description": "Excellent — everything is clear. You can confidently move on to the next question."
            }
        elif score >= 85:
            return {
                "title": "Great understanding",
                "description": "Nice work — the understanding looks complete or nearly complete."
            }
        elif score >= 60:
            return {
                "title": "Partial understanding",
                "description": "Consider a brief clarification before moving to the next question."
            }
        elif score >= 50:
            return {
                "title": "Weak understanding",
                "description": "A few important points are still unclear. A quick review would help."
            }
        else:
            return {
                "title": "Poor understanding",
                "description": "This looks quite incomplete. It is better to revisit the basics before continuing."
            }

    @staticmethod
    def get_understanding_tailwind(score: float) -> Tuple[str, str, str]:
        """
        Return Tailwind classes for border, text, and background based on percentage.
        """
        score = max(0, min(100, score))

        if score == 100:
            return (
                "border-yellow-300",
                "text-yellow-900",
                "bg-yellow-50",
            )
        elif score >= 85:
            return (
                "border-green-200",
                "text-green-800",
                "bg-green-50",
            )
        elif score >= 60:
            return (
                "border-orange-200",
                "text-orange-800",
                "bg-orange-50",
            )
        elif score >= 50:
            return (
                "border-amber-200",
                "text-amber-800",
                "bg-amber-50",
            )
        else:
            return (
                "border-red-200",
                "text-red-800",
                "bg-red-50",
            )

    @staticmethod
    def calculate_clarity_percentage(correct_answers: int, total_responded: int) -> float:
        """
        Calculate clarity percentage based on correct answers.
        
        Args:
            correct_answers: Number of participants who answered correctly
            total_responded: Total number of participants who responded
            
        Returns:
            Clarity percentage as float (0-100)
        """
        if total_responded == 0:
            return 0.0
        
        return (correct_answers / total_responded) * 100

    @staticmethod
    def get_clarity_analysis(correct_answers: int, total_responded: int) -> Dict[str, any]:
        """
        Get complete clarity analysis including percentage, message, and styling.
        
        Args:
            correct_answers: Number of participants who answered correctly
            total_responded: Total number of participants who responded
            
        Returns:
            Dictionary with percentage, message, styling classes, and metadata
        """
        percentage = UnderstandingService.calculate_clarity_percentage(correct_answers, total_responded)
        message = UnderstandingService.get_understanding_message(percentage)
        border_class, text_class, bg_class = UnderstandingService.get_understanding_tailwind(percentage)
        
        return {
            "percentage": round(percentage, 1),
            "correct_answers": correct_answers,
            "total_responded": total_responded,
            "title": message["title"],
            "description": message["description"],
            "border_class": border_class,
            "text_class": text_class,
            "bg_class": bg_class
        }
