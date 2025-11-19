"""
CVE Email Automation
Sends email reports about CVEs found in the system
"""

import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from common.smtp.models import SMTPConfig, EmailAutomation, EmailLog
from common.smtp.utils import decrypt_password
from .pdf_generator import CVEPDFGenerator

logger = logging.getLogger(__name__)


class CVEEmailAutomation:
    """CVE email automation handler"""
    
    def __init__(self, automation: EmailAutomation):
        self.automation = automation
        self.config = automation.config or {}
        self.cve_data = None  # Store CVE data for PDF generation
    
    def run(self) -> Dict[str, Any]:
        """
        Run CVE scan and send email report
        
        Returns:
            Dict with 'success', 'message', 'cves_found', 'emails_sent'
        """
        try:
            # Get active SMTP config
            smtp_config = SMTPConfig.objects.filter(is_active=True).first()
            if not smtp_config:
                return {
                    'success': False,
                    'message': 'No active SMTP configuration found',
                    'cves_found': 0,
                    'emails_sent': 0
                }
            
            # Run CVE scan
            cve_data = self._scan_cves()
            
            if not cve_data:
                logger.warning("CVE scan returned no data")
                return {
                    'success': False,
                    'message': 'CVE scan failed or returned no data',
                    'cves_found': 0,
                    'emails_sent': 0
                }
            
            # Check if we should send email (based on config)
            send_always = self.config.get('send_always', False)
            min_cves = self.config.get('min_cves', 0)
            
            cves_found = cve_data.get('total_matched', 0)
            
            if not send_always and cves_found < min_cves:
                logger.info(f"Skipping email: {cves_found} CVEs found, minimum is {min_cves}")
                return {
                    'success': True,
                    'message': f'Skipped: Only {cves_found} CVEs found (minimum: {min_cves})',
                    'cves_found': cves_found,
                    'emails_sent': 0
                }
            
            # Store CVE data for later use
            self.cve_data = cve_data
            
            # Generate email content
            email_content = self._generate_email_content(cve_data, smtp_config)
            
            # Get recipient email - use automation creator's email or SMTP config email
            recipient_email = None
            
            # First try: automation creator's email
            if self.automation.created_by:
                # Try profile email first
                try:
                    if hasattr(self.automation.created_by, 'profile'):
                        recipient_email = self.automation.created_by.profile.email
                except:
                    pass
                
                # Fallback to user's email
                if not recipient_email:
                    recipient_email = self.automation.created_by.email
            
            # Second try: SMTP config email
            if not recipient_email:
                recipient_email = smtp_config.from_email
            
            # Last resort: SMTP username (usually email)
            if not recipient_email:
                recipient_email = smtp_config.username
            
            if not recipient_email:
                return {
                    'success': False,
                    'message': 'No recipient email found. Please set email in user profile or SMTP configuration.',
                    'cves_found': cves_found,
                    'emails_sent': 0
                }
            
            # Use single recipient (user's email)
            recipients = [recipient_email]
            
            emails_sent = self._send_emails(
                smtp_config=smtp_config,
                recipients=recipients,
                subject=email_content['subject'],
                html_content=email_content['html'],
                text_content=email_content['text'],
                cve_data=cve_data
            )
            
            # Update automation status
            self.automation.last_run_at = timezone.now()
            self.automation.last_run_status = 'success' if emails_sent > 0 else 'error'
            self.automation.last_run_error = None if emails_sent > 0 else 'Failed to send emails'
            self.automation.save()
            
            return {
                'success': emails_sent > 0,
                'message': f'Sent {emails_sent} email(s) about {cves_found} CVEs',
                'cves_found': cves_found,
                'emails_sent': emails_sent
            }
            
        except Exception as e:
            logger.error(f"Error running CVE email automation: {e}", exc_info=True)
            self.automation.last_run_at = timezone.now()
            self.automation.last_run_status = 'error'
            self.automation.last_run_error = str(e)
            self.automation.save()
            
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'cves_found': 0,
                'emails_sent': 0
            }
    
    def _scan_cves(self) -> Optional[Dict[str, Any]]:
        """Run CVE scan using the system's CVE scanner"""
        try:
            from modul.cve_scanner.os import main as os_main
            
            handler = os_main.get_handler()
            if handler is None:
                logger.error("Unsupported OS for CVE scanning")
                return None
            
            # Run scan
            result = handler.run_scan(force_refresh=False, use_system=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning CVEs: {e}", exc_info=True)
            return None
    
    def _generate_email_content(self, cve_data: Dict[str, Any], smtp_config: SMTPConfig) -> Dict[str, str]:
        """Generate HTML and text email content"""
        
        total_installed = cve_data.get('total_installed', 0)
        total_advisories = cve_data.get('total_advisories', 0)
        total_matched = cve_data.get('total_matched', 0)
        matched = cve_data.get('matched', [])
        
        # Limit matched items for email (first 50)
        matched_display = matched[:50] if matched else []
        
        context = {
            'total_installed': total_installed,
            'total_advisories': total_advisories,
            'total_matched': total_matched,
            'matched': matched_display,
            'scan_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'has_more': len(matched) > 50,
        }
        
        # Get logo as inline SVG HTML - most compatible for email clients
        # Inline SVG works directly in HTML without external requests
        logo_svg_inline = self._get_logo_svg_inline()
        if logo_svg_inline:
            # Use inline SVG directly in HTML - best compatibility
            # SVG is embedded directly in the HTML, no external requests needed
            logo_html = f'''
            <div class="header-logo">
                <div style="max-width: 120px; height: auto; margin: 0 auto 15px auto; text-align: center;">
                    {logo_svg_inline}
                </div>
            </div>
            '''
        else:
            # Fallback: text logo if SVG not found
            logo_html = '''
            <div class="header-logo">
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 15px;">OPHIRON</div>
            </div>
            '''
        
        # Generate professional HTML email template (similar to PDF design)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6; 
                    color: #4a5568; 
                    background-color: #f7fafc;
                }}
                .email-wrapper {{
                    max-width: 800px; 
                    margin: 0 auto; 
                    background-color: #ffffff;
                }}
                .header {{
                    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                    color: white; 
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header-logo {{
                    margin-bottom: 15px;
                    text-align: center;
                }}
                .header-logo img {{
                    max-width: 120px;
                    width: 120px;
                    height: auto;
                    display: block;
                    margin: 0 auto 15px auto;
                }}
                /* SVG logo styling - ensure it's visible on dark background */
                .header-logo svg {{
                    max-width: 120px;
                    width: 120px;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                    color: white; /* Set currentColor to white for dark background */
                }}
                .header-logo svg path {{
                    stroke: currentColor !important;
                    fill: currentColor !important;
                }}
                .header-logo svg circle {{
                    fill: #0b0d0f !important; /* Keep eye color - override */
                }}
                /* Fallback for img tags */
                .header-logo img {{
                    filter: brightness(0) invert(1);
                    background-color: transparent;
                }}
                .header h1 {{
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    letter-spacing: 2px;
                }}
                .header p {{
                    font-size: 16px;
                    color: #e2e8f0;
                    margin-top: 5px;
                }}
                .content {{
                    padding: 30px;
                    background-color: #ffffff;
                }}
                .metadata-section {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                    border-left: 4px solid #4299e1;
                }}
                .metadata-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .metadata-table td {{
                    padding: 8px 0;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .metadata-table td:first-child {{
                    font-weight: bold;
                    color: #2d3748;
                    width: 45%;
                }}
                .metadata-table td:last-child {{
                    color: #4a5568;
                }}
                .summary-section {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    padding: 25px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                    border: 1px solid #e2e8f0;
                }}
                .summary-title {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #1a202c;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e53e3e;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin-top: 15px;
                }}
                .summary-card {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #e53e3e;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .summary-card-label {{
                    font-size: 12px;
                    color: #718096;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 5px;
                }}
                .summary-card-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #1a202c;
                }}
                .cve-section {{
                    margin-top: 30px;
                }}
                .cve-section-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #1a202c;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e53e3e;
                }}
                .cve-table {{
                    width: 100%;
                    border-collapse: collapse;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .cve-table thead {{
                    background-color: #e53e3e;
                    color: white;
                }}
                .cve-table th {{
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .cve-table td {{
                    padding: 12px;
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 13px;
                }}
                .cve-table tbody tr:hover {{
                    background-color: #f8f9fa;
                }}
                .cve-table tbody tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}
                .cve-badge {{
                    display: inline-block;
                    background-color: #fed7d7;
                    color: #c53030;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 2px;
                }}
                .footer {{
                    background-color: #1a202c;
                    color: #cbd5e0;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                }}
                .footer svg {{
                    max-width: 80px;
                    width: 80px;
                    height: auto;
                    display: block;
                    margin: 0 auto 15px auto;
                    color: white; /* Set currentColor to white for dark background */
                }}
                .footer svg path {{
                    stroke: currentColor !important;
                    fill: currentColor !important;
                }}
                .footer svg circle {{
                    fill: #0b0d0f !important; /* Keep eye color - override */
                }}
                .footer img {{
                    max-width: 80px;
                    height: auto;
                    margin-bottom: 15px;
                    filter: brightness(0) invert(1);
                    background-color: transparent;
                }}
                .footer p {{
                    margin: 5px 0;
                }}
                @media only screen and (max-width: 600px) {{
                    .summary-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .header h1 {{
                        font-size: 24px;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="header">
                    {logo_html}
                    <h1>OPHIRON</h1>
                    <p>CVE Security Report</p>
                    <p style="font-size: 14px; margin-top: 10px;">Automated Vulnerability Analysis</p>
                </div>
                
                <div class="content">
                    <div class="metadata-section">
                        <table class="metadata-table">
                            <tr>
                                <td>Report Generated:</td>
                                <td>{context['scan_date']}</td>
                            </tr>
                            <tr>
                                <td>Report Type:</td>
                                <td>Automated Security Analysis</td>
                            </tr>
                            <tr>
                                <td>System Status:</td>
                                <td>{'⚠️ Action Required' if total_matched > 0 else '✅ Secure'}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="summary-section">
                        <div class="summary-title">Executive Summary</div>
                        <div class="summary-grid">
                            <div class="summary-card">
                                <div class="summary-card-label">Installed Packages</div>
                                <div class="summary-card-value">{total_installed}</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-card-label">CVEs Found</div>
                                <div class="summary-card-value">{total_advisories}</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-card-label">Vulnerable Packages</div>
                                <div class="summary-card-value" style="color: #e53e3e;">{total_matched}</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-card-label">Security Status</div>
                                <div class="summary-card-value" style="color: {'#e53e3e' if total_matched > 0 else '#48bb78'}; font-size: 18px;">
                                    {'⚠️ Action Required' if total_matched > 0 else '✅ Secure'}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="cve-section">
                        {self._generate_cve_list_html(matched_display)}
                        {f'<p style="color: #718096; font-style: italic; margin-top: 15px;">Note: Showing first 50 packages. Total: {total_matched} vulnerable packages found.</p>' if context['has_more'] else ''}
                    </div>
                    
                </div>
                
                <div class="footer">
                    <p><strong>Generated by OPHIRON System Monitoring</strong></p>
                    <p>This is an automated security report</p>
                    <p style="margin-top: 10px; font-size: 11px; color: #718096;">
                        Generated at {context['scan_date']}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Generate text content
        text_content = f"""
CVE Security Report
==================

Scan Summary:
- Total Installed Packages: {total_installed}
- Total CVEs Found: {total_advisories}
- Matched Packages: {total_matched}
- Scan Date: {context['scan_date']}

{self._generate_cve_list_text(matched_display)}

{'-' * 50}
This is an automated email from Ophiron System Monitoring
Generated at {context['scan_date']}
        """
        
        return {
            'subject': f'CVE Security Report - {total_matched} Vulnerabilities Found',
            'html': html_content,
            'text': text_content
        }
    
    def _generate_cve_list_html(self, matched: List[Dict[str, Any]]) -> str:
        """Generate HTML for CVE list - professional table format"""
        if not matched:
            return '''
            <div class="cve-section">
                <div class="cve-section-title">Vulnerable Packages</div>
                <div style="background-color: #c6f6d5; padding: 20px; border-radius: 8px; border-left: 4px solid #48bb78;">
                    <p style="color: #22543d; font-weight: bold; margin: 0;">✅ No Vulnerabilities Found</p>
                    <p style="color: #2f855a; margin-top: 8px; margin-bottom: 0;">No CVEs were found matching your installed packages. Your system appears to be secure.</p>
                </div>
            </div>
            '''
        
        # Group matches by package name (same package can have multiple advisories)
        package_groups = {}
        for item in matched:
            package_name = item.get('package', 'Unknown')
            package_version = item.get('installed_version', item.get('version', 'Unknown'))
            advisory = item.get('advisory', '')
            issues = item.get('issues', [])
            
            if package_name not in package_groups:
                package_groups[package_name] = {
                    'version': package_version,
                    'advisories': [],
                    'all_issues': set()  # Use set to avoid duplicates
                }
            
            # Add advisory info
            package_groups[package_name]['advisories'].append({
                'advisory': advisory,
                'issues': issues
            })
            
            # Collect all unique CVE issues
            for issue in issues:
                if issue:
                    package_groups[package_name]['all_issues'].add(issue)
        
        # Build table rows
        table_rows = []
        for package_name, package_data in package_groups.items():
            package_version = package_data['version']
            all_cves = sorted(list(package_data['all_issues']))  # Sort for consistency
            
            # Format CVE badges from issues array
            cve_badges = []
            for cve in all_cves[:8]:  # Show first 8 CVEs
                if cve:
                    cve_badges.append(f'<span class="cve-badge">{cve}</span>')
            
            cve_html = ''.join(cve_badges)
            if len(all_cves) > 8:
                cve_html += f'<span class="cve-badge" style="background-color: #cbd5e0; color: #4a5568;">+{len(all_cves) - 8} more</span>'
            
            table_rows.append(f'''
            <tr>
                <td><strong>{package_name}</strong></td>
                <td>{package_version}</td>
                <td>{cve_html if cve_html else '<span class="cve-badge">Unknown</span>'}</td>
                <td style="text-align: center;"><strong style="color: #e53e3e;">{len(all_cves)}</strong></td>
            </tr>
            ''')
        
        return f'''
        <div class="cve-section">
            <div class="cve-section-title">Vulnerable Packages Details</div>
            <table class="cve-table">
                <thead>
                    <tr>
                        <th>Package Name</th>
                        <th>Version</th>
                        <th>CVEs</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
        '''
    
    def _generate_cve_list_text(self, matched: List[Dict[str, Any]]) -> str:
        """Generate text for CVE list"""
        if not matched:
            return 'No CVEs found matching installed packages.\n'
        
        # Group matches by package name
        package_groups = {}
        for item in matched:
            package_name = item.get('package', 'Unknown')
            package_version = item.get('installed_version', item.get('version', 'Unknown'))
            issues = item.get('issues', [])
            
            if package_name not in package_groups:
                package_groups[package_name] = {
                    'version': package_version,
                    'all_issues': set()
                }
            
            # Collect all unique CVE issues
            for issue in issues:
                if issue:
                    package_groups[package_name]['all_issues'].add(issue)
        
        lines = ['\nVulnerable Packages:\n']
        for package_name, package_data in package_groups.items():
            package_version = package_data['version']
            all_cves = sorted(list(package_data['all_issues']))
            
            lines.append(f'- {package_name} ({package_version})')
            for cve in all_cves[:5]:
                if cve:
                    lines.append(f'  * {cve}')
            if len(all_cves) > 5:
                lines.append(f'  ... and {len(all_cves) - 5} more')
            lines.append('')
        
        return '\n'.join(lines)
    
    def _get_logo_path(self) -> str:
        """Get logo file path"""
        try:
            import os
            from django.conf import settings
            
            # Try to find logo file - check multiple paths
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
            
            logo_path = None
            for path in logo_paths:
                if path and os.path.exists(path):
                    logo_path = path
                    logger.info(f"Found logo at: {logo_path}")
                    break
            
            if not logo_path:
                logger.warning(f"Logo file not found in any of these paths: {logo_paths}")
                return None
            
            return logo_path
                
        except Exception as e:
            logger.error(f"Error finding logo path: {e}", exc_info=True)
            return None
    
    def _get_logo_svg_inline(self) -> str:
        """Get logo as inline SVG HTML - most compatible method for email"""
        try:
            logo_path = self._get_logo_path()
            if not logo_path:
                return None
            
            # Read SVG file content
            with open(logo_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Remove XML declaration if present (not needed in HTML)
            svg_content = svg_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip()
            
            # Replace currentColor with white for header/footer (dark background)
            # and keep original colors for sender-info (light background)
            # We'll do color replacement in CSS instead for better control
            
            # Ensure SVG has proper attributes for email compatibility
            if 'viewBox' in svg_content and 'width' not in svg_content:
                # Add width/height from viewBox if not present
                import re
                viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
                if viewbox_match:
                    viewbox_values = viewbox_match.group(1).split()
                    if len(viewbox_values) >= 4:
                        width = viewbox_values[2]
                        height = viewbox_values[3]
                        # Insert width and height after viewBox
                        svg_content = svg_content.replace(
                            'viewBox="',
                            f'width="{width}" height="{height}" viewBox="'
                        )
            
            # Return inline SVG HTML
            return svg_content
                
        except Exception as e:
            logger.error(f"Error loading logo SVG for inline embedding: {e}", exc_info=True)
            return None
    
    def _send_emails(
        self,
        smtp_config: SMTPConfig,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str,
        cve_data: Dict[str, Any] = None
    ) -> int:
        """Send emails using SMTP configuration"""
        emails_sent = 0
        
        try:
            # Configure Django email backend
            from django.core.mail import get_connection
            from django.conf import settings
            
            # Decrypt password if needed
            # Get the user who last modified the config (or created_by if available)
            # For automation, we'll use the automation creator
            user = self.automation.created_by if self.automation.created_by else None
            if not user and smtp_config.last_modified_by:
                user = smtp_config.last_modified_by
            
            # Decrypt password
            decrypted_password = smtp_config.password
            if user:
                try:
                    decrypted_password = decrypt_password(smtp_config.password, user)
                except Exception as e:
                    logger.warning(f"Could not decrypt password, using as-is: {e}")
                    decrypted_password = smtp_config.password
            
            # Use SMTP backend
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_config.host,
                port=smtp_config.port,
                username=smtp_config.username,
                password=decrypted_password,
                use_tls=smtp_config.use_tls,
                use_ssl=smtp_config.use_ssl,
            )
            
            # Generate PDF report if CVE data is provided
            pdf_buffer = None
            if cve_data:
                pdf_generator = CVEPDFGenerator()
                scan_date = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Get full CVE data for PDF
                pdf_cve_data = {
                    'total_installed': cve_data.get('total_installed', 0),
                    'total_advisories': cve_data.get('total_advisories', 0),
                    'total_matched': cve_data.get('total_matched', 0),
                    'matched': cve_data.get('matched', [])  # Full list for PDF
                }
                
                pdf_buffer = pdf_generator.generate_pdf(pdf_cve_data, scan_date)
            
            # Get logo path for inline attachment
            logo_path = self._get_logo_path()
            
            for recipient in recipients:
                try:
                    # Create email with logo as sender avatar
                    # Note: Email clients don't support custom avatars directly,
                    # but we include logo in email content
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=f"{smtp_config.from_name} <{smtp_config.from_email}>",
                        to=[recipient],
                        connection=connection,
                        reply_to=[smtp_config.from_email]  # Add reply-to for better email client recognition
                    )
                    
                    # Logo is now embedded directly in HTML as inline SVG
                    # No need for separate attachment - this is the most compatible method
                    # Inline SVG works in most email clients (Gmail, Outlook, etc.)
                    email.attach_alternative(html_content, "text/html")
                    
                    # Attach PDF report if generated
                    if pdf_buffer:
                        pdf_filename = f"CVE_Report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        pdf_buffer.seek(0)  # Reset buffer position
                        email.attach(pdf_filename, pdf_buffer.read(), 'application/pdf')
                    
                    email.send()
                    
                    # Log success
                    EmailLog.objects.create(
                        automation=self.automation,
                        recipient=recipient,
                        subject=subject,
                        status='sent',
                        sent_at=timezone.now(),
                        error_message=''  # Empty string for successful sends
                    )
                    
                    emails_sent += 1
                    logger.info(f"Sent CVE report email to {recipient}")
                    
                except Exception as e:
                    logger.error(f"Error sending email to {recipient}: {e}")
                    EmailLog.objects.create(
                        automation=self.automation,
                        recipient=recipient,
                        subject=subject,
                        status='failed',
                        error_message=str(e)
                    )
            
            return emails_sent
            
        except Exception as e:
            logger.error(f"Error configuring email connection: {e}", exc_info=True)
            return 0

