# Content Extraction Module
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import trafilatura
from readability import Document
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import Dict, Optional, List
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Extracts clean content from web pages using multiple methods"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
        
    def extract_content(self, url: str) -> Optional[Dict]:
        """
        Extract content from a URL using multiple extraction methods
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing extracted content or None if extraction fails
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Try newspaper3k first (best for articles)
            content = self._extract_with_newspaper(url)
            if content and content.get('text') and len(content['text'].strip()) > 100:
                content['extraction_method'] = 'newspaper3k'
                return content
            
            # Fallback to trafilatura
            content = self._extract_with_trafilatura(url)
            if content and content.get('text') and len(content['text'].strip()) > 100:
                content['extraction_method'] = 'trafilatura'
                return content
            
            # Fallback to readability
            content = self._extract_with_readability(url)
            if content and content.get('text') and len(content['text'].strip()) > 100:
                content['extraction_method'] = 'readability'
                return content
            
            # Last resort: BeautifulSoup
            content = self._extract_with_beautifulsoup(url)
            if content and content.get('text') and len(content['text'].strip()) > 50:
                content['extraction_method'] = 'beautifulsoup'
                return content
            
            logger.warning(f"All extraction methods failed for: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            return None
    
    def _extract_with_newspaper(self, url: str) -> Optional[Dict]:
        """Extract content using newspaper3k library"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Basic validation
            if not article.text or len(article.text.strip()) < 100:
                return None
            
            # Extract metadata
            authors = article.authors if article.authors else []
            publish_date = None
            if article.publish_date:
                try:
                    publish_date = article.publish_date.isoformat()
                except:
                    publish_date = str(article.publish_date)
            
            return {
                'title': article.title or '',
                'text': self._clean_text(article.text),
                'summary': article.summary or '',
                'authors': authors,
                'publish_date': publish_date,
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(article.text.split()) if article.text else 0,
                'top_image': article.top_image or '',
                'keywords': list(article.keywords) if article.keywords else []
            }
            
        except Exception as e:
            logger.debug(f"Newspaper3k extraction failed for {url}: {str(e)}")
            return None
    
    def _extract_with_trafilatura(self, url: str) -> Optional[Dict]:
        """Extract content using trafilatura library"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            
            # Extract main content
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if not text or len(text.strip()) < 100:
                return None
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            title = ''
            authors = []
            publish_date = None
            
            if metadata:
                title = metadata.title or ''
                if metadata.author:
                    authors = [metadata.author]
                if metadata.date:
                    publish_date = metadata.date
            
            return {
                'title': title,
                'text': self._clean_text(text),
                'summary': self._generate_summary(text),
                'authors': authors,
                'publish_date': publish_date,
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(text.split()) if text else 0
            }
            
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed for {url}: {str(e)}")
            return None
    
    def _extract_with_readability(self, url: str) -> Optional[Dict]:
        """Extract content using readability library"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            doc = Document(response.content)
            
            title = doc.title()
            content = doc.summary()
            
            if not content or len(content.strip()) < 100:
                return None
            
            # Parse HTML to extract text
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            return {
                'title': title or '',
                'text': self._clean_text(text),
                'summary': self._generate_summary(text),
                'authors': [],
                'publish_date': None,
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(text.split()) if text else 0
            }
            
        except Exception as e:
            logger.debug(f"Readability extraction failed for {url}: {str(e)}")
            return None
    
    def _extract_with_beautifulsoup(self, url: str) -> Optional[Dict]:
        """Extract content using BeautifulSoup as last resort"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Try to find main content areas
            main_content = None
            for selector in ['main', 'article', '.content', '.post', '.entry']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body') or soup
            
            # Extract title
            title_elem = soup.find('title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract text
            text = main_content.get_text(separator=' ', strip=True)
            
            if not text or len(text.strip()) < 50:
                return None
            
            return {
                'title': title,
                'text': self._clean_text(text),
                'summary': self._generate_summary(text),
                'authors': [],
                'publish_date': None,
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(text.split()) if text else 0
            }
            
        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ''
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove very short lines (likely navigation/ads)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        # Join lines back
        text = ' '.join(cleaned_lines)
        
        # Remove common noise patterns
        noise_patterns = [
            r'cookie policy',
            r'privacy policy', 
            r'terms of service',
            r'subscribe to newsletter',
            r'follow us on',
            r'share this article'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate a simple extractive summary"""
        if not text:
            return ''
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
        
        # Simple ranking by sentence length and position
        ranked_sentences = []
        for i, sentence in enumerate(sentences[:10]):  # Only consider first 10 sentences
            score = len(sentence.split()) * (1 - i * 0.1)  # Prefer longer sentences and earlier position
            ranked_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        ranked_sentences.sort(reverse=True)
        top_sentences = [sentence for _, sentence in ranked_sentences[:max_sentences]]
        
        return '. '.join(top_sentences) + '.'
    
    def extract_batch(self, urls: List[str], max_workers: int = 5) -> List[Dict]:
        """Extract content from multiple URLs concurrently"""
        import concurrent.futures
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.extract_content, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    if content:
                        results.append(content)
                except Exception as e:
                    logger.error(f"Batch extraction failed for {url}: {str(e)}")
        
        return results