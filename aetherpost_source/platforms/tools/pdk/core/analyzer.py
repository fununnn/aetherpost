"""Platform specification analyzer."""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


@dataclass
class AuthenticationSpec:
    """Authentication specification."""
    
    type: str  # oauth2, api_key, jwt, basic_auth
    flows: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    requires_secret: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthenticationSpec':
        """Create from dictionary."""
        return cls(
            type=data['type'],
            flows=data.get('flows', []),
            scopes=data.get('scopes', []),
            endpoints=data.get('endpoints', {}),
            requires_secret=data.get('requires_secret', False)
        )


@dataclass
class ContentTypeSpec:
    """Content type specification."""
    
    name: str
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    max_media: Optional[int] = None
    supported_formats: List[str] = field(default_factory=list)
    max_file_size: Optional[str] = None
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'ContentTypeSpec':
        """Create from dictionary."""
        return cls(
            name=name,
            max_length=data.get('max_length'),
            min_length=data.get('min_length'),
            max_media=data.get('max_media'),
            supported_formats=data.get('supported_formats', []),
            max_file_size=data.get('max_file_size')
        )


@dataclass
class APIEndpointSpec:
    """API endpoint specification."""
    
    path: str
    method: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    response_format: Optional[Dict[str, Any]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, endpoint_def: Union[str, Dict[str, Any]]) -> 'APIEndpointSpec':
        """Create from dictionary or string."""
        if isinstance(endpoint_def, str):
            # Parse "METHOD /path" format
            parts = endpoint_def.split(' ', 1)
            method = parts[0] if len(parts) > 1 else 'GET'
            path = parts[1] if len(parts) > 1 else endpoint_def
            return cls(path=path, method=method)
        else:
            return cls(
                path=endpoint_def['path'],
                method=endpoint_def.get('method', 'GET'),
                description=endpoint_def.get('description'),
                parameters=endpoint_def.get('parameters', {}),
                request_body=endpoint_def.get('request_body'),
                response_format=endpoint_def.get('response_format'),
                rate_limit=endpoint_def.get('rate_limit')
            )


@dataclass
class FeatureSet:
    """Platform feature set."""
    
    content_posting: bool = True
    profile_management: bool = False
    media_upload: bool = False
    analytics: bool = False
    direct_messaging: bool = False
    live_streaming: bool = False
    stories: bool = False
    threads: bool = False
    scheduling: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureSet':
        """Create from dictionary."""
        return cls(
            content_posting=data.get('content_posting', True),
            profile_management=data.get('profile_management', False),
            media_upload=data.get('media_upload', False),
            analytics=data.get('analytics', False),
            direct_messaging=data.get('direct_messaging', False),
            live_streaming=data.get('live_streaming', False),
            stories=data.get('stories', False),
            threads=data.get('threads', False),
            scheduling=data.get('scheduling', False)
        )
    
    @property
    def enabled_features(self) -> List[str]:
        """Get list of enabled features."""
        return [
            feature for feature, enabled in self.__dict__.items()
            if enabled
        ]


@dataclass
class RateLimitSpec:
    """Rate limiting specification."""
    
    global_limits: Dict[str, int] = field(default_factory=dict)
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateLimitSpec':
        """Create from dictionary."""
        return cls(
            global_limits=data.get('global', {}),
            endpoint_limits=data.get('endpoints', {})
        )


@dataclass
class ErrorHandlingSpec:
    """Error handling specification."""
    
    standard_errors: Dict[int, str] = field(default_factory=dict)
    custom_errors: Dict[str, str] = field(default_factory=dict)
    retry_strategies: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorHandlingSpec':
        """Create from dictionary."""
        return cls(
            standard_errors=data.get('standard_errors', {}),
            custom_errors=data.get('custom_errors', {}),
            retry_strategies=data.get('retry_strategies', {})
        )


@dataclass
class PlatformSpec:
    """Complete platform specification."""
    
    name: str
    display_name: str
    description: str
    api_base_url: str
    api_version: str
    documentation_url: Optional[str] = None
    
    authentication: Optional[AuthenticationSpec] = None
    features: Optional[FeatureSet] = None
    content_types: Dict[str, ContentTypeSpec] = field(default_factory=dict)
    api_endpoints: Dict[str, APIEndpointSpec] = field(default_factory=dict)
    rate_limits: Optional[RateLimitSpec] = None
    error_handling: Optional[ErrorHandlingSpec] = None
    
    # Generation configuration
    class_name: Optional[str] = None
    module_name: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if not self.class_name:
            self.class_name = f"{self.name.title()}Platform"
        if not self.module_name:
            self.module_name = f"{self.name}_platform"
    
    @property
    def character_limit(self) -> int:
        """Get character limit for text posts."""
        text_post = self.content_types.get('text_post')
        if text_post and text_post.max_length:
            return text_post.max_length
        return 280  # Default fallback
    
    @property
    def supported_content_types(self) -> List[str]:
        """Get supported content type names."""
        return list(self.content_types.keys())
    
    @property
    def supported_media_types(self) -> List[str]:
        """Get all supported media MIME types."""
        media_types = set()
        for content_type in self.content_types.values():
            media_types.update(content_type.supported_formats)
        return list(media_types)
    
    def get_endpoint_by_category(self, category: str) -> Dict[str, APIEndpointSpec]:
        """Get endpoints by category (e.g., 'posts', 'profile', 'auth')."""
        return {
            name: endpoint for name, endpoint in self.api_endpoints.items()
            if name.startswith(category)
        }


class SpecificationAnalyzer:
    """Analyzer for platform specification files."""
    
    def __init__(self):
        self.schema_validators = {}
        self._setup_validation_schemas()
    
    def analyze_specification(self, spec_file: Path) -> PlatformSpec:
        """Analyze a platform specification file."""
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                raw_spec = yaml.safe_load(f)
            
            # Validate basic structure
            self._validate_basic_structure(raw_spec)
            
            # Extract platform information
            platform_info = raw_spec['platform']
            api_info = raw_spec['api']
            
            # Build specification object
            spec = PlatformSpec(
                name=platform_info['name'],
                display_name=platform_info['display_name'],
                description=platform_info.get('description', ''),
                api_base_url=api_info['base_url'],
                api_version=api_info.get('version', 'v1'),
                documentation_url=api_info.get('documentation')
            )
            
            # Parse authentication
            if 'authentication' in raw_spec:
                spec.authentication = AuthenticationSpec.from_dict(raw_spec['authentication'])
            
            # Parse features
            if 'features' in raw_spec:
                spec.features = FeatureSet.from_dict(raw_spec['features'])
            else:
                spec.features = FeatureSet()  # Default features
            
            # Parse content types
            if 'content_types' in raw_spec:
                spec.content_types = self._parse_content_types(raw_spec['content_types'])
            
            # Parse API endpoints
            if 'api_endpoints' in raw_spec:
                spec.api_endpoints = self._parse_api_endpoints(raw_spec['api_endpoints'])
            
            # Parse rate limits
            if 'rate_limits' in raw_spec:
                spec.rate_limits = RateLimitSpec.from_dict(raw_spec['rate_limits'])
            
            # Parse error handling
            if 'error_handling' in raw_spec:
                spec.error_handling = ErrorHandlingSpec.from_dict(raw_spec['error_handling'])
            
            logger.info(f"Successfully analyzed specification for {spec.display_name}")
            return spec
            
        except Exception as e:
            logger.error(f"Failed to analyze specification {spec_file}: {e}")
            raise ValueError(f"Specification analysis failed: {e}") from e
    
    def validate_specification(self, spec_file: Path) -> Dict[str, Any]:
        """Validate a specification file without full parsing."""
        
        errors = []
        warnings = []
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                raw_spec = yaml.safe_load(f)
            
            # Check required sections
            required_sections = ['platform', 'api']
            for section in required_sections:
                if section not in raw_spec:
                    errors.append(f"Missing required section: {section}")
            
            # Validate platform section
            if 'platform' in raw_spec:
                platform_errors = self._validate_platform_section(raw_spec['platform'])
                errors.extend(platform_errors)
            
            # Validate API section
            if 'api' in raw_spec:
                api_errors = self._validate_api_section(raw_spec['api'])
                errors.extend(api_errors)
            
            # Validate authentication section
            if 'authentication' in raw_spec:
                auth_errors = self._validate_authentication_section(raw_spec['authentication'])
                errors.extend(auth_errors)
            
            # Validate content types
            if 'content_types' in raw_spec:
                content_errors = self._validate_content_types_section(raw_spec['content_types'])
                errors.extend(content_errors)
            
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'file': str(spec_file)
        }
    
    def _validate_basic_structure(self, raw_spec: Dict[str, Any]):
        """Validate basic specification structure."""
        
        required_fields = ['platform', 'api']
        for field in required_fields:
            if field not in raw_spec:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate platform section
        platform = raw_spec['platform']
        required_platform_fields = ['name', 'display_name']
        for field in required_platform_fields:
            if field not in platform:
                raise ValueError(f"Missing required platform field: {field}")
        
        # Validate API section
        api = raw_spec['api']
        if 'base_url' not in api:
            raise ValueError("Missing required API field: base_url")
    
    def _parse_content_types(self, content_types_data: Dict[str, Any]) -> Dict[str, ContentTypeSpec]:
        """Parse content types specification."""
        
        content_types = {}
        
        # Parse supported types
        supported = content_types_data.get('supported', [])
        for content_type in supported:
            content_types[content_type] = ContentTypeSpec(name=content_type)
        
        # Parse limits
        limits = content_types_data.get('limits', {})
        for content_type, limit_data in limits.items():
            if content_type in content_types:
                content_types[content_type] = ContentTypeSpec.from_dict(content_type, limit_data)
            else:
                content_types[content_type] = ContentTypeSpec.from_dict(content_type, limit_data)
        
        return content_types
    
    def _parse_api_endpoints(self, endpoints_data: Dict[str, Any]) -> Dict[str, APIEndpointSpec]:
        """Parse API endpoints specification."""
        
        endpoints = {}
        
        def parse_endpoint_group(group_name: str, group_data: Dict[str, Any]):
            for endpoint_name, endpoint_def in group_data.items():
                full_name = f"{group_name}_{endpoint_name}" if group_name else endpoint_name
                endpoints[full_name] = APIEndpointSpec.from_dict(endpoint_def)
        
        # Parse grouped endpoints
        for section_name, section_data in endpoints_data.items():
            if isinstance(section_data, dict):
                parse_endpoint_group(section_name, section_data)
        
        return endpoints
    
    def _validate_platform_section(self, platform_data: Dict[str, Any]) -> List[str]:
        """Validate platform section."""
        errors = []
        
        required_fields = ['name', 'display_name']
        for field in required_fields:
            if field not in platform_data:
                errors.append(f"Missing platform field: {field}")
        
        # Validate name format
        if 'name' in platform_data:
            name = platform_data['name']
            if not isinstance(name, str) or not name.replace('_', '').isalnum():
                errors.append("Platform name must be alphanumeric with underscores")
        
        return errors
    
    def _validate_api_section(self, api_data: Dict[str, Any]) -> List[str]:
        """Validate API section."""
        errors = []
        
        if 'base_url' not in api_data:
            errors.append("Missing API base_url")
        elif not api_data['base_url'].startswith(('http://', 'https://')):
            errors.append("API base_url must be a valid HTTP(S) URL")
        
        return errors
    
    def _validate_authentication_section(self, auth_data: Dict[str, Any]) -> List[str]:
        """Validate authentication section."""
        errors = []
        
        if 'type' not in auth_data:
            errors.append("Missing authentication type")
        else:
            auth_type = auth_data['type']
            valid_types = ['oauth2', 'api_key', 'jwt', 'basic_auth']
            if auth_type not in valid_types:
                errors.append(f"Invalid authentication type: {auth_type}. Must be one of: {valid_types}")
        
        return errors
    
    def _validate_content_types_section(self, content_types_data: Dict[str, Any]) -> List[str]:
        """Validate content types section."""
        errors = []
        
        if 'supported' not in content_types_data:
            errors.append("Missing content_types.supported")
        elif not isinstance(content_types_data['supported'], list):
            errors.append("content_types.supported must be a list")
        
        return errors
    
    def _setup_validation_schemas(self):
        """Setup validation schemas for different sections."""
        # This could be expanded with JSON Schema validation
        pass
    
    def get_generation_context(self, spec: PlatformSpec) -> Dict[str, Any]:
        """Get context for template generation."""
        
        return {
            'spec': spec,
            'class_name': spec.class_name,
            'module_name': spec.module_name,
            'platform_name': spec.name,
            'display_name': spec.display_name,
            'base_url': spec.api_base_url,
            'api_version': spec.api_version,
            'character_limit': spec.character_limit,
            'supported_content_types': spec.supported_content_types,
            'supported_media_types': spec.supported_media_types,
            'features': spec.features,
            'authentication': spec.authentication,
            'api_endpoints': spec.api_endpoints,
            'rate_limits': spec.rate_limits,
            'error_handling': spec.error_handling
        }