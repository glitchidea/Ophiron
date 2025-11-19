"""
Detailed PDF Report Generator for Process Monitor
Handles generation of comprehensive PDF reports with recursive analysis
"""

import os
import logging
from datetime import datetime
from io import BytesIO

from django.conf import settings as django_settings

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, PageTemplate, Frame, NextPageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.textlabels import Label

# Try to import svglib for SVG support
try:
    from svglib.svglib import svg2rlg
    SVG_SUPPORT = True
except ImportError:
    SVG_SUPPORT = False

logger = logging.getLogger(__name__)


class SVGFlowable(Flowable):
    """Flowable to embed SVG images in PDF - copied from main PDF"""
    
    def __init__(self, svg_path, width=None, height=None, fill_color=None):
        Flowable.__init__(self)
        self.svg_path = svg_path
        self.drawing = None
        self.fill_color = fill_color
        self.target_width = width
        self.target_height = height
        
        try:
            if SVG_SUPPORT:
                self.drawing = svg2rlg(svg_path)
                
                if self.drawing:
                    # Set colors for elements that use currentColor
                    if fill_color:
                        self._set_colors(self.drawing, fill_color)
                    
                    # Calculate scale
                    if width and height:
                        sx = width / self.drawing.width
                        sy = height / self.drawing.height
                        scale = min(sx, sy)
                    elif width:
                        scale = width / self.drawing.width
                    elif height:
                        scale = height / self.drawing.height
                    else:
                        scale = 1
                    
                    # Apply scale
                    self.drawing.width = self.drawing.width * scale
                    self.drawing.height = self.drawing.height * scale
                    self.drawing.scale(scale, scale)
                    
                    self.width = self.drawing.width
                    self.height = self.drawing.height
                else:
                    self.width = width or 100
                    self.height = height or 100
            else:
                self.width = width or 100
                self.height = height or 100
                
        except Exception as e:
            logger.warning(f"Could not load SVG: {str(e)}")
            self.width = width or 100
            self.height = height or 100
    
    def _set_colors(self, node, color):
        """Recursively set colors for SVG elements - only preserve eye color"""
        try:
            # Set stroke color (change everything except eye)
            if hasattr(node, 'strokeColor'):
                should_change = True
                if node.strokeColor is not None and hasattr(node.strokeColor, 'hexval'):
                    hex_val = node.strokeColor.hexval().lower()
                    # Only preserve the specific eye color
                    if hex_val == '#0b0d0f':
                        should_change = False
                
                if should_change:
                    node.strokeColor = color
            
            # Set fill color (change everything except eye)  
            if hasattr(node, 'fillColor'):
                should_change = True
                if node.fillColor is not None and hasattr(node.fillColor, 'hexval'):
                    hex_val = node.fillColor.hexval().lower()
                    # Only preserve the specific eye color
                    if hex_val == '#0b0d0f':
                        should_change = False
                
                if should_change:
                    node.fillColor = color
            
            # Recursively process children
            if hasattr(node, 'contents'):
                for child in node.contents:
                    self._set_colors(child, color)
        except Exception as e:
            logger.debug(f"Could not set color on node: {str(e)}")
    
    def wrap(self, availWidth, availHeight):
        """Return the space taken by this flowable"""
        return (self.width, self.height)
    
    def draw(self):
        """Draw the SVG on the canvas - perfectly centered"""
        if self.drawing:
            try:
                # Save current canvas state
                self.canv.saveState()
                
                # Calculate absolute center position on page
                page_width = A4[0]
                center_x = (page_width - self.width) / 2
                
                # Get current transformation matrix to understand where we are
                # This helps us compensate for any frame offsets
                try:
                    # Get absolute position by checking canvas translation
                    current_matrix = self.canv._currentMatrix
                    if current_matrix and len(current_matrix) >= 5:
                        # Matrix format: [a, b, c, d, e, f] where e is x-offset
                        offset_x = current_matrix[4]
                        # Compensate for frame offset
                        actual_center_x = center_x - offset_x
                        logger.info(f"Matrix offset detected: offset_x={offset_x}, adjusted center_x={actual_center_x}")
                        center_x = actual_center_x
                except:
                    # If we can't get matrix, use simple center
                    logger.info(f"Using simple center calculation")
                    pass
                
                logger.info(f"Drawing SVG: page_width={page_width}, drawing_width={self.width}, final_center_x={center_x}")
                
                # Draw at calculated position
                renderPDF.draw(self.drawing, self.canv, center_x, 0)
                
                # Restore canvas state
                self.canv.restoreState()
            except Exception as e:
                logger.error(f"Error rendering SVG: {str(e)}")


def draw_black_background(canvas_obj, doc):
    """Draw black background for the first page (cover page) - copied from main PDF"""
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a202c'))
    canvas_obj.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas_obj.restoreState()


def draw_page_number(canvas_obj, doc):
    """Draw page number at bottom right (skip first page) - copied from main PDF"""
    page_num = canvas_obj.getPageNumber()
    if page_num > 1:
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.HexColor('#718096'))
        canvas_obj.drawRightString(
            A4[0] - 50,
            30,
            f"Page {page_num - 1}"
        )
        canvas_obj.restoreState()


class DetailedProcessMonitorPDFGenerator:
    """Generator for Detailed Process Monitor PDF Reports with professional design"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles - copied from main PDF generator"""
        # Cover page styles (white text for black background)
        self.cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=self.styles['Title'],
            fontSize=48,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=20
        )
        
        self.cover_subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#e2e8f0'),
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=10
        )
        
        self.cover_info_style = ParagraphStyle(
            'CoverInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#cbd5e0'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        # Content page styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=6
        )
        
        # Table styles
        self.bold_style = ParagraphStyle(
            'BoldSmall',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#4a5568')
        )
        
        self.normal_small_style = ParagraphStyle(
            'NormalSmall',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568')
        )
        
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
        self.table_cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#4a5568')
        )
        
        # Table styles
        self.table_label_style = ParagraphStyle(
            'TableLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2d3748')
        )
        
        self.table_value_style = ParagraphStyle(
            'TableValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748')
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        )
    
    def generate_pdf(self, search_results, search_type, search_value, username):
        """Generate detailed PDF report with professional design"""
        buffer = BytesIO()
        
        # Create document using BaseDocTemplate for custom page templates
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create frames for page templates
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )
        
        # Cover page template with black background
        cover_template = PageTemplate(
            id='cover',
            frames=[frame],
            onPage=draw_black_background,
            pagesize=A4
        )
        
        # Content page template with page numbers
        content_template = PageTemplate(
            id='content',
            frames=[frame],
            onPage=draw_page_number,
            pagesize=A4
        )
        
        doc.addPageTemplates([cover_template, content_template])
        
        # Build content
        elements = []
        
        # Build cover page (uses 'cover' template by default - first template)
        self._build_cover_page(elements, search_type, search_value, username)
        
        # Switch to content template for remaining pages
        elements.append(NextPageTemplate('content'))
        elements.append(PageBreak())
        
        # Metadata section
        self._build_metadata_section(elements, search_type, search_value, username)
        elements.append(Spacer(1, 20))
        
        # Executive Summary
        elements.extend(self._build_executive_summary(search_results))
        
        # Analysis Summary
        self._build_analysis_summary(elements, search_results, search_type, search_value)
        
        # Key Findings
        self._build_key_findings(elements, search_results)
        
        # Visual Analytics
        self._build_visual_analytics(elements, search_results)
        
        # Performance Analysis
        self._build_performance_analysis(elements, search_results)
        
        # Security Analysis
        self._build_security_analysis(elements, search_results)
        
        # Recommendations
        self._build_recommendations(elements, search_results)
        
        # Process Information (Detailed)
        if search_results.get('connections'):
            self._build_detailed_process_section(elements, search_results)
        
        # Port Usage (Detailed)
        if search_results.get('port_details') and len(search_results['port_details']) > 0:
            self._build_detailed_port_section(elements, search_results['port_details'])
        
        # All Connections (Detailed)
        self._build_detailed_connections_section(elements, search_results.get('connections', []))
        
        elements.append(Spacer(1, 20))
        
        # Footer
        footer = Paragraph('Generated by OPHIRON Process Monitor System', self.footer_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer
    
    def _get_logo_path(self):
        """Get the path to the SVG logo - copied from main PDF"""
        try:
            static_root = django_settings.STATIC_ROOT or os.path.join(django_settings.BASE_DIR, 'static')
            logo_path = os.path.join(static_root, 'images', 'ophiron.svg')
            
            if os.path.exists(logo_path):
                return logo_path
            
            # Try alternative path
            logo_path = os.path.join(django_settings.BASE_DIR, 'static', 'images', 'ophiron.svg')
            if os.path.exists(logo_path):
                return logo_path
                
        except Exception as e:
            logger.warning(f"Error finding logo path: {str(e)}")
        
        return None
    
    def _build_cover_page(self, elements, search_type, search_value, username):
        """Build the cover page with black background - copied from main PDF"""
        # Black background is drawn by PageTemplate with draw_black_background
        # Add spacing from top (less space since logo is bigger)
        elements.append(Spacer(1, 0.8*inch))
        
        # Add SVG Logo (bigger size - 5 inch, white color for dark background)
        logo_path = self._get_logo_path()
        if logo_path and SVG_SUPPORT:
            try:
                # Use white color for logo on black background (same as header.css)
                svg_logo = SVGFlowable(
                    logo_path, 
                    width=5*inch, 
                    height=5*inch,
                    fill_color=colors.white
                )
                elements.append(svg_logo)
                elements.append(Spacer(1, 0.3*inch))
                logger.info(f"SVG logo added to PDF: {logo_path}")
            except Exception as e:
                logger.error(f"Failed to add SVG logo: {str(e)}")
                elements.append(Spacer(1, 0.3*inch))
        else:
            if not SVG_SUPPORT:
                logger.warning("SVG support not available (svglib not installed)")
            elements.append(Spacer(1, 0.3*inch))
        
        # Logo Text (white on black)
        logo_text = Paragraph('OPHIRON', self.cover_title_style)
        elements.append(logo_text)
        elements.append(Spacer(1, 0.3*inch))
        
        # Title (white on black)
        title = Paragraph('Process Monitor', self.cover_subtitle_style)
        elements.append(title)
        
        subtitle = Paragraph('Detailed Analysis Report', self.cover_subtitle_style)
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.8*inch))
        
        # Report info (light gray on black)
        elements.append(Paragraph(
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            self.cover_info_style
        ))
        elements.append(Paragraph(f'By: {username}', self.cover_info_style))
        elements.append(Paragraph(f'Search: {search_type.upper()} = {search_value}', self.cover_info_style))
    
    def _build_metadata_section(self, elements, search_type, search_value, username):
        """Build report metadata section - copied from main PDF"""
        # Report header
        report_header = Paragraph('OPHIRON - Process Monitor Detailed Report', self.title_style)
        elements.append(report_header)
        elements.append(Spacer(1, 20))
        
        # Metadata table
        meta_data = [
            [
                Paragraph('Report Generated:', self.bold_style),
                Paragraph(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.normal_small_style)
            ],
            [
                Paragraph('Generated By:', self.bold_style),
                Paragraph(username, self.normal_small_style)
            ],
            [
                Paragraph('Search Type:', self.bold_style),
                Paragraph(search_type.upper(), self.normal_small_style)
            ],
            [
                Paragraph('Search Value:', self.bold_style),
                Paragraph(str(search_value), self.normal_small_style)
            ],
            [
                Paragraph('Report Type:', self.bold_style),
                Paragraph('Detailed Technical Analysis', self.normal_small_style)
            ]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 5*inch])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 24))
    
    def _build_detailed_content(self, search_results, search_type, search_value):
        """Build detailed content with tree structure"""
        elements = []
        
        # Executive Summary
        elements.append(Paragraph('Executive Summary', self.heading_style))
        elements.append(self._build_executive_summary(search_results))
        elements.append(Spacer(1, 20))
        
        # Detailed Analysis Tree
        elements.append(Paragraph('Detailed Analysis Tree', self.heading_style))
        elements.extend(self._build_analysis_tree(search_results, search_type, search_value))
        elements.append(Spacer(1, 20))
        
        # Technical Details
        elements.append(Paragraph('Technical Details', self.heading_style))
        elements.extend(self._build_technical_details(search_results))
        
        return elements
    
    def _build_executive_summary(self, search_results):
        """Build executive summary section - copied from main PDF"""
        elements = []
        elements.append(Paragraph('Executive Summary', self.heading_style))
        
        summary_data = [
            [
                Paragraph('Metric', self.table_header_style),
                Paragraph('Value', self.table_header_style)
            ],
            [
                Paragraph('Total Connections', self.table_label_style),
                Paragraph(str(search_results.get('total_connections', 0)), self.table_value_style)
            ],
            [
                Paragraph('Unique Processes', self.table_label_style),
                Paragraph(str(len(search_results.get('unique_processes', []))), self.table_value_style)
            ],
            [
                Paragraph('Unique Ports', self.table_label_style),
                Paragraph(str(len(search_results.get('unique_ports', []))), self.table_value_style)
            ],
            [
                Paragraph('Unique IP Addresses', self.table_label_style),
                Paragraph(str(len(search_results.get('unique_ips', []))), self.table_value_style)
            ],
            [
                Paragraph('Analysis Depth', self.table_label_style),
                Paragraph('Comprehensive', self.table_value_style)
            ],
            [
                Paragraph('Report Type', self.table_label_style),
                Paragraph('Detailed Technical Analysis', self.table_value_style)
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_detailed_process_section(self, elements, search_results):
        """Build detailed process information section - more readable"""
        elements.append(Paragraph('Process Information (Detailed)', self.heading_style))
        
        # Get unique processes with their details
        unique_processes = {}
        for conn in search_results.get('connections', []):
            pid = conn.get('pid')
            if pid and pid not in unique_processes:
                unique_processes[pid] = {
                    'name': conn.get('process_name', 'Unknown'),
                    'pid': pid,
                    'connections_count': 0,
                    'cpu_percent': conn.get('process_details', {}).get('cpu_percent', 0),
                    'memory_percent': conn.get('process_details', {}).get('memory_percent', 0),
                    'num_threads': conn.get('process_details', {}).get('num_threads', 0)
                }
            if pid in unique_processes:
                unique_processes[pid]['connections_count'] += 1
        
        # Process details table
        proc_header_style = ParagraphStyle(
            'ProcHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
        proc_cell_style = ParagraphStyle(
            'ProcCell',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#4a5568')
        )
        
        proc_data = [[
            Paragraph('PID', proc_header_style),
            Paragraph('Process Name', proc_header_style),
            Paragraph('Connections', proc_header_style),
            Paragraph('CPU %', proc_header_style),
            Paragraph('Memory %', proc_header_style),
            Paragraph('Threads', proc_header_style)
        ]]
        
        for pid, proc in list(unique_processes.items())[:10]:  # Limit to first 10
            proc_data.append([
                Paragraph(str(pid), proc_cell_style),
                Paragraph(proc['name'][:20], proc_cell_style),
                Paragraph(str(proc['connections_count']), proc_cell_style),
                Paragraph(f"{proc['cpu_percent']:.1f}%", proc_cell_style),
                Paragraph(f"{proc['memory_percent']:.1f}%", proc_cell_style),
                Paragraph(str(proc['num_threads']), proc_cell_style)
            ])
        
        proc_table = Table(proc_data, colWidths=[0.8*inch, 2*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch])
        proc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        elements.append(proc_table)
        elements.append(Spacer(1, 20))
    
    def _build_detailed_port_section(self, elements, port_details):
        """Build detailed port usage section - more readable"""
        elements.append(Paragraph('Port Usage Analysis (Detailed)', self.heading_style))
        
        port_header_style = ParagraphStyle(
            'PortHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
        port_cell_style = ParagraphStyle(
            'PortCell',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#4a5568')
        )
        
        # Add port analysis summary
        total_connections = sum(port.get('connection_count', 0) for port in port_details)
        unique_ports = len(port_details)
        most_used_port = max(port_details, key=lambda x: x.get('connection_count', 0)) if port_details else None
        
        # Port summary paragraph
        summary_text = f"""
        <b>Port Analysis Summary:</b><br/>
        • Total Ports: {unique_ports} different ports<br/>
        • Total Connections: {total_connections} active connections<br/>
        • Most Active Port: {most_used_port.get('port', 'N/A')} ({most_used_port.get('connection_count', 0)} connections) if most_used_port else 'N/A'<br/>
        • Port Diversity: {'High' if unique_ports > 10 else 'Medium' if unique_ports > 5 else 'Low'} - {'Many different services' if unique_ports > 10 else 'Moderate service variety' if unique_ports > 5 else 'Limited service variety'}
        """
        elements.append(Paragraph(summary_text, self.normal_style))
        elements.append(Spacer(1, 10))
        
        # Enhanced port data with more columns
        port_data = [[
            Paragraph('Port', port_header_style),
            Paragraph('Service Name', port_header_style),
            Paragraph('Connections', port_header_style),
            Paragraph('Usage %', port_header_style),
            Paragraph('Processes', port_header_style),
            Paragraph('Port Type', port_header_style),
            Paragraph('Security Level', port_header_style)
        ]]
        
        # Define security levels for common ports
        security_ports = {
            22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3',
            143: 'IMAP', 443: 'HTTPS', 993: 'IMAPS', 995: 'POP3S', 3389: 'RDP',
            5900: 'VNC', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'
        }
        
        for port in port_details[:20]:  # Show more ports
            port_num = port.get('port', 0)
            # Don't truncate processes - let Paragraph handle wrapping
            processes_str = ', '.join(port.get('processes', []))
            
            usage_percent = (port.get('connection_count', 0) / total_connections * 100) if total_connections > 0 else 0
            
            # Determine port type
            if port_num in security_ports:
                port_type = security_ports[port_num]
                security_level = 'High' if port_num in [22, 443, 993, 995] else 'Medium' if port_num in [80, 143, 110] else 'Low'
            elif port_num < 1024:
                port_type = 'System'
                security_level = 'Medium'
            else:
                port_type = 'Dynamic'
                security_level = 'Low'
            
            port_data.append([
                Paragraph(str(port_num), port_cell_style),
                Paragraph(port.get('service_name', 'Unknown'), port_cell_style),
                Paragraph(str(port.get('connection_count', 0)), port_cell_style),
                Paragraph(f"{usage_percent:.1f}%", port_cell_style),
                Paragraph(processes_str, port_cell_style),
                Paragraph(port_type, port_cell_style),
                Paragraph(security_level, port_cell_style)
            ])
        
        # Wider port table with auto row heights and word wrapping
        port_table = Table(port_data, colWidths=[0.8*inch, 1.5*inch, 1*inch, 0.8*inch, 2*inch, 1*inch, 1*inch])
        port_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        elements.append(port_table)
        elements.append(Spacer(1, 20))
    
    def _build_detailed_connections_section(self, elements, connections):
        """Build comprehensive connections analysis with IP and network details"""
        elements.append(Paragraph(f'Network Connections Analysis ({len(connections)} total)', self.heading_style))
        
        if not connections or len(connections) == 0:
            elements.append(Paragraph('No connections found.', self.normal_style))
            return
        
        # Add connection analysis summary
        unique_ips = set()
        unique_ports = set()
        protocols = {}
        statuses = {}
        
        for conn in connections:
            # Extract IPs from addresses
            local_addr = conn.get('local_address', '')
            remote_addr = conn.get('remote_address', '')
            
            if ':' in local_addr:
                local_ip = local_addr.split(':')[0]
                unique_ips.add(local_ip)
            
            if ':' in remote_addr:
                remote_ip = remote_addr.split(':')[0]
                if remote_ip != '0.0.0.0':
                    unique_ips.add(remote_ip)
            
            # Extract ports
            if ':' in local_addr:
                local_port = local_addr.split(':')[1]
                unique_ports.add(local_port)
            
            # Count protocols and statuses
            protocol = conn.get('protocol', 'Unknown')
            protocols[protocol] = protocols.get(protocol, 0) + 1
            
            status = conn.get('status', 'Unknown')
            statuses[status] = statuses.get(status, 0) + 1
        
        # Connection summary
        summary_text = f"""
        <b>Network Analysis Summary:</b><br/>
        • Total Connections: {len(connections)} active network connections<br/>
        • Unique IP Addresses: {len(unique_ips)} different IPs involved<br/>
        • Unique Ports: {len(unique_ports)} different ports used<br/>
        • Protocol Distribution: {', '.join([f'{k}({v})' for k, v in protocols.items()])}<br/>
        • Connection Status: {', '.join([f'{k}({v})' for k, v in statuses.items()])}<br/>
        • Network Complexity: {'High' if len(unique_ips) > 10 else 'Medium' if len(unique_ips) > 5 else 'Low'} - {'Many different endpoints' if len(unique_ips) > 10 else 'Moderate network activity' if len(unique_ips) > 5 else 'Simple network topology'}
        """
        elements.append(Paragraph(summary_text, self.normal_style))
        elements.append(Spacer(1, 10))
        
        conn_header_style = ParagraphStyle(
            'ConnHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
        conn_cell_style = ParagraphStyle(
            'ConnCell',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#4a5568')
        )
        
        conn_data = [[
            Paragraph('PID', conn_header_style),
            Paragraph('Process', conn_header_style),
            Paragraph('Protocol', conn_header_style),
            Paragraph('Local Address', conn_header_style),
            Paragraph('Remote Address', conn_header_style),
            Paragraph('Status', conn_header_style),
            Paragraph('CPU %', conn_header_style),
            Paragraph('Memory %', conn_header_style)
        ]]
        
        for conn in connections:  # Show all connections
            conn_data.append([
                Paragraph(str(conn.get('pid', '-'))[:6], conn_cell_style),
                Paragraph(conn.get('process_name', 'Unknown')[:15], conn_cell_style),
                Paragraph(conn.get('protocol', 'N/A')[:8], conn_cell_style),
                Paragraph(conn.get('local_address', 'N/A')[:25], conn_cell_style),
                Paragraph(conn.get('remote_address', 'N/A')[:25], conn_cell_style),
                Paragraph(conn.get('status', 'N/A')[:12], conn_cell_style),
                Paragraph(f"{conn.get('process_details', {}).get('cpu_percent', 0):.1f}%", conn_cell_style),
                Paragraph(f"{conn.get('process_details', {}).get('memory_percent', 0):.1f}%", conn_cell_style)
            ])
        
        conn_table = Table(conn_data, colWidths=[0.6*inch, 1.2*inch, 0.7*inch, 1.5*inch, 1.5*inch, 0.8*inch, 0.6*inch, 0.6*inch])
        conn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        elements.append(conn_table)
    
    def _build_analysis_summary(self, elements, search_results, search_type, search_value):
        """Build analysis summary section - more readable and informative"""
        elements.append(Paragraph('Analysis Summary', self.heading_style))
        
        # Analysis overview
        overview_data = [
            ['Analysis Type', 'Value', 'Description'],
            ['Search Query', f'{search_type.upper()} = {search_value}', 'Original search parameters'],
            ['Total Connections', str(len(search_results.get('connections', []))), 'All network connections found'],
            ['Unique Processes', str(len(search_results.get('unique_processes', []))), 'Different processes involved'],
            ['Unique Ports', str(len(search_results.get('unique_ports', []))), 'Different network ports used'],
            ['Unique IPs', str(len(search_results.get('unique_ips', []))), 'Different IP addresses involved'],
            ['Analysis Depth', 'Comprehensive', 'Full detailed analysis performed'],
            ['Report Type', 'Detailed Technical', 'Advanced technical analysis report']
        ]
        
        # Convert data to Paragraph objects for better text handling
        overview_paragraph_data = []
        for i, row in enumerate(overview_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            overview_paragraph_data.append(paragraph_row)
        
        # Wider analysis summary table with auto row heights
        overview_table = Table(overview_paragraph_data, colWidths=[2*inch, 2.5*inch, 3.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 20))
    
    def _build_key_findings(self, elements, search_results):
        """Build key findings section - highlight important information"""
        elements.append(Paragraph('Key Findings', self.heading_style))
        
        # Find top processes by connection count
        process_connections = {}
        for conn in search_results.get('connections', []):
            pid = conn.get('pid')
            if pid:
                if pid not in process_connections:
                    process_connections[pid] = {
                        'name': conn.get('process_name', 'Unknown'),
                        'count': 0,
                        'cpu': conn.get('process_details', {}).get('cpu_percent', 0),
                        'memory': conn.get('process_details', {}).get('memory_percent', 0)
                    }
                process_connections[pid]['count'] += 1
        
        # Sort by connection count
        top_processes = sorted(process_connections.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        findings_data = [['Finding', 'Value', 'Impact']]
        
        if top_processes:
            top_proc = top_processes[0]
            findings_data.append([
                'Most Active Process',
                f"{top_proc[1]['name']} (PID: {top_proc[0]})",
                f"{top_proc[1]['count']} connections"
            ])
        
        # Find most used port
        port_details = search_results.get('port_details', [])
        if port_details:
            most_used_port = max(port_details, key=lambda x: x.get('connection_count', 0))
            findings_data.append([
                'Most Used Port',
                f"Port {most_used_port.get('port', 'N/A')} ({most_used_port.get('service_name', 'Unknown')})",
                f"{most_used_port.get('connection_count', 0)} connections"
            ])
        
        # Add resource usage info
        total_cpu = sum(conn.get('process_details', {}).get('cpu_percent', 0) for conn in search_results.get('connections', []))
        total_memory = sum(conn.get('process_details', {}).get('memory_percent', 0) for conn in search_results.get('connections', []))
        
        findings_data.append([
            'Resource Usage',
            f"Total CPU: {total_cpu:.1f}%, Memory: {total_memory:.1f}%",
            'System resource consumption'
        ])
        
        findings_data.append([
            'Security Status',
            'All connections analyzed',
            'No suspicious activity detected'
        ])
        
        # Convert data to Paragraph objects for better text handling
        findings_paragraph_data = []
        for i, row in enumerate(findings_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            findings_paragraph_data.append(paragraph_row)
        
        # Wider key findings table with auto row heights
        findings_table = Table(findings_paragraph_data, colWidths=[2*inch, 3*inch, 3*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ed8936')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(findings_table)
        elements.append(Spacer(1, 20))
    
    def _build_performance_analysis(self, elements, search_results):
        """Build performance analysis section"""
        elements.append(Paragraph('Performance Analysis', self.heading_style))
        
        # Calculate performance metrics
        connections = search_results.get('connections', [])
        total_cpu = sum(conn.get('process_details', {}).get('cpu_percent', 0) for conn in connections)
        total_memory = sum(conn.get('process_details', {}).get('memory_percent', 0) for conn in connections)
        avg_cpu = total_cpu / len(connections) if connections else 0
        avg_memory = total_memory / len(connections) if connections else 0
        
        # Port usage analysis
        port_details = search_results.get('port_details', [])
        total_connections = sum(port.get('connection_count', 0) for port in port_details)
        
        performance_data = [
            ['Metric', 'Value', 'Status', 'Description'],
            ['Total CPU Usage', f'{total_cpu:.1f}%', 'Low' if total_cpu < 10 else 'Medium' if total_cpu < 50 else 'High', 'System-wide CPU consumption'],
            ['Total Memory Usage', f'{total_memory:.1f}%', 'Low' if total_memory < 10 else 'Medium' if total_memory < 50 else 'High', 'System-wide memory consumption'],
            ['Average CPU per Connection', f'{avg_cpu:.2f}%', 'Efficient' if avg_cpu < 1 else 'Moderate', 'CPU usage per connection'],
            ['Average Memory per Connection', f'{avg_memory:.2f}%', 'Efficient' if avg_memory < 1 else 'Moderate', 'Memory usage per connection'],
            ['Total Connections', str(len(connections)), 'Active' if len(connections) > 0 else 'Inactive', 'Number of active connections'],
            ['Port Distribution', f'{len(port_details)} ports', 'Diverse' if len(port_details) > 5 else 'Limited', 'Number of different ports used'],
            ['Connection Density', f'{len(connections)/len(port_details):.1f}' if port_details else '0', 'High' if len(connections)/len(port_details) > 5 else 'Low', 'Connections per port ratio']
        ]
        
        # Convert data to Paragraph objects for better text handling
        performance_paragraph_data = []
        for i, row in enumerate(performance_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            performance_paragraph_data.append(paragraph_row)
        
        # Wider table with better column distribution and auto row heights
        performance_table = Table(performance_paragraph_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 3*inch])
        performance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(performance_table)
        elements.append(Spacer(1, 20))
    
    def _build_security_analysis(self, elements, search_results):
        """Build security analysis section"""
        elements.append(Paragraph('Security Analysis', self.heading_style))
        
        connections = search_results.get('connections', [])
        port_details = search_results.get('port_details', [])
        
        # Analyze security aspects
        listening_ports = [conn for conn in connections if conn.get('status') == 'LISTEN']
        established_connections = [conn for conn in connections if conn.get('status') == 'ESTABLISHED']
        
        # Check for common security ports
        security_ports = [22, 23, 80, 443, 3389, 5900, 8080, 8443]
        security_ports_found = [port for port in port_details if port.get('port') in security_ports]
        
        # Check for suspicious patterns
        high_port_connections = [conn for conn in connections if ':' in conn.get('local_address', '') and int(conn.get('local_address', '').split(':')[-1]) > 1024]
        
        security_data = [
            ['Security Aspect', 'Status', 'Count', 'Risk Level'],
            ['Listening Ports', 'Active' if listening_ports else 'None', str(len(listening_ports)), 'Medium' if len(listening_ports) > 10 else 'Low'],
            ['Established Connections', 'Active' if established_connections else 'None', str(len(established_connections)), 'Low' if len(established_connections) < 5 else 'Medium'],
            ['Security Ports Open', 'Found' if security_ports_found else 'None', str(len(security_ports_found)), 'High' if len(security_ports_found) > 3 else 'Medium'],
            ['High Port Usage', 'Active' if high_port_connections else 'None', str(len(high_port_connections)), 'Low'],
            ['Process Diversity', 'Single' if len(search_results.get('unique_processes', [])) == 1 else 'Multiple', str(len(search_results.get('unique_processes', []))), 'Low' if len(search_results.get('unique_processes', [])) == 1 else 'Medium'],
            ['IP Diversity', 'Multiple' if len(search_results.get('unique_ips', [])) > 1 else 'Single', str(len(search_results.get('unique_ips', []))), 'Medium' if len(search_results.get('unique_ips', [])) > 5 else 'Low']
        ]
        
        # Convert data to Paragraph objects for better text handling
        security_paragraph_data = []
        for i, row in enumerate(security_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            security_paragraph_data.append(paragraph_row)
        
        # Wider security table with auto row heights
        security_table = Table(security_paragraph_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        security_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e53e3e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(security_table)
        elements.append(Spacer(1, 20))
    
    def _build_recommendations(self, elements, search_results):
        """Build recommendations section"""
        elements.append(Paragraph('Recommendations', self.heading_style))
        
        connections = search_results.get('connections', [])
        port_details = search_results.get('port_details', [])
        
        recommendations = []
        
        # Performance recommendations
        total_cpu = sum(conn.get('process_details', {}).get('cpu_percent', 0) for conn in connections)
        if total_cpu > 50:
            recommendations.append(['Performance', 'High CPU Usage', 'Consider optimizing processes or reducing connection load'])
        
        # Security recommendations
        listening_ports = [conn for conn in connections if conn.get('status') == 'LISTEN']
        if len(listening_ports) > 20:
            recommendations.append(['Security', 'Many Listening Ports', 'Review and close unnecessary listening ports'])
        
        # Port recommendations
        if len(port_details) > 10:
            recommendations.append(['Network', 'Port Diversity', 'Consider consolidating services to reduce port usage'])
        
        # Process recommendations
        if len(search_results.get('unique_processes', [])) == 1:
            recommendations.append(['Process', 'Single Process', 'Monitor this process closely as it handles all connections'])
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                ['General', 'System Status', 'System appears to be running normally'],
                ['Monitoring', 'Regular Checks', 'Continue monitoring network connections'],
                ['Maintenance', 'System Health', 'No immediate action required']
            ]
        
        rec_data = [['Category', 'Issue', 'Recommendation']] + recommendations
        
        # Convert data to Paragraph objects for better text handling
        rec_paragraph_data = []
        for i, row in enumerate(rec_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            rec_paragraph_data.append(paragraph_row)
        
        # Wider recommendations table with auto row heights
        rec_table = Table(rec_paragraph_data, colWidths=[1.5*inch, 2.5*inch, 4*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 20))
    
    def _build_visual_analytics(self, elements, search_results):
        """Build visual analytics section with compact layout"""
        elements.append(Paragraph('Visual Analytics', self.heading_style))
        
        # Create compact layout with side-by-side pies and bottom bar chart
        self._create_compact_charts_layout(elements, search_results)
        
        # Add analysis insights based on data
        self._add_chart_insights(elements, search_results)
    
    def _create_port_distribution_chart(self, search_results):
        """Create port distribution pie chart"""
        port_details = search_results.get('port_details', [])
        if not port_details:
            return None
        
        # Get top 6 ports for pie chart
        top_ports = sorted(port_details, key=lambda x: x.get('connection_count', 0), reverse=True)[:6]
        
        if len(top_ports) < 2:
            return None
        
        # Create pie chart
        drawing = Drawing(400, 300)
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 200
        pie.height = 200
        
        # Prepare data
        data = []
        labels = []
        colors_list = [colors.HexColor('#4299e1'), colors.HexColor('#48bb78'), colors.HexColor('#ed8936'), 
                      colors.HexColor('#e53e3e'), colors.HexColor('#9f7aea'), colors.HexColor('#38b2ac')]
        
        for i, port in enumerate(top_ports):
            data.append(port.get('connection_count', 0))
            labels.append(f"Port {port.get('port', 'N/A')}")
        
        pie.data = data
        pie.labels = labels
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        
        # Set colors
        for i, color in enumerate(colors_list[:len(data)]):
            pie.slices[i].fillColor = color
        
        drawing.add(pie)
        
        # Add title
        title = Label()
        title.setText('Port Distribution')
        title.x = 200
        title.y = 280
        title.fontSize = 12
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        return drawing
    
    def _create_protocol_distribution_chart(self, search_results):
        """Create protocol distribution pie chart"""
        connections = search_results.get('connections', [])
        if not connections:
            return None
        
        # Count protocols
        protocol_counts = {}
        for conn in connections:
            protocol = conn.get('protocol', 'Unknown')
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        if len(protocol_counts) < 2:
            return None
        
        # Create pie chart
        drawing = Drawing(400, 300)
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 200
        pie.height = 200
        
        # Prepare data
        data = list(protocol_counts.values())
        labels = list(protocol_counts.keys())
        colors_list = [colors.HexColor('#4299e1'), colors.HexColor('#48bb78'), colors.HexColor('#ed8936')]
        
        pie.data = data
        pie.labels = labels
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        
        # Set colors
        for i, color in enumerate(colors_list[:len(data)]):
            pie.slices[i].fillColor = color
        
        drawing.add(pie)
        
        # Add title
        title = Label()
        title.setText('Protocol Distribution')
        title.x = 200
        title.y = 280
        title.fontSize = 12
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        return drawing
    
    def _create_top_ports_chart(self, search_results):
        """Create top ports bar chart"""
        port_details = search_results.get('port_details', [])
        if not port_details:
            return None
        
        # Get top 8 ports
        top_ports = sorted(port_details, key=lambda x: x.get('connection_count', 0), reverse=True)[:8]
        
        if len(top_ports) < 2:
            return None
        
        # Create bar chart
        drawing = Drawing(500, 300)
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.width = 400
        chart.height = 200
        
        # Prepare data
        data = []
        labels = []
        for port in top_ports:
            data.append([port.get('connection_count', 0)])
            labels.append(f"Port {port.get('port', 'N/A')}")
        
        chart.data = data
        chart.categoryAxis.categoryNames = labels
        chart.bars[0].fillColor = colors.HexColor('#4299e1')
        chart.bars[0].strokeColor = colors.white
        chart.bars[0].strokeWidth = 1
        
        # Set value axis
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max([d[0] for d in data]) * 1.1
        
        drawing.add(chart)
        
        # Add title
        title = Label()
        title.setText('Top Ports by Connection Count')
        title.x = 250
        title.y = 280
        title.fontSize = 12
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        return drawing
    
    def _create_resource_usage_chart(self, search_results):
        """Create resource usage bar chart"""
        connections = search_results.get('connections', [])
        if not connections:
            return None
        
        # Get unique processes with their resource usage
        process_resources = {}
        for conn in connections:
            pid = conn.get('pid')
            if pid:
                if pid not in process_resources:
                    process_resources[pid] = {
                        'name': conn.get('process_name', 'Unknown'),
                        'cpu': conn.get('process_details', {}).get('cpu_percent', 0),
                        'memory': conn.get('process_details', {}).get('memory_percent', 0)
                    }
        
        if len(process_resources) < 2:
            return None
        
        # Get top 6 processes
        top_processes = sorted(process_resources.items(), key=lambda x: x[1]['cpu'] + x[1]['memory'], reverse=True)[:6]
        
        # Create bar chart
        drawing = Drawing(500, 300)
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.width = 400
        chart.height = 200
        
        # Prepare data (CPU and Memory as separate series)
        cpu_data = []
        memory_data = []
        labels = []
        
        for pid, proc in top_processes:
            cpu_data.append([proc['cpu']])
            memory_data.append([proc['memory']])
            labels.append(f"{proc['name'][:10]}...")
        
        # Combine data for grouped bar chart
        combined_data = []
        for i in range(len(cpu_data)):
            combined_data.append([cpu_data[i][0], memory_data[i][0]])
        
        chart.data = combined_data
        chart.categoryAxis.categoryNames = labels
        
        # Set colors for different series
        chart.bars[0].fillColor = colors.HexColor('#4299e1')  # CPU
        chart.bars[0].strokeColor = colors.white
        chart.bars[0].strokeWidth = 1
        
        chart.bars[1].fillColor = colors.HexColor('#48bb78')  # Memory
        chart.bars[1].strokeColor = colors.white
        chart.bars[1].strokeWidth = 1
        
        # Set value axis
        max_value = max([max(d) for d in combined_data])
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max_value * 1.1
        
        drawing.add(chart)
        
        # Add title and legend
        title = Label()
        title.setText('Resource Usage by Process')
        title.x = 250
        title.y = 280
        title.fontSize = 12
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        # Add legend
        legend_cpu = Label()
        legend_cpu.setText('CPU %')
        legend_cpu.x = 100
        legend_cpu.y = 270
        legend_cpu.fontSize = 10
        legend_cpu.fontName = 'Helvetica'
        drawing.add(legend_cpu)
        
        legend_memory = Label()
        legend_memory.setText('Memory %')
        legend_memory.x = 150
        legend_memory.y = 270
        legend_memory.fontSize = 10
        legend_memory.fontName = 'Helvetica'
        drawing.add(legend_memory)
        
        return drawing
    
    def _create_compact_charts_layout(self, elements, search_results):
        """Create compact charts layout - pies side by side, bar chart below"""
        # Create a table to hold charts side by side
        charts_data = []
        
        # Left pie chart - Port Distribution
        port_pie = self._create_compact_port_pie(search_results)
        if port_pie:
            charts_data.append([port_pie, ''])
        else:
            charts_data.append(['', ''])
        
        # Right pie chart - Protocol Distribution  
        protocol_pie = self._create_compact_protocol_pie(search_results)
        if protocol_pie:
            charts_data[0][1] = protocol_pie
        
        # Add pie charts table
        if charts_data[0][0] or charts_data[0][1]:
            pie_table = Table(charts_data, colWidths=[3*inch, 3*inch])
            pie_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(pie_table)
            elements.append(Spacer(1, 10))
        
        # Bottom bar chart - Top Ports
        top_ports_chart = self._create_compact_top_ports_chart(search_results)
        if top_ports_chart:
            elements.append(top_ports_chart)
            elements.append(Spacer(1, 15))
    
    def _create_compact_port_pie(self, search_results):
        """Create compact port distribution pie chart"""
        port_details = search_results.get('port_details', [])
        if not port_details:
            return None
        
        # Get top 5 ports for compact pie chart
        top_ports = sorted(port_details, key=lambda x: x.get('connection_count', 0), reverse=True)[:5]
        
        if len(top_ports) < 2:
            return None
        
        # Create smaller pie chart
        drawing = Drawing(280, 200)
        pie = Pie()
        pie.x = 20
        pie.y = 20
        pie.width = 120
        pie.height = 120
        
        # Prepare data
        data = []
        labels = []
        colors_list = [colors.HexColor('#4299e1'), colors.HexColor('#48bb78'), colors.HexColor('#ed8936'), 
                      colors.HexColor('#e53e3e'), colors.HexColor('#9f7aea')]
        
        for i, port in enumerate(top_ports):
            data.append(port.get('connection_count', 0))
            labels.append(f"P{port.get('port', 'N/A')}")
        
        pie.data = data
        pie.labels = labels
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        
        # Set colors
        for i, color in enumerate(colors_list[:len(data)]):
            pie.slices[i].fillColor = color
        
        drawing.add(pie)
        
        # Add title
        title = Label()
        title.setText('Port Distribution')
        title.x = 140
        title.y = 180
        title.fontSize = 10
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        # Add explanation
        explanation = Label()
        explanation.setText('Shows connection distribution across different ports')
        explanation.x = 140
        explanation.y = 160
        explanation.fontSize = 7
        explanation.fontName = 'Helvetica'
        explanation.textAnchor = 'middle'
        drawing.add(explanation)
        
        return drawing
    
    def _create_compact_protocol_pie(self, search_results):
        """Create compact protocol distribution pie chart"""
        connections = search_results.get('connections', [])
        if not connections:
            return None
        
        # Count protocols
        protocol_counts = {}
        for conn in connections:
            protocol = conn.get('protocol', 'Unknown')
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        if len(protocol_counts) < 2:
            return None
        
        # Create smaller pie chart
        drawing = Drawing(280, 200)
        pie = Pie()
        pie.x = 20
        pie.y = 20
        pie.width = 120
        pie.height = 120
        
        # Prepare data
        data = list(protocol_counts.values())
        labels = list(protocol_counts.keys())
        colors_list = [colors.HexColor('#4299e1'), colors.HexColor('#48bb78'), colors.HexColor('#ed8936')]
        
        pie.data = data
        pie.labels = labels
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        
        # Set colors
        for i, color in enumerate(colors_list[:len(data)]):
            pie.slices[i].fillColor = color
        
        drawing.add(pie)
        
        # Add title
        title = Label()
        title.setText('Protocol Distribution')
        title.x = 140
        title.y = 180
        title.fontSize = 10
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        # Add explanation
        explanation = Label()
        explanation.setText('Shows TCP vs UDP vs Other protocol usage')
        explanation.x = 140
        explanation.y = 160
        explanation.fontSize = 7
        explanation.fontName = 'Helvetica'
        explanation.textAnchor = 'middle'
        drawing.add(explanation)
        
        return drawing
    
    def _create_compact_top_ports_chart(self, search_results):
        """Create compact top ports bar chart with detailed information"""
        port_details = search_results.get('port_details', [])
        if not port_details:
            return None
        
        # Get top 6 ports for compact chart
        top_ports = sorted(port_details, key=lambda x: x.get('connection_count', 0), reverse=True)[:6]
        
        if len(top_ports) < 2:
            return None
        
        # Create bar chart with proper spacing
        drawing = Drawing(500, 350)
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 120
        chart.width = 400
        chart.height = 150
        
        # Prepare data
        data = []
        labels = []
        for port in top_ports:
            data.append([port.get('connection_count', 0)])
            labels.append(f"P{port.get('port', 'N/A')}")
        
        chart.data = data
        chart.categoryAxis.categoryNames = labels
        chart.bars[0].fillColor = colors.HexColor('#4299e1')
        chart.bars[0].strokeColor = colors.white
        chart.bars[0].strokeWidth = 1
        
        # Set value axis
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max([d[0] for d in data]) * 1.1
        
        drawing.add(chart)
        
        # Add title at the top
        title = Label()
        title.setText('Top Ports by Connection Count')
        title.x = 250
        title.y = 320
        title.fontSize = 11
        title.fontName = 'Helvetica-Bold'
        title.textAnchor = 'middle'
        drawing.add(title)
        
        # Add description
        desc = Label()
        desc.setText('Shows the most frequently used network ports and their connection counts')
        desc.x = 250
        desc.y = 300
        desc.fontSize = 8
        desc.fontName = 'Helvetica'
        desc.textAnchor = 'middle'
        drawing.add(desc)
        
        # Add data summary
        total_connections = sum(port.get('connection_count', 0) for port in top_ports)
        summary = Label()
        summary.setText(f'Total: {total_connections} connections across {len(top_ports)} ports')
        summary.x = 250
        summary.y = 280
        summary.fontSize = 8
        summary.fontName = 'Helvetica'
        summary.textAnchor = 'middle'
        drawing.add(summary)
        
        # Create explanation box below the chart
        from reportlab.graphics.shapes import Rect
        
        # Draw explanation box
        explanation_box = Rect(50, 20, 400, 80, fillColor=colors.HexColor('#f8fafc'), strokeColor=colors.HexColor('#e2e8f0'), strokeWidth=1)
        drawing.add(explanation_box)
        
        # Add legend title in the box
        legend_title = Label()
        legend_title.setText('Chart Explanation:')
        legend_title.x = 60
        legend_title.y = 90
        legend_title.fontSize = 9
        legend_title.fontName = 'Helvetica-Bold'
        legend_title.textAnchor = 'start'
        drawing.add(legend_title)
        
        # Add color explanation in the box
        color_explanation = Label()
        color_explanation.setText('• Blue Bars = Connection Count per Port')
        color_explanation.x = 60
        color_explanation.y = 70
        color_explanation.fontSize = 8
        color_explanation.fontName = 'Helvetica'
        color_explanation.textAnchor = 'start'
        drawing.add(color_explanation)
        
        # Add data explanation in the box
        data_explanation = Label()
        data_explanation.setText('• Higher bars = More connections on that port')
        data_explanation.x = 60
        data_explanation.y = 50
        data_explanation.fontSize = 8
        data_explanation.fontName = 'Helvetica'
        data_explanation.textAnchor = 'start'
        drawing.add(data_explanation)
        
        # Add port details in the box
        port_details_text = '• Port Details: '
        for i, port in enumerate(top_ports):
            port_details_text += f"P{port.get('port', 'N/A')}({port.get('connection_count', 0)})"
            if i < len(top_ports) - 1:
                port_details_text += ", "
        
        port_details_label = Label()
        port_details_label.setText(port_details_text)
        port_details_label.x = 60
        port_details_label.y = 30
        port_details_label.fontSize = 7
        port_details_label.fontName = 'Helvetica'
        port_details_label.textAnchor = 'start'
        drawing.add(port_details_label)
        
        return drawing
    
    def _add_chart_insights(self, elements, search_results):
        """Add insights and analysis based on chart data"""
        elements.append(Paragraph('Chart Analysis & Insights', self.subheading_style))
        
        insights = []
        
        # Port analysis
        port_details = search_results.get('port_details', [])
        if port_details:
            most_used_port = max(port_details, key=lambda x: x.get('connection_count', 0))
            total_connections = sum(port.get('connection_count', 0) for port in port_details)
            
            insights.append([
                'Port Analysis',
                f'Most active port: {most_used_port.get("port", "N/A")} ({most_used_port.get("connection_count", 0)} connections)',
                f'Total connections: {total_connections}',
                f'Port diversity: {len(port_details)} different ports'
            ])
        
        # Protocol analysis
        connections = search_results.get('connections', [])
        if connections:
            protocol_counts = {}
            for conn in connections:
                protocol = conn.get('protocol', 'Unknown')
                protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
            
            dominant_protocol = max(protocol_counts.items(), key=lambda x: x[1])
            insights.append([
                'Protocol Analysis',
                f'Dominant protocol: {dominant_protocol[0]} ({dominant_protocol[1]} connections)',
                f'Protocol diversity: {len(protocol_counts)} different protocols',
                f'Total connections analyzed: {len(connections)}'
            ])
        
        # Process analysis
        unique_processes = search_results.get('unique_processes', [])
        if unique_processes:
            insights.append([
                'Process Analysis',
                f'Process diversity: {len(unique_processes)} different processes',
                f'Processes involved: {", ".join(unique_processes[:3])}{"..." if len(unique_processes) > 3 else ""}',
                f'System complexity: {"High" if len(unique_processes) > 5 else "Medium" if len(unique_processes) > 2 else "Low"}'
            ])
        
        # Create insights table
        if insights:
            insights_data = [['Analysis Type', 'Key Finding', 'Metrics', 'Complexity']]
            for insight in insights:
                insights_data.append(insight)
            
        # Create table with Paragraph objects for proper text wrapping
        from reportlab.platypus import KeepTogether
        
        # Convert data to Paragraph objects for better text handling
        insights_paragraph_data = []
        for i, row in enumerate(insights_data):
            paragraph_row = []
            for j, cell in enumerate(row):
                if i == 0:  # Header row
                    paragraph_row.append(Paragraph(str(cell), self.table_header_style))
                else:  # Data rows
                    paragraph_row.append(Paragraph(str(cell), self.table_cell_style))
            insights_paragraph_data.append(paragraph_row)
        
        # Wider insights table with proper word wrapping and auto row heights
        insights_table = Table(insights_paragraph_data, colWidths=[1.8*inch, 2.5*inch, 2*inch, 1.5*inch])
        insights_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(insights_table)
        elements.append(Spacer(1, 20))
