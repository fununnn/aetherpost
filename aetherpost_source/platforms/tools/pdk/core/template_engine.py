"""Template engine for platform code generation."""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
    from jinja2.exceptions import TemplateError, TemplateNotFound
except ImportError:
    Environment = None
    FileSystemLoader = None
    select_autoescape = None
    Template = None
    TemplateError = Exception
    TemplateNotFound = Exception

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Jinja2-based template engine for platform generation."""
    
    def __init__(self, template_dirs: List[Path]):
        if Environment is None:
            raise ImportError("Jinja2 is required for template engine. Install with: pip install jinja2")
        
        self.template_dirs = template_dirs
        self.environment = Environment(
            loader=FileSystemLoader([str(d) for d in template_dirs]),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Setup custom filters and functions
        self._setup_custom_filters()
        self._setup_custom_functions()
        
        # Template cache
        self._template_cache: Dict[str, Template] = {}
    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        output_file: Optional[Path] = None
    ) -> str:
        """Render a template with the given context."""
        
        try:
            template = self._get_template(template_name)
            rendered_content = template.render(**context)
            
            if output_file:
                self._write_output(output_file, rendered_content)
                logger.debug(f"Rendered template {template_name} to {output_file}")
            
            return rendered_content
            
        except TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_name}")
        except TemplateError as e:
            raise ValueError(f"Template rendering failed for {template_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error rendering template {template_name}: {e}")
            raise
    
    def render_string_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template from string content."""
        
        try:
            template = self.environment.from_string(template_string)
            return template.render(**context)
        except TemplateError as e:
            raise ValueError(f"String template rendering failed: {e}")
    
    def list_available_templates(self) -> List[str]:
        """List all available templates."""
        
        templates = set()
        
        for template_dir in self.template_dirs:
            if template_dir.exists():
                for template_file in template_dir.rglob('*.j2'):
                    relative_path = template_file.relative_to(template_dir)
                    templates.add(str(relative_path))
        
        return sorted(templates)
    
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """Validate a template for syntax errors."""
        
        errors = []
        warnings = []
        
        try:
            template = self._get_template(template_name)
            
            # Try to parse the template
            try:
                template.new_context()
                logger.debug(f"Template {template_name} is valid")
            except Exception as e:
                errors.append(f"Template context error: {e}")
            
        except TemplateNotFound:
            errors.append(f"Template not found: {template_name}")
        except TemplateError as e:
            errors.append(f"Template syntax error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'template': template_name
        }
    
    def get_template_variables(self, template_name: str) -> Set[str]:
        """Extract variables used in a template."""
        
        try:
            template = self._get_template(template_name)
            
            # Parse template to find variables
            ast = self.environment.parse(template.source)
            variables = set()
            
            # Walk the AST to find variable references
            for node in ast.find_all((
                self.environment.nodes.Name,
                self.environment.nodes.Getattr,
                self.environment.nodes.Getitem
            )):
                if hasattr(node, 'name'):
                    variables.add(node.name)
            
            return variables
            
        except Exception as e:
            logger.warning(f"Failed to extract variables from {template_name}: {e}")
            return set()
    
    def _get_template(self, template_name: str) -> Template:
        """Get template with caching."""
        
        if template_name not in self._template_cache:
            self._template_cache[template_name] = self.environment.get_template(template_name)
        
        return self._template_cache[template_name]
    
    def _write_output(self, output_file: Path, content: str):
        """Write rendered content to file."""
        
        # Create parent directories if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _setup_custom_filters(self):
        """Setup custom Jinja2 filters."""
        
        @self.environment.filter('snake_case')
        def snake_case(text: str) -> str:
            """Convert text to snake_case."""
            # Handle camelCase and PascalCase
            text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)
            # Handle spaces and other separators
            text = re.sub(r'[\s\-\.]+', '_', text)
            return text.lower()
        
        @self.environment.filter('camel_case')
        def camel_case(text: str) -> str:
            """Convert text to camelCase."""
            words = re.split(r'[\s_\-\.]+', text.lower())
            if not words:
                return text
            return words[0] + ''.join(word.capitalize() for word in words[1:])
        
        @self.environment.filter('pascal_case')
        def pascal_case(text: str) -> str:
            """Convert text to PascalCase."""
            words = re.split(r'[\s_\-\.]+', text.lower())
            return ''.join(word.capitalize() for word in words)
        
        @self.environment.filter('kebab_case')
        def kebab_case(text: str) -> str:
            """Convert text to kebab-case."""
            # Handle camelCase and PascalCase
            text = re.sub('([a-z0-9])([A-Z])', r'\1-\2', text)
            # Handle spaces and other separators
            text = re.sub(r'[\s_\.]+', '-', text)
            return text.lower()
        
        @self.environment.filter('upper_snake_case')
        def upper_snake_case(text: str) -> str:
            """Convert text to UPPER_SNAKE_CASE."""
            return snake_case(text).upper()
        
        @self.environment.filter('http_method')
        def http_method(endpoint_or_method: str) -> str:
            """Extract HTTP method from endpoint string or return as-is."""
            if isinstance(endpoint_or_method, str):
                if ' ' in endpoint_or_method:
                    # Format: "METHOD /path"
                    return endpoint_or_method.split(' ')[0].upper()
                else:
                    # Assume it's just a method
                    return endpoint_or_method.upper()
            return 'GET'
        
        @self.environment.filter('endpoint_path')
        def endpoint_path(endpoint: str) -> str:
            """Extract path from endpoint string."""
            if ' ' in endpoint:
                # Format: "METHOD /path"
                return endpoint.split(' ', 1)[1]
            else:
                # Assume it's just a path
                return endpoint
        
        @self.environment.filter('json_safe')
        def json_safe(value: Any) -> str:
            """Convert value to JSON-safe string."""
            import json
            return json.dumps(value)
        
        @self.environment.filter('indent_code')
        def indent_code(text: str, spaces: int = 4) -> str:
            """Indent each line of text."""
            if not text:
                return text
            
            indent = ' ' * spaces
            lines = text.split('\n')
            indented_lines = [indent + line if line.strip() else line for line in lines]
            return '\n'.join(indented_lines)
        
        @self.environment.filter('comment_block')
        def comment_block(text: str, style: str = 'python') -> str:
            """Convert text to comment block."""
            if not text:
                return text
            
            lines = text.split('\n')
            
            if style == 'python':
                commented_lines = [f"# {line}" if line.strip() else "#" for line in lines]
            elif style == 'javascript':
                commented_lines = [f"// {line}" if line.strip() else "//" for line in lines]
            elif style == 'block':
                commented_lines = ["/*"] + [f" * {line}" if line.strip() else " *" for line in lines] + [" */"]
            else:
                commented_lines = [f"# {line}" if line.strip() else "#" for line in lines]
            
            return '\n'.join(commented_lines)
    
    def _setup_custom_functions(self):
        """Setup custom Jinja2 global functions."""
        
        @self.environment.global_function
        def now() -> str:
            """Get current timestamp."""
            return datetime.utcnow().isoformat()
        
        @self.environment.global_function
        def today() -> str:
            """Get current date."""
            return datetime.utcnow().strftime('%Y-%m-%d')
        
        @self.environment.global_function
        def range_list(start: int, end: int, step: int = 1) -> List[int]:
            """Generate range as list."""
            return list(range(start, end, step))
        
        @self.environment.global_function
        def has_feature(features, feature_name: str) -> bool:
            """Check if features object has a specific feature enabled."""
            if not features:
                return False
            
            if hasattr(features, feature_name):
                return getattr(features, feature_name, False)
            elif isinstance(features, dict):
                return features.get(feature_name, False)
            
            return False
        
        @self.environment.global_function
        def get_content_type_limit(content_types, content_type: str, limit_type: str) -> Optional[Any]:
            """Get limit for specific content type."""
            if not content_types or content_type not in content_types:
                return None
            
            content_spec = content_types[content_type]
            return getattr(content_spec, limit_type, None)
        
        @self.environment.global_function
        def filter_endpoints(endpoints, category: str) -> Dict[str, Any]:
            """Filter endpoints by category."""
            if not endpoints:
                return {}
            
            return {
                name: endpoint for name, endpoint in endpoints.items()
                if name.startswith(category)
            }
        
        @self.environment.global_function
        def format_docstring(text: str, width: int = 72) -> str:
            """Format text as Python docstring."""
            if not text:
                return '"""No description available."""'
            
            # Simple word wrapping
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                word_length = len(word)
                if current_length + word_length + 1 > width and current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    current_line.append(word)
                    current_length += word_length + (1 if current_line else 0)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            if len(lines) == 1:
                return f'"""{lines[0]}."""'
            else:
                return '"""' + lines[0] + '\n    \n    ' + '\n    '.join(lines[1:]) + '\n    """'
    
    def clear_cache(self):
        """Clear template cache."""
        self._template_cache.clear()
        logger.debug("Cleared template cache")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get template engine information."""
        
        return {
            'template_dirs': [str(d) for d in self.template_dirs],
            'available_templates': self.list_available_templates(),
            'cached_templates': list(self._template_cache.keys()),
            'jinja2_version': getattr(self.environment, 'version', 'unknown') if hasattr(self.environment, 'version') else 'unknown'
        }