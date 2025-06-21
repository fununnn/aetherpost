"""Git integration and project detection."""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, List
import re


class GitDetector:
    """Detects project information from Git repository."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.is_git_repo = self._check_git_repo()
    
    def _check_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_project_info(self) -> Dict:
        """Extract project information from Git and project files."""
        info = {
            "name": self._detect_project_name(),
            "description": self._detect_description(),
            "url": self._detect_project_url(),
            "type": self._detect_project_type(),
            "language": self._detect_primary_language(),
            "tags": self._generate_tags(),
            "has_releases": self._has_releases(),
            "is_open_source": self._is_open_source()
        }
        
        return {k: v for k, v in info.items() if v is not None}
    
    def _detect_project_name(self) -> Optional[str]:
        """Detect project name from various sources."""
        
        # Try package.json
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "name" in data:
                        return data["name"].replace("@", "").replace("/", "-")
            except Exception:
                pass
        
        # Try pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import toml
                with open(pyproject) as f:
                    data = toml.load(f)
                    if "project" in data and "name" in data["project"]:
                        return data["project"]["name"]
                    elif "tool" in data and "poetry" in data["tool"] and "name" in data["tool"]["poetry"]:
                        return data["tool"]["poetry"]["name"]
            except Exception:
                pass
        
        # Try Cargo.toml
        cargo_toml = self.repo_path / "Cargo.toml"
        if cargo_toml.exists():
            try:
                import toml
                with open(cargo_toml) as f:
                    data = toml.load(f)
                    if "package" in data and "name" in data["package"]:
                        return data["package"]["name"]
            except Exception:
                pass
        
        # Try git remote
        if self.is_git_repo:
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    url = result.stdout.strip()
                    # Extract repo name from git URL
                    match = re.search(r'/([^/]+?)(?:\.git)?/?$', url)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        
        # Fallback to directory name
        return self.repo_path.name
    
    def _detect_description(self) -> Optional[str]:
        """Detect project description from various sources."""
        
        # Try package.json
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "description" in data:
                        return data["description"]
            except Exception:
                pass
        
        # Try pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import toml
                with open(pyproject) as f:
                    data = toml.load(f)
                    if "project" in data and "description" in data["project"]:
                        return data["project"]["description"]
                    elif "tool" in data and "poetry" in data["tool"] and "description" in data["tool"]["poetry"]:
                        return data["tool"]["poetry"]["description"]
            except Exception:
                pass
        
        # Try README
        readme_files = ["README.md", "README.rst", "README.txt", "README"]
        for readme_file in readme_files:
            readme_path = self.repo_path / readme_file
            if readme_path.exists():
                try:
                    with open(readme_path, encoding='utf-8') as f:
                        content = f.read()
                        # Extract first meaningful line
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        for line in lines:
                            # Skip title lines and headers
                            if not line.startswith('#') and len(line) > 20 and len(line) < 200:
                                return line
                except Exception:
                    continue
        
        return None
    
    def _detect_project_url(self) -> Optional[str]:
        """Detect project URL from git remote or package files."""
        
        # Try package.json
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "homepage" in data:
                        return data["homepage"]
                    elif "repository" in data:
                        repo = data["repository"]
                        if isinstance(repo, dict) and "url" in repo:
                            return self._convert_git_to_web_url(repo["url"])
                        elif isinstance(repo, str):
                            return self._convert_git_to_web_url(repo)
            except Exception:
                pass
        
        # Try git remote
        if self.is_git_repo:
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    url = result.stdout.strip()
                    return self._convert_git_to_web_url(url)
            except Exception:
                pass
        
        return None
    
    def _convert_git_to_web_url(self, git_url: str) -> str:
        """Convert git URL to web URL."""
        # Handle GitHub URLs
        if "github.com" in git_url:
            git_url = git_url.replace("git@github.com:", "https://github.com/")
            git_url = git_url.replace("git+https://", "https://")
            git_url = git_url.replace(".git", "")
            return git_url
        
        # Handle GitLab URLs
        if "gitlab.com" in git_url:
            git_url = git_url.replace("git@gitlab.com:", "https://gitlab.com/")
            git_url = git_url.replace("git+https://", "https://")
            git_url = git_url.replace(".git", "")
            return git_url
        
        return git_url
    
    def _detect_project_type(self) -> Optional[str]:
        """Detect project type based on files and structure."""
        
        # JavaScript/Node.js
        if (self.repo_path / "package.json").exists():
            package_json = self.repo_path / "package.json"
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "react" in deps or "next" in deps:
                        return "react-app"
                    elif "vue" in deps:
                        return "vue-app"
                    elif "express" in deps:
                        return "node-backend"
                    elif "typescript" in deps:
                        return "typescript-app"
                    else:
                        return "javascript-app"
            except Exception:
                return "javascript-app"
        
        # Python
        if any((self.repo_path / f).exists() for f in ["pyproject.toml", "setup.py", "requirements.txt"]):
            if (self.repo_path / "manage.py").exists():
                return "django-app"
            elif any((self.repo_path / f).exists() for f in ["app.py", "main.py"]):
                return "python-web-app"
            else:
                return "python-package"
        
        # Rust
        if (self.repo_path / "Cargo.toml").exists():
            return "rust-app"
        
        # Go
        if (self.repo_path / "go.mod").exists():
            return "go-app"
        
        # Documentation
        if any((self.repo_path / f).exists() for f in ["docs", "_config.yml", "mkdocs.yml"]):
            return "documentation"
        
        return "general"
    
    def _detect_primary_language(self) -> Optional[str]:
        """Detect primary programming language."""
        
        # Simple detection based on file extensions
        extensions = {
            ".js": "javascript",
            ".ts": "typescript", 
            ".py": "python",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".php": "php",
            ".rb": "ruby"
        }
        
        counts = {}
        for ext, lang in extensions.items():
            count = len(list(self.repo_path.rglob(f"*{ext}")))
            if count > 0:
                counts[lang] = count
        
        if counts:
            return max(counts, key=counts.get)
        
        return None
    
    def _generate_tags(self) -> List[str]:
        """Generate appropriate hashtags based on project type."""
        
        project_type = self._detect_project_type()
        language = self._detect_primary_language()
        
        tags = []
        
        # Type-based tags
        type_tags = {
            "react-app": ["React", "WebDev", "Frontend"],
            "vue-app": ["VueJS", "WebDev", "Frontend"],
            "node-backend": ["NodeJS", "Backend", "API"],
            "django-app": ["Django", "Python", "WebDev"],
            "python-package": ["Python", "OpenSource"],
            "rust-app": ["Rust", "SystemsProgramming"],
            "go-app": ["Golang", "Backend"],
            "documentation": ["Documentation", "OpenSource"]
        }
        
        if project_type in type_tags:
            tags.extend(type_tags[project_type])
        
        # Language tags
        if language:
            tags.append(language.title())
        
        # Open source tag
        if self._is_open_source():
            tags.append("OpenSource")
        
        return list(set(tags))[:5]  # Limit to 5 tags
    
    def _has_releases(self) -> bool:
        """Check if project has releases."""
        if not self.is_git_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "tag", "--list"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False
    
    def _is_open_source(self) -> bool:
        """Check if project appears to be open source."""
        
        # Check for common open source indicators
        open_source_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"]
        for license_file in open_source_files:
            if (self.repo_path / license_file).exists():
                return True
        
        # Check if it's a public GitHub/GitLab repo
        url = self._detect_project_url()
        if url and ("github.com" in url or "gitlab.com" in url):
            return True
        
        return False
    
    def get_recent_commits(self, limit: int = 5) -> List[Dict]:
        """Get recent commit messages for campaign inspiration."""
        if not self.is_git_repo:
            return []
        
        try:
            result = subprocess.run([
                "git", "log", 
                f"--max-count={limit}",
                "--pretty=format:%h|%s|%ad",
                "--date=short"
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 2)
                    if len(parts) == 3:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "date": parts[2]
                        })
            
            return commits
        except Exception:
            return []
    
    def detect_release_events(self) -> Dict:
        """Detect if this might be a release commit."""
        if not self.is_git_repo:
            return {}
        
        try:
            # Check latest commit
            result = subprocess.run([
                "git", "log", "-1", "--pretty=format:%s"
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
            
            latest_commit = result.stdout.strip().lower()
            
            # Release indicators
            release_patterns = [
                r"release|version|bump|v\d+\.\d+",
                r"deploy|publish|launch",
                r"feat|feature|add",
                r"fix|bug|patch"
            ]
            
            event_type = None
            for pattern in release_patterns:
                if re.search(pattern, latest_commit):
                    if "release" in pattern or "version" in pattern:
                        event_type = "release"
                    elif "feat" in pattern or "feature" in pattern:
                        event_type = "feature"
                    elif "fix" in pattern:
                        event_type = "bugfix"
                    elif "deploy" in pattern:
                        event_type = "deployment"
                    break
            
            return {
                "event_type": event_type,
                "commit_message": result.stdout.strip(),
                "suggests_announcement": event_type is not None
            }
        
        except Exception:
            return {}