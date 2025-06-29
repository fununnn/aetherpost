#!/usr/bin/env python3
"""Test project context and plan functionality."""

import os
import sys
from pathlib import Path

# Add the aetherpost_source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

def test_project_context():
    """Test project context reading functionality."""
    print("🧪 Testing Project Context Reading")
    print("=" * 50)
    
    # Test 1: ProjectContextReader
    print("\n📋 ProjectContextReader Test:")
    try:
        from core.context.project_reader import ProjectContextReader
        
        reader = ProjectContextReader()
        
        # Test config loading
        config = reader.load_context_config("campaign.yaml")
        print(f"✅ Context config loaded: {config}")
        
        if config.get('enabled'):
            print(f"✅ Context enabled: True")
            print(f"✅ Watch paths: {config.get('watch', [])}")
            print(f"✅ Exclude patterns: {config.get('exclude', [])}")
            
            # Test project context reading
            context = reader.read_project_context("campaign.yaml")
            if context:
                print(f"✅ Project context read successfully")
                print(f"✅ Total files: {context.total_files}")
                print(f"✅ Total size: {context.total_size} bytes")
                print(f"✅ Safe files: {context.safe_files}")
                print(f"✅ Excluded files: {context.excluded_files}")
                print(f"✅ Scan time: {context.scan_time:.3f}s")
                
                # Show file summary
                summary = reader.get_file_summary(context)
                print(f"✅ File summary generated: {len(summary)} keys")
                
                if context.files:
                    print("\n📁 Detected files:")
                    for i, file_obj in enumerate(context.files[:5], 1):
                        print(f"  {i}. {file_obj.relative_path} ({file_obj.size} bytes)")
                    if len(context.files) > 5:
                        print(f"  ... and {len(context.files) - 5} more files")
            else:
                print("⚠️ No project context returned (context may be disabled)")
        else:
            print("⚠️ Context reading disabled in campaign.yaml")
            
    except Exception as e:
        print(f"❌ ProjectContextReader error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Diff Detector
    print("\n📋 ProjectDiffDetector Test:")
    try:
        from core.context.diff_detector import ProjectDiffDetector
        
        detector = ProjectDiffDetector()
        
        # Test snapshot info
        snapshot_info = detector.get_snapshot_info()
        if snapshot_info:
            print(f"✅ Existing snapshot found: {snapshot_info}")
        else:
            print("⚠️ No existing snapshot (first run)")
        
        # Test change detection
        diff = detector.detect_changes("campaign.yaml")
        if diff:
            print(f"✅ Diff detection completed")
            print(f"✅ Total changes: {diff.total_changes}")
            print(f"✅ Significant changes: {diff.has_significant_changes}")
            print(f"✅ Added files: {len(diff.added_files)}")
            print(f"✅ Modified files: {len(diff.modified_files)}")
            print(f"✅ Deleted files: {len(diff.deleted_files)}")
            
            # Show change summary
            summary = detector.get_changes_summary(diff)
            print(f"✅ Change summary generated: {len(summary)} keys")
            
            if diff.changes:
                print("\n📝 Recent changes:")
                for i, change in enumerate(diff.changes[:3], 1):
                    print(f"  {i}. {change.path} ({change.change_type})")
                if len(diff.changes) > 3:
                    print(f"  ... and {len(diff.changes) - 3} more changes")
        else:
            print("⚠️ No diff detection results (context may be disabled)")
            
    except Exception as e:
        print(f"❌ ProjectDiffDetector error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Content Generator Integration
    print("\n📋 Content Generator Integration Test:")
    try:
        from core.content.generator import ContentGenerator
        from core.config.models import CampaignConfig, ContentConfig
        
        # Create mock credentials
        class MockCredentials:
            def __init__(self):
                self.openai = {"api_key": "mock_key"}
                self.ai_service = None
        
        generator = ContentGenerator(MockCredentials())
        
        # Create mock config
        config = CampaignConfig(
            name="AetherPost",
            concept="Test project context integration",
            platforms=["twitter"],
            content=ContentConfig(style="friendly", language="en")
        )
        
        # Test project context integration in prompt building
        prompt = generator._build_prompt(config, "twitter")
        
        print(f"✅ Content generator prompt built")
        print(f"✅ Prompt length: {len(prompt)} characters")
        
        # Check if project context is included
        if "Project Context:" in prompt:
            print("✅ Project context integrated in prompt")
        else:
            print("⚠️ Project context not found in prompt")
        
        if "Recent Changes:" in prompt:
            print("✅ Recent changes integrated in prompt")
        else:
            print("⚠️ Recent changes not found in prompt")
        
        # Show prompt preview
        print("\n📝 AI Prompt Preview (first 500 chars):")
        print("-" * 40)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Content Generator integration error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Project context test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_project_context()