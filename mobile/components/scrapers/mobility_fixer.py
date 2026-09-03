import os
import re

def fix_scraper(filepath, new_source_template, extra_fallback=""):
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

base_dir = r"C:\Users\Mohammad Anas\Downloads\decision-advisor-main\decision-advisor-main\mobile\components\scrapers\\"

# Mobility
mob_dir = base_dir + "mobility\\"
fix_scraper(mob_dir + "UberScraper.tsx", "uri: 'https://m.uber.com/looking'")
fix_scraper(mob_dir + "OlaScraper.tsx", "uri: `https://book.olacabs.com/?pickup_lat=${latitude}&pickup_lng=${longitude}&serviceType=p2p`")
fix_scraper(mob_dir + "RapidoScraper.tsx", "uri: 'https://rapido.bike/'")
fix_scraper(mob_dir + "NammaYatriScraper.tsx", "uri: 'https://nammayatri.in/'")

print("Mobility Done!")
