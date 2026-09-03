import json
import subprocess
import os
import pytest
from app.connectors.blinkit import BlinkitConnector
from app.connectors.zepto import ZeptoConnector
from app.connectors.swiggy import SwiggyInstamartConnector
from app.connectors.bigbasket import BigBasketConnector

MOBILE_DIR = os.path.join(os.path.dirname(__file__), '../../mobile')

def setup_module():
    # Compile the current TS directly into a temp JS file
    subprocess.run(['npx', 'tsc', 'lib/scraperCertification/sanitizeCapture.ts', '--esModuleInterop', '--ignoreConfig', '--outDir', 'temp_build'], cwd=MOBILE_DIR, check=True, shell=True)

def run_js_sanitizer(payload):
    js_code = '''
    const { sanitizeCapture } = require('./temp_build/sanitizeCapture.js');
    const fs = require('fs');
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    console.log(JSON.stringify(sanitizeCapture(input)));
    '''
    process = subprocess.Popen(['node', '-e', js_code], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=MOBILE_DIR)
    out, err = process.communicate(input=json.dumps(payload).encode('utf-8'))
    if process.returncode != 0:
        raise Exception(f"JS Error: {err.decode('utf-8')}")
    return json.loads(out.decode('utf-8'))

def test_blinkit_sanitizer_contract():
    payload = {
        "cart_item": {"product_name": "Amul Milk", "price": 30},
        "cookie": "secret_cookie"
    }
    connector = BlinkitConnector()
    original_results = list(connector.parse_search_results(payload))
    sanitized = run_js_sanitizer(payload)
    sanitized_results = list(connector.parse_search_results(sanitized))
    
    assert len(original_results) > 0
    assert len(sanitized_results) > 0
    assert original_results[0].name == sanitized_results[0].name
    assert sanitized.get("cookie") == "[REDACTED]"

def test_zepto_sanitizer_contract():
    payload = {
        "layout": [{"widgetId": "PRODUCT_GRID", "data": {"resolver": {"data": {"items": [{"productResponse": {"name": "Amul Milk", "sellingPrice": 3000}}]}}}}],
        "access_token": "secret_token"
    }
    connector = ZeptoConnector()
    original_results = list(connector.parse_search_results(payload))
    sanitized = run_js_sanitizer(payload)
    sanitized_results = list(connector.parse_search_results(sanitized))
    
    assert len(original_results) > 0
    assert len(sanitized_results) > 0
    assert original_results[0].name == sanitized_results[0].name
    assert sanitized.get("access_token") == "[REDACTED]"

def test_swiggy_sanitizer_contract():
    payload = {
        "displayName": "Amul Milk", 
        "price": {"offerPrice": {"units": 30}, "mrp": {"units": 30}},
        "session_id": "secret_session"
    }
    connector = SwiggyInstamartConnector()
    original_results = list(connector.parse_search_results(payload))
    sanitized = run_js_sanitizer(payload)
    sanitized_results = list(connector.parse_search_results(sanitized))
    
    assert len(original_results) > 0
    assert len(sanitized_results) > 0
    assert original_results[0].name == sanitized_results[0].name
    assert sanitized.get("session_id") == "[REDACTED]"

def test_bigbasket_sanitizer_contract():
    payload = {
        "products": [{"desc": "Amul Milk", "pricing": {"discount": {"mrp": 30, "sp": 30}}}],
        "authorization": "Bearer secret"
    }
    connector = BigBasketConnector()
    original_results = list(connector.parse_search_results(payload))
    sanitized = run_js_sanitizer(payload)
    sanitized_results = list(connector.parse_search_results(sanitized))
    
    assert len(original_results) > 0
    assert len(sanitized_results) > 0
    assert original_results[0].name == sanitized_results[0].name
    assert sanitized.get("authorization") == "[REDACTED]"
