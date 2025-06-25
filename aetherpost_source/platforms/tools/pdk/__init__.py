"""AetherPost Platform Development Kit (PDK)."""

from .core.generator import PlatformGenerator, GenerationResult
from .core.validator import PlatformValidator, ValidationReport
from .core.template_engine import TemplateEngine
from .core.analyzer import SpecificationAnalyzer

__all__ = [
    'PlatformGenerator',
    'GenerationResult',
    'PlatformValidator', 
    'ValidationReport',
    'TemplateEngine',
    'SpecificationAnalyzer'
]

__version__ = "1.0.0"