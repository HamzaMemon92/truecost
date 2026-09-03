import os
import time
import subprocess
import re

MATRIX = [
    # Extra for 10+ item basket
    ("Britannia Good Day Cashew Cookies 600g", "snack_2"),
    ("Lays India's Magic Masala Potato Chips 50g", "snack_3"),
    ("Red Bull Energy Drink 250ml", "beverage_2")
]

PROVIDERS = ["blinkit", "zepto", "bigbasket"]
HARNESS_PATH = "mobile/screens/E2EScraperHarness.tsx"
OUT_DIR = "backend/tests/fixtures/scraper_certification/runs/MATRIX"

adb_path = os.environ.get('LOCALAPPDATA') + "\\Android\\Sdk\\platform-tools\\adb.exe"

for provider in PROVIDERS:
    for query, case_id in MATRIX:
        run_id = f"{provider}_{case_id}"
        print(f"=== Running extra {provider}: {query} ===")
        with open(HARNESS_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        new_route = f"const mockRoute = {{ params: {{ provider: '{provider}', query: '{query}', caseId: '{case_id}', domain: 'grocery', runId: '{run_id}' }} }};"
        content = re.sub(r"const mockRoute = \{ params: \{ provider: .*? \};", new_route, content)
        with open(HARNESS_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        subprocess.run([adb_path, "-s", "emulator-5554", "shell", "am", "force-stop", "com.anonymous.truecost"], check=False)
        time.sleep(1)
        subprocess.run([adb_path, "-s", "emulator-5554", "shell", "am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", "truecost://scraper_cert", "com.anonymous.truecost"], check=False)
        time.sleep(15)
        list_cmd = [adb_path, "-s", "emulator-5554", "exec-out", "run-as", "com.anonymous.truecost", "ls", f"files/scraper_captures/{run_id}"]
        res = subprocess.run(list_cmd, capture_output=True, text=True)
        files = [f for f in res.stdout.split() if f.endswith('.json')]
        if files:
            target_file = files[-1]
            out_path = os.path.join(OUT_DIR, f"{run_id}.json")
            cat_cmd = [adb_path, "-s", "emulator-5554", "exec-out", "run-as", "com.anonymous.truecost", "cat", f"files/scraper_captures/{run_id}/{target_file}"]
            with open(out_path, 'wb') as out_f:
                subprocess.run(cat_cmd, stdout=out_f)
            with open(out_path, 'rb') as in_f:
                raw_bytes = in_f.read()
            import codecs
            if raw_bytes.startswith(codecs.BOM_UTF8):
                raw_bytes = raw_bytes[3:]
            decoded = raw_bytes.decode('utf-8', errors='replace').replace('\r\n', '\n')
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(decoded)
            print(f"? Saved {out_path}")
        else:
            print(f"? Failed to capture {run_id}")
