"""
PDF Generator for CVE Email Reports
Generates professional PDF reports similar to process-monitor PDF style
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, PageTemplate, Frame, NextPageTemplate
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
                logger.error(f"Error rendering SVG: {e}")


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


class CVEPDFGenerator:
    """Generator for CVE PDF Reports with professional design"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _get_logo_path(self):
        """Get the path to the SVG logo"""
        try:
            import os
            from django.conf import settings
            
            logo_paths = []
            
            # Add STATIC_ROOT path
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                logo_paths.append(os.path.join(settings.STATIC_ROOT, 'images', 'ophiron.svg'))
            
            # Add BASE_DIR/static path
            logo_paths.append(os.path.join(settings.BASE_DIR, 'static', 'images', 'ophiron.svg'))
            
            # Add STATICFILES_DIRS paths
            if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
                for static_dir in settings.STATICFILES_DIRS:
                    logo_paths.append(os.path.join(str(static_dir), 'images', 'ophiron.svg'))
            
            for path in logo_paths:
                if path and os.path.exists(path):
                    logger.info(f"Found logo at: {path}")
                    return path
                    
        except Exception as e:
            logger.warning(f"Error finding logo path: {str(e)}")
        
        return None
    
    def _setup_custom_styles(self):
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
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.white
        )
        
        self.table_cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#4a5568')
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
    
    def generate_pdf(self, cve_data: Dict[str, Any], scan_date: str) -> BytesIO:
        """Generate CVE PDF report with professional design"""
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
        
        # Build cover page
        self._build_cover_page(elements, scan_date)
        
        # Switch to content template for remaining pages
        elements.append(NextPageTemplate('content'))
        elements.append(PageBreak())
        
        # Metadata section
        self._build_metadata_section(elements, cve_data, scan_date)
        elements.append(Spacer(1, 20))
        
        # Executive Summary
        self._build_executive_summary(elements, cve_data)
        
        # CVE Details
        self._build_cve_details_section(elements, cve_data)
        
        elements.append(Spacer(1, 20))
        
        # Footer
        footer = Paragraph('Generated by OPHIRON CVE Scanner System', self.footer_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer
    
    def _build_cover_page(self, elements, scan_date: str):
        """Build the cover page with black background"""
        elements.append(Spacer(1, 0.8*inch))
        
        # Add SVG Logo (bigger size - 5 inch, white color for dark background)
        logo_path = self._get_logo_path()
        if logo_path and SVG_SUPPORT:
            try:
                # Use white color for logo on black background
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
        title = Paragraph('CVE Security Report', self.cover_subtitle_style)
        elements.append(title)
        
        subtitle = Paragraph('Vulnerability Analysis', self.cover_subtitle_style)
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.8*inch))
        
        # Report info (light gray on black)
        elements.append(Paragraph(
            f'Generated: {scan_date}',
            self.cover_info_style
        ))
        elements.append(Paragraph('Automated Security Scan', self.cover_info_style))
    
    def _build_metadata_section(self, elements, cve_data: Dict[str, Any], scan_date: str):
        """Build report metadata section"""
        # Report header
        report_header = Paragraph('OPHIRON - CVE Security Report', self.title_style)
        elements.append(report_header)
        elements.append(Spacer(1, 20))
        
        # Metadata table
        total_installed = cve_data.get('total_installed', 0)
        total_advisories = cve_data.get('total_advisories', 0)
        total_matched = cve_data.get('total_matched', 0)
        
        meta_data = [
            [
                Paragraph('Report Generated:', self.table_label_style),
                Paragraph(scan_date, self.table_value_style)
            ],
            [
                Paragraph('Total Installed Packages:', self.table_label_style),
                Paragraph(str(total_installed), self.table_value_style)
            ],
            [
                Paragraph('Total CVEs Found:', self.table_label_style),
                Paragraph(str(total_advisories), self.table_value_style)
            ],
            [
                Paragraph('Matched Packages:', self.table_label_style),
                Paragraph(str(total_matched), self.table_value_style)
            ],
            [
                Paragraph('Report Type:', self.table_label_style),
                Paragraph('Automated Security Analysis', self.table_value_style)
            ]
        ]
        
        meta_table = Table(meta_data, colWidths=[2.5*inch, 5*inch])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 24))
    
    def _build_executive_summary(self, elements, cve_data: Dict[str, Any]):
        """Build executive summary section"""
        elements.append(Paragraph('Executive Summary', self.heading_style))
        
        total_installed = cve_data.get('total_installed', 0)
        total_advisories = cve_data.get('total_advisories', 0)
        total_matched = cve_data.get('total_matched', 0)
        matched = cve_data.get('matched', [])
        
        summary_data = [
            [
                Paragraph('Metric', self.table_header_style),
                Paragraph('Value', self.table_header_style)
            ],
            [
                Paragraph('Total Installed Packages', self.table_label_style),
                Paragraph(str(total_installed), self.table_value_style)
            ],
            [
                Paragraph('Total CVEs Found', self.table_label_style),
                Paragraph(str(total_advisories), self.table_value_style)
            ],
            [
                Paragraph('Vulnerable Packages', self.table_label_style),
                Paragraph(str(total_matched), self.table_value_style)
            ],
            [
                Paragraph('Security Status', self.table_label_style),
                Paragraph(
                    'Action Required' if total_matched > 0 else 'No Issues Detected',
                    self.table_value_style
                )
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e53e3e')),
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
    
    def _build_cve_details_section(self, elements, cve_data: Dict[str, Any]):
        """Build detailed CVE information section"""
        matched = cve_data.get('matched', [])
        
        if not matched:
            elements.append(Paragraph('No Vulnerabilities Found', self.heading_style))
            elements.append(Paragraph(
                'No CVEs were found matching your installed packages. Your system appears to be secure.',
                self.normal_style
            ))
            return
        
        elements.append(Paragraph('Vulnerable Packages Details', self.heading_style))
        
        # Group matches by package name (same package can have multiple advisories)
        package_groups = {}
        for item in matched:
            package_name = item.get('package', 'Unknown')
            package_version = item.get('installed_version', item.get('version', 'Unknown'))
            issues = item.get('issues', [])
            
            if package_name not in package_groups:
                package_groups[package_name] = {
                    'version': package_version,
                    'all_issues': set()  # Use set to avoid duplicates
                }
            
            # Collect all unique CVE issues
            for issue in issues:
                if issue:
                    package_groups[package_name]['all_issues'].add(issue)
        
        # CVE table header
        cve_header_data = [[
            Paragraph('Package', self.table_header_style),
            Paragraph('Version', self.table_header_style),
            Paragraph('CVEs', self.table_header_style),
            Paragraph('Count', self.table_header_style)
        ]]
        
        # Add CVE data - show ALL packages and ALL CVEs (no limits)
        for package_name, package_data in package_groups.items():
            package_version = package_data['version']
            all_cves = sorted(list(package_data['all_issues']))
            
            # Format CVE list - show ALL CVEs (no limit)
            cve_text = ', '.join(all_cves)
            
            # If text is too long, wrap it to multiple lines
            # ReportLab will handle wrapping automatically, but we can break it into paragraphs for better readability
            if len(cve_text) > 150:
                # Split into chunks for better readability in PDF
                chunk_size = 100
                cve_chunks = [all_cves[i:i+chunk_size] for i in range(0, len(all_cves), chunk_size)]
                cve_paragraphs = []
                for chunk in cve_chunks:
                    cve_paragraphs.append(', '.join(chunk))
                cve_text = '\n'.join(cve_paragraphs)
            
            cve_header_data.append([
                Paragraph(package_name[:30], self.table_cell_style),
                Paragraph(str(package_version)[:20], self.table_cell_style),
                Paragraph(cve_text if cve_text else 'Unknown', self.table_cell_style),
                Paragraph(str(len(all_cves)), self.table_cell_style)
            ])
        
        cve_table = Table(cve_header_data, colWidths=[2*inch, 1.5*inch, 3*inch, 0.8*inch])
        cve_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e53e3e')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        elements.append(cve_table)
        
        # Show summary of total packages found
        if package_groups:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f'Total: {len(package_groups)} vulnerable package(s) found.',
                self.normal_style
            ))

