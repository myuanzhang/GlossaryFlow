"""
Progress Tracking Types for Translation

Shared progress data structures used across translation components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


class ProgressPhase:
    """Translation progress phases for detailed tracking"""
    VALIDATION = "validation"
    PROMPT_BUILDING = "prompt_building"
    LLM_REQUEST = "llm_request"
    OUTPUT_CLEANING = "output_cleaning"
    COMPLETED = "completed"

    # Phase weights for overall progress calculation
    PHASE_WEIGHTS = {
        VALIDATION: 10,
        PROMPT_BUILDING: 5,
        LLM_REQUEST: 80,
        OUTPUT_CLEANING: 5,
    }


@dataclass
class ProgressData:
    """Progress information for real-time updates"""
    phase: str
    progress: int  # 0-100 within current phase
    overall_progress: int  # 0-100 overall
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def calculate_overall_progress(cls, current_phase: str, phase_progress: int) -> int:
        """Calculate overall progress based on current phase and its progress"""
        total_weight = sum(ProgressPhase.PHASE_WEIGHTS.values())
        completed_weight = 0

        for phase, weight in ProgressPhase.PHASE_WEIGHTS.items():
            if phase == current_phase:
                completed_weight += weight * (phase_progress / 100)
                break
            else:
                completed_weight += weight

        return int((completed_weight / total_weight) * 100)