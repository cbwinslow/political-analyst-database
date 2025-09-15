"""Social media integration module for analyzing politician social media accounts."""

import tweepy
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from textblob import TextBlob
import re

from ..database.models import (
    Politician, SocialMediaAccount, SocialMediaPost, 
    Document, DocumentAnalysis
)
from ..core.config import settings


class TwitterAPIClient:
    """Twitter API client for accessing Twitter data."""
    
    def __init__(self):
        self.api = None
        self.client = None
        self._initialize_twitter_api()
    
    def _initialize_twitter_api(self):
        """Initialize Twitter API client."""
        try:
            # Initialize Twitter API v1.1 (for legacy endpoints)
            auth = tweepy.OAuthHandler(
                settings.twitter.api_key,
                settings.twitter.api_secret
            )
            auth.set_access_token(
                settings.twitter.access_token,
                settings.twitter.access_token_secret
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize Twitter API v2 (for newer endpoints)
            self.client = tweepy.Client(
                bearer_token=settings.twitter.bearer_token,
                consumer_key=settings.twitter.api_key,
                consumer_secret=settings.twitter.api_secret,
                access_token=settings.twitter.access_token,
                access_token_secret=settings.twitter.access_token_secret,
                wait_on_rate_limit=True
            )
            
            print("Twitter API clients initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Twitter API: {e}")
            self.api = None
            self.client = None
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information from Twitter."""
        if not self.client:
            return None
        
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            user = self.client.get_user(
                username=username,
                user_fields=['created_at', 'description', 'followers_count', 
                           'following_count', 'public_metrics', 'verified']
            )
            
            if user.data:
                return {
                    'id': user.data.id,
                    'username': user.data.username,
                    'name': user.data.name,
                    'description': user.data.description,
                    'followers_count': user.data.public_metrics.get('followers_count', 0),
                    'following_count': user.data.public_metrics.get('following_count', 0),
                    'tweet_count': user.data.public_metrics.get('tweet_count', 0),
                    'verified': user.data.verified,
                    'created_at': user.data.created_at
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user info for {username}: {e}")
            return None
    
    def get_user_tweets(self, username: str, count: int = 100, 
                       days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent tweets from a user."""
        if not self.client:
            return []
        
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            # Get user ID first
            user = self.client.get_user(username=username)
            if not user.data:
                return []
            
            user_id = user.data.id
            
            # Calculate date range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Get tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(count, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                start_time=start_time,
                end_time=end_time
            )
            
            tweet_data = []
            if tweets.data:
                for tweet in tweets.data:
                    tweet_info = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                        'like_count': tweet.public_metrics.get('like_count', 0),
                        'reply_count': tweet.public_metrics.get('reply_count', 0),
                        'quote_count': tweet.public_metrics.get('quote_count', 0)
                    }
                    
                    # Add context annotations if available
                    if hasattr(tweet, 'context_annotations') and tweet.context_annotations:
                        tweet_info['context_annotations'] = [
                            {
                                'domain': annotation.domain.name,
                                'entity': annotation.entity.name
                            }
                            for annotation in tweet.context_annotations
                        ]
                    
                    tweet_data.append(tweet_info)
            
            return tweet_data
            
        except Exception as e:
            print(f"Error getting tweets for {username}: {e}")
            return []


class SocialMediaAnalyzer:
    """Analyzes social media content for political insights."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.twitter_client = TwitterAPIClient()
    
    def analyze_tweet_sentiment(self, tweet_text: str) -> Dict[str, Any]:
        """Analyze sentiment of a tweet."""
        try:
            # Clean tweet text
            cleaned_text = self._clean_tweet_text(tweet_text)
            
            # Analyze sentiment
            blob = TextBlob(cleaned_text)
            
            return {
                'polarity': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity,  # 0 to 1
                'sentiment_label': self._get_sentiment_label(blob.sentiment.polarity)
            }
            
        except Exception as e:
            print(f"Error analyzing tweet sentiment: {e}")
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'sentiment_label': 'neutral'
            }
    
    def _clean_tweet_text(self, text: str) -> str:
        """Clean tweet text for analysis."""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags for sentiment analysis
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """Convert polarity score to sentiment label."""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_political_topics(self, tweet_text: str) -> List[str]:
        """Extract political topics from tweet text."""
        topics = []
        text_lower = tweet_text.lower()
        
        # Political keywords mapping
        political_keywords = {
            'healthcare': ['healthcare', 'health care', 'medicare', 'medicaid', 'obamacare', 'aca'],
            'economy': ['economy', 'jobs', 'unemployment', 'recession', 'inflation', 'gdp'],
            'immigration': ['immigration', 'border', 'deportation', 'daca', 'refugee'],
            'climate': ['climate', 'environment', 'global warming', 'green new deal', 'renewable'],
            'gun_control': ['gun control', 'second amendment', 'firearm', 'shooting', 'nra'],
            'abortion': ['abortion', 'roe v wade', 'pro choice', 'pro life', 'reproductive rights'],
            'taxes': ['taxes', 'tax cut', 'tax reform', 'irs', 'tax code'],
            'education': ['education', 'school', 'student loan', 'college', 'university'],
            'foreign_policy': ['foreign policy', 'nato', 'china', 'russia', 'middle east'],
            'election': ['election', 'voting', 'ballot', 'democracy', 'voter']
        }
        
        for topic, keywords in political_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def create_social_media_account(self, politician: Politician, 
                                  platform: str, username: str) -> Optional[SocialMediaAccount]:
        """Create a social media account record for a politician."""
        try:
            # Check if account already exists
            existing_account = self.db.query(SocialMediaAccount).filter(
                SocialMediaAccount.politician_id == politician.id,
                SocialMediaAccount.platform == platform,
                SocialMediaAccount.username == username
            ).first()
            
            if existing_account:
                return existing_account
            
            # Get user info from Twitter API
            user_info = None
            if platform.lower() == 'twitter':
                user_info = self.twitter_client.get_user_info(username)
            
            # Create account record
            account = SocialMediaAccount(
                politician_id=politician.id,
                platform=platform,
                username=username,
                user_id=user_info.get('id') if user_info else None,
                url=f"https://twitter.com/{username}" if platform.lower() == 'twitter' else None,
                followers_count=user_info.get('followers_count', 0) if user_info else 0,
                following_count=user_info.get('following_count', 0) if user_info else 0,
                verified=user_info.get('verified', False) if user_info else False
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            return account
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating social media account: {e}")
            return None
    
    def sync_twitter_posts(self, account: SocialMediaAccount, 
                          days_back: int = 30, max_posts: int = 100) -> List[SocialMediaPost]:
        """Sync recent Twitter posts for an account."""
        if account.platform.lower() != 'twitter':
            return []
        
        try:
            # Get tweets from Twitter API
            tweets = self.twitter_client.get_user_tweets(
                account.username, 
                count=max_posts, 
                days_back=days_back
            )
            
            posts = []
            for tweet_data in tweets:
                # Check if post already exists
                existing_post = self.db.query(SocialMediaPost).filter(
                    SocialMediaPost.account_id == account.id,
                    SocialMediaPost.post_id == str(tweet_data['id'])
                ).first()
                
                if existing_post:
                    # Update metrics
                    existing_post.likes_count = tweet_data['like_count']
                    existing_post.retweets_count = tweet_data['retweet_count']
                    existing_post.replies_count = tweet_data['reply_count']
                    posts.append(existing_post)
                    continue
                
                # Analyze sentiment
                sentiment_analysis = self.analyze_tweet_sentiment(tweet_data['text'])
                
                # Extract topics
                topics = self.extract_political_topics(tweet_data['text'])
                
                # Create post record
                post = SocialMediaPost(
                    account_id=account.id,
                    post_id=str(tweet_data['id']),
                    content=tweet_data['text'],
                    posted_date=tweet_data['created_at'],
                    likes_count=tweet_data['like_count'],
                    retweets_count=tweet_data['retweet_count'],
                    replies_count=tweet_data['reply_count'],
                    sentiment_score=sentiment_analysis['polarity'],
                    metadata={
                        'sentiment_analysis': sentiment_analysis,
                        'political_topics': topics,
                        'context_annotations': tweet_data.get('context_annotations', [])
                    }
                )
                
                self.db.add(post)
                posts.append(post)
            
            self.db.commit()
            
            # Refresh all posts
            for post in posts:
                self.db.refresh(post)
            
            print(f"Synced {len(posts)} posts for {account.username}")
            return posts
            
        except Exception as e:
            self.db.rollback()
            print(f"Error syncing Twitter posts for {account.username}: {e}")
            return []
    
    def analyze_politician_social_media(self, politician: Politician) -> Dict[str, Any]:
        """Analyze all social media activity for a politician."""
        analysis = {
            'politician_id': politician.id,
            'politician_name': politician.name,
            'accounts': [],
            'overall_metrics': {
                'total_posts': 0,
                'total_followers': 0,
                'avg_sentiment': 0.0,
                'top_topics': []
            }
        }
        
        # Analyze each social media account
        for account in politician.social_media_accounts:
            account_analysis = self._analyze_account(account)
            analysis['accounts'].append(account_analysis)
            
            # Add to overall metrics
            analysis['overall_metrics']['total_posts'] += account_analysis['post_count']
            analysis['overall_metrics']['total_followers'] += account.followers_count
        
        # Calculate overall sentiment
        all_posts = []
        for account in politician.social_media_accounts:
            all_posts.extend(account.posts)
        
        if all_posts:
            avg_sentiment = sum(post.sentiment_score or 0 for post in all_posts) / len(all_posts)
            analysis['overall_metrics']['avg_sentiment'] = avg_sentiment
            
            # Get top topics
            all_topics = []
            for post in all_posts:
                if post.metadata and 'political_topics' in post.metadata:
                    all_topics.extend(post.metadata['political_topics'])
            
            from collections import Counter
            topic_counts = Counter(all_topics)
            analysis['overall_metrics']['top_topics'] = topic_counts.most_common(5)
        
        return analysis
    
    def _analyze_account(self, account: SocialMediaAccount) -> Dict[str, Any]:
        """Analyze a single social media account."""
        posts = account.posts
        
        analysis = {
            'account_id': account.id,
            'platform': account.platform,
            'username': account.username,
            'followers_count': account.followers_count,
            'verified': account.verified,
            'post_count': len(posts),
            'engagement_metrics': {},
            'sentiment_distribution': {},
            'topic_distribution': {},
            'posting_frequency': {}
        }
        
        if not posts:
            return analysis
        
        # Calculate engagement metrics
        total_likes = sum(post.likes_count for post in posts)
        total_retweets = sum(post.retweets_count for post in posts)
        total_replies = sum(post.replies_count for post in posts)
        
        analysis['engagement_metrics'] = {
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'total_replies': total_replies,
            'avg_likes_per_post': total_likes / len(posts),
            'avg_retweets_per_post': total_retweets / len(posts),
            'avg_replies_per_post': total_replies / len(posts)
        }
        
        # Analyze sentiment distribution
        sentiments = [post.sentiment_score for post in posts if post.sentiment_score is not None]
        if sentiments:
            sentiment_labels = [self._get_sentiment_label(s) for s in sentiments]
            from collections import Counter
            sentiment_counts = Counter(sentiment_labels)
            analysis['sentiment_distribution'] = dict(sentiment_counts)
        
        # Analyze topic distribution
        all_topics = []
        for post in posts:
            if post.metadata and 'political_topics' in post.metadata:
                all_topics.extend(post.metadata['political_topics'])
        
        if all_topics:
            from collections import Counter
            topic_counts = Counter(all_topics)
            analysis['topic_distribution'] = dict(topic_counts.most_common(10))
        
        return analysis
    
    def compare_politician_social_media(self, politician1: Politician, 
                                      politician2: Politician) -> Dict[str, Any]:
        """Compare social media activity between two politicians."""
        analysis1 = self.analyze_politician_social_media(politician1)
        analysis2 = self.analyze_politician_social_media(politician2)
        
        comparison = {
            'politician1': {
                'name': politician1.name,
                'analysis': analysis1
            },
            'politician2': {
                'name': politician2.name,
                'analysis': analysis2
            },
            'comparison': {
                'follower_difference': (
                    analysis1['overall_metrics']['total_followers'] - 
                    analysis2['overall_metrics']['total_followers']
                ),
                'post_count_difference': (
                    analysis1['overall_metrics']['total_posts'] - 
                    analysis2['overall_metrics']['total_posts']
                ),
                'sentiment_difference': (
                    analysis1['overall_metrics']['avg_sentiment'] - 
                    analysis2['overall_metrics']['avg_sentiment']
                )
            }
        }
        
        return comparison


class SocialMediaPipeline:
    """Coordinates social media data collection and analysis."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.analyzer = SocialMediaAnalyzer(db_session)
    
    def sync_all_politician_accounts(self, days_back: int = 7) -> Dict[str, Any]:
        """Sync social media posts for all politicians."""
        try:
            # Get all politicians with social media accounts
            politicians = self.db.query(Politician).filter(
                Politician.social_media_accounts.any()
            ).all()
            
            total_synced = 0
            total_posts = 0
            
            for politician in politicians:
                for account in politician.social_media_accounts:
                    try:
                        posts = self.analyzer.sync_twitter_posts(account, days_back=days_back)
                        total_posts += len(posts)
                        total_synced += 1
                        print(f"Synced {len(posts)} posts for {politician.name} (@{account.username})")
                    except Exception as e:
                        print(f"Error syncing account {account.username}: {e}")
                        continue
            
            return {
                'status': 'completed',
                'accounts_synced': total_synced,
                'total_posts_synced': total_posts,
                'politicians_processed': len(politicians)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'accounts_synced': 0
            }