"""OpenAI API provider implementation."""

import asyncio
from typing import Dict, Any

try:
    import openai
except ImportError:
    openai = None

from ...base import AIProviderBase


class OpenAIProvider(AIProviderBase):
    """OpenAI API provider for text generation."""
    
    def __init__(self, config: Dict[str, Any]):
        if openai is None:
            raise ImportError("openai is required for OpenAI provider. Install with: pip install openai")
        
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.config = config
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate text using OpenAI API."""
        try:
            # Merge default config with request config
            merged_config = {**self.config, **config}
            
            # Prepare messages for ChatGPT
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional social media content creator. Generate engaging, authentic posts that sound natural and avoid being overly promotional."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=merged_config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=merged_config.get("max_tokens", 300),
                temperature=merged_config.get("temperature", 0.7),
                top_p=merged_config.get("top_p", 1.0),
                frequency_penalty=merged_config.get("frequency_penalty", 0.0),
                presence_penalty=merged_config.get("presence_penalty", 0.0),
                seed=merged_config.get("seed")  # For deterministic generation
            )
            
            # Extract generated text
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content.strip()
            else:
                raise Exception("No response generated")
                
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def generate_image_prompt(self, content: str, style: str = "photorealistic") -> str:
        """Generate image prompt using OpenAI."""
        try:
            prompt = f"""Create a detailed image prompt for DALL-E based on this social media content:

Content: {content}
Style: {style}

Generate a prompt that would create an appropriate, eye-catching image for this social media post. The image should be relevant, professional, and engaging. Keep the prompt under 1000 characters.

Image prompt:"""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating image prompts for AI image generation. Create detailed, specific prompts that result in high-quality, relevant images."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=200,
                temperature=0.8
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("No image prompt generated")
                
        except Exception as e:
            raise Exception(f"OpenAI image prompt error: {e}")
    
    async def generate_hashtags(self, content: str, platform: str, count: int = 5) -> list[str]:
        """Generate relevant hashtags using OpenAI."""
        try:
            prompt = f"""Generate {count} relevant, trending hashtags for this {platform} post:

Content: {content}

Requirements:
- Make hashtags specific and relevant
- Include a mix of broad and niche tags
- Avoid overly generic hashtags
- Consider current trends
- Format: return only hashtags separated by spaces, with # symbols

Hashtags:"""

            messages = [
                {
                    "role": "system",
                    "content": "You are a social media expert who knows which hashtags work best for different platforms and content types."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            if response.choices and len(response.choices) > 0:
                hashtag_text = response.choices[0].message.content.strip()
                # Parse hashtags from response
                hashtags = [tag.strip() for tag in hashtag_text.split() if tag.startswith('#')]
                return hashtags[:count]
            else:
                return []
                
        except Exception as e:
            print(f"OpenAI hashtag generation error: {e}")
            return []
    
    async def improve_content(self, content: str, platform: str, feedback: str) -> str:
        """Improve content based on feedback using OpenAI."""
        try:
            prompt = f"""Improve this {platform} post based on the feedback provided:

Original Content: {content}
Feedback: {feedback}

Please rewrite the content to address the feedback while maintaining the core message and appropriate tone for {platform}. Keep within platform character limits.

Improved Content:"""

            messages = [
                {
                    "role": "system",
                    "content": "You are a professional social media content editor. Improve content based on feedback while maintaining authenticity and engagement."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return content  # Return original if improvement fails
                
        except Exception as e:
            print(f"OpenAI content improvement error: {e}")
            return content