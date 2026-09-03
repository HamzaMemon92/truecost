import os
import re

def fix_scraper(filepath, new_source_template):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove isReady state
    content = re.sub(r'const \[isReady, setIsReady\] = React\.useState\(false\);\n?', '', content)
    # Remove useEffect navigation
    content = re.sub(r'useEffect\(\(\) => \{[\s\S]*?\}, \[query, isReady\]\);\n?', '', content)
    content = re.sub(r'useEffect\(\(\) => \{[\s\S]*?\}, \[query\]\);\n?', '', content)
    # Remove onLoad
    content = re.sub(r'onLoad=\{\(\) => \{ setIsReady\(true\); \}\}', '', content)
    
    # Replace source
    content = re.sub(r'source=\{\{\s*uri:\s*[^}]+\s*\}\}', 'source={{' + new_source_template + '}}', content)

    # Clean up imports
    content = content.replace('import React, { useRef, useEffect }', 'import React, { useRef }')
    content = content.replace('import React, { useRef, useState, useEffect }', 'import React, { useRef }')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

food_dir = r"C:\Users\Mohammad Anas\Downloads\decision-advisor-main\decision-advisor-main\mobile\components\scrapers\food\\"

fix_scraper(food_dir + "ZomatoScraper.tsx", "uri: query ? `https://www.zomato.com/search?q=${encodeURIComponent(query)}` : 'https://www.zomato.com/'")
fix_scraper(food_dir + "SwiggyFoodScraper.tsx", "uri: query ? `https://www.swiggy.com/search?query=${encodeURIComponent(query)}` : 'https://www.swiggy.com/'")
fix_scraper(food_dir + "MagicPinScraper.tsx", "uri: query ? `https://magicpin.in/explore/?nearby=1&q=${encodeURIComponent(query)}` : 'https://magicpin.in/'")
fix_scraper(food_dir + "EatSureScraper.tsx", "uri: query ? `https://www.eatsure.com/search?q=${encodeURIComponent(query)}` : 'https://www.eatsure.com/'")

print("Food Done!")
