"""
This file serves as a bridge to make the adaptive_learning module importable
from the project root, maintaining compatibility with existing code.
"""

# Re-export AdaptiveLearningSystem from its actual location
from src.adaptive_learning import AdaptiveLearningSystem

# Re-export any other required classes or functions
# from src.adaptive_learning import OtherClass, some_function

# Define __all__ to control what gets imported with "from adaptive_learning import *"
__all__ = ['AdaptiveLearningSystem'] 