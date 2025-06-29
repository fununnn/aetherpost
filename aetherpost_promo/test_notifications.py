#!/usr/bin/env python3
"""Test notification system functionality."""

import os
import sys
import asyncio
from pathlib import Path

# Add the aetherpost_source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

from core.preview.notifiers import LINENotifier, SlackNotifier, NotificationChannel
from core.preview.generator import ContentPreviewGenerator
from core.config.parser import ConfigLoader

async def test_notification_system():
    """Test the notification system with mock data."""
    print("🧪 Testing AetherPost Notification System")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.aetherpost')
    
    # Test 1: Environment Variables
    print("\n📋 Environment Variables Check:")
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    line_token = os.getenv('LINE_NOTIFY_TOKEN')
    
    print(f"SLACK_WEBHOOK_URL: {'✅ Set' if slack_webhook else '❌ Missing'}")
    print(f"LINE_NOTIFY_TOKEN: {'✅ Set' if line_token else '❌ Missing'}")
    
    # Test 2: Campaign Config Loading
    print("\n📋 Campaign Configuration Check:")
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config("campaign.yaml")
        
        print(f"✅ Config loaded: {config.name}")
        print(f"✅ Config attributes: {[attr for attr in dir(config) if not attr.startswith('_')]}")
        
        notifications = getattr(config, 'notifications', None)
        if notifications:
            if hasattr(notifications, 'get'):
                print(f"✅ Notifications enabled: {notifications.get('enabled', False)}")
                print(f"✅ Auto apply: {notifications.get('auto_apply', False)}")
                channels = notifications.get('channels', {})
                print(f"✅ Configured channels: {list(channels.keys())}")
            else:
                print(f"✅ Notifications object: {notifications}")
        else:
            print("❌ No notifications configuration found")
            
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        return
    
    # Test 3: Create Preview Session
    print("\n📋 Preview Session Creation:")
    try:
        preview_generator = ContentPreviewGenerator()
        
        # Mock content items
        content_items = [
            {
                'platform': 'twitter',
                'text': '🚀 Testing AetherPost notification system! This is a mock Twitter post to verify our Slack/LINE integration works correctly. #AetherPost #Testing',
                'character_count': 150,
                'estimated_reach': 1500
            },
            {
                'platform': 'bluesky',
                'text': '🔵 AetherPost notification test on Bluesky! Checking if our preview system correctly handles multiple platforms and sends proper notifications.',
                'character_count': 140,
                'estimated_reach': 800
            }
        ]
        
        session = preview_generator.create_preview_session("AetherPost Test", content_items)
        print(f"✅ Preview session created: {session.session_id}")
        print(f"✅ Campaign: {session.campaign_name}")
        print(f"✅ Total platforms: {session.total_platforms}")
        print(f"✅ Estimated reach: {session.total_estimated_reach:,}")
        
    except Exception as e:
        print(f"❌ Preview session creation error: {e}")
        return
    
    # Test 4: LINE Notifier
    print("\n📋 LINE Notifier Test:")
    if line_token:
        try:
            line_notifier = LINENotifier(line_token)
            line_channel = NotificationChannel(
                name="line_test",
                type="line",
                webhook_url=line_token,
                enabled=True
            )
            
            # This will fail with mock token, but we can test the formatting
            message = line_notifier._format_line_message(session)
            print(f"✅ LINE message formatted ({len(message)} chars)")
            print("📝 LINE Message Preview:")
            print("-" * 40)
            print(message)
            print("-" * 40)
            
            # Test actual sending (will fail with mock token)
            try:
                result = await line_notifier.send_preview(session, line_channel)
                print(f"LINE send result: {result}")
            except Exception as e:
                print(f"⚠️ LINE send failed (expected with mock token): {type(e).__name__}")
                
        except Exception as e:
            print(f"❌ LINE notifier error: {e}")
    else:
        print("⚠️ Skipping LINE test - no token configured")
    
    # Test 5: Slack Notifier  
    print("\n📋 Slack Notifier Test:")
    if slack_webhook:
        try:
            slack_notifier = SlackNotifier(slack_webhook)
            slack_channel = NotificationChannel(
                name="slack_test",
                type="slack",
                webhook_url=slack_webhook,
                channel_id="#dev-updates",
                enabled=True
            )
            
            # Test block generation
            blocks = preview_generator.generate_slack_blocks(session)
            print(f"✅ Slack blocks generated ({len(blocks)} blocks)")
            
            # Test actual sending (will fail with mock webhook)
            try:
                result = await slack_notifier.send_preview(session, slack_channel)
                print(f"Slack send result: {result}")
            except Exception as e:
                print(f"⚠️ Slack send failed (expected with mock webhook): {type(e).__name__}")
                
        except Exception as e:
            print(f"❌ Slack notifier error: {e}")
    else:
        print("⚠️ Skipping Slack test - no webhook configured")
    
    # Test 6: Apply Command Integration Test
    print("\n📋 Apply Command Integration Test:")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))
        from cli.commands.apply import send_real_preview_notification
        
        # Create a mock config object
        class MockConfig:
            def __init__(self):
                self.name = "AetherPost"
                self.notifications = notifications
        
        mock_config = MockConfig()
        platforms = ['twitter', 'bluesky']
        
        print("🔄 Testing apply command notification integration...")
        result = await send_real_preview_notification(mock_config, platforms, content_items)
        
        print(f"✅ Apply integration test result: {result}")
        
    except Exception as e:
        print(f"❌ Apply integration test error: {e}")
    
    print("\n🎉 Notification system test completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_notification_system())