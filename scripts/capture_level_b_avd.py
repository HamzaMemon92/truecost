"""
TrueCost - Level-B Real Device Data Capture Automator

This script connects to a running Android AVD (Android Virtual Device)
via ADB and automates the React Native application to execute searches
across all 28 target providers.

Prerequisites:
- App must be installed on the emulator: `adb install path/to/app.apk`
- Emulator must be running: `adb devices` should show it.
- TCP interception or React Native Debugger should be active to sniff 
  the `window.fetch` payload, OR the app must be configured to log 
  its /capture endpoint POSTs to adb logcat.

Usage:
  python scripts/capture_level_b_avd.py
"""
import subprocess
import time
import json
import os

PROVIDERS = [
    # Food
    "swiggy_food", "zomato", "magicpin", "eatsure",
    # Pharmacy
    "tata1mg", "pharmeasy", "apollo247", "netmeds",
    # Shopping
    "amazon", "flipkart", "meesho", "myntra",
    # Mobility
    "uber", "ola", "rapido", "namma_yatri",
    # Travel
    "makemytrip", "goibibo", "ixigo", "cleartrip",
    # Finance
    "bankbazaar", "policybazaar", "paisabazaar", "creditmantri",
    # Productivity
    "notion", "figma", "slack", "canva"
]

TEST_QUERIES = {
    "food": "Margherita Pizza",
    "pharmacy": "Paracetamol 500mg",
    "shopping": "Apple AirPods Pro",
    "mobility": "MG Road to Indiranagar",
    "travel": "DEL to BOM",
    "finance": "Credit Card",
    "services": "Enterprise Plan"
}

def run_adb(cmd):
    result = subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def check_device():
    devices = run_adb("devices").split('\n')[1:]
    active = [d for d in devices if 'device' in d and 'offline' not in d]
    if not active:
        print("[-] FATAL: No active Android AVD detected. Boot your emulator first.")
        print("    Run: emulator -avd <Your_AVD_Name>")
        return False
    print(f"[+] Connected to AVD: {active[0].split()[0]}")
    return True

def launch_app():
    print("[+] Launching TrueCost Mobile App...")
    # Adjust package name based on your React Native build
    run_adb("shell monkey -p com.decisionadvisor -c android.intent.category.LAUNCHER 1")
    time.sleep(5) # Wait for React Native bundle to load

def trigger_provider_search(provider, query):
    """
    Uses ADB shell deep links to force the app to navigate and search.
    Requires React Native Navigation deep linking to be configured.
    """
    print(f"[*] Dispatching deep link for {provider} -> '{query}'")
    deeplink = f"truecost://search?provider={provider}&q={query.replace(' ', '%20')}"
    run_adb(f'shell am start -W -a android.intent.action.VIEW -d "{deeplink}" com.decisionadvisor')
    
    # Wait for the scraper WebView to execute and postMessage
    print("    Waiting for scraper execution (10s)...")
    time.sleep(10)

def extract_logcat_payload(provider):
    """
    Dumps logcat, searches for the 'TRUECOST_CAPTURE_SUCCESS' log,
    and extracts the JSON payload emitted by the native bridge.
    """
    logs = run_adb("logcat -d -s TrueCostScraper:V")
    
    for line in reversed(logs.split('\n')):
        if "TRUECOST_CAPTURE_SUCCESS" in line and provider in line:
            try:
                # Extract JSON substring
                json_str = line[line.find('{'):]
                payload = json.loads(json_str)
                return payload
            except Exception as e:
                print(f"    [!] Failed to parse JSON from logcat: {e}")
                return None
    return None

def main():
    print("=========================================================")
    print(" TRUECOST LEVEL-B AUTOMATED DEVICE CAPTURE SCRIPT")
    print("=========================================================")
    
    if not check_device():
        return

    # Clear logcat buffer
    run_adb("logcat -c")
    launch_app()

    out_dir = "backend/tests/fixtures/scraper_certification/runs/MATRIX"
    os.makedirs(out_dir, exist_ok=True)
    
    captured = 0
    for provider in PROVIDERS:
        # Determine generic category by naive substring (for test demo purposes)
        cat = "shopping"
        for k in TEST_QUERIES.keys():
            if k in provider.lower() or provider in ["uber", "ola"]: 
                cat = "mobility"
            # In a full run, we'd pull the exact category from provider_catalog.json
            
        query = TEST_QUERIES.get(cat, "Test Query")
        
        trigger_provider_search(provider, query)
        payload = extract_logcat_payload(provider)
        
        if payload:
            fname = f"{out_dir}/{provider}_automated_capture.json"
            with open(fname, 'w') as f:
                json.dump(payload, f, indent=2)
            print(f"    [+] SUCCESS: Saved {fname}")
            captured += 1
        else:
            print(f"    [-] FAILED: No capture payload detected in logcat for {provider}")
    
    print("=========================================================")
    print(f" CAPTURE RUN COMPLETE. Successfully acquired {captured}/{len(PROVIDERS)} payloads.")
    print("=========================================================")

if __name__ == "__main__":
    main()
