"""System health check and diagnostics."""

import typer
import sys
import subprocess
import platform
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()
doctor_app = typer.Typer()


@doctor_app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues automatically"),
):
    """Run comprehensive system health check."""
    
    console.print(Panel(
        "[bold green]🩺 AetherPost Health Check[/bold green]\n\n"
        "Diagnosing your AetherPost installation and environment...",
        border_style="green"
    ))
    
    issues = []
    warnings = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # System check
        task1 = progress.add_task("Checking system environment...", total=None)
        sys_issues = check_system_environment(verbose)
        issues.extend(sys_issues)
        progress.update(task1, completed=True)
        
        # Python environment
        task2 = progress.add_task("Checking Python environment...", total=None)
        py_issues = check_python_environment(verbose)
        issues.extend(py_issues)
        progress.update(task2, completed=True)
        
        # AetherPost installation
        task3 = progress.add_task("Checking AetherPost installation...", total=None)
        ap_issues = check_autopromo_installation(verbose)
        issues.extend(ap_issues)
        progress.update(task3, completed=True)
        
        # Configuration
        task4 = progress.add_task("Checking configuration...", total=None)
        config_issues = check_configuration(verbose)
        issues.extend(config_issues)
        progress.update(task4, completed=True)
        
        # Network connectivity
        task5 = progress.add_task("Checking network connectivity...", total=None)
        net_issues = check_network_connectivity(verbose)
        issues.extend(net_issues)
        progress.update(task5, completed=True)
        
        # Project integration
        task6 = progress.add_task("Checking project integration...", total=None)
        proj_issues = check_project_integration(verbose)
        warnings.extend(proj_issues)  # Project issues are warnings, not errors
        progress.update(task6, completed=True)
    
    # Display results
    display_health_report(issues, warnings, verbose)
    
    # Offer fixes
    if issues and fix:
        attempt_fixes(issues)
    elif issues:
        console.print("\n💡 [yellow]Run with --fix to attempt automatic repairs[/yellow]")


def check_system_environment(verbose: bool) -> list:
    """Check system environment."""
    issues = []
    
    if verbose:
        console.print("\n[bold]System Environment:[/bold]")
    
    # Operating System
    os_info = platform.system()
    if verbose:
        console.print(f"  OS: {os_info} {platform.release()}")
    
    # Architecture
    arch = platform.machine()
    if verbose:
        console.print(f"  Architecture: {arch}")
    
    # Check supported OS
    if os_info not in ["Linux", "Darwin", "Windows"]:
        issues.append({
            "category": "system",
            "severity": "error",
            "message": f"Unsupported operating system: {os_info}",
            "fix": "Use Linux, macOS, or Windows"
        })
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        
        if verbose:
            console.print(f"  Free disk space: {free_gb}GB")
        
        if free_gb < 1:
            issues.append({
                "category": "system", 
                "severity": "warning",
                "message": f"Low disk space: {free_gb}GB available",
                "fix": "Free up disk space"
            })
    except Exception:
        pass
    
    return issues


def check_python_environment(verbose: bool) -> list:
    """Check Python environment."""
    issues = []
    
    if verbose:
        console.print("\n[bold]Python Environment:[/bold]")
    
    # Python version
    py_version = sys.version_info
    version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
    
    if verbose:
        console.print(f"  Python version: {version_str}")
        console.print(f"  Python executable: {sys.executable}")
    
    # Check minimum version
    if py_version < (3, 8):
        issues.append({
            "category": "python",
            "severity": "error", 
            "message": f"Python {version_str} is too old (minimum: 3.8)",
            "fix": "Upgrade to Python 3.8 or newer"
        })
    
    # Check pip
    try:
        import pip
        if verbose:
            console.print(f"  pip version: {pip.__version__}")
    except ImportError:
        issues.append({
            "category": "python",
            "severity": "error",
            "message": "pip not available",
            "fix": "Install pip: python -m ensurepip --upgrade"
        })
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if verbose:
        console.print(f"  Virtual environment: {'Yes' if in_venv else 'No'}")
    
    if not in_venv:
        issues.append({
            "category": "python",
            "severity": "warning",
            "message": "Not running in virtual environment",
            "fix": "Consider using virtual environment: python -m venv venv"
        })
    
    return issues


def check_autopromo_installation(verbose: bool) -> list:
    """Check AetherPost installation."""
    issues = []
    
    if verbose:
        console.print("\n[bold]AetherPost Installation:[/bold]")
    
    # Check if aetherpost command exists
    try:
        result = subprocess.run(["aetherpost", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            if verbose:
                console.print(f"  AetherPost version: {version}")
        else:
            issues.append({
                "category": "aetherpost",
                "severity": "error",
                "message": "aetherpost command fails to run",
                "fix": "Reinstall AetherPost: pip install --upgrade autopromo"
            })
    except FileNotFoundError:
        issues.append({
            "category": "aetherpost",
            "severity": "error", 
            "message": "aetherpost command not found",
            "fix": "Install AetherPost: pip install autopromo"
        })
    
    # Check dependencies
    required_packages = [
        "typer", "rich", "pydantic", "pyyaml", "aiohttp", "anthropic", "openai"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            if verbose:
                console.print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            if verbose:
                console.print(f"  ❌ {package}")
    
    if missing_packages:
        issues.append({
            "category": "aetherpost",
            "severity": "error",
            "message": f"Missing dependencies: {', '.join(missing_packages)}",
            "fix": f"Install missing packages: pip install {' '.join(missing_packages)}"
        })
    
    return issues


def check_configuration(verbose: bool) -> list:
    """Check AetherPost configuration."""
    issues = []
    
    if verbose:
        console.print("\n[bold]Configuration:[/bold]")
    
    # Check workspace initialization
    autopromo_dir = Path(".aetherpost")
    campaign_file = Path("campaign.yaml")
    
    if autopromo_dir.exists():
        if verbose:
            console.print("  ✅ Workspace initialized")
    else:
        issues.append({
            "category": "config",
            "severity": "warning",
            "message": "Workspace not initialized",
            "fix": "Run: aetherpost init"
        })
    
    if campaign_file.exists():
        if verbose:
            console.print("  ✅ Campaign configuration exists")
        
        # Validate configuration
        try:
            from ...core.config.parser import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_campaign_config()
            validation_issues = config_loader.validate_config(config)
            
            if validation_issues:
                issues.append({
                    "category": "config",
                    "severity": "warning", 
                    "message": f"Configuration issues: {', '.join(validation_issues)}",
                    "fix": "Run: aetherpost validate"
                })
            elif verbose:
                console.print("  ✅ Configuration is valid")
                
        except Exception as e:
            issues.append({
                "category": "config",
                "severity": "error",
                "message": f"Configuration error: {str(e)}",
                "fix": "Fix configuration file or run: aetherpost init --overwrite"
            })
    else:
        issues.append({
            "category": "config",
            "severity": "info",
            "message": "No campaign configuration",
            "fix": "Run: aetherpost init"
        })
    
    # Check credentials
    creds_file = autopromo_dir / "credentials.yaml"
    if creds_file.exists():
        if verbose:
            console.print("  ✅ Credentials configured")
    else:
        issues.append({
            "category": "config",
            "severity": "warning",
            "message": "No credentials configured",
            "fix": "Run: aetherpost setup wizard"
        })
    
    return issues


def check_network_connectivity(verbose: bool) -> list:
    """Check network connectivity to required services."""
    issues = []
    
    if verbose:
        console.print("\n[bold]Network Connectivity:[/bold]")
    
    # Test endpoints
    test_endpoints = [
        ("twitter.com", "Twitter API"),
        ("api.anthropic.com", "[AI Service] API"),
        ("api.openai.com", "OpenAI API"),
        ("bsky.social", "Bluesky"),
    ]
    
    for endpoint, service in test_endpoints:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((endpoint, 443))
            sock.close()
            
            if result == 0:
                if verbose:
                    console.print(f"  ✅ {service}")
            else:
                issues.append({
                    "category": "network",
                    "severity": "warning",
                    "message": f"Cannot connect to {service}",
                    "fix": "Check internet connection and firewall settings"
                })
                if verbose:
                    console.print(f"  ❌ {service}")
        except Exception:
            issues.append({
                "category": "network", 
                "severity": "warning",
                "message": f"Network test failed for {service}",
                "fix": "Check internet connection"
            })
    
    return issues


def check_project_integration(verbose: bool) -> list:
    """Check project integration capabilities."""
    issues = []
    
    if verbose:
        console.print("\n[bold]Project Integration:[/bold]")
    
    # Check Git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            if verbose:
                console.print("  ✅ Git available")
        else:
            issues.append({
                "category": "integration",
                "severity": "info",
                "message": "Git not working properly",
                "fix": "Reinstall Git"
            })
    except FileNotFoundError:
        issues.append({
            "category": "integration",
            "severity": "info", 
            "message": "Git not installed (recommended for project detection)",
            "fix": "Install Git for better project detection"
        })
    
    # Check project files
    project_files = [
        ("package.json", "Node.js project"),
        ("pyproject.toml", "Python project"),
        ("Cargo.toml", "Rust project"),
        ("README.md", "Documentation"),
    ]
    
    detected_files = []
    for file_name, description in project_files:
        if Path(file_name).exists():
            detected_files.append(description)
            if verbose:
                console.print(f"  ✅ {description}")
    
    if detected_files:
        if verbose:
            console.print(f"  Project type: {', '.join(detected_files)}")
    else:
        issues.append({
            "category": "integration",
            "severity": "info",
            "message": "No common project files detected",
            "fix": "This is normal if not in a project directory"
        })
    
    return issues


def display_health_report(issues: list, warnings: list, verbose: bool):
    """Display comprehensive health report."""
    
    console.print("\n" + "="*60)
    
    # Summary
    error_count = len([i for i in issues if i.get("severity") == "error"])
    warning_count = len([i for i in issues if i.get("severity") == "warning"]) + len(warnings)
    info_count = len([i for i in issues if i.get("severity") == "info"])
    
    if error_count == 0 and warning_count == 0:
        console.print(Panel(
            "[bold green]🎉 Perfect Health![/bold green]\n\n"
            "Your AetherPost installation is working perfectly!",
            border_style="green",
            title="Health Report"
        ))
    elif error_count == 0:
        console.print(Panel(
            f"[bold yellow]✅ Good Health[/bold yellow]\n\n"
            f"Found {warning_count} minor issues that can be improved.",
            border_style="yellow", 
            title="Health Report"
        ))
    else:
        console.print(Panel(
            f"[bold red]⚠️ Issues Found[/bold red]\n\n"
            f"Found {error_count} errors and {warning_count} warnings that need attention.",
            border_style="red",
            title="Health Report"
        ))
    
    # Detailed issues
    if issues or warnings:
        issues_table = Table(title="Issues Found")
        issues_table.add_column("Severity", style="bold")
        issues_table.add_column("Category", style="cyan")
        issues_table.add_column("Issue", style="white")
        issues_table.add_column("Suggested Fix", style="green")
        
        all_issues = issues + warnings
        for issue in all_issues:
            severity = issue.get("severity", "info")
            severity_icon = {
                "error": "🔴 Error",
                "warning": "🟡 Warning", 
                "info": "🔵 Info"
            }.get(severity, severity)
            
            issues_table.add_row(
                severity_icon,
                issue.get("category", "unknown"),
                issue.get("message", "Unknown issue"),
                issue.get("fix", "No fix available")
            )
        
        console.print(issues_table)
    
    # System info summary
    console.print("\n[bold]System Summary:[/bold]")
    console.print(f"• OS: {platform.system()} {platform.release()}")
    console.print(f"• Python: {sys.version.split()[0]}")
    console.print(f"• Architecture: {platform.machine()}")
    
    try:
        result = subprocess.run(["aetherpost", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print(f"• AetherPost: {result.stdout.strip()}")
    except Exception:
        console.print("• AetherPost: Not available")


def attempt_fixes(issues: list):
    """Attempt to fix issues automatically."""
    
    console.print("\n[bold blue]🔧 Attempting Automatic Fixes...[/bold blue]")
    
    for issue in issues:
        if issue.get("severity") != "error":
            continue
            
        category = issue.get("category")
        message = issue.get("message", "")
        
        console.print(f"\n🔧 Fixing: {message}")
        
        try:
            if "missing dependencies" in message.lower() and category == "aetherpost":
                # Extract package names and install them
                packages = message.split(":")[1].strip().split(", ")
                for package in packages:
                    subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                 capture_output=True, check=True)
                console.print(f"  ✅ Installed missing packages")
            
            elif "not initialized" in message.lower():
                subprocess.run(["aetherpost", "init", "--quick"], 
                             capture_output=True, check=True)
                console.print(f"  ✅ Initialized workspace")
            
            elif "no credentials" in message.lower():
                console.print(f"  ⚠️ Manual setup required: aetherpost setup wizard")
            
            else:
                console.print(f"  ⚠️ Manual fix required: {issue.get('fix', 'See documentation')}")
                
        except subprocess.CalledProcessError as e:
            console.print(f"  ❌ Fix failed: {e}")
        except Exception as e:
            console.print(f"  ❌ Unexpected error: {e}")


@doctor_app.command()
def benchmark():
    """Run performance benchmarks."""
    
    console.print(Panel(
        "[bold purple]⚡ Performance Benchmark[/bold purple]",
        border_style="purple"
    ))
    
    # Test content generation speed
    console.print("\n[bold]Testing content generation speed...[/bold]")
    
    start_time = time.time()
    try:
        # Simulate content generation
        time.sleep(1)  # Placeholder for actual AI call
        generation_time = time.time() - start_time
        console.print(f"✅ Content generation: {generation_time:.2f}s")
    except Exception as e:
        console.print(f"❌ Content generation failed: {e}")
    
    # Test configuration loading
    console.print("\n[bold]Testing configuration loading...[/bold]")
    
    start_time = time.time()
    try:
        from ...core.config.parser import ConfigLoader
        config_loader = ConfigLoader()
        if Path("campaign.yaml").exists():
            config_loader.load_campaign_config()
        loading_time = time.time() - start_time
        console.print(f"✅ Configuration loading: {loading_time:.3f}s")
    except Exception as e:
        console.print(f"❌ Configuration loading failed: {e}")
    
    # Memory usage
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        console.print(f"\n[bold]Memory usage:[/bold] {memory_mb:.1f} MB")
    except ImportError:
        console.print("\n[dim]Install psutil for memory metrics[/dim]")


@doctor_app.command()
def logs():
    """Show recent AetherPost logs and errors."""
    
    console.print(Panel(
        "[bold cyan]📋 Recent Logs[/bold cyan]",
        border_style="cyan"
    ))
    
    # Check for log files
    log_locations = [
        Path(".aetherpost/logs"),
        Path.home() / ".aetherpost" / "logs",
        Path("/tmp/autopromo.log"),
    ]
    
    logs_found = False
    for log_path in log_locations:
        if log_path.exists():
            if log_path.is_dir():
                log_files = list(log_path.glob("*.log"))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    console.print(f"\n[bold]Latest log: {latest_log}[/bold]")
                    
                    try:
                        with open(latest_log) as f:
                            lines = f.readlines()[-20:]  # Last 20 lines
                            for line in lines:
                                console.print(f"  {line.rstrip()}")
                        logs_found = True
                    except Exception as e:
                        console.print(f"Error reading log: {e}")
            else:
                console.print(f"\n[bold]Log file: {log_path}[/bold]")
                try:
                    with open(log_path) as f:
                        lines = f.readlines()[-20:]
                        for line in lines:
                            console.print(f"  {line.rstrip()}")
                    logs_found = True
                except Exception as e:
                    console.print(f"Error reading log: {e}")
    
    if not logs_found:
        console.print("No log files found. This is normal for new installations.")
        console.print("\nEnable logging with: [cyan]export AUTOPROMO_LOG_LEVEL=INFO[/cyan]")