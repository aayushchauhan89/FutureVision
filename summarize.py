# Text Summarization Module
import os
from typing import List, Dict, Optional
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class TextSummarizer:
    """Handles text summarization using various LLM approaches"""
    
    def __init__(self):
        self.max_content_length = 8000  # Max tokens for LLM input
        self.summary_methods = ['transformers', 'openai', 'anthropic']
        
    def summarize_content(self, extracted_content: List[Dict], topic: str) -> Dict:
    """
    Summarize extracted content for a given research topic
    (Modified to use only the lightweight rule-based method for Render's free tier)
    """
    try:
        logger.info(f"Summarizing content for topic: {topic} using lightweight rule-based method.")
        
        combined_text = self._prepare_content(extracted_content)
        
        if not combined_text:
            return self._create_empty_summary(topic)
        
        # Directly call the rule-based summary as the only option
        summary = self._summarize_with_rules(combined_text, topic, extracted_content)
        return summary
        
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        return self._create_empty_summary(topic)
    
    def _prepare_content(self, extracted_content: List[Dict]) -> str:
        """Prepare and combine content for summarization"""
        content_parts = []
        
        for item in extracted_content:
            text = item.get('text', '')
            title = item.get('title', '')
            
            if text and len(text.strip()) > 50:
                # Add title and text
                if title:
                    content_parts.append(f"Title: {title}")
                content_parts.append(f"Content: {text[:1000]}...")  # Limit per source
                content_parts.append("---")
        
        combined = '\n'.join(content_parts)
        
        # Truncate if too long
        if len(combined) > self.max_content_length:
            combined = combined[:self.max_content_length] + "..."
        
        return combined
    
    def _summarize_with_transformers(self, text: str, topic: str) -> Dict:
        """Summarize using Hugging Face transformers"""
        try:
            from transformers import pipeline
            
            # Initialize summarization pipeline
            summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # Use CPU
            )
            
            # Split text into chunks if too long
            chunks = self._split_text(text, max_length=1000)
            summaries = []
            
            for chunk in chunks:
                if len(chunk.strip()) > 100:
                    try:
                        summary = summarizer(
                            chunk,
                            max_length=150,
                            min_length=50,
                            do_sample=False,
                            truncation=True
                        )
                        summaries.append(summary[0]['summary_text'])
                    except Exception as e:
                        logger.warning(f"Failed to summarize chunk: {str(e)}")
                        continue
            
            # Combine summaries
            if summaries:
                main_summary = self._combine_summaries(summaries)
                key_points = self._extract_key_points(summaries)
                
                return {
                    'main_summary': main_summary,
                    'key_points': key_points,
                    'method': 'transformers',
                    'topic': topic,
                    'generated_at': datetime.now().isoformat()
                }
            
            return None
            
        except ImportError:
            logger.warning("Transformers library not available")
            return None
        except Exception as e:
            logger.error(f"Transformers summarization error: {str(e)}")
            return None
    
    def _summarize_with_openai(self, text: str, topic: str) -> Dict:
        """Summarize using OpenAI API"""
        try:
            import openai
            from config import Config
            
            config = Config()
            if not config.OPENAI_API_KEY:
                return None
            
            openai.api_key = config.OPENAI_API_KEY
            
            prompt = f"""
            Research Topic: {topic}
            
            Please analyze the following research content and provide:
            1. A comprehensive summary (2-3 paragraphs)
            2. Key findings (bullet points)
            3. Different viewpoints or debates (if any)
            4. Gaps or limitations mentioned
            
            Content:
            {text[:3000]}
            
            Please structure your response as a clear, academic summary.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research assistant that creates structured summaries from academic and web content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content
            
            # Parse the structured response
            return self._parse_openai_response(summary_text, topic)
            
        except ImportError:
            logger.warning("OpenAI library not available")
            return None
        except Exception as e:
            logger.error(f"OpenAI summarization error: {str(e)}")
            return None
    
    def _summarize_with_rules(self, text: str, topic: str, extracted_content: List[Dict]) -> Dict:
        """Rule-based summarization as fallback"""
        try:
            # Extract sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            # Score sentences based on relevance to topic
            topic_words = set(topic.lower().split())
            scored_sentences = []
            
            for sentence in sentences[:50]:  # Limit processing
                words = set(sentence.lower().split())
                relevance_score = len(topic_words.intersection(words))
                length_score = min(len(sentence.split()), 30) / 30  # Prefer medium-length sentences
                position_score = max(0, 1 - len(scored_sentences) * 0.1)  # Prefer earlier sentences
                
                total_score = relevance_score * 2 + length_score + position_score
                scored_sentences.append((total_score, sentence))
            
            # Sort and select top sentences
            scored_sentences.sort(reverse=True)
            top_sentences = [sentence for _, sentence in scored_sentences[:5]]
            
            # Create key points from titles and high-scoring sentences
            key_points = []
            
            # Add insights from titles
            for item in extracted_content[:5]:
                title = item.get('title', '')
                if title and len(title) > 10:
                    key_points.append(f"Source discusses: {title}")
            
            # Add top sentences as points
            for sentence in top_sentences[:3]:
                if len(sentence) > 30:
                    key_points.append(sentence)
            
            main_summary = '. '.join(top_sentences) + '.'
            
            return {
                'main_summary': main_summary,
                'key_points': key_points[:8],  # Limit to 8 points
                'method': 'rule_based',
                'topic': topic,
                'generated_at': datetime.now().isoformat(),
                'total_sources': len(extracted_content),
                'confidence': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Rule-based summarization error: {str(e)}")
            return self._create_empty_summary(topic)
    
    def _split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _combine_summaries(self, summaries: List[str]) -> str:
        """Combine multiple summaries into one coherent summary"""
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        # Simple combination - could be improved with more sophisticated merging
        combined = '. '.join(summaries)
        
        # Remove duplicate sentences
        sentences = combined.split('. ')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence)
        
        return '. '.join(unique_sentences) + '.'
    
    def _extract_key_points(self, summaries: List[str]) -> List[str]:
        """Extract key points from summaries"""
        points = []
        
        for summary in summaries:
            # Split by common delimiters
            sentences = re.split(r'[.!?;]+', summary)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 200:
                    points.append(sentence)
        
        # Remove duplicates and limit
        unique_points = []
        seen = set()
        
        for point in points:
            if point not in seen:
                unique_points.append(point)
                seen.add(point)
                if len(unique_points) >= 8:
                    break
        
        return unique_points
    
    def _parse_openai_response(self, response: str, topic: str) -> Dict:
        """Parse structured response from OpenAI"""
        try:
            lines = response.split('\n')
            
            summary_lines = []
            key_points = []
            current_section = 'summary'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'key findings' in line.lower() or 'key points' in line.lower():
                    current_section = 'points'
                elif line.startswith('- ') or line.startswith('• '):
                    if current_section == 'points':
                        key_points.append(line[2:].strip())
                else:
                    if current_section == 'summary' and not line.startswith('#'):
                        summary_lines.append(line)
            
            main_summary = ' '.join(summary_lines)
            
            return {
                'main_summary': main_summary,
                'key_points': key_points,
                'method': 'openai',
                'topic': topic,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return self._create_empty_summary(topic)
    
    def _create_empty_summary(self, topic: str) -> Dict:
        """Create empty summary structure"""
        return {
            'main_summary': f"Unable to generate summary for topic: {topic}",
            'key_points': ["Content extraction or summarization failed"],
            'method': 'fallback',
            'topic': topic,
            'generated_at': datetime.now().isoformat(),
            'error': True
        }