# Utility Functions
import re
import string
from typing import Optional, List
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def validate_topic(topic: str) -> bool:
    """
    Validate research topic input
    
    Args:
        topic: The research topic string
        
    Returns:
        True if valid, False otherwise
    """
    if not topic or not isinstance(topic, str):
        return False
    
    # Clean and check length
    topic = topic.strip()
    if len(topic) < 3 or len(topic) > 500:
        return False
    
    # Check if topic contains only valid characters
    valid_chars = string.ascii_letters + string.digits + string.punctuation + ' '
    if not all(char in valid_chars for char in topic):
        return False
    
    # Check for spam patterns
    spam_patterns = [
        r'^(.)\1{10,}',  # Repeated characters
        r'http[s]?://',  # URLs
        r'[A-Z]{20,}',   # All caps spam
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, topic):
            return False
    
    return True

def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Remove very long repeated patterns
    text = re.sub(r'(.{1,10})\1{5,}', r'\1', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Remove excessive punctuation
    text = re.sub(r'[!?]{3,}', '!', text)
    text = re.sub(r'\.{3,}', '...', text)
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract important keywords from text
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
        'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'must', 'can', 'shall'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter and count
    word_freq = {}
    for word in words:
        if len(word) > 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:max_keywords]]
    
    return keywords

def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If word boundary is reasonably close
        truncated = truncated[:last_space]
    
    return truncated + suffix

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time for text
    
    Args:
        text: Text to estimate
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    if not text:
        return 0
    
    word_count = len(text.split())
    reading_time = max(1, round(word_count / words_per_minute))
    
    return reading_time

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe saving
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename

def extract_domain_info(url: str) -> dict:
    """
    Extract domain information from URL
    
    Args:
        url: URL to analyze
        
    Returns:
        Dictionary with domain info
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract top-level domain
        parts = domain.split('.')
        tld = parts[-1] if parts else ''
        
        # Determine domain type
        domain_type = 'unknown'
        if tld in ['edu', 'ac']:
            domain_type = 'academic'
        elif tld in ['gov', 'mil']:
            domain_type = 'government'
        elif tld in ['org']:
            domain_type = 'organization'
        elif tld in ['com', 'net', 'biz']:
            domain_type = 'commercial'
        
        return {
            'domain': domain,
            'tld': tld,
            'type': domain_type,
            'is_secure': parsed.scheme == 'https'
        }
        
    except Exception as e:
        logger.warning(f"Failed to extract domain info from {url}: {str(e)}")
        return {
            'domain': 'unknown',
            'tld': 'unknown',
            'type': 'unknown',
            'is_secure': False
        }

def rate_limit_decorator(calls_per_minute: int = 60):
    """
    Decorator for rate limiting function calls
    
    Args:
        calls_per_minute: Maximum calls per minute
        
    Returns:
        Decorator function
    """
    import time
    from functools import wraps
    
    call_times = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove calls older than 1 minute
            call_times[:] = [t for t in call_times if now - t < 60]
            
            # Check if we're at the limit
            if len(call_times) >= calls_per_minute:
                sleep_time = 60 - (now - call_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Clean up again after sleeping
                    now = time.time()
                    call_times[:] = [t for t in call_times if now - t < 60]
            
            # Record this call
            call_times.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator