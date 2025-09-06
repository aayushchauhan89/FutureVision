# Export Module for Report Generation
import os
import tempfile
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ReportExporter:
    """Handles exporting research reports to various formats"""
    
    def __init__(self):
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def export_pdf(self, report: Dict) -> str:
        """Export research report as PDF"""
        try:
            # Create markdown content first
            md_content = self._generate_markdown_content(report)
            
            # Convert to PDF using markdown2pdf or reportlab
            pdf_path = self._markdown_to_pdf(md_content, report['session_id'])
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            raise Exception(f"Failed to export PDF: {str(e)}")
    
    def export_markdown(self, report: Dict) -> str:
        """Export research report as Markdown"""
        try:
            md_content = self._generate_markdown_content(report)
            
            # Save to file
            filename = f"research_report_{report['session_id']}.md"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Markdown export failed: {str(e)}")
            raise Exception(f"Failed to export Markdown: {str(e)}")
    
    def _generate_markdown_content(self, report: Dict) -> str:
        """Generate markdown content from research report"""
        topic = report.get('topic', 'Research Topic')
        summary = report.get('summary', {})
        sources = report.get('sources', [])
        citations = report.get('citations', [])
        timestamp = report.get('timestamp', datetime.now().isoformat())
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            formatted_date = timestamp
        
        # Build markdown content
        md_lines = [
            f"# Research Report: {topic}",
            "",
            f"**Generated:** {formatted_date}",
            f"**Sources:** {len(sources)} articles analyzed",
            "",
            "---",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add main summary
        main_summary = summary.get('main_summary', '')
        if main_summary:
            md_lines.extend([
                main_summary,
                ""
            ])
        
        # Add key findings
        key_points = summary.get('key_points', [])
        if key_points:
            md_lines.extend([
                "## Key Findings",
                ""
            ])
            
            for i, point in enumerate(key_points, 1):
                md_lines.append(f"{i}. {point}")
            
            md_lines.append("")
        
        # Add source analysis
        if sources:
            md_lines.extend([
                "## Source Analysis",
                "",
                "| Source | Domain | Date | Reliability |",
                "|--------|--------|------|-------------|"
            ])
            
            for i, source in enumerate(sources, 1):
                title = source.get('title', 'Unknown Title')[:50] + "..."
                domain = source.get('domain', 'Unknown')
                date = source.get('publish_date', 'N/A')
                if date and len(date) > 10:
                    date = date[:10]  # Just the date part
                
                # Get reliability from citations if available
                reliability = "Medium"
                for citation in citations:
                    if citation.get('url') == source.get('url'):
                        score = citation.get('reliability_score', 0.5)
                        if score >= 0.8:
                            reliability = "High"
                        elif score >= 0.6:
                            reliability = "Medium"
                        else:
                            reliability = "Low"
                        break
                
                md_lines.append(f"| {title} | {domain} | {date} | {reliability} |")
            
            md_lines.append("")
        
        # Add detailed source information
        if sources:
            md_lines.extend([
                "## Detailed Sources",
                ""
            ])
            
            for i, source in enumerate(sources, 1):
                title = source.get('title', 'Unknown Title')
                url = source.get('url', '')
                summary_text = source.get('summary', '')
                
                md_lines.extend([
                    f"### {i}. {title}",
                    "",
                    f"**URL:** [{url}]({url})",
                    ""
                ])
                
                if summary_text:
                    md_lines.extend([
                        f"**Summary:** {summary_text}",
                        ""
                    ])
        
        # Add bibliography
        if citations:
            md_lines.extend([
                "## Bibliography",
                ""
            ])
            
            for citation in citations:
                formatted = citation.get('formatted', '')
                if formatted:
                    md_lines.extend([
                        f"{citation.get('index', '')}. {formatted}",
                        ""
                    ])
        
        # Add footer
        md_lines.extend([
            "---",
            "",
            f"*This report was generated by AI Research Agent on {formatted_date}*",
            "",
            f"*Total sources analyzed: {len(sources)}*"
        ])
        
        return "\n".join(md_lines)
    
    def _markdown_to_pdf(self, md_content: str, session_id: str) -> str:
        """Convert markdown content to PDF"""
        try:
            # Try using markdown-pdf library
            return self._convert_with_markdown_pdf(md_content, session_id)
        except:
            try:
                # Fallback to weasyprint
                return self._convert_with_weasyprint(md_content, session_id)
            except:
                # Final fallback to reportlab
                return self._convert_with_reportlab(md_content, session_id)
    
    def _convert_with_markdown_pdf(self, md_content: str, session_id: str) -> str:
        """Convert using markdown-pdf library"""
        try:
            import markdown
            from weasyprint import HTML, CSS
            from io import StringIO
            
            # Convert markdown to HTML
            html_content = markdown.markdown(md_content, extensions=['tables', 'toc'])
            
            # Add basic CSS styling
            css_style = """
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                margin: 40px;
                color: #333;
            }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
            h2 { color: #34495e; margin-top: 30px; }
            h3 { color: #7f8c8d; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            blockquote { border-left: 4px solid #3498db; padding-left: 20px; margin: 20px 0; }
            """
            
            # Create full HTML document
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Generate PDF
            filename = f"research_report_{session_id}.pdf"
            filepath = self.export_dir / filename
            
            HTML(string=full_html).write_pdf(str(filepath))
            
            return str(filepath)
            
        except ImportError:
            raise Exception("markdown and weasyprint libraries required for PDF export")
        except Exception as e:
            raise Exception(f"Markdown-PDF conversion failed: {str(e)}")
    
    def _convert_with_weasyprint(self, md_content: str, session_id: str) -> str:
        """Convert using weasyprint directly"""
        try:
            from weasyprint import HTML
            import markdown
            
            # Convert markdown to HTML
            html_content = markdown.markdown(md_content)
            
            filename = f"research_report_{session_id}.pdf"
            filepath = self.export_dir / filename
            
            HTML(string=html_content).write_pdf(str(filepath))
            
            return str(filepath)
            
        except ImportError:
            raise Exception("weasyprint library required")
    
    def _convert_with_reportlab(self, md_content: str, session_id: str) -> str:
        """Convert using reportlab as final fallback"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            import re
            
            filename = f"research_report_{session_id}.pdf"
            filepath = self.export_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Process markdown content line by line
            lines = md_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 0.2*inch))
                    continue
                
                # Handle headers
                if line.startswith('# '):
                    text = line[2:]
                    para = Paragraph(text, styles['Title'])
                    story.append(para)
                    story.append(Spacer(1, 0.3*inch))
                elif line.startswith('## '):
                    text = line[3:]
                    para = Paragraph(text, styles['Heading1'])
                    story.append(para)
                    story.append(Spacer(1, 0.2*inch))
                elif line.startswith('### '):
                    text = line[4:]
                    para = Paragraph(text, styles['Heading2'])
                    story.append(para)
                    story.append(Spacer(1, 0.1*inch))
                # Handle bold text
                elif line.startswith('**') and line.endswith('**'):
                    text = line[2:-2]
                    para = Paragraph(f"<b>{text}</b>", styles['Normal'])
                    story.append(para)
                # Handle regular text
                else:
                    if line and not line.startswith('|') and not line.startswith('-'):
                        para = Paragraph(line, styles['Normal'])
                        story.append(para)
                        story.append(Spacer(1, 0.1*inch))
            
            # Build PDF
            doc.build(story)
            
            return str(filepath)
            
        except ImportError:
            raise Exception("reportlab library required")
        except Exception as e:
            raise Exception(f"ReportLab conversion failed: {str(e)}")
    
    def export_json(self, report: Dict) -> str:
        """Export research report as JSON"""
        try:
            import json
            
            filename = f"research_report_{report['session_id']}.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            raise Exception(f"Failed to export JSON: {str(e)}")
    
    def cleanup_old_exports(self, days: int = 7):
        """Clean up old export files"""
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            for file_path in self.export_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Deleted old export: {file_path.name}")
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def get_export_stats(self) -> Dict:
        """Get statistics about exports"""
        try:
            files = list(self.export_dir.iterdir())
            
            stats = {
                'total_files': len(files),
                'pdf_files': len([f for f in files if f.suffix == '.pdf']),
                'md_files': len([f for f in files if f.suffix == '.md']),
                'json_files': len([f for f in files if f.suffix == '.json']),
                'total_size_mb': sum(f.stat().st_size for f in files) / (1024 * 1024)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats calculation failed: {str(e)}")
            return {'error': str(e)}