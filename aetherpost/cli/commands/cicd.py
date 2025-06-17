"""CI/CD integration commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import yaml

console = Console()
cicd_app = typer.Typer()


@cicd_app.command()
def setup(
    provider: str = typer.Option("github", "--provider", help="CI/CD provider (github, gitlab, etc.)"),
    workflow_type: str = typer.Option("release", "--type", help="Workflow type (release, feature, daily)"),
):
    """Set up CI/CD integration for automatic announcements."""
    
    console.print(Panel(
        f"[bold blue]🔄 CI/CD Integration Setup[/bold blue]\n\n"
        f"Setting up {provider} integration for {workflow_type} announcements.",
        border_style="blue"
    ))
    
    if provider.lower() == "github":
        setup_github_actions(workflow_type)
    elif provider.lower() == "gitlab":
        setup_gitlab_ci(workflow_type)
    else:
        console.print(f"❌ [red]Unsupported provider: {provider}[/red]")
        console.print("Supported providers: github, gitlab")


def setup_github_actions(workflow_type: str):
    """Set up GitHub Actions workflow."""
    
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    if workflow_type == "release":
        create_release_workflow(workflows_dir)
    elif workflow_type == "feature":
        create_feature_workflow(workflows_dir)
    elif workflow_type == "daily":
        create_daily_workflow(workflows_dir)
    else:
        console.print(f"❌ [red]Unknown workflow type: {workflow_type}[/red]")
        return
    
    console.print("✅ [green]GitHub Actions workflow created![/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Add secrets to your GitHub repository:")
    console.print("   • TWITTER_API_KEY")
    console.print("   • TWITTER_API_SECRET") 
    console.print("   • TWITTER_ACCESS_TOKEN")
    console.print("   • TWITTER_ACCESS_TOKEN_SECRET")
    console.print("   • AI_API_KEY")
    console.print("2. Commit and push the workflow file")
    console.print("3. Test with your next release/push")


def create_release_workflow(workflows_dir: Path):
    """Create GitHub Actions workflow for release announcements."""
    
    workflow_content = """name: Release Announcement

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      message:
        description: 'Custom announcement message'
        required: false
        default: ''

jobs:
  announce:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install AetherPost
      run: |
        pip install autopromo
        # Or if using from source:
        # pip install -r requirements.txt
        # pip install -e .
    
    - name: Create release announcement
      run: |
        if [ -n "${{ github.event.inputs.message }}" ]; then
          # Custom message from manual trigger
          aetherpost now "${{ github.event.inputs.message }}" \\
            --to twitter,bluesky \\
            --style professional \\
            --yes
        else
          # Auto-generate from release
          aetherpost now "🚀 ${{ github.event.release.name || github.ref_name }} is now available! ${{ github.event.release.body && 'Check out the new features and improvements.' || '' }}" \\
            --to twitter,bluesky \\
            --style casual \\
            --yes
        fi
      env:
        TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
        TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
        TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
        TWITTER_ACCESS_TOKEN_SECRET: ${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    
    - name: Post to dev-focused platforms
      if: contains(github.repository, 'dev') || contains(github.repository, 'cli') || contains(github.repository, 'tool')
      run: |
        aetherpost now "New release: ${{ github.ref_name }} with developer-focused improvements! 🛠️" \\
          --to dev_to,mastodon \\
          --style technical \\
          --yes
      env:
        TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
        TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
        TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
        TWITTER_ACCESS_TOKEN_SECRET: ${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
"""
    
    workflow_file = workflows_dir / "autopromo-release.yml"
    with open(workflow_file, "w") as f:
        f.write(workflow_content)
    
    console.print(f"📄 Created: {workflow_file}")


def create_feature_workflow(workflows_dir: Path):
    """Create GitHub Actions workflow for feature announcements."""
    
    workflow_content = """name: Feature Announcement

on:
  push:
    branches: [main, master]
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - '.github/**'
  workflow_dispatch:

jobs:
  check-and-announce:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 2
    
    - name: Check for feature commits
      id: check_features
      run: |
        # Check if recent commits contain feature indicators
        RECENT_COMMITS=$(git log --oneline -5 --grep="feat\\|feature\\|add" --grep="new" --grep="implement")
        if [ -n "$RECENT_COMMITS" ]; then
          echo "has_features=true" >> $GITHUB_OUTPUT
          echo "latest_feature=$(echo "$RECENT_COMMITS" | head -1)" >> $GITHUB_OUTPUT
        else
          echo "has_features=false" >> $GITHUB_OUTPUT
        fi
    
    - name: Set up Python
      if: steps.check_features.outputs.has_features == 'true'
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install AetherPost
      if: steps.check_features.outputs.has_features == 'true'
      run: pip install autopromo
    
    - name: Announce new feature
      if: steps.check_features.outputs.has_features == 'true'
      run: |
        aetherpost now "🆕 New feature shipped! ${{ steps.check_features.outputs.latest_feature }} Check it out!" \\
          --to twitter \\
          --style casual \\
          --yes
      env:
        TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
        TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
        TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
        TWITTER_ACCESS_TOKEN_SECRET: ${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
"""
    
    workflow_file = workflows_dir / "autopromo-features.yml"
    with open(workflow_file, "w") as f:
        f.write(workflow_content)
    
    console.print(f"📄 Created: {workflow_file}")


def create_daily_workflow(workflows_dir: Path):
    """Create GitHub Actions workflow for daily/weekly updates."""
    
    workflow_content = """name: Scheduled Updates

on:
  schedule:
    # Run every Monday at 10 AM UTC
    - cron: '0 10 * * 1'
  workflow_dispatch:

jobs:
  weekly-update:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 30  # Get last 30 commits for analysis
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install AetherPost
      run: pip install autopromo
    
    - name: Generate weekly summary
      id: summary
      run: |
        # Get commits from last 7 days
        WEEK_COMMITS=$(git log --since="7 days ago" --oneline --no-merges)
        COMMIT_COUNT=$(echo "$WEEK_COMMITS" | wc -l)
        
        if [ $COMMIT_COUNT -gt 0 ]; then
          echo "has_activity=true" >> $GITHUB_OUTPUT
          echo "commit_count=$COMMIT_COUNT" >> $GITHUB_OUTPUT
          
          # Check for different types of changes
          FEATURES=$(echo "$WEEK_COMMITS" | grep -E "feat|feature|add|new" | wc -l)
          FIXES=$(echo "$WEEK_COMMITS" | grep -E "fix|bug|patch" | wc -l)
          
          echo "features=$FEATURES" >> $GITHUB_OUTPUT
          echo "fixes=$FIXES" >> $GITHUB_OUTPUT
        else
          echo "has_activity=false" >> $GITHUB_OUTPUT
        fi
    
    - name: Post weekly update
      if: steps.summary.outputs.has_activity == 'true'
      run: |
        MESSAGE="📊 Week in review: ${{ steps.summary.outputs.commit_count }} commits"
        
        if [ ${{ steps.summary.outputs.features }} -gt 0 ]; then
          MESSAGE="$MESSAGE, ${{ steps.summary.outputs.features }} new features"
        fi
        
        if [ ${{ steps.summary.outputs.fixes }} -gt 0 ]; then
          MESSAGE="$MESSAGE, ${{ steps.summary.outputs.fixes }} fixes"
        fi
        
        MESSAGE="$MESSAGE. Keep building! 🚀"
        
        aetherpost now "$MESSAGE" \\
          --to twitter \\
          --style casual \\
          --yes
      env:
        TWITTER_API_KEY: ${{ secrets.TWITTER_API_KEY }}
        TWITTER_API_SECRET: ${{ secrets.TWITTER_API_SECRET }}
        TWITTER_ACCESS_TOKEN: ${{ secrets.TWITTER_ACCESS_TOKEN }}
        TWITTER_ACCESS_TOKEN_SECRET: ${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
"""
    
    workflow_file = workflows_dir / "autopromo-weekly.yml"
    with open(workflow_file, "w") as f:
        f.write(workflow_content)
    
    console.print(f"📄 Created: {workflow_file}")


def setup_gitlab_ci(workflow_type: str):
    """Set up GitLab CI/CD pipeline."""
    
    gitlab_ci_file = Path(".gitlab-ci.yml")
    
    if gitlab_ci_file.exists():
        console.print("⚠️ [yellow].gitlab-ci.yml already exists[/yellow]")
        if not Confirm.ask("Add AetherPost job to existing file?"):
            return
        
        # Append to existing file
        with open(gitlab_ci_file, "a") as f:
            f.write("\n" + get_gitlab_ci_content(workflow_type))
    else:
        # Create new file
        with open(gitlab_ci_file, "w") as f:
            f.write(get_gitlab_ci_content(workflow_type))
    
    console.print("✅ [green]GitLab CI configuration updated![/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Add variables to your GitLab project:")
    console.print("   • TWITTER_API_KEY")
    console.print("   • TWITTER_API_SECRET")
    console.print("   • TWITTER_ACCESS_TOKEN") 
    console.print("   • TWITTER_ACCESS_TOKEN_SECRET")
    console.print("   • AI_API_KEY")
    console.print("2. Commit and push the .gitlab-ci.yml file")


def get_gitlab_ci_content(workflow_type: str) -> str:
    """Get GitLab CI configuration content."""
    
    if workflow_type == "release":
        return """
# AetherPost Release Announcement
announce_release:
  stage: deploy
  image: python:3.10
  script:
    - pip install autopromo
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        aetherpost now "🚀 $CI_COMMIT_TAG released! Check out the latest updates." \\
          --to twitter,bluesky \\
          --style professional \\
          --yes
      fi
  rules:
    - if: $CI_COMMIT_TAG
  variables:
    TWITTER_API_KEY: $TWITTER_API_KEY
    TWITTER_API_SECRET: $TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN: $TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_TOKEN_SECRET: $TWITTER_ACCESS_TOKEN_SECRET
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
"""
    
    elif workflow_type == "feature":
        return """
# AetherPost Feature Announcement
announce_features:
  stage: deploy
  image: python:3.10
  script:
    - pip install autopromo
    - |
      if git log --oneline -1 | grep -E "feat|feature|add|new"; then
        COMMIT_MSG=$(git log --oneline -1)
        aetherpost now "🆕 New feature: $COMMIT_MSG" \\
          --to twitter \\
          --style casual \\
          --yes
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  variables:
    TWITTER_API_KEY: $TWITTER_API_KEY
    TWITTER_API_SECRET: $TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN: $TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_TOKEN_SECRET: $TWITTER_ACCESS_TOKEN_SECRET
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
"""
    
    else:
        return """
# AetherPost Scheduled Updates
weekly_update:
  stage: deploy
  image: python:3.10
  script:
    - pip install autopromo
    - aetherpost now "📊 Weekly project update! Still building awesome things 🚀" \\
        --to twitter \\
        --style casual \\
        --yes
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  variables:
    TWITTER_API_KEY: $TWITTER_API_KEY
    TWITTER_API_SECRET: $TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN: $TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_TOKEN_SECRET: $TWITTER_ACCESS_TOKEN_SECRET
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
"""


@cicd_app.command()
def templates():
    """List available CI/CD templates."""
    
    console.print(Panel(
        "[bold blue]🔄 CI/CD Templates[/bold blue]",
        border_style="blue"
    ))
    
    templates_table = Table(title="Available CI/CD Templates")
    templates_table.add_column("Provider", style="cyan")
    templates_table.add_column("Type", style="green")
    templates_table.add_column("Description", style="white")
    templates_table.add_column("Trigger", style="yellow")
    
    templates_data = [
        ("GitHub Actions", "Release", "Announce new releases automatically", "On release published"),
        ("GitHub Actions", "Feature", "Announce major features", "On push to main"),
        ("GitHub Actions", "Weekly", "Weekly project updates", "Scheduled (Mondays)"),
        ("GitLab CI", "Release", "Release announcements", "On tag creation"),
        ("GitLab CI", "Feature", "Feature announcements", "On main branch push"),
        ("GitLab CI", "Scheduled", "Regular updates", "Scheduled pipeline"),
    ]
    
    for provider, type_name, description, trigger in templates_data:
        templates_table.add_row(provider, type_name, description, trigger)
    
    console.print(templates_table)
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("• [cyan]aetherpost cicd setup --provider github --type release[/cyan]")
    console.print("• [cyan]aetherpost cicd setup --provider gitlab --type feature[/cyan]")
    console.print("• [cyan]aetherpost cicd validate[/cyan] - Check existing setup")


@cicd_app.command()
def validate():
    """Validate existing CI/CD setup."""
    
    console.print(Panel(
        "[bold yellow]🔍 CI/CD Validation[/bold yellow]",
        border_style="yellow"
    ))
    
    issues = []
    
    # Check GitHub Actions
    github_workflows = Path(".github/workflows")
    if github_workflows.exists():
        workflow_files = list(github_workflows.glob("*.yml")) + list(github_workflows.glob("*.yaml"))
        
        if workflow_files:
            console.print("✅ [green]GitHub Actions workflows found[/green]")
            
            for workflow_file in workflow_files:
                if "aetherpost" in workflow_file.read_text():
                    console.print(f"  • {workflow_file.name} - Contains AetherPost")
                else:
                    console.print(f"  • {workflow_file.name}")
        else:
            console.print("⚠️ [yellow]No GitHub Actions workflows found[/yellow]")
    else:
        console.print("ℹ️ No .github/workflows directory")
    
    # Check GitLab CI
    gitlab_ci = Path(".gitlab-ci.yml")
    if gitlab_ci.exists():
        content = gitlab_ci.read_text()
        if "aetherpost" in content:
            console.print("✅ [green]GitLab CI with AetherPost found[/green]")
        else:
            console.print("⚠️ [yellow]GitLab CI found but no AetherPost integration[/yellow]")
    else:
        console.print("ℹ️ No .gitlab-ci.yml file")
    
    # Check for common issues
    console.print("\n[bold]Common Setup Issues:[/bold]")
    
    # Check if aetherpost is installed/configured locally
    if not Path("campaign.yaml").exists():
        issues.append("No campaign.yaml - Run 'aetherpost init' first")
    
    if not Path(".aetherpost/credentials.yaml").exists():
        issues.append("No credentials configured - Run 'aetherpost setup wizard'")
    
    if issues:
        console.print("❌ [red]Issues found:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("✅ [green]No obvious issues found[/green]")
    
    console.print("\n[bold]Recommendations:[/bold]")
    console.print("• Test workflows manually before relying on automation")
    console.print("• Set up repository secrets for API keys")
    console.print("• Monitor workflow runs for errors")
    console.print("• Consider rate limiting for high-frequency projects")


@cicd_app.command()
def secrets():
    """Show required secrets for CI/CD integration."""
    
    console.print(Panel(
        "[bold purple]🔐 Required Secrets[/bold purple]",
        border_style="purple"
    ))
    
    secrets_table = Table(title="CI/CD Secrets Configuration")
    secrets_table.add_column("Secret Name", style="cyan")
    secrets_table.add_column("Description", style="white")
    secrets_table.add_column("Required For", style="green")
    
    secrets_data = [
        ("TWITTER_API_KEY", "Twitter API key", "Twitter posting"),
        ("TWITTER_API_SECRET", "Twitter API secret", "Twitter posting"),
        ("TWITTER_ACCESS_TOKEN", "Twitter access token", "Twitter posting"),
        ("TWITTER_ACCESS_TOKEN_SECRET", "Twitter access token secret", "Twitter posting"),
        ("AI_API_KEY", "[AI Service] API key", "AI content generation"),
        ("OPENAI_API_KEY", "OpenAI API key (optional)", "AI content generation"),
        ("BLUESKY_USERNAME", "Bluesky username (optional)", "Bluesky posting"),
        ("BLUESKY_PASSWORD", "Bluesky app password (optional)", "Bluesky posting"),
    ]
    
    for name, description, required_for in secrets_data:
        secrets_table.add_row(name, description, required_for)
    
    console.print(secrets_table)
    
    console.print("\n[bold]Setup Instructions:[/bold]")
    
    console.print("\n[cyan]GitHub:[/cyan]")
    console.print("1. Go to your repository settings")
    console.print("2. Navigate to Secrets and variables > Actions")
    console.print("3. Add each secret with the exact name shown above")
    
    console.print("\n[cyan]GitLab:[/cyan]")
    console.print("1. Go to your project settings")
    console.print("2. Navigate to CI/CD > Variables")
    console.print("3. Add each variable (mark as protected and masked)")
    
    console.print("\n[bold]Security Notes:[/bold]")
    console.print("• Never commit API keys to your repository")
    console.print("• Use environment-specific secrets for different deployments")
    console.print("• Regularly rotate your API keys")
    console.print("• Monitor API usage to detect unauthorized access")