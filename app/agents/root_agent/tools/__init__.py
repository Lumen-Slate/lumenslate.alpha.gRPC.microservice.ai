"""
Tools for root agent that provide direct MongoDB access functionality.
These tools replace the previous utils that called the gin backend.
"""

from .get_assignment_by_id import get_assignment_by_id
from .get_assignment_results_by_student_id import get_assignment_results_by_student_id
from .get_report_card_by_student_id import get_report_card_by_student_id

__all__ = [
    "get_assignment_by_id",
    "get_assignment_results_by_student_id", 
    "get_report_card_by_student_id"
] 