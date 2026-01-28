"""
Top 60 Most Influential Countries by Political Power, Economic Influence, and Global Impact
Includes country codes, names, and flag emojis
"""

TOP_COUNTRIES = [
    # G7 Countries
    {"code": "USA", "name": "United States", "flag": "🇺🇸"},
    {"code": "GBR", "name": "United Kingdom", "flag": "🇬🇧"},
    {"code": "DEU", "name": "Germany", "flag": "🇩🇪"},
    {"code": "FRA", "name": "France", "flag": "🇫🇷"},
    {"code": "JPN", "name": "Japan", "flag": "🇯🇵"},
    {"code": "ITA", "name": "Italy", "flag": "🇮🇹"},
    {"code": "CAN", "name": "Canada", "flag": "🇨🇦"},
    
    # Major European Powers
    {"code": "ESP", "name": "Spain", "flag": "🇪🇸"},
    {"code": "NLD", "name": "Netherlands", "flag": "🇳🇱"},
    {"code": "CHE", "name": "Switzerland", "flag": "🇨🇭"},
    {"code": "SWE", "name": "Sweden", "flag": "🇸🇪"},
    {"code": "POL", "name": "Poland", "flag": "🇵🇱"},
    {"code": "BEL", "name": "Belgium", "flag": "🇧🇪"},
    {"code": "AUT", "name": "Austria", "flag": "🇦🇹"},
    {"code": "NOR", "name": "Norway", "flag": "🇳🇴"},
    {"code": "DNK", "name": "Denmark", "flag": "🇩🇰"},
    {"code": "FIN", "name": "Finland", "flag": "🇫🇮"},
    {"code": "IRL", "name": "Ireland", "flag": "🇮🇪"},
    {"code": "PRT", "name": "Portugal", "flag": "🇵🇹"},
    {"code": "GRC", "name": "Greece", "flag": "🇬🇷"},
    {"code": "CZE", "name": "Czech Republic", "flag": "🇨🇿"},
    {"code": "ROU", "name": "Romania", "flag": "🇷🇴"},
    
    # Major Asian Powers
    {"code": "CHN", "name": "China", "flag": "🇨🇳"},
    {"code": "IND", "name": "India", "flag": "🇮🇳"},
    {"code": "KOR", "name": "South Korea", "flag": "🇰🇷"},
    {"code": "IDN", "name": "Indonesia", "flag": "🇮🇩"},
    {"code": "TUR", "name": "Turkey", "flag": "🇹🇷"},
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
    
    # Other Influential Countries
    {"code": "RUS", "name": "Russia", "flag": "🇷🇺"},
    {"code": "UKR", "name": "Ukraine", "flag": "🇺🇦"},
    {"code": "HUN", "name": "Hungary", "flag": "🇭🇺"},
    {"code": "HRV", "name": "Croatia", "flag": "🇭🇷"},
    {"code": "SVK", "name": "Slovakia", "flag": "🇸🇰"},
    {"code": "LUX", "name": "Luxembourg", "flag": "🇱🇺"},
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
