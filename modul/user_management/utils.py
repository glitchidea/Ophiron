"""
User Management Utilities
Clean and simple utility functions for user management operations
"""

import re
from datetime import datetime


def parse_timestamp_safe(timestamp_str):
    """
    Safely parse timestamp strings that might be in different languages.
    Handles both English and Turkish date formats.
    """
    if not timestamp_str:
        return None
    
    # Turkish month mappings
    turkish_months = {
        'Ocak': 'Jan', 'Şubat': 'Feb', 'Mart': 'Mar', 'Nisan': 'Apr',
        'Mayıs': 'May', 'Haziran': 'Jun', 'Temmuz': 'Jul', 'Ağustos': 'Aug',
        'Eylül': 'Sep', 'Ekim': 'Oct', 'Kasım': 'Nov', 'Aralık': 'Dec',
        'Oca': 'Jan', 'Şub': 'Feb', 'Mar': 'Mar', 'Nis': 'Apr',
        'May': 'May', 'Haz': 'Jun', 'Tem': 'Jul', 'Ağu': 'Aug',
        'Eyl': 'Sep', 'Eki': 'Oct', 'Kas': 'Nov', 'Ara': 'Dec'
    }
    
    try:
        # First try direct parsing (English format)
        return datetime.strptime(timestamp_str, '%Y %b %d %H:%M:%S')
    except ValueError:
        try:
            # Try to convert Turkish months to English
            for turkish, english in turkish_months.items():
                if turkish in timestamp_str:
                    timestamp_str = timestamp_str.replace(turkish, english)
                    break
            
            # Parse with converted month
            return datetime.strptime(timestamp_str, '%Y %b %d %H:%M:%S')
        except ValueError:
            # If all else fails, try alternative formats
            alternative_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%d.%m.%Y %H:%M:%S',
                '%d-%m-%Y %H:%M:%S'
            ]
            
            for fmt in alternative_formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # Return current time as fallback
            return datetime.now()


def clean_timestamp_for_display(timestamp):
    """
    Clean timestamp for display purposes.
    Returns a formatted string or 'Never' if timestamp is None.
    """
    if not timestamp:
        return 'Never'
    
    try:
        if isinstance(timestamp, str):
            timestamp = parse_timestamp_safe(timestamp)
        
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return 'Invalid Date'


def safe_strptime(date_string, format_string):
    """
    Safe strptime that handles Turkish locale issues.
    Falls back to current time if parsing fails.
    """
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError:
        # Try to fix Turkish month names
        turkish_months = {
            'Eki': 'Oct', 'Oca': 'Jan', 'Şub': 'Feb', 'Mar': 'Mar',
            'Nis': 'Apr', 'May': 'May', 'Haz': 'Jun', 'Tem': 'Jul',
            'Ağu': 'Aug', 'Eyl': 'Sep', 'Kas': 'Nov', 'Ara': 'Dec'
        }
        
        for turkish, english in turkish_months.items():
            if turkish in date_string:
                date_string = date_string.replace(turkish, english)
                break
        
        try:
            return datetime.strptime(date_string, format_string)
        except ValueError:
            return datetime.now()  # Fallback to current time
