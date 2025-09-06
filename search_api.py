# Web Search API Integration
import requests
import os
from typing import List, Dict, Optional
import time
from config import Config
import logging

logger = logging.getLogger(__name__)

class WebSearcher:
    """Handles web search operations using multiple APIs"""
    
    def __init__(self):
        self.config = Config()
        self.search_engines = {
            'serpapi': self._search_serpapi,
            'bing': self._search_bing,
            'brave': self._search_brave
        }
        
    def search(self, query: str, num_results: int = 10, engine: str = 'serpapi') -> List[Dict]:
        """
        Search for web results using specified engine
        
        Args:
            query: Search query string
            num_results: Number of results to return
            engine: Search engine to use ('serpapi', 'bing', 'brave')
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            if engine not in self.search_engines:
                raise ValueError(f"Unsupported search engine: {engine}")
            
            logger.info(f"Searching with {engine}: {query}")
            results = self.search_engines[engine](query, num_results)
            
            # Filter and clean results
            cleaned_results = self._clean_results(results)
            return cleaned_results[:num_results]
            
        except Exception as e:
            logger.error(f"Search failed with {engine}: {str(e)}")
            # Try fallback engines
            for fallback_engine in self.search_engines:
                if fallback_engine != engine:
                    try:
                        logger.info(f"Trying fallback engine: {fallback_engine}")
                        results = self.search_engines[fallback_engine](query, num_results)
                        return self._clean_results(results)[:num_results]
                    except Exception as fallback_error:
                        logger.warning(f"Fallback {fallback_engine} also failed: {str(fallback_error)}")
                        continue
            
            raise Exception("All search engines failed")
    
    def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        """Search using SerpAPI Google Search"""
        try:
            from serpapi import GoogleSearch
            
            params = {
                "q": query,
                "api_key": self.config.SERPAPI_KEY,
                "num": min(num_results, 20),  # SerpAPI limit
                "safe": "active"
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                raise Exception(f"SerpAPI error: {results['error']}")
            
            organic_results = results.get("organic_results", [])
            
            formatted_results = []
            for result in organic_results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'source': 'serpapi'
                })
            
            return formatted_results
            
        except ImportError:
            raise Exception("SerpAPI library not installed. Run: pip install google-search-results")
        except Exception as e:
            raise Exception(f"SerpAPI search failed: {str(e)}")
    
    def _search_bing(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing Web Search API"""
        try:
            if not self.config.BING_API_KEY:
                raise Exception("Bing API key not configured")
            
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                'Ocp-Apim-Subscription-Key': self.config.BING_API_KEY,
                'User-Agent': 'AI-Research-Agent/1.0'
            }
            params = {
                'q': query,
                'count': min(num_results, 50),  # Bing limit
                'textDecorations': True,
                'textFormat': 'HTML',
                'safeSearch': 'Moderate'
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            web_pages = data.get('webPages', {}).get('value', [])
            
            formatted_results = []
            for result in web_pages:
                formatted_results.append({
                    'title': result.get('name', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', ''),
                    'source': 'bing'
                })
            
            return formatted_results
            
        except requests.RequestException as e:
            raise Exception(f"Bing API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Bing search failed: {str(e)}")
    
    def _search_brave(self, query: str, num_results: int) -> List[Dict]:
        """Search using Brave Search API"""
        try:
            if not self.config.BRAVE_API_KEY:
                raise Exception("Brave API key not configured")
            
            endpoint = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                'X-Subscription-Token': self.config.BRAVE_API_KEY,
                'Accept': 'application/json',
                'User-Agent': 'AI-Research-Agent/1.0'
            }
            params = {
                'q': query,
                'count': min(num_results, 20),  # Brave limit
                'safesearch': 'moderate',
                'freshness': 'py'  # Past year
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            web_results = data.get('web', {}).get('results', [])
            
            formatted_results = []
            for result in web_results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('description', ''),
                    'source': 'brave'
                })
            
            return formatted_results
            
        except requests.RequestException as e:
            raise Exception(f"Brave API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Brave search failed: {str(e)}")
    
    def _clean_results(self, results: List[Dict]) -> List[Dict]:
        """Clean and filter search results"""
        cleaned = []
        seen_urls = set()
        
        for result in results:
            url = result.get('url', '').strip()
            title = result.get('title', '').strip()
            snippet = result.get('snippet', '').strip()
            
            # Skip invalid or duplicate results
            if not url or not title or url in seen_urls:
                continue
            
            # Skip certain domains that are not useful for research
            excluded_domains = [
                'youtube.com', 'tiktok.com', 'instagram.com', 
                'facebook.com', 'twitter.com', 'reddit.com'
            ]
            
            if any(domain in url.lower() for domain in excluded_domains):
                continue
            
            seen_urls.add(url)
            cleaned.append({
                'title': title,
                'url': url,
                'snippet': snippet,
                'source': result.get('source', 'unknown')
            })
        
        return cleaned

class SearchRateLimiter:
    """Simple rate limiter for search APIs"""
    
    def __init__(self):
        self.last_requests = {}
        self.rate_limits = {
            'serpapi': 1.0,  # 1 second between requests
            'bing': 0.5,     # 0.5 seconds between requests
            'brave': 1.0     # 1 second between requests
        }
    
    def wait_if_needed(self, engine: str):
        """Wait if necessary to respect rate limits"""
        if engine in self.rate_limits:
            last_request = self.last_requests.get(engine, 0)
            time_since_last = time.time() - last_request
            min_interval = self.rate_limits[engine]
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_requests[engine] = time.time()