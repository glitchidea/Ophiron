"""
PDF Report Generator for Process Monitor
Handles generation of professional PDF reports for connection searches
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

# Try to import svglib for SVG support
try:
    from svglib.svglib import svg2rlg
    SVG_SUPPORT = True
except ImportError:
    SVG_SUPPORT = False

logger = logging.getLogger(__name__)


def draw_black_background(canvas_obj, doc):
    """Draw black background for the first page (cover page)"""
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#1a202c'))
    canvas_obj.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas_obj.restoreState()


def draw_page_number(canvas_obj, doc):
    """Draw page number at bottom right (skip first page)"""
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


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for adding page numbers"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


class SVGFlowable(Flowable):
    """Flowable to embed SVG images in PDF"""
    
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


class ProcessMonitorPDFGenerator:
    """Generator for Process Monitor PDF Reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom paragraph styles"""
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
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
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
    
    def _get_logo_path(self):
        """Get the path to the SVG logo"""
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
    
    def _build_cover_page(self, elements, username):
        """Build the cover page with black background"""
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
        
        subtitle = Paragraph('Connection Search Report', self.cover_subtitle_style)
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.8*inch))
        
        # Report info (light gray on black)
        elements.append(Paragraph(
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            self.cover_info_style
        ))
        elements.append(Paragraph(f'By: {username}', self.cover_info_style))
        
        # No PageBreak here - it's added in generate_pdf() to switch templates
    
    def _build_metadata_section(self, elements, search_type, search_value, username):
        """Build report metadata section"""
        # Report header
        report_header = Paragraph('OPHIRON - Process Monitor Report', self.title_style)
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
    
    def _build_summary_section(self, elements, summary):
        """Build executive summary section"""
        elements.append(Paragraph('Executive Summary', self.heading_style))
        
        summary_data = [
            [
                Paragraph('Metric', self.table_header_style),
                Paragraph('Value', self.table_header_style)
            ],
            [
                Paragraph('Total Connections', self.table_label_style),
                Paragraph(str(summary.get('total_connections', 0)), self.table_value_style)
            ],
            [
                Paragraph('Unique Processes', self.table_label_style),
                Paragraph(str(summary.get('unique_processes', 0)), self.table_value_style)
            ],
            [
                Paragraph('Unique Ports', self.table_label_style),
                Paragraph(str(summary.get('unique_ports', 0)), self.table_value_style)
            ],
            [
                Paragraph('Unique IP Addresses', self.table_label_style),
                Paragraph(str(summary.get('unique_ips', 0)), self.table_value_style)
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
    
    def _build_process_section(self, elements, process_details):
        """Build process information section"""
        elements.append(Paragraph('Process Information', self.heading_style))
        
        proc_label_style = ParagraphStyle(
            'ProcLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#4a5568')
        )
        
        proc_value_style = ParagraphStyle(
            'ProcValue',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4a5568')
        )
        
        for pid, proc in list(process_details.items())[:5]:  # Limit to first 5
            proc_title = f"Process: {proc.get('name', 'Unknown')} (PID: {pid})"
            elements.append(Paragraph(proc_title, self.subheading_style))
            
            proc_data = [
                [Paragraph('Property', proc_label_style), Paragraph('Value', proc_label_style)],
                [Paragraph('PID', proc_label_style), Paragraph(str(pid), proc_value_style)],
                [Paragraph('Status', proc_label_style), Paragraph(proc.get('status', 'N/A'), proc_value_style)],
                [Paragraph('CPU Usage', proc_label_style), Paragraph(f"{proc.get('cpu_percent', 0):.1f}%", proc_value_style)],
                [Paragraph('Memory Usage', proc_label_style), Paragraph(f"{proc.get('memory_percent', 0):.1f}%", proc_value_style)],
                [Paragraph('Username', proc_label_style), Paragraph(proc.get('username', 'N/A'), proc_value_style)]
            ]
            
            proc_table = Table(proc_data, colWidths=[2*inch, 5*inch])
            proc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(proc_table)
            elements.append(Spacer(1, 12))
    
    def _build_port_section(self, elements, port_details):
        """Build port usage section"""
        elements.append(Paragraph('Port Usage Statistics', self.heading_style))
        
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
        
        port_data = [[
            Paragraph('Port', port_header_style),
            Paragraph('Service', port_header_style),
            Paragraph('Connections', port_header_style),
            Paragraph('Processes', port_header_style)
        ]]
        
        for port in port_details[:10]:  # Limit to first 10
            processes_str = ', '.join(port.get('processes', []))
            if len(processes_str) > 30:
                processes_str = processes_str[:30] + '...'
            
            port_data.append([
                Paragraph(str(port.get('port', 'N/A')), port_cell_style),
                Paragraph(port.get('service_name', 'Unknown'), port_cell_style),
                Paragraph(str(port.get('connection_count', 0)), port_cell_style),
                Paragraph(processes_str, port_cell_style)
            ])
        
        port_table = Table(port_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 3*inch])
        port_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        elements.append(port_table)
        elements.append(Spacer(1, 20))
    
    def _build_connections_section(self, elements, connections):
        """Build connections list section"""
        elements.append(Paragraph(f'Detailed Connection List ({len(connections)} connections)', self.heading_style))
        
        if not connections or len(connections) == 0:
            elements.append(Paragraph('No connections found.', self.normal_style))
            return
        
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
            Paragraph('Local', conn_header_style),
            Paragraph('Remote', conn_header_style),
            Paragraph('Status', conn_header_style)
        ]]
        
        for conn in connections:  # Show all connections
            conn_data.append([
                Paragraph(str(conn.get('pid', '-'))[:6], conn_cell_style),
                Paragraph(conn.get('process_name', 'Unknown')[:12], conn_cell_style),
                Paragraph(conn.get('protocol', 'N/A')[:8], conn_cell_style),
                Paragraph(conn.get('local_address', 'N/A')[:22], conn_cell_style),
                Paragraph(conn.get('remote_address', 'N/A')[:22], conn_cell_style),
                Paragraph(conn.get('status', 'N/A')[:10], conn_cell_style)
            ])
        
        conn_table = Table(conn_data, colWidths=[0.6*inch, 1*inch, 0.8*inch, 1.8*inch, 1.8*inch, 0.8*inch])
        conn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
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
        elements.append(conn_table)
    
    def generate_pdf(self, search_results, search_type, search_value, username):
        """
        Generate a complete PDF report
        
        Args:
            search_results (dict): The search results data
            search_type (str): Type of search (pid, port, ip)
            search_value (str): Search value
            username (str): Username of the person generating the report
        
        Returns:
            BytesIO: Buffer containing the PDF data
        """
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
        
        elements = []
        
        # Build cover page (uses 'cover' template by default - first template)
        self._build_cover_page(elements, username)
        
        # Switch to content template for remaining pages
        elements.append(NextPageTemplate('content'))
        elements.append(PageBreak())
        
        # Build content pages
        self._build_metadata_section(elements, search_type, search_value, username)
        
        # Executive summary
        summary = search_results.get('summary', {})
        self._build_summary_section(elements, summary)
        
        # Process information
        if search_results.get('process_details'):
            self._build_process_section(elements, search_results['process_details'])
        
        # Port usage
        if search_results.get('port_details') and len(search_results['port_details']) > 0:
            self._build_port_section(elements, search_results['port_details'])
        
        # Connections
        self._build_connections_section(elements, search_results.get('connections', []))
        
        elements.append(Spacer(1, 20))
        
        # Footer
        footer = Paragraph('Generated by OPHIRON Process Monitor System', self.footer_style)
        elements.append(footer)
        
        # Build PDF with templates
        doc.build(elements)
        buffer.seek(0)
        
        logger.info(f"PDF generated successfully for {search_type}={search_value}")
        
        return buffer

