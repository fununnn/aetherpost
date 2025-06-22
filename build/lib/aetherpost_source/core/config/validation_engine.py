"""Configuration validation rule engine for AetherPost."""

import re
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

from aetherpost.core.common.base_models import OperationResult, Platform


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A validation issue found during configuration validation."""
    field_path: str
    severity: ValidationSeverity
    message: str
    suggested_fix: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    issues: List[ValidationIssue]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class ValidationRule(ABC):
    """Abstract base class for validation rules."""
    
    def __init__(self, field_path: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.field_path = field_path
        self.severity = severity
    
    @abstractmethod
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a value and return any issues found."""
        pass
    
    def create_issue(self, message: str, suggested_fix: Optional[str] = None,
                    error_code: Optional[str] = None) -> ValidationIssue:
        """Helper to create a validation issue."""
        return ValidationIssue(
            field_path=self.field_path,
            severity=self.severity,
            message=message,
            suggested_fix=suggested_fix,
            error_code=error_code
        )


class RequiredRule(ValidationRule):
    """Rule to check if a required field is present and not empty."""
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return [self.create_issue(
                f"Field '{self.field_path}' is required",
                suggested_fix="Provide a value for this field"
            )]
        return []


class TypeRule(ValidationRule):
    """Rule to check if a field matches the expected type."""
    
    def __init__(self, field_path: str, expected_type: type, 
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(field_path, severity)
        self.expected_type = expected_type
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is not None and not isinstance(value, self.expected_type):
            return [self.create_issue(
                f"Field '{self.field_path}' must be of type {self.expected_type.__name__}, got {type(value).__name__}",
                suggested_fix=f"Convert value to {self.expected_type.__name__}"
            )]
        return []


class RegexRule(ValidationRule):
    """Rule to validate a field against a regular expression."""
    
    def __init__(self, field_path: str, pattern: str, 
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(field_path, severity)
        self.pattern = re.compile(pattern)
        self.pattern_str = pattern
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is not None and isinstance(value, str):
            if not self.pattern.match(value):
                return [self.create_issue(
                    f"Field '{self.field_path}' does not match required pattern: {self.pattern_str}",
                    suggested_fix="Ensure the value matches the required format"
                )]
        return []


class LengthRule(ValidationRule):
    """Rule to validate string length constraints."""
    
    def __init__(self, field_path: str, min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(field_path, severity)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        
        if value is not None and isinstance(value, str):
            length = len(value)
            
            if self.min_length is not None and length < self.min_length:
                issues.append(self.create_issue(
                    f"Field '{self.field_path}' must be at least {self.min_length} characters, got {length}",
                    suggested_fix=f"Provide at least {self.min_length} characters"
                ))
            
            if self.max_length is not None and length > self.max_length:
                issues.append(self.create_issue(
                    f"Field '{self.field_path}' must be no more than {self.max_length} characters, got {length}",
                    suggested_fix=f"Limit to {self.max_length} characters"
                ))
        
        return issues


class ChoicesRule(ValidationRule):
    """Rule to validate that a field value is from a set of allowed choices."""
    
    def __init__(self, field_path: str, choices: List[Any],
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(field_path, severity)
        self.choices = choices
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is not None and value not in self.choices:
            return [self.create_issue(
                f"Field '{self.field_path}' must be one of {self.choices}, got '{value}'",
                suggested_fix=f"Choose from: {', '.join(map(str, self.choices))}"
            )]
        return []


class EmailRule(ValidationRule):
    """Rule to validate email addresses."""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is not None and isinstance(value, str):
            if not re.match(self.EMAIL_PATTERN, value):
                return [self.create_issue(
                    f"Field '{self.field_path}' must be a valid email address",
                    suggested_fix="Provide a valid email address (e.g., user@example.com)"
                )]
        return []


class URLRule(ValidationRule):
    """Rule to validate URLs."""
    
    URL_PATTERN = r'^https?://(?:[-\\w.])+(?:\\:[0-9]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:\\#(?:[\\w.])*)?)?$'
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if value is not None and isinstance(value, str):
            if not re.match(self.URL_PATTERN, value):
                return [self.create_issue(
                    f"Field '{self.field_path}' must be a valid URL",
                    suggested_fix="Provide a valid URL (e.g., https://example.com)"
                )]
        return []


class ConditionalRule(ValidationRule):
    """Rule that applies validation based on a condition."""
    
    def __init__(self, field_path: str, condition: Callable[[Dict[str, Any]], bool],
                 rule: ValidationRule):
        super().__init__(field_path, rule.severity)
        self.condition = condition
        self.rule = rule
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        if self.condition(context):
            return self.rule.validate(value, context)
        return []


class CustomRule(ValidationRule):
    """Rule with custom validation logic."""
    
    def __init__(self, field_path: str, validator: Callable[[Any, Dict[str, Any]], List[ValidationIssue]],
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(field_path, severity)
        self.validator = validator
    
    def validate(self, value: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        return self.validator(value, context)


class ValidationEngine:
    """Engine for running validation rules on configuration."""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.global_rules: List[ValidationRule] = []
    
    def add_rule(self, field_path: str, rule: ValidationRule) -> None:
        """Add a validation rule for a specific field."""
        if field_path not in self.rules:
            self.rules[field_path] = []
        self.rules[field_path].append(rule)
    
    def add_global_rule(self, rule: ValidationRule) -> None:
        """Add a rule that applies to the entire configuration."""
        self.global_rules.append(rule)
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against all rules."""
        issues = []
        
        # Apply field-specific rules
        for field_path, rules in self.rules.items():
            value = self._get_nested_value(config, field_path)
            
            for rule in rules:
                try:
                    field_issues = rule.validate(value, config)
                    issues.extend(field_issues)
                except Exception as e:
                    logger.error(f"Error running validation rule for {field_path}: {e}")
                    issues.append(ValidationIssue(
                        field_path=field_path,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule error: {e}",
                        error_code="RULE_ERROR"
                    ))
        
        # Apply global rules
        for rule in self.global_rules:
            try:
                global_issues = rule.validate(config, config)
                issues.extend(global_issues)
            except Exception as e:
                logger.error(f"Error running global validation rule: {e}")
                issues.append(ValidationIssue(
                    field_path="global",
                    severity=ValidationSeverity.ERROR,
                    message=f"Global validation rule error: {e}",
                    error_code="GLOBAL_RULE_ERROR"
                ))
        
        # Determine if configuration is valid (no errors)
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=not has_errors,
            issues=issues
        )
    
    def _get_nested_value(self, config: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        try:
            keys = field_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            
            return value
        except Exception:
            return None


class ConfigValidationBuilder:
    """Builder for creating common validation configurations."""
    
    def __init__(self):
        self.engine = ValidationEngine()
    
    def require_field(self, field_path: str) -> 'ConfigValidationBuilder':
        """Add required field validation."""
        self.engine.add_rule(field_path, RequiredRule(field_path))
        return self
    
    def validate_type(self, field_path: str, expected_type: type) -> 'ConfigValidationBuilder':
        """Add type validation."""
        self.engine.add_rule(field_path, TypeRule(field_path, expected_type))
        return self
    
    def validate_email(self, field_path: str) -> 'ConfigValidationBuilder':
        """Add email validation."""
        self.engine.add_rule(field_path, EmailRule(field_path))
        return self
    
    def validate_url(self, field_path: str) -> 'ConfigValidationBuilder':
        """Add URL validation."""
        self.engine.add_rule(field_path, URLRule(field_path))
        return self
    
    def validate_length(self, field_path: str, min_length: Optional[int] = None,
                       max_length: Optional[int] = None) -> 'ConfigValidationBuilder':
        """Add length validation."""
        self.engine.add_rule(field_path, LengthRule(field_path, min_length, max_length))
        return self
    
    def validate_choices(self, field_path: str, choices: List[Any]) -> 'ConfigValidationBuilder':
        """Add choices validation."""
        self.engine.add_rule(field_path, ChoicesRule(field_path, choices))
        return self
    
    def build(self) -> ValidationEngine:
        """Build and return the validation engine."""
        return self.engine


# Pre-built validation engines for common configurations
def create_autopromo_config_validator() -> ValidationEngine:
    """Create validation engine for AetherPost configuration."""
    builder = ConfigValidationBuilder()
    
    # Basic app info
    builder.require_field("app_name")
    builder.validate_type("app_name", str)
    builder.validate_length("app_name", min_length=1, max_length=100)
    
    builder.require_field("description")
    builder.validate_type("description", str)
    builder.validate_length("description", min_length=10, max_length=500)
    
    # Optional fields with validation
    builder.validate_email("contact_email")
    builder.validate_url("website_url")
    builder.validate_url("github_url")
    
    # Platform validation
    platform_values = [p.value for p in Platform]
    
    # AI configuration
    builder.validate_choices("ai.provider", ["openai", "[AI Service]", "gemini"])
    
    # Feature flags
    builder.validate_type("features.auto_posting", bool)
    builder.validate_type("features.content_review", bool)
    builder.validate_type("features.analytics", bool)
    
    # Add custom rules
    def validate_platform_credentials(platforms_config: Any, context: Dict[str, Any]) -> List[ValidationIssue]:
        """Custom validation for platform credentials."""
        issues = []
        
        if isinstance(platforms_config, dict):
            for platform_name, creds in platforms_config.items():
                if platform_name not in platform_values:
                    issues.append(ValidationIssue(
                        field_path=f"platforms.{platform_name}",
                        severity=ValidationSeverity.ERROR,
                        message=f"Unknown platform: {platform_name}",
                        suggested_fix=f"Use one of: {', '.join(platform_values)}"
                    ))
                
                # Validate platform-specific requirements
                if platform_name == "twitter":
                    required_fields = ["api_key", "api_secret", "access_token", "access_token_secret"]
                    for field in required_fields:
                        if not isinstance(creds, dict) or not creds.get(field):
                            issues.append(ValidationIssue(
                                field_path=f"platforms.{platform_name}.{field}",
                                severity=ValidationSeverity.ERROR,
                                message=f"Twitter requires {field}",
                                suggested_fix=f"Provide {field} from Twitter Developer Portal"
                            ))
        
        return issues
    
    builder.engine.add_rule("platforms", CustomRule("platforms", validate_platform_credentials))
    
    return builder.build()