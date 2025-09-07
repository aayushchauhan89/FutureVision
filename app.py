# AI Research Agent - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import uuid
from search_api import WebSearcher
from extract import ContentExtractor
from summarize import TextSummarizer
from citation import CitationManager
from export import ReportExporter
from utils import validate_topic, clean_text
import logging
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize components
searcher = WebSearcher()
extractor = ContentExtractor()
summarizer = TextSummarizer()
citation_manager = CitationManager()
exporter = ReportExporter()

@app.route('/')
def index():
    """Main page for topic input"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_topic():
    """Handle research topic search"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        
        if not validate_topic(topic):
            return jsonify({'error': 'Please enter a valid research topic'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Step 1: Web Search
        logger.info(f"Searching for topic: {topic}")
        search_results = searcher.search(topic, num_results=3)
        
        if not search_results:
            return jsonify({'error': 'No search results found'}), 404
        
        # Step 2: Content Extraction
        logger.info("Extracting content from URLs")
        extracted_content = []
        for result in search_results:
            try:
                content = extractor.extract_content(result['url'])
                if content:
                    content.update({
                        'search_title': result.get('title', ''),
                        'search_snippet': result.get('snippet', ''),
                        'url': result['url']
                    })
                    extracted_content.append(content)
            except Exception as e:
                logger.warning(f"Failed to extract content from {result['url']}: {str(e)}")
                continue
        
        if not extracted_content:
            return jsonify({'error': 'Could not extract content from search results'}), 500
        
        # Step 3: Summarization
        logger.info("Generating summary")
        summary_data = summarizer.summarize_content(extracted_content, topic)
        
        # Step 4: Generate Citations
        logger.info("Generating citations")
        citations = citation_manager.generate_citations(extracted_content)
        
        # Combine results
        research_report = {
            'session_id': session_id,
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'summary': summary_data,
            'sources': extracted_content,
            'citations': citations,
            'total_sources': len(extracted_content)
        }
        
        # Cache the report for export
        cache_report(session_id, research_report)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'report': research_report
        })
        
    except Exception as e:
        logger.error(f"Error in search_topic: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/export/<session_id>/<format>')
def export_report(session_id, format):
    """Export research report in specified format"""
    try:
        report = get_cached_report(session_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if format == 'pdf':
            pdf_file = exporter.export_pdf(report)
            return send_file(pdf_file, as_attachment=True, 
                           download_name=f"research_report_{session_id}.pdf")
        
        elif format == 'markdown':
            md_content = exporter.export_markdown(report)
            return send_file(md_content, as_attachment=True,
                           download_name=f"research_report_{session_id}.md")
        
        else:
            return jsonify({'error': 'Invalid export format'}), 400
            
    except Exception as e:
        logger.error(f"Error in export_report: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/results/<session_id>')
def view_results(session_id):
    """Display research results page"""
    report = get_cached_report(session_id)
    if not report:
        return render_template('error.html', error='Report not found'), 404
    
    return render_template('results.html', report=report)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Cache management functions
def cache_report(session_id, report):
    """Cache report data"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = os.path.join(cache_dir, f"{session_id}.json")
    with open(cache_file, 'w') as f:
        json.dump(report, f, indent=2)

def get_cached_report(session_id):
    """Retrieve cached report"""
    cache_file = os.path.join('cache', f"{session_id}.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('cache', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)