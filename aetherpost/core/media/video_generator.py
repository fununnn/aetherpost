"""Video generation utilities for promotional content."""

import asyncio
from typing import Dict, Any, Optional, List
import logging
import hashlib
import os
from datetime import datetime

from .audio_generator import AudioGenerator

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Video generation for promotional content."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cache_dir = self.config.get('cache_dir', '/tmp/autopromo_video')
        self.audio_generator = AudioGenerator(config)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def create_text_video(self, content: Dict[str, Any]) -> str:
        """Create video from text content."""
        try:
            text = content['text']
            style = content.get('style', 'modern')
            duration = content.get('duration', 30)
            
            # キャッシュチェック
            cache_key = self._get_cache_key(content)
            video_path = os.path.join(self.cache_dir, f"{cache_key}.mp4")
            
            if os.path.exists(video_path):
                logger.info(f"Using cached video: {cache_key}")
                return video_path
            
            # 音声生成
            voice_config = content.get('voice_config', {
                'voice': 'professional',
                'speed': 1.0,
                'language': 'ja-JP'
            })
            audio_path = await self.audio_generator.text_to_speech(text, voice_config)
            
            # 背景音楽
            if content.get('background_music', True):
                music_path = await self.audio_generator.create_background_music(duration, 'modern')
                audio_path = await self.audio_generator.mix_audio(audio_path, music_path)
            
            # 動画生成
            video_config = {
                'style': style,
                'duration': duration,
                'text': text,
                'audio_path': audio_path,
                'effects': content.get('effects', ['fade_in', 'text_animation'])
            }
            
            await self._generate_video(video_config, video_path)
            
            logger.info(f"Generated video: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    async def create_shorts_video(self, content: Dict[str, Any]) -> str:
        """Create vertical short-form video (TikTok/YouTube Shorts)."""
        try:
            text = content['text']
            hook = content.get('hook', 'これ知らないとヤバい...')
            cta = content.get('cta', '保存して後で見返そう！')
            
            # Shorts用設定
            shorts_config = {
                'text': f"{hook}\n\n{text}\n\n{cta}",
                'style': 'viral_shorts',
                'duration': min(content.get('duration', 15), 60),  # 最大60秒
                'aspect_ratio': '9:16',  # 縦型
                'effects': ['quick_cuts', 'text_overlay', 'zoom_in', 'trendy_transitions'],
                'voice_config': {
                    'voice': 'energetic',
                    'speed': 1.1,
                    'language': 'ja-JP'
                },
                'background_music': True,
                'trending_elements': content.get('trending_elements', True)
            }
            
            return await self.create_text_video(shorts_config)
            
        except Exception as e:
            logger.error(f"Shorts video generation failed: {e}")
            raise
    
    async def create_slideshow_video(self, slides: List[Dict[str, Any]]) -> str:
        """Create slideshow video from multiple slides."""
        try:
            slide_videos = []
            
            for i, slide in enumerate(slides):
                slide_config = {
                    'text': slide['text'],
                    'style': slide.get('style', 'presentation'),
                    'duration': slide.get('duration', 5),
                    'background': slide.get('background', 'gradient'),
                    'transition': slide.get('transition', 'fade')
                }
                
                slide_video = await self._create_slide(slide_config, i)
                slide_videos.append(slide_video)
            
            # スライド結合
            final_video = await self._concatenate_videos(slide_videos)
            
            logger.info(f"Created slideshow video: {final_video}")
            return final_video
            
        except Exception as e:
            logger.error(f"Slideshow video creation failed: {e}")
            raise
    
    async def create_tutorial_video(self, tutorial_data: Dict[str, Any]) -> str:
        """Create tutorial/how-to video."""
        try:
            title = tutorial_data['title']
            steps = tutorial_data['steps']
            
            # イントロスライド
            intro_slide = {
                'text': f"{title}\n\n今日は{len(steps)}ステップで解説します！",
                'style': 'tutorial_intro',
                'duration': 3
            }
            
            # ステップスライド
            step_slides = []
            for i, step in enumerate(steps, 1):
                step_slide = {
                    'text': f"ステップ{i}: {step['title']}\n\n{step['description']}",
                    'style': 'tutorial_step',
                    'duration': step.get('duration', 8),
                    'code': step.get('code'),  # コードサンプルがある場合
                }
                step_slides.append(step_slide)
            
            # アウトロスライド
            outro_slide = {
                'text': "お疲れ様でした！\n\n役に立ったらコメント、シェアお願いします！",
                'style': 'tutorial_outro',
                'duration': 3
            }
            
            all_slides = [intro_slide] + step_slides + [outro_slide]
            return await self.create_slideshow_video(all_slides)
            
        except Exception as e:
            logger.error(f"Tutorial video creation failed: {e}")
            raise
    
    def _get_cache_key(self, content: Dict[str, Any]) -> str:
        """Generate cache key for video."""
        # コンテンツのハッシュを生成
        content_str = str(sorted(content.items()))
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def _generate_video(self, config: Dict[str, Any], output_path: str):
        """Generate video file (implementation placeholder)."""
        # 実際の実装では以下のツールを使用:
        # - FFmpeg for video processing
        # - Remotion for programmatic video creation
        # - Runway ML API for AI video generation
        # - Synthesia API for AI avatar videos
        # - Loom API for screen recording
        
        style_templates = {
            'modern': {
                'background': 'gradient_animation',
                'font': 'modern_sans',
                'colors': ['#667eea', '#764ba2'],
                'animations': ['fade_in', 'slide_up']
            },
            'viral_shorts': {
                'background': 'dynamic_shapes',
                'font': 'bold_impact',
                'colors': ['#ff6b6b', '#4ecdc4'],
                'animations': ['zoom_in', 'quick_cuts', 'text_pop']
            },
            'presentation': {
                'background': 'clean_white',
                'font': 'professional',
                'colors': ['#2c3e50', '#3498db'],
                'animations': ['fade_in', 'smooth_transition']
            },
            'tutorial_intro': {
                'background': 'tech_grid',
                'font': 'title_font',
                'colors': ['#1e3c72', '#2a5298']
            },
            'tutorial_step': {
                'background': 'code_editor',
                'font': 'monospace',
                'colors': ['#282c34', '#61dafb']
            },
            'tutorial_outro': {
                'background': 'celebration',
                'font': 'friendly',
                'colors': ['#fd79a8', '#fdcb6e']
            }
        }
        
        template = style_templates.get(config['style'], style_templates['modern'])
        
        # モック実装
        await asyncio.sleep(2)  # 生成時間シミュレーション
        
        # ダミーファイル作成
        with open(output_path, 'w') as f:
            f.write(f"# Video file\n")
            f.write(f"# Text: {config['text'][:50]}...\n")
            f.write(f"# Style: {config['style']}\n")
            f.write(f"# Duration: {config['duration']}s\n")
            f.write(f"# Template: {template}\n")
            f.write(f"# Generated: {datetime.now()}\n")
    
    async def _create_slide(self, slide_config: Dict[str, Any], slide_number: int) -> str:
        """Create individual slide video."""
        output_path = os.path.join(self.cache_dir, f"slide_{slide_number}_{hashlib.md5(str(slide_config).encode()).hexdigest()}.mp4")
        
        if os.path.exists(output_path):
            return output_path
        
        await self._generate_video(slide_config, output_path)
        return output_path
    
    async def _concatenate_videos(self, video_files: List[str]) -> str:
        """Concatenate multiple video files."""
        output_path = os.path.join(self.cache_dir, f"concatenated_{hashlib.md5(str(video_files).encode()).hexdigest()}.mp4")
        
        if os.path.exists(output_path):
            return output_path
        
        # FFmpeg等を使用した実装
        await asyncio.sleep(1)
        
        with open(output_path, 'w') as f:
            f.write(f"# Concatenated video from {len(video_files)} segments\n")
            f.write(f"# Generated: {datetime.now()}\n")
        
        return output_path


class LiveStreamGenerator(VideoGenerator):
    """Live streaming and real-time video generation."""
    
    async def create_stream_overlay(self, stream_data: Dict[str, Any]) -> str:
        """Create overlay graphics for live streams."""
        try:
            overlay_config = {
                'title': stream_data.get('title', 'ライブ配信中'),
                'viewer_count': stream_data.get('viewer_count', 0),
                'chat_messages': stream_data.get('recent_chat', []),
                'alerts': stream_data.get('alerts', []),
                'style': 'live_overlay'
            }
            
            return await self._create_overlay(overlay_config)
            
        except Exception as e:
            logger.error(f"Stream overlay creation failed: {e}")
            raise
    
    async def _create_overlay(self, config: Dict[str, Any]) -> str:
        """Create overlay graphics."""
        output_path = os.path.join(self.cache_dir, f"overlay_{hashlib.md5(str(config).encode()).hexdigest()}.png")
        
        # OBS Studio等で使用するオーバーレイ画像生成
        await asyncio.sleep(0.5)
        
        with open(output_path, 'w') as f:
            f.write(f"# Overlay graphics\n")
            f.write(f"# Title: {config['title']}\n")
            f.write(f"# Generated: {datetime.now()}\n")
        
        return output_path