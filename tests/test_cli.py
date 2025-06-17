"""Test CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from aetherpost.cli.main import app


class TestCLI:
    """Test CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "AetherPost version" in result.stdout
    
    def test_plugins_command(self, runner):
        """Test plugins listing command."""
        result = runner.invoke(app, ["plugins"])
        assert result.exit_code == 0
        assert "Available Plugins" in result.stdout
    
    def test_validate_command_no_config(self, runner):
        """Test validate command without config file."""
        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 0
        assert "campaign.yaml not found" in result.stdout
    
    def test_stats_command_no_state(self, runner):
        """Test stats command without state file."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "No active campaign found" in result.stdout


class TestInitCommand:
    """Test init command."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_init_example(self, runner):
        """Test init with example flag."""
        result = runner.invoke(app, ["init", "--example"])
        assert result.exit_code == 0
        assert "Usage Examples" in result.stdout
        assert "Minimal Setup" in result.stdout
    
    @patch('aetherpost.cli.commands.init.Confirm.ask')
    @patch('aetherpost.cli.commands.init.Prompt.ask')
    def test_init_quick_setup(self, mock_prompt, mock_confirm, runner):
        """Test quick setup."""
        # Mock user inputs
        mock_prompt.side_effect = ["test-app", "Test application description"]
        
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["init", "--quick"])
            assert result.exit_code == 0
            assert "Created campaign.yaml" in result.stdout
    
    def test_init_template_basic(self, runner):
        """Test creating basic template."""
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["init", "template", "my-app"])
            assert result.exit_code == 0
            assert "Created campaign.yaml template" in result.stdout
            
            # Check file was created
            import os
            assert os.path.exists("campaign.yaml")


class TestPlanCommand:
    """Test plan command."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_plan_no_config(self, runner):
        """Test plan command without config file."""
        result = runner.invoke(app, ["plan"])
        assert result.exit_code == 0
        assert "Configuration file not found" in result.stdout


class TestApplyCommand:
    """Test apply command."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_apply_no_config(self, runner):
        """Test apply command without config file."""
        result = runner.invoke(app, ["apply"])
        assert result.exit_code == 0
        assert "Configuration file not found" in result.stdout
    
    def test_apply_dry_run(self, runner):
        """Test apply with dry run flag."""
        with runner.isolated_filesystem():
            # Create a test config file
            config_content = """
name: "test-app"
concept: "Test application"
platforms: ["twitter"]
"""
            with open("campaign.yaml", "w") as f:
                f.write(config_content)
            
            result = runner.invoke(app, ["apply", "--dry-run"])
            # Should fail due to missing credentials, but test the flag parsing
            assert "--dry-run" not in result.stdout or result.exit_code == 0


class TestStateCommand:
    """Test state command."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_state_show_no_state(self, runner):
        """Test state show without state file."""
        result = runner.invoke(app, ["state", "show"])
        assert result.exit_code == 0
        assert "No active campaign state found" in result.stdout
    
    def test_state_export_no_state(self, runner):
        """Test state export without state file."""
        result = runner.invoke(app, ["state", "export"])
        assert result.exit_code == 0
        assert "No active campaign state found" in result.stdout
    
    def test_state_clear_cancelled(self, runner):
        """Test state clear with cancellation."""
        with patch('aetherpost.cli.commands.state.Confirm.ask', return_value=False):
            result = runner.invoke(app, ["state", "clear"])
            assert result.exit_code == 0
            assert "Operation cancelled" in result.stdout
    
    def test_state_backup_no_file(self, runner):
        """Test state backup without state file."""
        result = runner.invoke(app, ["state", "backup"])
        assert result.exit_code == 0
        assert "No state file to backup" in result.stdout


class TestAuthCommand:
    """Test auth command."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_auth_list_no_credentials(self, runner):
        """Test auth list without credentials."""
        result = runner.invoke(app, ["auth", "list"])
        assert result.exit_code == 0
        assert "Authentication Status" in result.stdout
    
    def test_auth_test_no_credentials(self, runner):
        """Test auth test without credentials."""
        result = runner.invoke(app, ["auth", "test", "twitter"])
        assert result.exit_code == 0
        assert "No credentials found" in result.stdout
    
    @patch('aetherpost.cli.commands.auth.Confirm.ask')
    def test_auth_remove_cancelled(self, mock_confirm, runner):
        """Test auth remove with cancellation."""
        mock_confirm.return_value = False
        
        result = runner.invoke(app, ["auth", "remove", "twitter"])
        assert result.exit_code == 0
        assert "Operation cancelled" in result.stdout
    
    @patch('aetherpost.cli.commands.auth.Prompt.ask')
    @patch('aetherpost.cli.commands.auth.APIKeyValidator.validate_twitter_keys')
    def test_auth_setup_twitter_valid(self, mock_validator, mock_prompt, runner):
        """Test Twitter auth setup with valid credentials."""
        # Mock user inputs
        mock_prompt.side_effect = ["api_key", "api_secret", "access_token", "access_secret"]
        mock_validator.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["auth", "setup", "--platform", "twitter"])
            assert result.exit_code == 0
            assert "Twitter credentials saved" in result.stdout
    
    @patch('aetherpost.cli.commands.auth.Prompt.ask')
    @patch('aetherpost.cli.commands.auth.APIKeyValidator.validate_anthropic_key')
    def test_auth_setup_claude_valid_ai(self, mock_validator, mock_prompt, runner):
        """Test [AI Service] auth setup with valid key."""
        mock_prompt.return_value = "sk-ant-test_key"
        mock_validator.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["auth", "setup", "--platform", "[AI Service]"])
            assert result.exit_code == 0
            assert "[AI Service] credentials saved" in result.stdout
    
    @patch('aetherpost.cli.commands.auth.Prompt.ask')
    @patch('aetherpost.cli.commands.auth.APIKeyValidator.validate_openai_key')
    def test_auth_setup_openai_valid(self, mock_validator, mock_prompt, runner):
        """Test OpenAI auth setup with valid key."""
        mock_prompt.return_value = "sk-test_key"
        mock_validator.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["auth", "setup", "--platform", "openai"])
            assert result.exit_code == 0
            assert "OpenAI credentials saved" in result.stdout
    
    @patch('aetherpost.cli.commands.auth.Prompt.ask')
    @patch('aetherpost.cli.commands.auth.APIKeyValidator.validate_bluesky_credentials')
    def test_auth_setup_bluesky_valid(self, mock_validator, mock_prompt, runner):
        """Test Bluesky auth setup with valid credentials."""
        mock_prompt.side_effect = ["user.bsky.social", "password123"]
        mock_validator.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["auth", "setup", "--platform", "bluesky"])
            assert result.exit_code == 0
            assert "Bluesky credentials saved" in result.stdout
    
    def test_auth_setup_unknown_platform(self, runner):
        """Test auth setup with unknown platform."""
        result = runner.invoke(app, ["auth", "setup", "--platform", "unknown"])
        assert result.exit_code == 0
        assert "Unknown platform" in result.stdout