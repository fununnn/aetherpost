"""AI-powered avatar/icon generation for social media profiles."""

import asyncio
import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class AvatarGenerator:
    """AI-powered avatar generation using OpenAI DALL-E 3."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize the avatar generator.
        
        Args:
            credentials: Dictionary containing OpenAI credentials
        """
        self.credentials = credentials
        self.openai_client = None
        self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI client if credentials available."""
        openai_creds = self.credentials.get('openai', {})
        api_key = openai_creds.get('api_key')
        
        if api_key and api_key != "test-openai-key":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for avatar generation")
            except ImportError:
                logger.warning("OpenAI library not available. Install with: pip install openai")
            except Exception as e:
                logger.warning(f"Failed to setup OpenAI client: {e}")
    
    async def generate_avatar(self, name: str, description: str, output_path: str = "avatar.png") -> bool:
        """Generate an AI avatar for the project.
        
        Args:
            name: Project/app name
            description: Project description
            output_path: Path to save the generated avatar
            
        Returns:
            bool: True if avatar generated successfully, False otherwise
        """
        # Check if avatar already exists
        if os.path.exists(output_path):
            logger.info(f"Avatar already exists at {output_path}, skipping generation")
            return True
        
        # Try OpenAI DALL-E 3 generation
        if self.openai_client:
            success = await self._generate_with_dalle(name, description, output_path)
            if success:
                return True
        
        # Fallback to PIL generation
        return self._generate_fallback_avatar(name, description, output_path)
    
    async def _generate_with_dalle(self, name: str, description: str, output_path: str) -> bool:
        """Generate avatar using OpenAI DALL-E 3."""
        try:
            # Build optimized prompt for logo generation
            prompt = self._build_avatar_prompt(name, description)
            
            logger.info(f"Generating avatar with DALL-E 3 for {name}")
            
            # Generate image
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                style="vivid",
                n=1
            )
            
            # Download and save image
            image_url = response.data[0].url
            image_response = requests.get(image_url, timeout=30)
            
            if image_response.status_code == 200:
                # Resize to 400x400 for social media optimization
                import io
                from PIL import Image
                
                image = Image.open(io.BytesIO(image_response.content))
                image = image.resize((400, 400), Image.Resampling.LANCZOS)
                image.save(output_path, "PNG")
                
                logger.info(f"Avatar generated successfully: {output_path}")
                return True
            else:
                logger.error(f"Failed to download generated image: {image_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"DALL-E 3 avatar generation failed: {e}")
            return False
    
    def _build_avatar_prompt(self, name: str, description: str) -> str:
        """Build optimized prompt for avatar generation."""
        prompt = f"""Professional logo design for "{name}": {description}. 
        
Style requirements:
- Clean, minimal, modern design
- High contrast for social media visibility
- Geometric shapes or simple icon-based design
- Suitable for use as profile picture/avatar
- Tech company or app aesthetic
- Square format optimized for social platforms
- Bold, readable design that works at small sizes
- Professional but approachable feel

Color: Use vibrant but professional colors. Avoid too many colors - 2-3 maximum.
Background: Clean background that contrasts well with the main design elements.
Text: Minimal or no text - focus on iconic symbol/logo design.
"""
        return prompt
    
    def _generate_fallback_avatar(self, name: str, description: str, output_path: str) -> bool:
        """Generate simple fallback avatar using PIL."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create 400x400 image with gradient background
            size = (400, 400)
            image = Image.new('RGB', size, color=(41, 128, 185))  # Blue background
            draw = ImageDraw.Draw(image)
            
            # Add gradient effect
            for y in range(size[1]):
                gradient_color = int(41 + (85 * y / size[1]))  # Gradient from 41 to 126
                draw.line([(0, y), (size[0], y)], fill=(gradient_color, 128, 185))
            
            # Get first letter of name for the icon
            letter = name[0].upper() if name else "A"
            
            # Try to use a large font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 200)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 200)
                except:
                    font = ImageFont.load_default()
            
            # Get text bounding box and center the text
            bbox = draw.textbbox((0, 0), letter, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            # Add white text with shadow
            draw.text((x+3, y+3), letter, font=font, fill=(0, 0, 0, 128))  # Shadow
            draw.text((x, y), letter, font=font, fill=(255, 255, 255))      # Main text
            
            # Save the image
            image.save(output_path, "PNG")
            
            logger.info(f"Fallback avatar generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fallback avatar generation failed: {e}")
            return False
    
    def get_avatar_path(self, default_name: str = "avatar.png") -> Optional[str]:
        """Get path to existing avatar file."""
        if os.path.exists(default_name):
            return default_name
        return None


async def get_or_generate_avatar(config, credentials, force_generate: bool = False) -> Optional[str]:
    """Get existing avatar or generate new one if needed.
    
    Args:
        config: Campaign configuration containing name and concept
        credentials: Credentials dictionary with OpenAI API key
        force_generate: Force generation even if avatar exists
        
    Returns:
        str: Path to avatar file, or None if generation failed
    """
    avatar_path = "avatar.png"
    
    # Check if avatar already exists
    if os.path.exists(avatar_path) and not force_generate:
        logger.info(f"Using existing avatar: {avatar_path}")
        return avatar_path
    
    # Generate new avatar
    generator = AvatarGenerator(credentials)
    
    name = getattr(config, 'name', 'AetherPost')
    description = getattr(config, 'concept', getattr(config, 'description', 'Social media automation tool'))
    
    success = await generator.generate_avatar(name, description, avatar_path)
    
    if success:
        return avatar_path
    else:
        logger.error("Avatar generation failed")
        return None