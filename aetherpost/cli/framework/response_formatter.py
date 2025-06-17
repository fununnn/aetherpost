"""Unified response formatting for consistent CLI output."""

import json
import yaml
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.syntax import Syntax

from aetherpost.core.common.base_models import OperationResult


class OutputFormat(Enum):
    """Supported output formats."""
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    PANEL = "panel"


@dataclass
class FormatterConfig:
    """Configuration for response formatting."""
    format_type: OutputFormat = OutputFormat.TABLE
    show_headers: bool = True
    show_metadata: bool = False
    color_enabled: bool = True
    compact_mode: bool = False
    max_width: Optional[int] = None


class ResponseFormatter:
    """Unified formatter for CLI responses."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def format_result(self, result: OperationResult, config: FormatterConfig) -> None:
        """Format and display operation result."""
        if result.success:
            self._format_success(result, config)
        else:
            self._format_error(result, config)
    
    def _format_success(self, result: OperationResult, config: FormatterConfig) -> None:
        """Format successful result."""
        # Display main message
        if not config.compact_mode:
            self.console.print(f"✅ [green]{result.message}[/green]")
        
        # Display data based on format
        if result.data:
            self._format_data(result.data, config)
        
        # Display metadata if requested
        if config.show_metadata and result.metadata:
            self._format_metadata(result.metadata, config)
    
    def _format_error(self, result: OperationResult, config: FormatterConfig) -> None:
        """Format error result."""
        self.console.print(f"❌ [red]{result.message}[/red]")
        
        # Display errors
        if result.errors:
            for error in result.errors:
                self.console.print(f"  • [red]{error}[/red]")
        
        # Display warnings
        if result.warnings:
            for warning in result.warnings:
                self.console.print(f"  ⚠️ [yellow]{warning}[/yellow]")
    
    def _format_data(self, data: Any, config: FormatterConfig) -> None:
        """Format data based on configuration."""
        if config.format_type == OutputFormat.TABLE:
            self._format_as_table(data, config)
        elif config.format_type == OutputFormat.JSON:
            self._format_as_json(data, config)
        elif config.format_type == OutputFormat.YAML:
            self._format_as_yaml(data, config)
        elif config.format_type == OutputFormat.PANEL:
            self._format_as_panel(data, config)
        else:
            self._format_as_text(data, config)
    
    def _format_as_table(self, data: Any, config: FormatterConfig) -> None:
        """Format data as a table."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries -> table
            table = Table(show_header=config.show_headers)
            
            # Add columns from first item
            headers = list(data[0].keys())
            for header in headers:
                table.add_column(header.replace('_', ' ').title())
            
            # Add rows
            for item in data:
                row = [str(item.get(header, '')) for header in headers]
                table.add_row(*row)
            
            self.console.print(table)
            
        elif isinstance(data, dict):
            # Dictionary -> key-value table
            table = Table(show_header=config.show_headers)
            table.add_column("Property")
            table.add_column("Value")
            
            for key, value in data.items():
                table.add_row(
                    key.replace('_', ' ').title(),
                    str(value)
                )
            
            self.console.print(table)
        else:
            # Fallback to text
            self._format_as_text(data, config)
    
    def _format_as_json(self, data: Any, config: FormatterConfig) -> None:
        """Format data as JSON."""
        json_str = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        
        if config.color_enabled:
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        else:
            self.console.print(json_str)
    
    def _format_as_yaml(self, data: Any, config: FormatterConfig) -> None:
        """Format data as YAML."""
        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        
        if config.color_enabled:
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        else:
            self.console.print(yaml_str)
    
    def _format_as_panel(self, data: Any, config: FormatterConfig) -> None:
        """Format data as a panel."""
        if isinstance(data, dict):
            content = ""
            for key, value in data.items():
                content += f"[bold]{key.replace('_', ' ').title()}:[/bold] {value}\\n"
            
            panel = Panel(
                content.rstrip(),
                title="Result Details",
                border_style="blue"
            )
            self.console.print(panel)
        else:
            panel = Panel(
                str(data),
                title="Result",
                border_style="blue"
            )
            self.console.print(panel)
    
    def _format_as_text(self, data: Any, config: FormatterConfig) -> None:
        """Format data as plain text."""
        if isinstance(data, (dict, list)):
            self.console.print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        else:
            self.console.print(str(data))
    
    def _format_metadata(self, metadata: Dict[str, Any], config: FormatterConfig) -> None:
        """Format metadata information."""
        if not config.compact_mode:
            self.console.print("\\n[dim]Metadata:[/dim]")
            for key, value in metadata.items():
                self.console.print(f"[dim]  {key}: {value}[/dim]")


class TableBuilder:
    """Helper class for building complex tables."""
    
    def __init__(self, title: Optional[str] = None):
        self.table = Table(title=title, show_header=True)
        self.columns_added = False
    
    def add_columns(self, *columns: str) -> 'TableBuilder':
        """Add columns to the table."""
        for column in columns:
            self.table.add_column(column)
        self.columns_added = True
        return self
    
    def add_row(self, *values: Any) -> 'TableBuilder':
        """Add a row to the table."""
        if not self.columns_added:
            raise ValueError("Must add columns before adding rows")
        
        str_values = [str(value) for value in values]
        self.table.add_row(*str_values)
        return self
    
    def add_rows(self, rows: List[List[Any]]) -> 'TableBuilder':
        """Add multiple rows to the table."""
        for row in rows:
            self.add_row(*row)
        return self
    
    def build(self) -> Table:
        """Build and return the table."""
        return self.table


class ProgressFormatter:
    """Formatter for progress-based operations."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def show_progress(self, items: List[Any], operation_name: str,
                     processor: callable) -> List[Any]:
        """Show progress while processing items."""
        results = []
        
        with Progress(console=self.console) as progress:
            task = progress.add_task(f"[cyan]{operation_name}...", total=len(items))
            
            for item in items:
                result = processor(item)
                results.append(result)
                progress.advance(task)
        
        return results


class StatusFormatter:
    """Formatter for status displays."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def show_status_grid(self, status_items: Dict[str, Dict[str, Any]],
                        title: str = "Status Overview") -> None:
        """Display status information in a grid format."""
        table = Table(title=title, show_header=True)
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Details")
        
        for component, info in status_items.items():
            status = info.get('status', 'unknown')
            details = info.get('details', '')
            
            # Color-code status
            if status.lower() in ['ok', 'success', 'active', 'enabled']:
                status_display = f"[green]{status}[/green]"
            elif status.lower() in ['error', 'failed', 'disabled']:
                status_display = f"[red]{status}[/red]"
            elif status.lower() in ['warning', 'partial']:
                status_display = f"[yellow]{status}[/yellow]"
            else:
                status_display = status
            
            table.add_row(component, status_display, str(details))
        
        self.console.print(table)


# Convenience functions for common formatting patterns
def format_simple_result(result: OperationResult, 
                        format_type: OutputFormat = OutputFormat.TABLE) -> None:
    """Format result with default configuration."""
    formatter = ResponseFormatter()
    config = FormatterConfig(format_type=format_type)
    formatter.format_result(result, config)


def format_data_as_table(data: List[Dict[str, Any]], title: Optional[str] = None) -> None:
    """Quick table formatting for list of dictionaries."""
    console = Console()
    
    if not data:
        console.print("[dim]No data to display[/dim]")
        return
    
    builder = TableBuilder(title)
    builder.add_columns(*data[0].keys())
    
    for item in data:
        builder.add_row(*item.values())
    
    console.print(builder.build())


def format_key_value_pairs(data: Dict[str, Any], title: str = "Information") -> None:
    """Quick formatting for key-value pairs."""
    console = Console()
    
    table = Table(title=title, show_header=True)
    table.add_column("Property")
    table.add_column("Value")
    
    for key, value in data.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)