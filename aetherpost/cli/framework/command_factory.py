"""Command factory pattern for creating standardized CLI commands."""

import asyncio
import functools
import logging
from typing import Type, Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import click
from rich.console import Console

from aetherpost.core.common.base_models import OperationResult
from aetherpost.core.common.error_handler import handle_errors, error_handler
from aetherpost.core.common.config_manager import config_manager
from aetherpost.cli.common.base_command import BaseCommand, CommandMetadata


logger = logging.getLogger(__name__)


@dataclass
class CommandConfig:
    """Configuration for command behavior and requirements."""
    requires_config: bool = True
    requires_auth: bool = False
    supports_dry_run: bool = True
    supports_platforms: bool = False
    supports_output_format: bool = False
    auto_validate_input: bool = True
    log_execution: bool = True
    cache_results: bool = False


@dataclass
class ExecutionContext:
    """Context passed to command during execution."""
    command_name: str
    user_input: Dict[str, Any]
    config: Any
    console: Console
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False


class AetherPostCommand(ABC):
    """Enhanced base class for AetherPost commands with standard lifecycle."""
    
    def __init__(self, config: CommandConfig):
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
    @abstractmethod
    def get_metadata(self) -> CommandMetadata:
        """Return command metadata."""
        pass
    
    @abstractmethod
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Implement core business logic here."""
        pass
    
    async def pre_execute(self, context: ExecutionContext) -> OperationResult:
        """Standard pre-execution hooks and validation."""
        # Configuration validation
        if self.config.requires_config:
            issues = config_manager.validate_config()
            if issues:
                return OperationResult.error_result(
                    "Configuration validation failed",
                    errors=issues
                )
        
        # Authentication validation
        if self.config.requires_auth:
            configured_platforms = config_manager.config.get_configured_platforms()
            if not configured_platforms:
                return OperationResult.error_result(
                    "Authentication required but no platforms configured"
                )
        
        # Platform-specific validation
        if self.config.supports_platforms:
            platforms = context.user_input.get('platforms', [])
            if platforms:
                for platform in platforms:
                    creds = config_manager.config.get_platform_credentials(platform)
                    if not creds or not creds.is_valid():
                        return OperationResult.error_result(
                            f"Invalid credentials for platform: {platform}"
                        )
        
        return OperationResult.success_result("Pre-execution validation passed")
    
    async def post_execute(self, context: ExecutionContext, result: OperationResult) -> None:
        """Standard post-execution hooks."""
        if self.config.log_execution:
            self._log_execution(context, result)
        
        if self.config.cache_results and result.success:
            await self._cache_result(context, result)
    
    def _log_execution(self, context: ExecutionContext, result: OperationResult) -> None:
        """Log command execution for audit trail."""
        self.logger.info(
            f"Command executed: {context.command_name}",
            extra={
                'command': context.command_name,
                'success': result.success,
                'dry_run': context.dry_run,
                'execution_time': getattr(result, 'execution_time', 'unknown')
            }
        )
    
    async def _cache_result(self, context: ExecutionContext, result: OperationResult) -> None:
        """Cache successful results for performance."""
        # Implementation would depend on caching strategy
        pass
    
    def handle_dry_run(self, context: ExecutionContext, action_description: str) -> bool:
        """Standard dry-run handling."""
        if context.dry_run:
            self.console.print(f"[yellow]DRY RUN:[/yellow] Would {action_description}")
            return True
        return False


class CommandFactory:
    """Factory for creating standardized CLI commands."""
    
    def __init__(self):
        self.middleware_stack: List[Callable] = []
        self.global_options: Dict[str, click.Option] = {}
        
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the execution stack."""
        self.middleware_stack.append(middleware)
    
    def add_global_option(self, name: str, option: click.Option) -> None:
        """Add global option available to all commands."""
        self.global_options[name] = option
    
    def create_command(self, command_class: Type[AetherPostCommand], 
                      config: CommandConfig) -> click.Command:
        """Create a Click command from an AetherPostCommand class."""
        
        def command_wrapper(**kwargs):
            """Wrapper function that executes the command with middleware."""
            return asyncio.run(self._execute_with_middleware(command_class, config, kwargs))
        
        # Create command instance to get metadata
        temp_instance = command_class(config)
        metadata = temp_instance.get_metadata()
        
        # Create Click command
        cmd = click.command(name=metadata.name, help=metadata.description)(command_wrapper)
        
        # Add command-specific options
        if hasattr(temp_instance, 'get_options'):
            for option in reversed(temp_instance.get_options()):
                cmd = option.to_click_option()(cmd)
        
        # Add global options based on config
        if config.supports_dry_run:
            cmd = click.option('--dry-run', is_flag=True, help="Preview without executing")(cmd)
        
        if config.supports_platforms:
            cmd = click.option('--platforms', '-p', multiple=True, 
                             help="Target platforms (comma-separated)")(cmd)
        
        if config.supports_output_format:
            cmd = click.option('--format', type=click.Choice(['table', 'json', 'yaml']),
                             default='table', help="Output format")(cmd)
        
        # Add common options
        cmd = click.option('--verbose', '-v', is_flag=True, help="Verbose output")(cmd)
        cmd = click.option('--quiet', '-q', is_flag=True, help="Suppress output")(cmd)
        
        return cmd
    
    async def _execute_with_middleware(self, command_class: Type[AetherPostCommand],
                                     config: CommandConfig, kwargs: Dict[str, Any]) -> None:
        """Execute command with middleware stack."""
        command = command_class(config)
        console = Console()
        
        # Create execution context
        context = ExecutionContext(
            command_name=command.get_metadata().name,
            user_input=kwargs,
            config=config_manager.config,
            console=console,
            dry_run=kwargs.get('dry_run', False),
            verbose=kwargs.get('verbose', False),
            quiet=kwargs.get('quiet', False)
        )
        
        try:
            # Apply middleware stack
            for middleware in self.middleware_stack:
                result = await middleware(context)
                if not result.success:
                    self._display_error(console, result)
                    return
            
            # Pre-execution validation
            pre_result = await command.pre_execute(context)
            if not pre_result.success:
                self._display_error(console, pre_result)
                return
            
            # Execute core logic
            with self._execution_timer() as timer:
                result = await command.execute_core_logic(context)
                result.metadata = result.metadata or {}
                result.metadata['execution_time'] = timer.elapsed
            
            # Post-execution hooks
            await command.post_execute(context, result)
            
            # Display results
            self._display_result(console, context, result)
            
        except Exception as e:
            error = error_handler.handle_exception(e)
            error_result = OperationResult.error_result(error.message, errors=[str(e)])
            self._display_error(console, error_result)
    
    def _display_result(self, console: Console, context: ExecutionContext, 
                       result: OperationResult) -> None:
        """Display command execution results."""
        if context.quiet:
            return
        
        if result.success:
            if not context.quiet:
                console.print(f"✅ [green]{result.message}[/green]")
                
                if context.verbose and result.data:
                    console.print("\n[bold]Details:[/bold]")
                    console.print(result.data)
        else:
            self._display_error(console, result)
    
    def _display_error(self, console: Console, result: OperationResult) -> None:
        """Display error results."""
        console.print(f"❌ [red]{result.message}[/red]")
        
        if result.errors:
            for error in result.errors:
                console.print(f"  • [red]{error}[/red]")
        
        if result.warnings:
            for warning in result.warnings:
                console.print(f"  ⚠️ [yellow]{warning}[/yellow]")
    
    def _execution_timer(self):
        """Simple execution timer context manager."""
        import time
        
        class Timer:
            def __init__(self):
                self.start_time = None
                self.elapsed = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, *args):
                self.elapsed = time.time() - self.start_time
        
        return Timer()


# Middleware functions
async def auth_middleware(context: ExecutionContext) -> OperationResult:
    """Authentication middleware."""
    if context.config.requires_auth:
        # Implementation would check authentication status
        pass
    return OperationResult.success_result("Authentication middleware passed")


async def validation_middleware(context: ExecutionContext) -> OperationResult:
    """Input validation middleware."""
    if context.config.auto_validate_input:
        # Implementation would validate user input
        pass
    return OperationResult.success_result("Validation middleware passed")


async def logging_middleware(context: ExecutionContext) -> OperationResult:
    """Logging middleware."""
    logger.info(f"Executing command: {context.command_name}")
    return OperationResult.success_result("Logging middleware passed")


# Global factory instance
command_factory = CommandFactory()

# Configure default middleware
command_factory.add_middleware(logging_middleware)
command_factory.add_middleware(validation_middleware)
command_factory.add_middleware(auth_middleware)