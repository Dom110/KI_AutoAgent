"""
Cognitive Architecture for KI AutoAgent v6

Advanced AI capabilities:
- Learning System: Learn from workflow outcomes
- Curiosity System: Identify knowledge gaps and ask questions
- Predictive System: Predict workflow duration and issues
- Query Classifier: Intelligently route user queries
- Neurosymbolic Reasoner: Hybrid neural + symbolic reasoning
- Self-Diagnosis: Autonomous error detection and recovery

Author: KI AutoAgent Team
Version: 6.0.0
"""

from .curiosity_system_v6 import CuriositySystemV6
from .learning_system_v6 import LearningSystemV6
from .neurosymbolic_reasoner_v6 import NeurosymbolicReasonerV6
from .predictive_system_v6 import PredictiveSystemV6
from .query_classifier_v6 import QueryClassifierV6
from .self_diagnosis_v6 import SelfDiagnosisV6

__all__ = [
    "LearningSystemV6",
    "CuriositySystemV6",
    "PredictiveSystemV6",
    "QueryClassifierV6",
    "NeurosymbolicReasonerV6",
    "SelfDiagnosisV6",
]
