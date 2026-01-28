"""
All European Countries + Major Global Powers
Includes all 44 European countries plus influential countries worldwide with Persian names
"""

from .persian_countries import get_persian_name

TOP_COUNTRIES = [
    # G7 Countries (Non-European)
    {"code": "USA", "name": "United States", "name_persian": "ایالات متحده", "flag": "🇺🇸"},
    {"code": "JPN", "name": "Japan", "name_persian": "ژاپن", "flag": "🇯🇵"},
    {"code": "CAN", "name": "Canada", "name_persian": "کانادا", "flag": "🇨🇦"},
    
    # All European Countries (44 countries)
    # Western Europe
    {"code": "GBR", "name": "United Kingdom", "name_persian": "انگلستان", "flag": "🇬🇧"},
    {"code": "DEU", "name": "Germany", "name_persian": "آلمان", "flag": "🇩🇪"},
    {"code": "FRA", "name": "France", "name_persian": "فرانسه", "flag": "🇫🇷"},
    {"code": "ITA", "name": "Italy", "name_persian": "ایتالیا", "flag": "🇮🇹"},
    {"code": "ESP", "name": "Spain", "name_persian": "اسپانیا", "flag": "🇪🇸"},
    {"code": "NLD", "name": "Netherlands", "name_persian": "هلند", "flag": "🇳🇱"},
    {"code": "CHE", "name": "Switzerland", "name_persian": "سوئیس", "flag": "🇨🇭"},
    {"code": "BEL", "name": "Belgium", "flag": "🇧🇪"},
    {"code": "AUT", "name": "Austria", "flag": "🇦🇹"},
    {"code": "IRL", "name": "Ireland", "flag": "🇮🇪"},
    {"code": "PRT", "name": "Portugal", "flag": "🇵🇹"},
    {"code": "LUX", "name": "Luxembourg", "flag": "🇱🇺"},
    {"code": "MCO", "name": "Monaco", "flag": "🇲🇨"},
    {"code": "LIE", "name": "Liechtenstein", "flag": "🇱🇮"},
    {"code": "AND", "name": "Andorra", "flag": "🇦🇩"},
    {"code": "SMR", "name": "San Marino", "flag": "🇸🇲"},
    {"code": "VAT", "name": "Vatican City", "flag": "🇻🇦"},
    
    # Nordic Countries
    {"code": "SWE", "name": "Sweden", "flag": "🇸🇪"},
    {"code": "NOR", "name": "Norway", "flag": "🇳🇴"},
    {"code": "DNK", "name": "Denmark", "flag": "🇩🇰"},
    {"code": "FIN", "name": "Finland", "flag": "🇫🇮"},
    {"code": "ISL", "name": "Iceland", "flag": "🇮🇸"},
    
    # Eastern Europe
    {"code": "POL", "name": "Poland", "flag": "🇵🇱"},
    {"code": "CZE", "name": "Czech Republic", "flag": "🇨🇿"},
    {"code": "HUN", "name": "Hungary", "flag": "🇭🇺"},
    {"code": "ROU", "name": "Romania", "flag": "🇷🇴"},
    {"code": "BGR", "name": "Bulgaria", "flag": "🇧🇬"},
    {"code": "SVK", "name": "Slovakia", "flag": "🇸🇰"},
    {"code": "UKR", "name": "Ukraine", "flag": "🇺🇦"},
    {"code": "BLR", "name": "Belarus", "flag": "🇧🇾"},
    {"code": "MDA", "name": "Moldova", "flag": "🇲🇩"},
    {"code": "RUS", "name": "Russia", "flag": "🇷🇺"},
    
    # Baltic States
    {"code": "EST", "name": "Estonia", "flag": "🇪🇪"},
    {"code": "LVA", "name": "Latvia", "flag": "🇱🇻"},
    {"code": "LTU", "name": "Lithuania", "flag": "🇱🇹"},
    
    # Southern Europe
    {"code": "GRC", "name": "Greece", "flag": "🇬🇷"},
    {"code": "HRV", "name": "Croatia", "flag": "🇭🇷"},
    {"code": "SVN", "name": "Slovenia", "flag": "🇸🇮"},
    {"code": "SRB", "name": "Serbia", "flag": "🇷🇸"},
    {"code": "BIH", "name": "Bosnia and Herzegovina", "flag": "🇧🇦"},
    {"code": "MNE", "name": "Montenegro", "flag": "🇲🇪"},
    {"code": "MKD", "name": "North Macedonia", "flag": "🇲🇰"},
    {"code": "ALB", "name": "Albania", "flag": "🇦🇱"},
    {"code": "MLT", "name": "Malta", "flag": "🇲🇹"},
    {"code": "CYP", "name": "Cyprus", "flag": "🇨🇾"},
    
    {"code": "CYP", "name": "Cyprus", "flag": "🇨🇾"},
    {"code": "KOS", "name": "Kosovo", "flag": "🇽🇰"},
    
    # Turkey (Transcontinental)
    {"code": "TUR", "name": "Turkey", "flag": "🇹🇷"},
    
    # Major Asian Powers
    {"code": "CHN", "name": "China", "flag": "🇨🇳"},
    {"code": "IND", "name": "India", "flag": "🇮🇳"},
    {"code": "KOR", "name": "South Korea", "flag": "🇰🇷"},
    {"code": "IDN", "name": "Indonesia", "flag": "🇮🇩"},
    {"code": "SAU", "name": "Saudi Arabia", "flag": "🇸🇦"},
    {"code": "ARE", "name": "United Arab Emirates", "flag": "🇦🇪"},
    {"code": "ISR", "name": "Israel", "flag": "🇮🇱"},
    {"code": "THA", "name": "Thailand", "flag": "🇹🇭"},
    {"code": "MYS", "name": "Malaysia", "flag": "🇲🇾"},
    {"code": "SGP", "name": "Singapore", "flag": "🇸🇬"},
    {"code": "PAK", "name": "Pakistan", "flag": "🇵🇰"},
    {"code": "BGD", "name": "Bangladesh", "flag": "🇧🇩"},
    {"code": "VNM", "name": "Vietnam", "flag": "🇻🇳"},
    {"code": "PHL", "name": "Philippines", "flag": "🇵🇭"},
    
    # Americas
    {"code": "BRA", "name": "Brazil", "flag": "🇧🇷"},
    {"code": "MEX", "name": "Mexico", "flag": "🇲🇽"},
    {"code": "ARG", "name": "Argentina", "flag": "🇦🇷"},
    {"code": "CHL", "name": "Chile", "flag": "🇨🇱"},
    {"code": "COL", "name": "Colombia", "flag": "🇨🇴"},
    {"code": "PER", "name": "Peru", "flag": "🇵🇪"},
    
    # Oceania
    {"code": "AUS", "name": "Australia", "flag": "🇦🇺"},
    {"code": "NZL", "name": "New Zealand", "flag": "🇳🇿"},
    
    # Africa & Middle East
    {"code": "ZAF", "name": "South Africa", "flag": "🇿🇦"},
    {"code": "EGY", "name": "Egypt", "flag": "🇪🇬"},
    {"code": "NGA", "name": "Nigeria", "flag": "🇳🇬"},
    {"code": "KEN", "name": "Kenya", "flag": "🇰🇪"},
    {"code": "MAR", "name": "Morocco", "flag": "🇲🇦"},
    {"code": "ETH", "name": "Ethiopia", "flag": "🇪🇹"},
    {"code": "QAT", "name": "Qatar", "flag": "🇶🇦"},
    {"code": "KWT", "name": "Kuwait", "flag": "🇰🇼"},
    {"code": "JOR", "name": "Jordan", "flag": "🇯🇴"},
]

def get_country_flag(code: str) -> str:
    """Get flag emoji for country code"""
    for country in TOP_COUNTRIES:
        if country["code"] == code:
            return country["flag"]
    return "🏳️"  # Default flag

def is_influential_country(code: str) -> bool:
    """Check if country is in top 60 list"""
    return any(c["code"] == code for c in TOP_COUNTRIES)
