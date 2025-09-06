# Citation Management Module
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger(__name__)

class CitationManager:
    """Handles citation generation and formatting"""
    
    def __init__(self):
        self.citation_styles = {
            'apa': self._format_apa,
            'mla': self._format_mla,
            'chicago': self._format_chicago,
            'harvard': self._format_harvard
        }
        self.default_style = 'apa'
    
    def generate_citations(self, content_list: List[Dict], style: str = None) -> List[Dict]:
        """
        Generate citations for extracted content
        
        Args:
            content_list: List of extracted content with metadata
            style: Citation style ('apa', 'mla', 'chicago', 'harvard')
            
        Returns:
            List of formatted citations
        """
        if style is None:
            style = self.default_style
        
        if style not in self.citation_styles:
            logger.warning(f"Unknown citation style: {style}, using {self.default_style}")
            style = self.default_style
        
        citations = []
        
        for i, content in enumerate(content_list, 1):
            try:
                citation = self._create_citation(content, style, i)
                if citation:
                    citations.append(citation)
            except Exception as e:
                logger.error(f"Failed to create citation for {content.get('url', 'unknown')}: {str(e)}")
                continue
        
        return citations
    
    def _create_citation(self, content: Dict, style: str, index: int) -> Optional[Dict]:
        """Create a single citation"""
        try:
            # Extract metadata
            metadata = self._extract_metadata(content)
            
            # Format citation based on style
            formatted_citation = self.citation_styles[style](metadata)
            
            return {
                'index': index,
                'style': style,
                'formatted': formatted_citation,
                'metadata': metadata,
                'url': content.get('url', ''),
                'reliability_score': self._assess_reliability(content)
            }
            
        except Exception as e:
            logger.error(f"Citation creation failed: {str(e)}")
            return None
    
    def _extract_metadata(self, content: Dict) -> Dict:
        """Extract and normalize metadata from content"""
        url = content.get('url', '')
        domain = content.get('domain') or urlparse(url).netloc
        
        # Extract authors
        authors = content.get('authors', [])
        if not authors and 'author' in content:
            authors = [content['author']]
        
        # Clean and format authors
        formatted_authors = self._format_authors(authors)
        
        # Extract and format date
        publish_date = content.get('publish_date')
        formatted_date = self._format_date(publish_date)
        
        # Extract title
        title = content.get('title', '').strip()
        if not title:
            title = content.get('search_title', '').strip()
        
        # Clean title
        title = re.sub(r'\s+', ' ', title)
        if len(title) > 200:
            title = title[:200] + "..."
        
        # Extract publisher/website name
        publisher = self._extract_publisher(domain, content)
        
        return {
            'authors': formatted_authors,
            'title': title,
            'publisher': publisher,
            'date': formatted_date,
            'url': url,
            'domain': domain,
            'access_date': datetime.now().strftime("%B %d, %Y")
        }
    
    def _format_authors(self, authors: List[str]) -> str:
        """Format author names"""
        if not authors:
            return ""
        
        # Clean author names
        cleaned_authors = []
        for author in authors[:3]:  # Limit to 3 authors
            author = author.strip()
            if author and len(author) > 1:
                cleaned_authors.append(author)
        
        if not cleaned_authors:
            return ""
        
        if len(cleaned_authors) == 1:
            return cleaned_authors[0]
        elif len(cleaned_authors) == 2:
            return f"{cleaned_authors[0]} & {cleaned_authors[1]}"
        else:
            return f"{cleaned_authors[0]}, {cleaned_authors[1]}, & {cleaned_authors[2]}"
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """Format publication date"""
        if not date_str:
            return "n.d."  # no date
        
        try:
            # Try to parse various date formats
            if isinstance(date_str, str):
                # Remove time if present
                date_str = date_str.split('T')[0]
                
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return date_obj.strftime("%Y")
                    except ValueError:
                        continue
                
                # Extract year with regex
                year_match = re.search(r'20\d{2}', date_str)
                if year_match:
                    return year_match.group()
        
        except Exception:
            pass
        
        return "n.d."
    
    def _extract_publisher(self, domain: str, content: Dict) -> str:
        """Extract publisher/website name"""
        if not domain:
            return "Unknown Publisher"
        
        # Clean domain
        domain = domain.lower().replace('www.', '')
        
        # Common website name mappings
        website_names = {
            'wikipedia.org': 'Wikipedia',
            'nytimes.com': 'The New York Times',
            'washingtonpost.com': 'The Washington Post',
            'bbc.com': 'BBC',
            'cnn.com': 'CNN',
            'reuters.com': 'Reuters',
            'nature.com': 'Nature',
            'science.org': 'Science',
            'pubmed.ncbi.nlm.nih.gov': 'PubMed',
            'arxiv.org': 'arXiv',
            'scholar.google.com': 'Google Scholar',
            'researchgate.net': 'ResearchGate'
        }
        
        if domain in website_names:
            return website_names[domain]
        
        # Extract main domain name
        parts = domain.split('.')
        if len(parts) >= 2:
            main_name = parts[-2]
            return main_name.capitalize()
        
        return domain.capitalize()
    
    def _format_apa(self, metadata: Dict) -> str:
        """Format citation in APA style"""
        authors = metadata['authors']
        title = metadata['title']
        publisher = metadata['publisher']
        date = metadata['date']
        url = metadata['url']
        access_date = metadata['access_date']
        
        # Start with authors
        citation_parts = []
        
        if authors:
            citation_parts.append(f"{authors}.")
        else:
            citation_parts.append(f"{publisher}.")
        
        # Add date
        citation_parts.append(f"({date}).")
        
        # Add title
        if title:
            citation_parts.append(f"{title}.")
        
        # Add publisher if not already used as author
        if authors and publisher:
            citation_parts.append(f"{publisher}.")
        
        # Add URL and access date
        citation_parts.append(f"Retrieved {access_date}, from {url}")
        
        return " ".join(citation_parts)
    
    def _format_mla(self, metadata: Dict) -> str:
        """Format citation in MLA style"""
        authors = metadata['authors']
        title = metadata['title']
        publisher = metadata['publisher']
        date = metadata['date']
        url = metadata['url']
        access_date = metadata['access_date']
        
        citation_parts = []
        
        # Author
        if authors:
            citation_parts.append(f"{authors}.")
        
        # Title
        if title:
            citation_parts.append(f'"{title}."')
        
        # Publisher
        if publisher:
            citation_parts.append(f"{publisher},")
        
        # Date
        citation_parts.append(f"{date},")
        
        # URL
        citation_parts.append(f"{url}.")
        
        # Access date
        citation_parts.append(f"Accessed {access_date}.")
        
        return " ".join(citation_parts)
    
    def _format_chicago(self, metadata: Dict) -> str:
        """Format citation in Chicago style"""
        authors = metadata['authors']
        title = metadata['title']
        publisher = metadata['publisher']
        date = metadata['date']
        url = metadata['url']
        access_date = metadata['access_date']
        
        citation_parts = []
        
        # Author
        if authors:
            citation_parts.append(f"{authors}.")
        
        # Title
        if title:
            citation_parts.append(f'"{title}."')
        
        # Publisher
        if publisher:
            citation_parts.append(f"{publisher}.")
        
        # Date
        citation_parts.append(f"Last modified {date}.")
        
        # URL and access date
        citation_parts.append(f"Accessed {access_date}. {url}.")
        
        return " ".join(citation_parts)
    
    def _format_harvard(self, metadata: Dict) -> str:
        """Format citation in Harvard style"""
        authors = metadata['authors']
        title = metadata['title']
        publisher = metadata['publisher']
        date = metadata['date']
        url = metadata['url']
        access_date = metadata['access_date']
        
        citation_parts = []
        
        # Author and date
        if authors:
            citation_parts.append(f"{authors} {date}.")
        else:
            citation_parts.append(f"{publisher} {date}.")
        
        # Title
        if title:
            citation_parts.append(f"{title}.")
        
        # Publisher
        if authors and publisher:
            citation_parts.append(f"{publisher}.")
        
        # URL and access date
        citation_parts.append(f"Available at: {url} (Accessed: {access_date}).")
        
        return " ".join(citation_parts)
    
    def _assess_reliability(self, content: Dict) -> float:
        """Assess the reliability of a source"""
        score = 0.5  # Base score
        
        domain = content.get('domain', '').lower()
        
        # High-reliability domains
        high_reliability = [
            'edu', 'gov', 'nature.com', 'science.org', 'pubmed',
            'arxiv.org', 'jstor.org', 'springer.com', 'wiley.com'
        ]
        
        # Medium-reliability domains
        medium_reliability = [
            'bbc.com', 'reuters.com', 'nytimes.com', 'washingtonpost.com',
            'wikipedia.org', 'britannica.com'
        ]
        
        # Check domain reliability
        if any(reliable in domain for reliable in high_reliability):
            score += 0.3
        elif any(reliable in domain for reliable in medium_reliability):
            score += 0.2
        
        # Check for author
        if content.get('authors') or content.get('author'):
            score += 0.1
        
        # Check for publication date
        if content.get('publish_date'):
            score += 0.1
        
        # Check content quality
        text = content.get('text', '')
        if len(text) > 500:
            score += 0.1
        
        return min(score, 1.0)
    
    def export_bibliography(self, citations: List[Dict], style: str = None) -> str:
        """Export formatted bibliography"""
        if style is None:
            style = self.default_style
        
        if not citations:
            return f"No citations available.\n\nGenerated on {datetime.now().strftime('%B %d, %Y')}"
        
        bibliography_lines = [
            f"Bibliography ({style.upper()} Style)",
            "=" * 40,
            ""
        ]
        
        for citation in citations:
            if citation['style'] == style or style == 'all':
                bibliography_lines.append(f"{citation['index']}. {citation['formatted']}")
                bibliography_lines.append("")
        
        bibliography_lines.extend([
            "",
            f"Generated on {datetime.now().strftime('%B %d, %Y')} by AI Research Agent"
        ])
        
        return "\n".join(bibliography_lines)