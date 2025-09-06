# Configuration Module
import os
from typing import Optional

class Config:
    """Configuration settings for AI Research Agent"""
    
    def __init__(self):
        # API Keys
        self.SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
        self.BING_API_KEY = os.environ.get('BING_API_KEY')
        self.BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')
        self.OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        self.ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
        
        # Search Settings
        self.DEFAULT_SEARCH_ENGINE = os.environ.get('DEFAULT_SEARCH_ENGINE', 'serpapi')
        self.MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', '10'))
        self.SEARCH_TIMEOUT = int(os.environ.get('SEARCH_TIMEOUT', '30'))
        
        # Content Extraction Settings
        self.EXTRACTION_TIMEOUT = int(os.environ.get('EXTRACTION_TIMEOUT', '30'))
        self.MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '8000'))
        self.MIN_CONTENT_LENGTH = int(os.environ.get('MIN_CONTENT_LENGTH', '100'))
        
        # Summarization Settings
        self.DEFAULT_SUMMARY_METHOD = os.environ.get('DEFAULT_SUMMARY_METHOD', 'transformers')
        self.MAX_SUMMARY_LENGTH = int(os.environ.get('MAX_SUMMARY_LENGTH', '500'))
        self.MAX_KEY_POINTS = int(os.environ.get('MAX_KEY_POINTS', '8'))
        
        # Citation Settings
        self.DEFAULT_CITATION_STYLE = os.environ.get('DEFAULT_CITATION_STYLE', 'apa')
        
        # Cache Settings
        self.CACHE_DURATION = int(os.environ.get('CACHE_DURATION', '3600'))  # 1 hour
        self.MAX_CACHE_SIZE = int(os.environ.get('MAX_CACHE_SIZE', '100'))
        
        # Export Settings
        self.EXPORT_CLEANUP_DAYS = int(os.environ.get('EXPORT_CLEANUP_DAYS', '7'))
        
        # Flask Settings
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
        self.DEBUG = os.environ.get('FLASK_ENV') == 'development'
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '30'))
        
        # Logging
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    def validate(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check if at least one search API is configured
        search_apis = [self.SERPAPI_KEY, self.BING_API_KEY, self.BRAVE_API_KEY]
        if not any(search_apis):
            issues.append("No search API keys configured. Please set SERPAPI_KEY, BING_API_KEY, or BRAVE_API_KEY")
        
        # Check summarization APIs if transformers is not available
        try:
            import transformers
        except ImportError:
            if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                issues.append("No LLM APIs configured and transformers not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY, or install transformers")
        
        # Check secret key in production
        if not self.DEBUG and self.SECRET_KEY == 'your-secret-key-change-in-production':
            issues.append("Please change SECRET_KEY in production environment")
        
        return issues

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.LOG_LEVEL = 'WARNING'
        
class TestingConfig(Config):
    """Testing configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.LOG_LEVEL = 'DEBUG'
        self.MAX_SEARCH_RESULTS = 3  # Faster tests