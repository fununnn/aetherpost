"""Unified testing helpers for AetherPost components."""

import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List, Type, Union
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager

from aetherpost.core.common.base_models import Platform, ContentType, OperationResult
from aetherpost.core.common.config_manager import ConfigManager, AetherPostConfig
from aetherpost.core.services.container import Container
from aetherpost.cli.framework.command_factory import AetherPostCommand, ExecutionContext


@dataclass
class MockCredentials:
    """Mock credentials for testing."""
    platform: Platform
    api_key: str = "test_key"
    api_secret: str = "test_secret"
    access_token: str = "test_token"
    access_token_secret: str = "test_token_secret"
    
    def is_valid(self) -> bool:
        return True


@dataclass
class TestConfig:
    """Configuration for test scenarios."""
    app_name: str = "TestApp"
    description: str = "Test application"
    platforms: List[Platform] = None
    ai_enabled: bool = False
    mock_credentials: bool = True
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = [Platform.TWITTER, Platform.REDDIT]


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_operation_result(success: bool = True, 
                              message: str = "Test operation",
                              data: Any = None,
                              errors: List[str] = None) -> OperationResult:
        """Create test operation result."""
        if success:
            return OperationResult.success_result(message, data)
        else:
            return OperationResult.error_result(message, errors or ["Test error"])
    
    @staticmethod
    def create_execution_context(command_name: str = "test-command",
                               user_input: Dict[str, Any] = None,
                               dry_run: bool = False,
                               verbose: bool = False) -> ExecutionContext:
        """Create test execution context."""
        from rich.console import Console
        
        return ExecutionContext(
            command_name=command_name,
            user_input=user_input or {},
            config=TestDataFactory.create_mock_config(),
            console=Console(),
            dry_run=dry_run,
            verbose=verbose
        )
    
    @staticmethod
    def create_mock_config() -> AetherPostConfig:
        """Create mock configuration for testing."""
        return AetherPostConfig(
            app_name="TestApp",
            description="Test application for unit tests",
            author="Test Author"
        )
    
    @staticmethod
    def create_mock_platform_data() -> Dict[str, Any]:
        """Create mock platform-specific data."""
        return {
            "twitter": {
                "followers": 1000,
                "posts": 50,
                "engagement_rate": 0.05
            },
            "reddit": {
                "karma": 500,
                "posts": 25,
                "subreddits": ["r/programming", "r/webdev"]
            }
        }


class MockServiceContainer:
    """Mock service container for testing."""
    
    def __init__(self):
        self.services = {}
        self.instances = {}
    
    def register_mock_service(self, interface: Type, mock_instance: Any):
        """Register a mock service instance."""
        self.services[interface] = mock_instance
        self.instances[interface] = mock_instance
    
    def get_service(self, interface: Type):
        """Get mock service instance."""
        if interface in self.instances:
            return self.instances[interface]
        
        # Create default mock
        mock_service = Mock()
        self.instances[interface] = mock_service
        return mock_service


class CommandTestCase:
    """Base test case for AetherPost commands."""
    
    def __init__(self, command_class: Type[AetherPostCommand]):
        self.command_class = command_class
        self.mock_container = MockServiceContainer()
        self.temp_dirs = []
    
    def create_command(self, config: Optional[TestConfig] = None) -> AetherPostCommand:
        """Create command instance for testing."""
        from aetherpost.cli.framework.command_factory import CommandConfig
        
        test_config = config or TestConfig()
        command_config = CommandConfig(
            requires_config=False,  # Disable for testing
            requires_auth=False,    # Disable for testing
            log_execution=False     # Disable for testing
        )
        
        return self.command_class(command_config)
    
    async def execute_command(self, command: AetherPostCommand,
                            user_input: Dict[str, Any] = None,
                            dry_run: bool = False) -> OperationResult:
        """Execute command with test context."""
        context = TestDataFactory.create_execution_context(
            command_name=command.get_metadata().name,
            user_input=user_input or {},
            dry_run=dry_run
        )
        
        return await command.execute_core_logic(context)
    
    def create_temp_dir(self) -> Path:
        """Create temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up test resources."""
        import shutil
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()


@contextmanager
def mock_config_manager(config: Optional[AetherPostConfig] = None):
    """Context manager for mocking config manager."""
    mock_manager = Mock()
    mock_manager.config = config or TestDataFactory.create_mock_config()
    mock_manager.validate_config.return_value = []
    
    with patch('autopromo.core.common.config_manager.config_manager', mock_manager):
        yield mock_manager


@contextmanager
def mock_platform_service():
    """Context manager for mocking platform service."""
    mock_service = Mock()
    mock_service.get_authenticated_connector = AsyncMock()
    mock_service.validate_platform_config.return_value = OperationResult.success_result("Valid")
    mock_service.get_configured_platforms.return_value = [Platform.TWITTER, Platform.REDDIT]
    
    with patch('autopromo.core.services.platform_service.PlatformService', return_value=mock_service):
        yield mock_service


@contextmanager
def mock_file_system(files: Dict[str, str] = None):
    """Context manager for mocking file system operations."""
    files = files or {}
    
    def mock_read_file(path):
        str_path = str(path)
        for file_path, content in files.items():
            if str_path.endswith(file_path):
                return content
        raise FileNotFoundError(f"Mock file not found: {path}")
    
    def mock_write_file(path, content):
        files[str(path)] = content
    
    with patch('builtins.open') as mock_open:
        # Configure mock based on files dict
        mock_open.return_value.__enter__.return_value.read = mock_read_file
        yield mock_open


class AsyncMock(Mock):
    """Mock for async functions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


def create_mock_connector(platform: Platform) -> Mock:
    """Create mock connector for a platform."""
    mock_connector = Mock()
    mock_connector.authenticate = AsyncMock(return_value=True)
    mock_connector.post = AsyncMock(return_value={"status": "success", "id": "mock_post_123"})
    mock_connector.validate_content = AsyncMock(
        return_value=OperationResult.success_result("Content valid")
    )
    mock_connector.get_capabilities.return_value = ["post", "validate", "schedule"]
    
    return mock_connector


class TestMetrics:
    """Helper for collecting test metrics."""
    
    def __init__(self):
        self.execution_times = []
        self.error_counts = {}
        self.success_counts = {}
    
    def record_execution_time(self, command: str, duration: float):
        """Record command execution time."""
        self.execution_times.append({
            "command": command,
            "duration": duration
        })
    
    def record_error(self, command: str, error_type: str):
        """Record command error."""
        key = f"{command}.{error_type}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def record_success(self, command: str):
        """Record successful command execution."""
        self.success_counts[command] = self.success_counts.get(command, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test metrics summary."""
        total_executions = len(self.execution_times)
        avg_duration = sum(e["duration"] for e in self.execution_times) / total_executions if total_executions else 0
        
        return {
            "total_executions": total_executions,
            "average_duration": avg_duration,
            "total_errors": sum(self.error_counts.values()),
            "total_successes": sum(self.success_counts.values()),
            "error_details": self.error_counts,
            "success_details": self.success_counts
        }


# Convenience functions for common test scenarios
def run_command_test(command_class: Type[AetherPostCommand],
                    user_input: Dict[str, Any] = None,
                    expected_success: bool = True,
                    config: Optional[TestConfig] = None) -> OperationResult:
    """Run a simple command test."""
    
    async def _run_test():
        test_case = CommandTestCase(command_class)
        command = test_case.create_command(config)
        
        try:
            result = await test_case.execute_command(command, user_input)
            assert result.success == expected_success, f"Expected success={expected_success}, got {result.success}"
            return result
        finally:
            test_case.cleanup()
    
    return asyncio.run(_run_test())


def create_integration_test_env() -> Dict[str, Any]:
    """Create environment for integration testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create mock config
    config_dir = temp_dir / ".aetherpost"
    config_dir.mkdir()
    
    # Create mock files
    (config_dir / "config.yaml").write_text("""
app_name: TestApp
description: Integration test application
features:
  auto_posting: true
  content_review: true
""")
    
    (config_dir / "credentials.yaml").write_text("""
twitter:
  api_key: test_key
  api_secret: test_secret
""")
    
    return {
        "temp_dir": temp_dir,
        "config_dir": config_dir,
        "cleanup": lambda: __import__("shutil").rmtree(temp_dir)
    }


# Assertion helpers
def assert_operation_success(result: OperationResult, expected_message: str = None):
    """Assert that operation result is successful."""
    assert result.success, f"Operation failed: {result.message}, errors: {result.errors}"
    if expected_message:
        assert expected_message in result.message, f"Expected '{expected_message}' in '{result.message}'"


def assert_operation_error(result: OperationResult, expected_error: str = None):
    """Assert that operation result is an error."""
    assert not result.success, f"Expected operation to fail, but it succeeded: {result.message}"
    if expected_error:
        assert any(expected_error in error for error in result.errors), \
            f"Expected error '{expected_error}' not found in: {result.errors}"


def assert_has_data(result: OperationResult, expected_keys: List[str] = None):
    """Assert that operation result has data with expected keys."""
    assert result.data is not None, "Expected result to have data"
    
    if expected_keys:
        if isinstance(result.data, dict):
            for key in expected_keys:
                assert key in result.data, f"Expected key '{key}' not found in result data"
        elif isinstance(result.data, list) and result.data and isinstance(result.data[0], dict):
            for key in expected_keys:
                assert key in result.data[0], f"Expected key '{key}' not found in first result item"