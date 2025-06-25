"""Validator for generated platform implementations."""

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A validation issue found in generated code."""
    
    severity: str  # 'error', 'warning', 'info'
    file_path: Path
    line_number: Optional[int] = None
    column: Optional[int] = None
    message: str = ""
    rule: str = ""
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'severity': self.severity,
            'file_path': str(self.file_path),
            'line_number': self.line_number,
            'column': self.column,
            'message': self.message,
            'rule': self.rule,
            'suggestion': self.suggestion
        }


@dataclass
class ValidationReport:
    """Complete validation report for a platform implementation."""
    
    platform_name: str
    validation_time: datetime = field(default_factory=datetime.utcnow)
    issues: List[ValidationIssue] = field(default_factory=list)
    files_checked: List[Path] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        """Number of errors found."""
        return len([i for i in self.issues if i.severity == 'error'])
    
    @property
    def warning_count(self) -> int:
        """Number of warnings found."""
        return len([i for i in self.issues if i.severity == 'warning'])
    
    @property
    def info_count(self) -> int:
        """Number of info issues found."""
        return len([i for i in self.issues if i.severity == 'info'])
    
    @property
    def is_valid(self) -> bool:
        """Whether the implementation is valid (no errors)."""
        return self.error_count == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform_name': self.platform_name,
            'validation_time': self.validation_time.isoformat(),
            'is_valid': self.is_valid,
            'summary': {
                'errors': self.error_count,
                'warnings': self.warning_count,
                'info': self.info_count,
                'files_checked': len(self.files_checked)
            },
            'issues': [issue.to_dict() for issue in self.issues],
            'files_checked': [str(f) for f in self.files_checked]
        }


class PlatformValidator:
    """Validator for platform implementations."""
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
        self.required_methods = self._get_required_methods()
        self.required_properties = self._get_required_properties()
    
    def validate_implementation(self, platform_dir: Path) -> ValidationReport:
        """Validate a complete platform implementation."""
        
        platform_name = platform_dir.name
        report = ValidationReport(platform_name=platform_name)
        
        try:
            # Find Python files to validate
            python_files = list(platform_dir.glob('**/*.py'))
            report.files_checked = python_files
            
            if not python_files:
                report.issues.append(ValidationIssue(
                    severity='error',
                    file_path=platform_dir,
                    message="No Python files found in platform directory",
                    rule='file_structure'
                ))
                return report
            
            # Find main platform file
            main_platform_file = self._find_main_platform_file(python_files)
            if not main_platform_file:
                report.issues.append(ValidationIssue(
                    severity='error',
                    file_path=platform_dir,
                    message="No main platform file found (should contain class inheriting from BasePlatform)",
                    rule='platform_class'
                ))
                return report
            
            # Validate each Python file
            for py_file in python_files:
                file_issues = self._validate_python_file(py_file, is_main=(py_file == main_platform_file))
                report.issues.extend(file_issues)
            
            # Validate platform structure
            structure_issues = self._validate_platform_structure(platform_dir, main_platform_file)
            report.issues.extend(structure_issues)
            
            logger.info(f"Validation complete: {report.error_count} errors, {report.warning_count} warnings")
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            report.issues.append(ValidationIssue(
                severity='error',
                file_path=platform_dir,
                message=f"Validation failed: {e}",
                rule='validation_error'
            ))
        
        return report
    
    def validate_single_file(self, file_path: Path, is_main_platform: bool = False) -> List[ValidationIssue]:
        """Validate a single Python file."""
        
        return self._validate_python_file(file_path, is_main_platform)
    
    def _validate_python_file(self, file_path: Path, is_main: bool = False) -> List[ValidationIssue]:
        """Validate a single Python file."""
        
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    severity='error',
                    file_path=file_path,
                    line_number=e.lineno,
                    column=e.offset,
                    message=f"Syntax error: {e.msg}",
                    rule='syntax'
                ))
                return issues
            
            # Analyze AST
            analyzer = ASTAnalyzer(file_path, content)
            analyzer.visit(tree)
            
            # Check imports
            import_issues = self._check_imports(analyzer, is_main)
            issues.extend(import_issues)
            
            # Check class definitions
            class_issues = self._check_class_definitions(analyzer, is_main)
            issues.extend(class_issues)
            
            # Check method implementations
            method_issues = self._check_method_implementations(analyzer, is_main)
            issues.extend(method_issues)
            
            # Check code quality
            quality_issues = self._check_code_quality(analyzer)
            issues.extend(quality_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                severity='error',
                file_path=file_path,
                message=f"File validation failed: {e}",
                rule='file_error'
            ))
        
        return issues
    
    def _check_imports(self, analyzer: 'ASTAnalyzer', is_main: bool) -> List[ValidationIssue]:
        """Check import statements."""
        
        issues = []
        
        if is_main:
            # Main platform file should import BasePlatform
            has_base_platform = any(
                'BasePlatform' in imp for imp in analyzer.imports
            )
            
            if not has_base_platform:
                issues.append(ValidationIssue(
                    severity='error',
                    file_path=analyzer.file_path,
                    line_number=1,
                    message="Main platform file must import BasePlatform",
                    rule='required_imports',
                    suggestion="Add: from ...core.base_platform import BasePlatform"
                ))
            
            # Check for required authentication imports
            if analyzer.has_authentication_code and not any(
                'authenticator' in imp.lower() for imp in analyzer.imports
            ):
                issues.append(ValidationIssue(
                    severity='warning',
                    file_path=analyzer.file_path,
                    message="Authentication code detected but no authenticator imports found",
                    rule='authentication_imports'
                ))
        
        # Check for unused imports
        for imp in analyzer.imports:
            if not analyzer.is_import_used(imp):
                issues.append(ValidationIssue(
                    severity='info',
                    file_path=analyzer.file_path,
                    message=f"Possibly unused import: {imp}",
                    rule='unused_imports'
                ))
        
        return issues
    
    def _check_class_definitions(self, analyzer: 'ASTAnalyzer', is_main: bool) -> List[ValidationIssue]:
        """Check class definitions."""
        
        issues = []
        
        if is_main:
            # Should have exactly one class inheriting from BasePlatform
            platform_classes = [
                cls for cls in analyzer.classes
                if 'BasePlatform' in cls.get('bases', [])
            ]
            
            if not platform_classes:
                issues.append(ValidationIssue(
                    severity='error',
                    file_path=analyzer.file_path,
                    message="Main platform file must contain a class inheriting from BasePlatform",
                    rule='platform_class_inheritance'
                ))
            elif len(platform_classes) > 1:
                issues.append(ValidationIssue(
                    severity='warning',
                    file_path=analyzer.file_path,
                    message="Multiple classes inherit from BasePlatform",
                    rule='multiple_platform_classes'
                ))
            
            # Check class naming
            for cls in platform_classes:
                class_name = cls['name']
                if not class_name.endswith('Platform'):
                    issues.append(ValidationIssue(
                        severity='warning',
                        file_path=analyzer.file_path,
                        line_number=cls.get('line_number'),
                        message=f"Platform class name '{class_name}' should end with 'Platform'",
                        rule='naming_convention'
                    ))
        
        return issues
    
    def _check_method_implementations(self, analyzer: 'ASTAnalyzer', is_main: bool) -> List[ValidationIssue]:
        """Check method implementations."""
        
        issues = []
        
        if is_main:
            # Check for required methods
            platform_class = next(
                (cls for cls in analyzer.classes if 'BasePlatform' in cls.get('bases', [])),
                None
            )
            
            if platform_class:
                class_methods = set(platform_class.get('methods', []))
                
                # Check required abstract methods
                for method in self.required_methods:
                    if method not in class_methods:
                        issues.append(ValidationIssue(
                            severity='error',
                            file_path=analyzer.file_path,
                            message=f"Missing required method: {method}",
                            rule='required_methods'
                        ))
                
                # Check required properties
                class_properties = set(platform_class.get('properties', []))
                for prop in self.required_properties:
                    if prop not in class_properties:
                        issues.append(ValidationIssue(
                            severity='error',
                            file_path=analyzer.file_path,
                            message=f"Missing required property: {prop}",
                            rule='required_properties'
                        ))
                
                # Check method signatures
                for method_name, method_info in platform_class.get('method_details', {}).items():
                    if method_name.startswith('_') and not method_name.startswith('__'):
                        # Private method - check naming
                        if not re.match(r'^_[a-z][a-z0-9_]*$', method_name):
                            issues.append(ValidationIssue(
                                severity='info',
                                file_path=analyzer.file_path,
                                line_number=method_info.get('line_number'),
                                message=f"Method name '{method_name}' doesn't follow snake_case convention",
                                rule='naming_convention'
                            ))
        
        return issues
    
    def _check_code_quality(self, analyzer: 'ASTAnalyzer') -> List[ValidationIssue]:
        """Check code quality metrics."""
        
        issues = []
        
        # Check for long methods
        for class_info in analyzer.classes:
            for method_name, method_info in class_info.get('method_details', {}).items():
                line_count = method_info.get('line_count', 0)
                if line_count > 50:
                    issues.append(ValidationIssue(
                        severity='warning',
                        file_path=analyzer.file_path,
                        line_number=method_info.get('line_number'),
                        message=f"Method '{method_name}' is very long ({line_count} lines)",
                        rule='method_length',
                        suggestion="Consider breaking into smaller methods"
                    ))
        
        # Check for missing docstrings
        for class_info in analyzer.classes:
            if not class_info.get('has_docstring'):
                issues.append(ValidationIssue(
                    severity='info',
                    file_path=analyzer.file_path,
                    line_number=class_info.get('line_number'),
                    message=f"Class '{class_info['name']}' missing docstring",
                    rule='docstrings'
                ))
            
            for method_name, method_info in class_info.get('method_details', {}).items():
                if not method_name.startswith('_') and not method_info.get('has_docstring'):
                    issues.append(ValidationIssue(
                        severity='info',
                        file_path=analyzer.file_path,
                        line_number=method_info.get('line_number'),
                        message=f"Public method '{method_name}' missing docstring",
                        rule='docstrings'
                    ))
        
        return issues
    
    def _validate_platform_structure(self, platform_dir: Path, main_file: Path) -> List[ValidationIssue]:
        """Validate overall platform structure."""
        
        issues = []
        
        # Check for __init__.py
        init_file = platform_dir / "__init__.py"
        if not init_file.exists():
            issues.append(ValidationIssue(
                severity='warning',
                file_path=platform_dir,
                message="Missing __init__.py file",
                rule='file_structure',
                suggestion="Create __init__.py to make directory a Python package"
            ))
        
        # Check for tests
        test_files = list(platform_dir.glob('**/test_*.py'))
        if not test_files:
            issues.append(ValidationIssue(
                severity='info',
                file_path=platform_dir,
                message="No test files found",
                rule='testing',
                suggestion="Add test files to ensure code quality"
            ))
        
        return issues
    
    def _find_main_platform_file(self, python_files: List[Path]) -> Optional[Path]:
        """Find the main platform implementation file."""
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Quick check for BasePlatform inheritance
                if 'class ' in content and 'BasePlatform' in content:
                    # Parse to confirm
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if (isinstance(node, ast.ClassDef) and 
                                any(isinstance(base, ast.Name) and base.id == 'BasePlatform' 
                                    for base in node.bases)):
                                return py_file
                    except SyntaxError:
                        continue
                        
            except Exception:
                continue
        
        return None
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules configuration."""
        
        return {
            'syntax': {'severity': 'error'},
            'required_imports': {'severity': 'error'},
            'platform_class_inheritance': {'severity': 'error'},
            'required_methods': {'severity': 'error'},
            'required_properties': {'severity': 'error'},
            'naming_convention': {'severity': 'warning'},
            'method_length': {'severity': 'warning', 'max_lines': 50},
            'docstrings': {'severity': 'info'},
            'unused_imports': {'severity': 'info'},
            'testing': {'severity': 'info'}
        }
    
    def _get_required_methods(self) -> Set[str]:
        """Get set of required method names."""
        
        return {
            '_setup_authenticator',
            '_post_content_impl',
            '_update_profile_impl',
            '_delete_post_impl'
        }
    
    def _get_required_properties(self) -> Set[str]:
        """Get set of required property names."""
        
        return {
            'platform_name',
            'platform_display_name',
            'supported_content_types',
            'supported_media_types',
            'platform_capabilities',
            'character_limit'
        }


class ASTAnalyzer(ast.NodeVisitor):
    """AST analyzer for extracting code information."""
    
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        
        # Analysis results
        self.imports = []
        self.classes = []
        self.functions = []
        self.current_class = None
        self.has_authentication_code = False
        
        # Track usage
        self.used_names = set()
    
    def visit_Import(self, node):
        """Visit import statements."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from import statements."""
        module = node.module or ''
        for alias in node.names:
            import_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(import_name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Visit class definitions."""
        class_info = {
            'name': node.name,
            'line_number': node.lineno,
            'bases': [self._get_base_name(base) for base in node.bases],
            'methods': [],
            'properties': [],
            'method_details': {},
            'has_docstring': ast.get_docstring(node) is not None
        }
        
        self.current_class = class_info
        self.classes.append(class_info)
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        if self.current_class:
            # Method within a class
            self.current_class['methods'].append(node.name)
            
            # Analyze method details
            method_details = {
                'line_number': node.lineno,
                'line_count': self._count_method_lines(node),
                'has_docstring': ast.get_docstring(node) is not None,
                'is_property': any(
                    isinstance(decorator, ast.Name) and decorator.id == 'property'
                    for decorator in node.decorator_list
                )
            }
            
            if method_details['is_property']:
                self.current_class['properties'].append(node.name)
            
            self.current_class['method_details'][node.name] = method_details
        else:
            # Top-level function
            self.functions.append(node.name)
        
        # Check for authentication-related code
        if 'auth' in node.name.lower() or 'token' in node.name.lower():
            self.has_authentication_code = True
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name references."""
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def is_import_used(self, import_name: str) -> bool:
        """Check if an import is used."""
        # Simple heuristic - check if any part of import name is used
        import_parts = import_name.split('.')
        return any(part in self.used_names for part in import_parts)
    
    def _get_base_name(self, base_node) -> str:
        """Get base class name from AST node."""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            return base_node.attr
        else:
            return str(base_node)
    
    def _count_method_lines(self, node) -> int:
        """Count lines in a method."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        else:
            # Fallback: estimate based on body
            return len(node.body) + 2  # Rough estimate