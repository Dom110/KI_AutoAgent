"""
Cognitive Architecture for KI AutoAgent v6

Advanced AI capabilities:
- Learning System: Learn from workflow outcomes
- Curiosity System: Identify knowledge gaps and ask questions
- Predictive System: Predict workflow duration and issues

Author: KI AutoAgent Team
Version: 6.0.0
"""

from .curiosity_system_v6 import CuriositySystemV6
from .learning_system_v6 import LearningSystemV6
from .predictive_system_v6 import PredictiveSystemV6

__all__ = ["LearningSystemV6", "CuriositySystemV6", "PredictiveSystemV6"]
