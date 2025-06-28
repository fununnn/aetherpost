#!/usr/bin/env python3
"""Comprehensive test suite for ContentGenerator."""

import sys
import os
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

# Add project to Python path
sys.path.insert(0, '/home/ubuntu/doc/autopromo/aetherpost_source')

from core.content.generator import ContentGenerator
from core.config.models import CampaignConfig, CredentialsConfig, ContentConfig

# Console colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float = 0.0

class ContentGeneratorTester:
    """Comprehensive test suite for ContentGenerator."""
    
    def __init__(self):
        self.results = []
        self.temp_dir = None
        self.generator = None
        
    def setup(self):
        """Setup test environment."""
        print(f"{Colors.BLUE}🔧 Setting up test environment...{Colors.END}")
        
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        os.chdir(self.temp_dir)
        
        # Create test credentials (will work without actual API keys for most tests)
        credentials = CredentialsConfig(
            ai_service={"api_key": "test-anthropic-key"},
            openai={"api_key": "test-openai-key"}
        )
        
        # Initialize content generator
        self.generator = ContentGenerator(credentials)
        
        print(f"{Colors.GREEN}✅ Test environment ready{Colors.END}")
    
    def cleanup(self):
        """Cleanup test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_provider_setup(self):
        """Test AI provider initialization."""
        print(f"\n{Colors.CYAN}📡 Testing AI Provider Setup{Colors.END}")
        
        # Test provider detection
        expected_providers = ["anthropic", "openai"]
        detected_providers = list(self.generator.ai_providers.keys())
        
        if set(expected_providers).issubset(set(detected_providers)):
            self.results.append(TestResult("provider_setup", True, f"Providers detected: {detected_providers}"))
        else:
            self.results.append(TestResult("provider_setup", False, f"Missing providers. Expected: {expected_providers}, Got: {detected_providers}"))
    
    def test_cache_functionality(self):
        """Test content caching and idempotency."""
        print(f"\n{Colors.CYAN}💾 Testing Content Caching{Colors.END}")
        
        try:
            # Create test config
            config = self._create_test_config()
            
            # Test cache key generation
            cache_key1 = self.generator._get_cache_key(config, "twitter")
            cache_key2 = self.generator._get_cache_key(config, "twitter")
            cache_key3 = self.generator._get_cache_key(config, "bluesky")
            
            # Same config should generate same key
            if cache_key1 == cache_key2:
                self.results.append(TestResult("cache_key_consistency", True, "Cache keys are consistent"))
            else:
                self.results.append(TestResult("cache_key_consistency", False, "Cache keys are inconsistent"))
            
            # Different platforms should generate different keys
            if cache_key1 != cache_key3:
                self.results.append(TestResult("cache_key_uniqueness", True, "Cache keys are unique per platform"))
            else:
                self.results.append(TestResult("cache_key_uniqueness", False, "Cache keys not unique per platform"))
            
            # Test caching mechanism
            test_content = {"text": "Test content", "platform": "twitter"}
            self.generator._cache_content(cache_key1, test_content)
            cached_content = self.generator._get_cached_content(cache_key1)
            
            if cached_content == test_content:
                self.results.append(TestResult("cache_storage_retrieval", True, "Content caching works correctly"))
            else:
                self.results.append(TestResult("cache_storage_retrieval", False, "Content caching failed"))
                
        except Exception as e:
            self.results.append(TestResult("cache_functionality", False, f"Cache test failed: {e}"))
    
    def test_platform_optimization(self):
        """Test platform-specific optimizations."""
        print(f"\n{Colors.CYAN}⚙️ Testing Platform Optimizations{Colors.END}")
        
        platforms = ["twitter", "bluesky", "linkedin", "mastodon", "discord"]
        
        for platform in platforms:
            try:
                # Test character limits
                char_limit = self.generator._get_platform_char_limit(platform)
                if char_limit > 0:
                    self.results.append(TestResult(f"char_limit_{platform}", True, f"{platform}: {char_limit} chars"))
                else:
                    self.results.append(TestResult(f"char_limit_{platform}", False, f"{platform}: Invalid char limit"))
                
                # Test platform features
                features = self.generator._get_platform_features(platform)
                if isinstance(features, str):
                    self.results.append(TestResult(f"features_{platform}", True, f"{platform}: Features defined"))
                else:
                    self.results.append(TestResult(f"features_{platform}", False, f"{platform}: No features"))
                    
            except Exception as e:
                self.results.append(TestResult(f"platform_optimization_{platform}", False, f"Error: {e}"))
    
    def test_style_variations(self):
        """Test different content styles."""
        print(f"\n{Colors.CYAN}🎨 Testing Style Variations{Colors.END}")
        
        styles = ["casual", "professional", "technical", "humorous"]
        
        for style in styles:
            try:
                instructions = self.generator._get_style_instructions(style)
                if instructions and len(instructions) > 100:  # Should be detailed
                    self.results.append(TestResult(f"style_{style}", True, f"{style}: Instructions provided"))
                else:
                    self.results.append(TestResult(f"style_{style}", False, f"{style}: No/insufficient instructions"))
                    
            except Exception as e:
                self.results.append(TestResult(f"style_{style}", False, f"Error: {e}"))
    
    def test_language_support(self):
        """Test multilingual support."""
        print(f"\n{Colors.CYAN}🌍 Testing Language Support{Colors.END}")
        
        languages = ["en", "ja", "es", "fr", "de", "ko", "zh", "pt", "ru", "ar"]
        
        for lang in languages:
            try:
                # Test language name resolution
                lang_name = self.generator._get_language_name(lang)
                if lang_name and lang_name != lang.upper():
                    self.results.append(TestResult(f"lang_name_{lang}", True, f"{lang}: {lang_name}"))
                else:
                    self.results.append(TestResult(f"lang_name_{lang}", False, f"{lang}: No name mapping"))
                
                # Test language instructions
                instructions = self.generator._get_language_instructions(lang)
                if instructions and len(instructions) > 50:
                    self.results.append(TestResult(f"lang_instructions_{lang}", True, f"{lang}: Instructions provided"))
                else:
                    self.results.append(TestResult(f"lang_instructions_{lang}", False, f"{lang}: No instructions"))
                    
            except Exception as e:
                self.results.append(TestResult(f"language_{lang}", False, f"Error: {e}"))
    
    def test_prompt_building(self):
        """Test AI prompt construction."""
        print(f"\n{Colors.CYAN}📝 Testing Prompt Building{Colors.END}")
        
        try:
            config = self._create_test_config()
            
            # Test basic prompt building
            prompt = self.generator._build_prompt(config, "twitter")
            if len(prompt) > 500:  # Should be detailed
                self.results.append(TestResult("prompt_basic", True, f"Prompt length: {len(prompt)} chars"))
            else:
                self.results.append(TestResult("prompt_basic", False, "Prompt too short"))
            
            # Test prompt contains key elements
            required_elements = [config.name, config.concept, "twitter", "280"]
            missing_elements = [elem for elem in required_elements if str(elem).lower() not in prompt.lower()]
            
            if not missing_elements:
                self.results.append(TestResult("prompt_content", True, "All required elements in prompt"))
            else:
                self.results.append(TestResult("prompt_content", False, f"Missing: {missing_elements}"))
                
        except Exception as e:
            self.results.append(TestResult("prompt_building", False, f"Error: {e}"))
    
    def test_hashtag_generation(self):
        """Test hashtag generation."""
        print(f"\n{Colors.CYAN}🏷️ Testing Hashtag Generation{Colors.END}")
        
        try:
            # Test with AI concept
            config1 = self._create_test_config()
            config1.concept = "AI-powered productivity app"
            hashtags1 = self.generator._generate_hashtags(config1, "instagram")
            
            if "#AI" in hashtags1:
                self.results.append(TestResult("hashtag_ai_detection", True, "AI hashtag detected"))
            else:
                self.results.append(TestResult("hashtag_ai_detection", False, "AI hashtag missing"))
            
            # Test platform limits
            twitter_hashtags = self.generator._generate_hashtags(config1, "twitter")
            instagram_hashtags = self.generator._generate_hashtags(config1, "instagram")
            
            if len(twitter_hashtags) <= 2:
                self.results.append(TestResult("hashtag_twitter_limit", True, f"Twitter: {len(twitter_hashtags)} hashtags"))
            else:
                self.results.append(TestResult("hashtag_twitter_limit", False, f"Twitter: too many hashtags ({len(twitter_hashtags)})"))
            
            if len(instagram_hashtags) <= 10:
                self.results.append(TestResult("hashtag_instagram_limit", True, f"Instagram: {len(instagram_hashtags)} hashtags"))
            else:
                self.results.append(TestResult("hashtag_instagram_limit", False, f"Instagram: too many hashtags ({len(instagram_hashtags)})"))
                
        except Exception as e:
            self.results.append(TestResult("hashtag_generation", False, f"Error: {e}"))
    
    def test_fallback_content(self):
        """Test fallback content generation."""
        print(f"\n{Colors.CYAN}🔄 Testing Fallback Content{Colors.END}")
        
        try:
            config = self._create_test_config()
            
            # Test all style fallbacks
            styles = ["casual", "professional", "technical", "humorous"]
            for style in styles:
                config.content.style = style
                fallback_content = self.generator._generate_fallback_content(config, "twitter")
                
                if fallback_content and len(fallback_content) > 20:
                    self.results.append(TestResult(f"fallback_{style}", True, f"{style}: Generated content"))
                else:
                    self.results.append(TestResult(f"fallback_{style}", False, f"{style}: No content"))
                
                # Check if content contains key elements
                if config.name in fallback_content and config.concept in fallback_content:
                    self.results.append(TestResult(f"fallback_content_{style}", True, f"{style}: Contains key info"))
                else:
                    self.results.append(TestResult(f"fallback_content_{style}", False, f"{style}: Missing key info"))
                    
        except Exception as e:
            self.results.append(TestResult("fallback_content", False, f"Error: {e}"))
    
    def test_media_discovery(self):
        """Test media file discovery."""
        print(f"\n{Colors.CYAN}📸 Testing Media Discovery{Colors.END}")
        
        try:
            # Create test media files
            test_files = ["test.png", "screenshot.jpg", "demo.gif"]
            for filename in test_files:
                with open(filename, "w") as f:
                    f.write("test")
            
            # Test media discovery
            discovered_media = self.generator._discover_media_files()
            
            if len(discovered_media) > 0:
                self.results.append(TestResult("media_discovery", True, f"Found {len(discovered_media)} files"))
            else:
                self.results.append(TestResult("media_discovery", False, "No media files discovered"))
            
            # Test discovery limits
            if len(discovered_media) <= 4:
                self.results.append(TestResult("media_limit", True, f"Respects 4-file limit"))
            else:
                self.results.append(TestResult("media_limit", False, f"Exceeds 4-file limit: {len(discovered_media)}"))
                
        except Exception as e:
            self.results.append(TestResult("media_discovery", False, f"Error: {e}"))
    
    async def test_content_generation_integration(self):
        """Test complete content generation flow (without API calls)."""
        print(f"\n{Colors.CYAN}🔄 Testing Content Generation Integration{Colors.END}")
        
        try:
            config = self._create_test_config()
            
            # Mock the AI generation to avoid actual API calls
            original_generate_text = self.generator._generate_text
            self.generator._generate_text = self._mock_generate_text
            
            # Test content generation for different platforms
            platforms = ["twitter", "bluesky", "linkedin"]
            for platform in platforms:
                try:
                    content = await self.generator.generate_content(config, platform)
                    
                    # Validate content structure
                    required_keys = ["text", "media", "hashtags", "platform"]
                    missing_keys = [key for key in required_keys if key not in content]
                    
                    if not missing_keys:
                        self.results.append(TestResult(f"content_structure_{platform}", True, f"{platform}: All keys present"))
                    else:
                        self.results.append(TestResult(f"content_structure_{platform}", False, f"{platform}: Missing {missing_keys}"))
                    
                    # Validate content length
                    char_limit = self.generator._get_platform_char_limit(platform)
                    if len(content["text"]) <= char_limit:
                        self.results.append(TestResult(f"content_length_{platform}", True, f"{platform}: Within limits"))
                    else:
                        self.results.append(TestResult(f"content_length_{platform}", False, f"{platform}: Too long"))
                        
                except Exception as e:
                    self.results.append(TestResult(f"content_generation_{platform}", False, f"Error: {e}"))
            
            # Restore original method
            self.generator._generate_text = original_generate_text
            
        except Exception as e:
            self.results.append(TestResult("content_integration", False, f"Error: {e}"))
    
    async def _mock_generate_text(self, prompt: str, config, platform: str) -> str:
        """Mock AI text generation for testing."""
        return f"🚀 Introducing {config.name} - {config.concept}! Check it out!"
    
    def _create_test_config(self) -> CampaignConfig:
        """Create a test campaign configuration."""
        content_config = ContentConfig(
            style="casual",
            action="Check it out!",
            hashtags=["#test", "#app"],
            language="en",
            max_length=280
        )
        
        return CampaignConfig(
            name="TestApp",
            concept="Revolutionary productivity app for developers",
            url="https://testapp.com",
            content=content_config,
            image="auto",
            platforms=["twitter", "bluesky", "linkedin"]  # Add required platforms field
        )
    
    def print_results(self):
        """Print comprehensive test results."""
        print(f"\n{Colors.BOLD}📊 CONTENT GENERATOR TEST RESULTS{Colors.END}")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        # Group results by category
        categories = {}
        for result in self.results:
            category = result.name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Print results by category
        for category, results in sorted(categories.items()):
            print(f"\n{Colors.CYAN}🔧 {category.upper()} TESTS{Colors.END}")
            for result in results:
                if result.passed:
                    print(f"  {Colors.GREEN}✅ {result.name}{Colors.END}: {result.message}")
                    passed += 1
                else:
                    print(f"  {Colors.RED}❌ {result.name}{Colors.END}: {result.message}")
                    failed += 1
        
        # Summary
        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}SUMMARY{Colors.END}")
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"Pass Rate: {Colors.GREEN if pass_rate >= 80 else Colors.YELLOW}{pass_rate:.1f}%{Colors.END}")
        
        if pass_rate >= 90:
            print(f"\n{Colors.GREEN}🎉 EXCELLENT! Content Generator is working great!{Colors.END}")
        elif pass_rate >= 80:
            print(f"\n{Colors.YELLOW}👍 GOOD! Content Generator is mostly working well.{Colors.END}")
        else:
            print(f"\n{Colors.RED}⚠️  NEEDS WORK! Content Generator has some issues.{Colors.END}")
        
        return pass_rate >= 80

async def main():
    """Run comprehensive Content Generator tests."""
    print(f"{Colors.BOLD}🧪 AetherPost Content Generator Test Suite{Colors.END}")
    print(f"{Colors.BLUE}Testing all aspects of content generation functionality...{Colors.END}")
    
    tester = ContentGeneratorTester()
    
    try:
        # Setup test environment
        tester.setup()
        
        # Run all tests
        tester.test_provider_setup()
        tester.test_cache_functionality()
        tester.test_platform_optimization()
        tester.test_style_variations()
        tester.test_language_support()
        tester.test_prompt_building()
        tester.test_hashtag_generation()
        tester.test_fallback_content()
        tester.test_media_discovery()
        await tester.test_content_generation_integration()
        
        # Print results
        success = tester.print_results()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"{Colors.RED}❌ Test suite failed: {e}{Colors.END}")
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)