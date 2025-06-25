"""Platform implementation generator."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from .analyzer import SpecificationAnalyzer, PlatformSpec
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """Information about a generated file."""
    
    template_name: str
    output_path: Path
    size_bytes: int
    lines_count: int
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'template_name': self.template_name,
            'output_path': str(self.output_path),
            'size_bytes': self.size_bytes,
            'lines_count': self.lines_count,
            'generated_at': self.generated_at.isoformat()
        }


@dataclass
class GenerationResult:
    """Result of platform generation."""
    
    success: bool
    platform_name: str
    generated_files: List[GeneratedFile] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generation_time: Optional[float] = None
    output_directory: Optional[Path] = None
    
    @property
    def total_files(self) -> int:
        """Total number of generated files."""
        return len(self.generated_files)
    
    @property
    def total_size_bytes(self) -> int:
        """Total size of generated files."""
        return sum(f.size_bytes for f in self.generated_files)
    
    @property
    def total_lines(self) -> int:
        """Total lines of generated code."""
        return sum(f.lines_count for f in self.generated_files)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'platform_name': self.platform_name,
            'generated_files': [f.to_dict() for f in self.generated_files],
            'errors': self.errors,
            'warnings': self.warnings,
            'generation_time': self.generation_time,
            'output_directory': str(self.output_directory) if self.output_directory else None,
            'stats': {
                'total_files': self.total_files,
                'total_size_bytes': self.total_size_bytes,
                'total_lines': self.total_lines
            }
        }


class PlatformGenerator:
    """Generator for platform implementations from specifications."""
    
    def __init__(self, template_dirs: Optional[List[Path]] = None):
        # Setup template directories
        if template_dirs is None:
            default_template_dir = Path(__file__).parent.parent / "templates"
            template_dirs = [default_template_dir]
        
        self.template_dirs = template_dirs
        self.template_engine = TemplateEngine(template_dirs)
        self.analyzer = SpecificationAnalyzer()
        
        # Template selection rules
        self.template_rules = self._setup_template_rules()
        
        # Generation configuration
        self.config = {
            'overwrite_existing': False,
            'create_directories': True,
            'backup_existing': True,
            'validate_output': True
        }
    
    def generate_platform(
        self, 
        spec_file: Path, 
        output_dir: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Generate platform implementation from specification."""
        
        start_time = datetime.utcnow()
        
        try:
            # Update configuration
            if config:
                self.config.update(config)
            
            # Analyze specification
            logger.info(f"Analyzing specification: {spec_file}")
            spec = self.analyzer.analyze_specification(spec_file)
            
            # Create generation context
            context = self.analyzer.get_generation_context(spec)
            context['generation_timestamp'] = start_time.isoformat()
            
            # Select templates to generate
            templates_to_generate = self._select_templates(spec)
            
            logger.info(f"Generating {len(templates_to_generate)} files for {spec.display_name}")
            
            # Generate files
            generated_files = []
            errors = []
            warnings = []
            
            for template_name, template_config in templates_to_generate.items():
                try:
                    generated_file = self._generate_file(
                        template_name,
                        template_config,
                        context,
                        output_dir
                    )
                    generated_files.append(generated_file)
                    
                except Exception as e:
                    error_msg = f"Failed to generate {template_name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Validate generated code if enabled
            if self.config.get('validate_output', True) and generated_files:
                validation_warnings = self._validate_generated_code(output_dir)
                warnings.extend(validation_warnings)
            
            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = GenerationResult(
                success=len(errors) == 0,
                platform_name=spec.name,
                generated_files=generated_files,
                errors=errors,
                warnings=warnings,
                generation_time=generation_time,
                output_directory=output_dir
            )
            
            if result.success:
                logger.info(
                    f"Successfully generated {spec.display_name} platform: "
                    f"{result.total_files} files, {result.total_lines} lines, "
                    f"{result.total_size_bytes} bytes in {generation_time:.2f}s"
                )
            else:
                logger.error(f"Platform generation failed with {len(errors)} errors")
            
            return result
            
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Platform generation failed: {e}")
            
            return GenerationResult(
                success=False,
                platform_name=spec_file.stem if 'spec' not in locals() else spec.name,
                errors=[f"Generation failed: {e}"],
                generation_time=generation_time
            )
    
    def generate_from_spec(
        self, 
        spec: PlatformSpec, 
        output_dir: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Generate platform implementation from parsed specification."""
        
        start_time = datetime.utcnow()
        
        try:
            # Update configuration
            if config:
                self.config.update(config)
            
            # Create generation context
            context = self.analyzer.get_generation_context(spec)
            context['generation_timestamp'] = start_time.isoformat()
            
            # Select templates to generate
            templates_to_generate = self._select_templates(spec)
            
            logger.info(f"Generating {len(templates_to_generate)} files for {spec.display_name}")
            
            # Generate files
            generated_files = []
            errors = []
            warnings = []
            
            for template_name, template_config in templates_to_generate.items():
                try:
                    generated_file = self._generate_file(
                        template_name,
                        template_config,
                        context,
                        output_dir
                    )
                    generated_files.append(generated_file)
                    
                except Exception as e:
                    error_msg = f"Failed to generate {template_name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            return GenerationResult(
                success=len(errors) == 0,
                platform_name=spec.name,
                generated_files=generated_files,
                errors=errors,
                warnings=warnings,
                generation_time=generation_time,
                output_directory=output_dir
            )
            
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Platform generation failed: {e}")
            
            return GenerationResult(
                success=False,
                platform_name=spec.name,
                errors=[f"Generation failed: {e}"],
                generation_time=generation_time
            )
    
    def _select_templates(self, spec: PlatformSpec) -> Dict[str, Dict[str, Any]]:
        """Select templates to generate based on specification."""
        
        templates = {}
        
        # Always generate base platform file
        templates['platform_base.py.j2'] = {
            'output_filename': f"{spec.module_name}.py",
            'context_updates': {}
        }
        
        # Generate __init__.py
        templates['__init__.py.j2'] = {
            'output_filename': "__init__.py",
            'context_updates': {}
        }
        
        # Generate authentication module if needed
        if spec.authentication:
            auth_template = f"authentication/{spec.authentication.type}.py.j2"
            if auth_template in self.template_engine.list_available_templates():
                templates[auth_template] = {
                    'output_filename': f"auth_{spec.authentication.type}.py",
                    'context_updates': {'auth_config': spec.authentication}
                }
        
        # Generate content type handlers
        for content_type in spec.content_types:
            content_template = f"content_types/{content_type}.py.j2"
            if content_template in self.template_engine.list_available_templates():
                templates[content_template] = {
                    'output_filename': f"content_{content_type}.py",
                    'context_updates': {
                        'content_type': content_type,
                        'content_spec': spec.content_types[content_type]
                    }
                }
        
        # Generate feature modules
        if spec.features:
            if spec.features.profile_management:
                templates['features/profile_management.py.j2'] = {
                    'output_filename': "profile_manager.py",
                    'context_updates': {}
                }
            
            if spec.features.analytics:
                templates['features/analytics.py.j2'] = {
                    'output_filename': "analytics.py",
                    'context_updates': {}
                }
            
            if spec.features.media_upload:
                templates['features/media_upload.py.j2'] = {
                    'output_filename': "media_handler.py",
                    'context_updates': {}
                }
        
        # Generate configuration files
        templates['config/platform_config.py.j2'] = {
            'output_filename': "config.py",
            'context_updates': {}
        }
        
        # Generate tests
        templates['tests/test_platform.py.j2'] = {
            'output_filename': f"test_{spec.module_name}.py",
            'output_subdir': "tests",
            'context_updates': {}
        }
        
        # Filter templates that actually exist
        available_templates = set(self.template_engine.list_available_templates())
        existing_templates = {
            name: config for name, config in templates.items()
            if name in available_templates
        }
        
        logger.debug(f"Selected {len(existing_templates)} templates from {len(templates)} candidates")
        return existing_templates
    
    def _generate_file(
        self,
        template_name: str,
        template_config: Dict[str, Any],
        base_context: Dict[str, Any],
        output_dir: Path
    ) -> GeneratedFile:
        """Generate a single file from template."""
        
        # Prepare output path
        output_filename = template_config.get('output_filename', template_name.replace('.j2', ''))
        output_subdir = template_config.get('output_subdir')
        
        if output_subdir:
            final_output_dir = output_dir / output_subdir
        else:
            final_output_dir = output_dir
        
        output_path = final_output_dir / output_filename
        
        # Create directories if needed
        if self.config.get('create_directories', True):
            final_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and handle accordingly
        if output_path.exists() and not self.config.get('overwrite_existing', False):
            if self.config.get('backup_existing', True):
                backup_path = output_path.with_suffix(f'.backup.{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
                output_path.rename(backup_path)
                logger.info(f"Backed up existing file to {backup_path}")
        
        # Prepare context
        context = base_context.copy()
        context.update(template_config.get('context_updates', {}))
        
        # Render template
        rendered_content = self.template_engine.render_template(
            template_name,
            context,
            output_path
        )
        
        # Calculate file statistics
        size_bytes = len(rendered_content.encode('utf-8'))
        lines_count = len(rendered_content.split('\n'))
        
        return GeneratedFile(
            template_name=template_name,
            output_path=output_path,
            size_bytes=size_bytes,
            lines_count=lines_count
        )
    
    def _validate_generated_code(self, output_dir: Path) -> List[str]:
        """Validate generated code for basic syntax and structure."""
        
        warnings = []
        
        # Check for Python syntax errors
        for py_file in output_dir.glob('**/*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Basic syntax check
                try:
                    compile(code, str(py_file), 'exec')
                except SyntaxError as e:
                    warnings.append(f"Syntax error in {py_file}: {e}")
                
                # Check for required imports
                if 'from ...core.base_platform import BasePlatform' not in code and 'BasePlatform' in code:
                    warnings.append(f"Missing BasePlatform import in {py_file}")
                
            except Exception as e:
                warnings.append(f"Failed to validate {py_file}: {e}")
        
        return warnings
    
    def _setup_template_rules(self) -> Dict[str, Any]:
        """Setup template selection rules."""
        
        return {
            'authentication': {
                'oauth2': 'authentication/oauth2.py.j2',
                'api_key': 'authentication/api_key.py.j2',
                'jwt': 'authentication/jwt.py.j2',
                'basic_auth': 'authentication/basic_auth.py.j2'
            },
            'content_types': {
                'text_post': 'content_types/text_post.py.j2',
                'media_post': 'content_types/media_post.py.j2',
                'thread_post': 'content_types/thread_post.py.j2',
                'story_post': 'content_types/story_post.py.j2'
            },
            'features': {
                'profile_management': 'features/profile_management.py.j2',
                'analytics': 'features/analytics.py.j2',
                'media_upload': 'features/media_upload.py.j2'
            }
        }
    
    def list_available_templates(self) -> Dict[str, List[str]]:
        """List available templates by category."""
        
        templates = self.template_engine.list_available_templates()
        categorized = {
            'core': [],
            'authentication': [],
            'content_types': [],
            'features': [],
            'config': [],
            'tests': [],
            'other': []
        }
        
        for template in templates:
            if template.startswith('authentication/'):
                categorized['authentication'].append(template)
            elif template.startswith('content_types/'):
                categorized['content_types'].append(template)
            elif template.startswith('features/'):
                categorized['features'].append(template)
            elif template.startswith('config/'):
                categorized['config'].append(template)
            elif template.startswith('tests/'):
                categorized['tests'].append(template)
            elif template in ['platform_base.py.j2', '__init__.py.j2']:
                categorized['core'].append(template)
            else:
                categorized['other'].append(template)
        
        return categorized
    
    def get_generator_info(self) -> Dict[str, Any]:
        """Get generator information."""
        
        return {
            'template_dirs': [str(d) for d in self.template_dirs],
            'available_templates': self.list_available_templates(),
            'template_rules': self.template_rules,
            'config': self.config,
            'engine_info': self.template_engine.get_engine_info()
        }