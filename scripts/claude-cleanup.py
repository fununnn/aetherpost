#!/usr/bin/env python3
"""
Claude Code痕跡完全除去ツール for AetherPost
GitHub Releases配布用の完全クリーンアップ
"""

import os
import re
import shutil
import json
from pathlib import Path
from typing import List, Dict, Set


class ClaudeCodeCleanup:
    """Claude Code関連痕跡の完全除去"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_before_cleanup"
        self.removed_files = []
        self.modified_files = []
        
        # Claude関連キーワード（大文字小文字区別なし）
        self.claude_keywords = [
            r'\bclaude\b(?!-?(?:3|sonnet|haiku))',  # claude（モデル名除く）
            r'claude.?code',
            r'claude.?ai',
            r'anthropic.?claude',
            r'generated.?with.?claude',
            r'created.?by.?claude',
            r'claude.?generated',
            r'powered.?by.?claude',
        ]
        
        # 削除対象ファイル・ディレクトリ
        self.files_to_remove = [
            'docs/CLAUDE-CODE.md',
            'aetherpost/cli/commands/claude.py',
            'aetherpost/plugins/ai_providers/claude/',
            '.claude',
            '.claudeconfig',
            'claude.yaml',
            'claude.yml',
        ]
        
        # 修正対象ファイルパターン
        self.file_patterns = [
            '**/*.py',
            '**/*.md',
            '**/*.json',
            '**/*.yaml',
            '**/*.yml',
            '**/*.txt',
            '**/*.rst',
            '**/*.toml',
        ]
    
    def create_backup(self):
        """実行前バックアップ作成"""
        print("🔄 Creating backup...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        # 重要ファイルのみバックアップ（.gitは除外）
        shutil.copytree(
            self.project_root,
            self.backup_dir,
            ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'node_modules')
        )
        print(f"✅ Backup created at: {self.backup_dir}")
    
    def remove_claude_files(self):
        """Claude関連ファイル・ディレクトリの削除"""
        print("🗑️  Removing Claude-specific files...")
        
        for file_path in self.files_to_remove:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                    print(f"   Removed directory: {file_path}")
                else:
                    full_path.unlink()
                    print(f"   Removed file: {file_path}")
                
                self.removed_files.append(str(file_path))
    
    def clean_python_files(self):
        """Pythonファイルの痕跡除去"""
        print("🐍 Cleaning Python files...")
        
        python_files = list(self.project_root.glob('**/*.py'))
        
        for py_file in python_files:
            if self._is_excluded_path(py_file):
                continue
                
            original_content = py_file.read_text(encoding='utf-8', errors='ignore')
            cleaned_content = original_content
            modified = False
            
            # Import文の削除
            claude_imports = [
                r'from\s+.*claude.*\s+import.*\n',
                r'import\s+.*claude.*\n',
                r'from\s+.*anthropic.*claude.*\n',
            ]
            
            for pattern in claude_imports:
                new_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.MULTILINE)
                if new_content != cleaned_content:
                    cleaned_content = new_content
                    modified = True
            
            # コメント内の痕跡削除
            cleaned_content = self._clean_comments_and_strings(cleaned_content)
            if cleaned_content != original_content:
                modified = True
            
            # 関数・クラス名の変更
            claude_function_patterns = [
                (r'def\s+(.*claude.*)\(', r'def \1_ai('),
                (r'class\s+(.*Claude.*)\(', r'class \1AI('),
            ]
            
            for pattern, replacement in claude_function_patterns:
                new_content = re.sub(pattern, replacement, cleaned_content, flags=re.IGNORECASE)
                if new_content != cleaned_content:
                    cleaned_content = new_content
                    modified = True
            
            if modified:
                py_file.write_text(cleaned_content, encoding='utf-8')
                self.modified_files.append(str(py_file.relative_to(self.project_root)))
                print(f"   Cleaned: {py_file.relative_to(self.project_root)}")
    
    def clean_documentation(self):
        """ドキュメントファイルの痕跡除去"""
        print("📚 Cleaning documentation...")
        
        doc_files = []
        for pattern in ['**/*.md', '**/*.rst', '**/*.txt']:
            doc_files.extend(self.project_root.glob(pattern))
        
        for doc_file in doc_files:
            if self._is_excluded_path(doc_file):
                continue
                
            original_content = doc_file.read_text(encoding='utf-8', errors='ignore')
            cleaned_content = self._clean_text_content(original_content)
            
            if cleaned_content != original_content:
                doc_file.write_text(cleaned_content, encoding='utf-8')
                self.modified_files.append(str(doc_file.relative_to(self.project_root)))
                print(f"   Cleaned: {doc_file.relative_to(self.project_root)}")
    
    def clean_config_files(self):
        """設定ファイルの痕跡除去"""
        print("⚙️  Cleaning configuration files...")
        
        config_files = []
        for pattern in ['**/*.json', '**/*.yaml', '**/*.yml', '**/*.toml']:
            config_files.extend(self.project_root.glob(pattern))
        
        for config_file in config_files:
            if self._is_excluded_path(config_file):
                continue
            
            try:
                if config_file.suffix.lower() == '.json':
                    self._clean_json_file(config_file)
                elif config_file.suffix.lower() in ['.yaml', '.yml']:
                    self._clean_yaml_file(config_file)
                elif config_file.suffix.lower() == '.toml':
                    self._clean_toml_file(config_file)
                    
            except Exception as e:
                print(f"   Warning: Could not clean {config_file}: {e}")
    
    def _clean_json_file(self, json_file: Path):
        """JSONファイルのクリーニング"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_str = json.dumps(data, indent=2)
            cleaned_data = self._clean_json_recursively(data)
            cleaned_str = json.dumps(cleaned_data, indent=2)
            
            if cleaned_str != original_str:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2)
                
                self.modified_files.append(str(json_file.relative_to(self.project_root)))
                print(f"   Cleaned JSON: {json_file.relative_to(self.project_root)}")
                
        except json.JSONDecodeError:
            # JSONでない場合はテキストとして処理
            original_content = json_file.read_text(encoding='utf-8', errors='ignore')
            cleaned_content = self._clean_text_content(original_content)
            
            if cleaned_content != original_content:
                json_file.write_text(cleaned_content, encoding='utf-8')
                self.modified_files.append(str(json_file.relative_to(self.project_root)))
    
    def _clean_yaml_file(self, yaml_file: Path):
        """YAMLファイルのクリーニング"""
        original_content = yaml_file.read_text(encoding='utf-8', errors='ignore')
        cleaned_content = self._clean_text_content(original_content)
        
        if cleaned_content != original_content:
            yaml_file.write_text(cleaned_content, encoding='utf-8')
            self.modified_files.append(str(yaml_file.relative_to(self.project_root)))
            print(f"   Cleaned YAML: {yaml_file.relative_to(self.project_root)}")
    
    def _clean_toml_file(self, toml_file: Path):
        """TOMLファイルのクリーニング"""
        original_content = toml_file.read_text(encoding='utf-8', errors='ignore')
        cleaned_content = self._clean_text_content(original_content)
        
        if cleaned_content != original_content:
            toml_file.write_text(cleaned_content, encoding='utf-8')
            self.modified_files.append(str(toml_file.relative_to(self.project_root)))
            print(f"   Cleaned TOML: {toml_file.relative_to(self.project_root)}")
    
    def _clean_json_recursively(self, obj):
        """JSON データの再帰的クリーニング"""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # キーのクリーニング
                cleaned_key = self._clean_text_content(str(key)) if isinstance(key, str) else key
                
                # 値のクリーニング
                if isinstance(value, str):
                    cleaned_value = self._clean_text_content(value)
                else:
                    cleaned_value = self._clean_json_recursively(value)
                
                cleaned[cleaned_key] = cleaned_value
            return cleaned
            
        elif isinstance(obj, list):
            return [self._clean_json_recursively(item) for item in obj]
            
        elif isinstance(obj, str):
            return self._clean_text_content(obj)
            
        else:
            return obj
    
    def _clean_text_content(self, content: str) -> str:
        """テキストコンテンツの一般的なクリーニング"""
        cleaned = content
        
        # Claude関連キーワードの置換
        replacements = {
            # 具体的な置換パターン
            r'\bClaude\s+Code\b': 'Advanced AI',
            r'\bclaude\.ai\b': 'ai-service.com',
            r'\bClaude\s+AI\b': 'AI Assistant',
            r'\bGenerated\s+with\s+Claude\s+Code\b': 'Generated with AI assistance',
            r'\bPowered\s+by\s+Claude\b': 'Powered by AI',
            r'\bAnthropic\s+Claude\b': 'AI Provider',
            r'\bclaude-3-sonnet\b': 'ai-model-v3',
            r'\bclaude-3-haiku\b': 'ai-model-lite',
            
            # URL・ドメインの置換
            r'https://claude\.ai[^\s]*': 'https://ai-service.com',
            r'https://console\.anthropic\.com[^\s]*': 'https://ai-provider.com/console',
            
            # API関連
            r'ANTHROPIC_API_KEY': 'AI_API_KEY',
            r'CLAUDE_API_KEY': 'AI_API_KEY',
        }
        
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # 一般的なClaude参照の除去
        for keyword_pattern in self.claude_keywords:
            # センシティブな箇所は [AI Service] で置換
            cleaned = re.sub(keyword_pattern, '[AI Service]', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _clean_comments_and_strings(self, content: str) -> str:
        """Python コメントと文字列のクリーニング"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # コメント行の処理
            if line.strip().startswith('#'):
                cleaned_line = self._clean_text_content(line)
                cleaned_lines.append(cleaned_line)
            # 文字列リテラル内の処理（簡易版）
            elif '"' in line or "'" in line:
                cleaned_line = self._clean_text_content(line)
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _is_excluded_path(self, path: Path) -> bool:
        """除外対象パスかどうかチェック"""
        excluded_patterns = [
            'backup_before_cleanup',
            '__pycache__',
            '.git',
            'node_modules',
            '.pytest_cache',
            'scripts/claude-cleanup.py',  # 自分自身は除外
        ]
        
        path_str = str(path)
        return any(pattern in path_str for pattern in excluded_patterns)
    
    def update_main_files(self):
        """メインファイルの更新"""
        print("📝 Updating main project files...")
        
        # README.mdの更新
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            
            # Claude Code関連記述の削除
            cleaned = re.sub(
                r'.*Claude\s+Code.*\n', 
                '', 
                content, 
                flags=re.IGNORECASE | re.MULTILINE
            )
            
            # Acknowledgments section from Claude Code references
            cleaned = re.sub(
                r'- Built with \[.*Claude.*\].*\n',
                '',
                cleaned,
                flags=re.IGNORECASE
            )
            
            if cleaned != content:
                readme_path.write_text(cleaned, encoding='utf-8')
                print("   Updated README.md")
        
        # package.json の更新
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                # 説明からClaude参照を削除
                if 'description' in data:
                    data['description'] = self._clean_text_content(data['description'])
                
                # キーワードからClaude関連を削除
                if 'keywords' in data and isinstance(data['keywords'], list):
                    data['keywords'] = [
                        kw for kw in data['keywords'] 
                        if not any(re.search(pattern, kw, re.IGNORECASE) for pattern in self.claude_keywords)
                    ]
                
                with open(package_json, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("   Updated package.json")
                
            except Exception as e:
                print(f"   Warning: Could not update package.json: {e}")
    
    def generate_report(self):
        """クリーンアップレポート生成"""
        report_path = self.project_root / 'cleanup_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("Claude Code 痕跡除去レポート\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"実行日時: {os.popen('date').read().strip()}\n\n")
            
            f.write(f"削除されたファイル ({len(self.removed_files)}):\n")
            for file_path in self.removed_files:
                f.write(f"  - {file_path}\n")
            
            f.write(f"\n修正されたファイル ({len(self.modified_files)}):\n")
            for file_path in self.modified_files:
                f.write(f"  - {file_path}\n")
            
            f.write("\n⚠️  注意事項:\n")
            f.write("- バックアップが backup_before_cleanup/ に保存されています\n")
            f.write("- 必要に応じて手動での最終確認を行ってください\n")
            f.write("- Git履歴はクリーンアップされていません\n")
        
        print(f"📊 Cleanup report generated: {report_path}")
    
    def run_cleanup(self):
        """完全クリーンアップの実行"""
        print("🚀 Starting Claude Code cleanup process...")
        print("=" * 60)
        
        # バックアップ作成
        self.create_backup()
        
        # ファイル削除
        self.remove_claude_files()
        
        # コード内容のクリーニング
        self.clean_python_files()
        self.clean_documentation()
        self.clean_config_files()
        
        # メインファイルの更新
        self.update_main_files()
        
        # レポート生成
        self.generate_report()
        
        print("\n" + "=" * 60)
        print("✅ Claude Code cleanup completed!")
        print(f"📁 Files removed: {len(self.removed_files)}")
        print(f"📝 Files modified: {len(self.modified_files)}")
        print(f"💾 Backup location: {self.backup_dir}")
        print("\n⚠️  推奨次ステップ:")
        print("1. cleanup_report.txt を確認")
        print("2. 重要ファイルの手動検証")
        print("3. テスト実行でエラーがないか確認")
        print("4. Git で新規リポジトリ作成")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    cleanup = ClaudeCodeCleanup(project_root)
    
    # 実行確認
    print("⚠️  Claude Code痕跡除去を実行します")
    print(f"対象ディレクトリ: {os.path.abspath(project_root)}")
    
    response = input("\n実行しますか？ (y/N): ")
    if response.lower() != 'y':
        print("❌ 実行をキャンセルしました")
        sys.exit(1)
    
    cleanup.run_cleanup()