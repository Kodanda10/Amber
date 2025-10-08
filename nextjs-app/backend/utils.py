
from datetime import datetime
from babel.dates import format_date

def format_date_in_hindi(date_obj: datetime) -> str:
    """
    Formats a datetime object into a Hindi string using Devanagari numerals.
    Example: datetime(2025, 10, 4) -> '०४ अक्तूबर २०२५'
    """
    # Format the date using the standard Hindi locale.
    formatted_date = format_date(date_obj, 'dd MMMM yyyy', locale='hi')
    
    # Manually replace Latin numerals with Devanagari equivalents.
    devanagari_numerals = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४', '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    for lat, deva in devanagari_numerals.items():
        formatted_date = formatted_date.replace(lat, deva)
        
    return formatted_date
