"""Reddit connector implementation."""

import asyncio
from typing import Dict, Any, Optional, List
import logging
import re

try:
    import praw
    from praw.exceptions import RedditAPIException, PRAWException
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    praw = None

from ...base import BaseConnector

logger = logging.getLogger(__name__)


class RedditConnector(BaseConnector):
    """Reddit connector for community-based promotion."""
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        
        if not PRAW_AVAILABLE:
            raise ImportError("PRAW library is required for Reddit connector. Install with: pip install praw>=7.0.0")
        
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.username = credentials.get('username')
        self.password = credentials.get('password')
        self.user_agent = credentials.get('user_agent', 'AetherPost/1.0')
        self.reddit = None
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Reddit API."""
        try:
            logger.info("Authenticating with Reddit API")
            
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
            
            # Test authentication by getting user info
            user = self.reddit.user.me()
            logger.info(f"Successfully authenticated as Reddit user: {user.name}")
            return True
            
        except PRAWException as e:
            logger.error(f"Reddit authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected Reddit authentication error: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post to Reddit with subreddit optimization."""
        try:
            text_content = content.get('text', '')
            post_type = content.get('type', 'text')
            
            # 1. 適切なサブレディット検索
            subreddits = await self._find_relevant_subreddits(text_content)
            
            # 2. サブレディット別コンテンツ最適化
            optimized_posts = []
            
            for subreddit in subreddits[:3]:  # 最大3つのサブレディットに投稿
                optimized_content = await self._optimize_for_subreddit(
                    text_content, subreddit, post_type
                )
                
                post_result = await self._submit_post(subreddit, optimized_content)
                optimized_posts.append(post_result)
            
            return {
                'status': 'published',
                'platform': 'reddit',
                'posts': optimized_posts,
                'subreddits_posted': [post['subreddit'] for post in optimized_posts]
            }
            
        except Exception as e:
            logger.error(f"Reddit post failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _find_relevant_subreddits(self, content: str) -> List[str]:
        """コンテンツに関連するサブレディットを検索."""
        
        # テック・プログラミング関連サブレディット
        tech_subreddits = {
            'programming': ['code', 'program', 'development', 'software'],
            'webdev': ['web', 'frontend', 'backend', 'html', 'css', 'javascript'],
            'javascript': ['js', 'javascript', 'react', 'node'],
            'python': ['python', 'django', 'flask'],
            'MachineLearning': ['ai', 'ml', 'machine learning', 'deep learning'],
            'startups': ['startup', 'entrepreneur', 'business'],
            'technology': ['tech', 'innovation', 'digital'],
            'SideProject': ['side project', 'project', 'app', 'tool'],
            'learnprogramming': ['learn', 'tutorial', 'beginner', 'help'],
            'cscareerquestions': ['career', 'job', 'interview', 'salary'],
            'opensource': ['open source', 'github', 'oss'],
            'devtools': ['tool', 'development tool', 'productivity']
        }
        
        content_lower = content.lower()
        relevant_subreddits = []
        
        # キーワードマッチング
        for subreddit, keywords in tech_subreddits.items():
            if any(keyword in content_lower for keyword in keywords):
                relevant_subreddits.append(subreddit)
        
        # デフォルトサブレディット（キーワードマッチしない場合）
        if not relevant_subreddits:
            relevant_subreddits = ['technology', 'programming', 'SideProject']
        
        return relevant_subreddits
    
    async def _optimize_for_subreddit(self, content: str, subreddit: str, post_type: str) -> Dict[str, Any]:
        """サブレディット固有のルールに合わせてコンテンツ最適化."""
        
        # サブレディット別最適化ルール
        subreddit_rules = {
            'programming': {
                'title_style': 'technical_focus',
                'tone': 'informative',
                'required_tags': [],
                'avoid_words': ['promotion', 'marketing', 'buy']
            },
            'webdev': {
                'title_style': 'project_showcase',
                'tone': 'collaborative',
                'required_tags': ['[Project]', '[Help]', '[Discussion]'],
                'avoid_words': ['spam', 'advertisement']
            },
            'SideProject': {
                'title_style': 'project_announcement',
                'tone': 'enthusiastic',
                'required_tags': [],
                'avoid_words': []
            },
            'startups': {
                'title_style': 'business_focus',
                'tone': 'professional',
                'required_tags': [],
                'avoid_words': ['get rich', 'easy money']
            },
            'learnprogramming': {
                'title_style': 'educational',
                'tone': 'helpful',
                'required_tags': [],
                'avoid_words': ['expert', 'advanced only']
            }
        }
        
        rules = subreddit_rules.get(subreddit, subreddit_rules['programming'])
        
        # タイトル生成
        title = await self._generate_subreddit_title(content, rules)
        
        # 本文最適化
        body = await self._optimize_post_body(content, rules)
        
        return {
            'subreddit': subreddit,
            'title': title,
            'body': body,
            'type': post_type,
            'flair': self._suggest_flair(subreddit, content)
        }
    
    async def _generate_subreddit_title(self, content: str, rules: Dict[str, Any]) -> str:
        """サブレディット向けタイトル生成."""
        
        title_styles = {
            'technical_focus': "New {project}: {description}",
            'project_showcase': "Built a {project} - {description}",
            'project_announcement': "Launched: {project} - {description}",
            'business_focus': "Startup Update: {project} - {description}",
            'educational': "Learning Resource: {project} - {description}"
        }
        
        # コンテンツから重要な情報を抽出
        project_name = self._extract_project_name(content)
        description = self._extract_description(content)
        
        style = rules['title_style']
        template = title_styles.get(style, title_styles['technical_focus'])
        
        title = template.format(
            project=project_name,
            description=description[:50] + "..." if len(description) > 50 else description
        )
        
        return title
    
    async def _optimize_post_body(self, content: str, rules: Dict[str, Any]) -> str:
        """投稿本文最適化."""
        
        # 避けるべき単語をチェック
        avoid_words = rules.get('avoid_words', [])
        optimized_content = content
        
        for word in avoid_words:
            if word in optimized_content.lower():
                # より中立的な表現に置き換え
                replacements = {
                    'promotion': 'sharing',
                    'marketing': 'introduction',
                    'buy': 'try',
                    'spam': 'content',
                    'advertisement': 'announcement'
                }
                replacement = replacements.get(word, 'project')
                optimized_content = re.sub(word, replacement, optimized_content, flags=re.IGNORECASE)
        
        # Reddit形式のフォーマット追加
        reddit_formatted = f"{optimized_content}\n\n"
        
        # 技術詳細の追加
        reddit_formatted += "**Technical Details:**\n"
        reddit_formatted += "- Built with: [Technology Stack]\n"
        reddit_formatted += "- Features: [Key Features]\n"
        reddit_formatted += "- GitHub: [Repository Link]\n\n"
        
        # コミュニティへの貢献意図を明示
        reddit_formatted += "Happy to answer any questions or receive feedback from the community!\n"
        
        return reddit_formatted
    
    def _extract_project_name(self, content: str) -> str:
        """プロジェクト名を抽出."""
        # 簡単なヒューリスティック
        lines = content.split('\n')
        first_line = lines[0] if lines else content
        
        # 最初の10単語以内からプロジェクト名を推測
        words = first_line.split()[:10]
        return ' '.join(words[:3])  # 最初の3単語
    
    def _extract_description(self, content: str) -> str:
        """説明文を抽出."""
        # 最初の50文字程度を説明として使用
        return content[:100].replace('\n', ' ').strip()
    
    def _suggest_flair(self, subreddit: str, content: str) -> Optional[str]:
        """適切なフレアを提案."""
        
        flair_mapping = {
            'programming': {
                'showcase': ['project', 'app', 'built'],
                'discussion': ['question', 'help', 'advice'],
                'news': ['announcement', 'release', 'update']
            },
            'webdev': {
                'project': ['project', 'site', 'app'],
                'help': ['question', 'help', 'stuck'],
                'resource': ['tool', 'library', 'framework']
            }
        }
        
        content_lower = content.lower()
        subreddit_flairs = flair_mapping.get(subreddit, {})
        
        for flair, keywords in subreddit_flairs.items():
            if any(keyword in content_lower for keyword in keywords):
                return flair
        
        return None
    
    async def _submit_post(self, subreddit: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reddit投稿実行."""
        try:
            if not self.reddit:
                raise Exception("Reddit client not authenticated")
            
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            # Check if subreddit exists and is accessible
            try:
                subreddit_obj.display_name  # This will raise an exception if subreddit doesn't exist
            except Exception:
                logger.warning(f"Subreddit r/{subreddit} not accessible, falling back to general tech subreddit")
                subreddit_obj = self.reddit.subreddit('technology')
                subreddit = 'technology'
            
            # Submit the post
            submission = subreddit_obj.submit(
                title=post_data['title'],
                selftext=post_data['body'],
                flair_text=post_data.get('flair')
            )
            
            # Add rate limiting delay
            await asyncio.sleep(2)  # Reddit rate limiting
            
            return {
                'subreddit': subreddit,
                'post_id': submission.id,
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'title': post_data['title'],
                'flair': post_data.get('flair'),
                'status': 'posted',
                'created_utc': submission.created_utc
            }
            
        except RedditAPIException as e:
            logger.error(f"Reddit API error for r/{subreddit}: {e}")
            return {
                'subreddit': subreddit,
                'status': 'failed',
                'error': f"Reddit API error: {str(e)}",
                'error_type': 'api_error'
            }
        except Exception as e:
            logger.error(f"Failed to submit post to r/{subreddit}: {e}")
            return {
                'subreddit': subreddit,
                'status': 'failed',
                'error': str(e),
                'error_type': 'submission_error'
            }
    
    async def get_subreddit_analytics(self, subreddit: str) -> Dict[str, Any]:
        """サブレディット分析情報取得."""
        try:
            if not self.reddit:
                raise Exception("Reddit client not authenticated")
            
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            return {
                'subreddit': subreddit,
                'subscribers': subreddit_obj.subscribers,
                'active_users': subreddit_obj.active_user_count,
                'display_name': subreddit_obj.display_name,
                'description': subreddit_obj.public_description,
                'created_utc': subreddit_obj.created_utc,
                'over18': subreddit_obj.over18,
                'submission_type': subreddit_obj.submission_type,
                'best_posting_time': '14:00-18:00 UTC',  # Would need historical analysis
                'popular_post_types': ['text', 'link', 'image'],
                'engagement_rate': 0.12  # Would need historical analysis
            }
        except Exception as e:
            logger.error(f"Failed to get analytics for r/{subreddit}: {e}")
            return {
                'subreddit': subreddit,
                'error': str(e),
                'status': 'failed'
            }
    
    async def monitor_post_performance(self, post_id: str) -> Dict[str, Any]:
        """投稿パフォーマンス監視."""
        try:
            if not self.reddit:
                raise Exception("Reddit client not authenticated")
            
            submission = self.reddit.submission(id=post_id)
            
            return {
                'post_id': post_id,
                'title': submission.title,
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'awards': len(submission.all_awardings) if hasattr(submission, 'all_awardings') else 0,
                'created_utc': submission.created_utc,
                'subreddit': submission.subreddit.display_name,
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'is_self': submission.is_self,
                'engagement_score': (submission.score + submission.num_comments) * submission.upvote_ratio
            }
        except Exception as e:
            logger.error(f"Failed to monitor post {post_id}: {e}")
            return {
                'post_id': post_id,
                'error': str(e),
                'status': 'failed'
            }