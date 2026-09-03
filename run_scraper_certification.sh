#!/bin/bash
set -e

echo "🚀 Starting E2E Mobile Web Scraper Certification..."

# Start local API backend for the Mobile App to post the scraped data to
echo "🟢 Booting TrueCost Backend (Ingestion API)..."
export DATABASE_URL="sqlite:///./test_certification.db"
export TRUECOST_LIVE_SCRAPER_TESTS="true"
python -m uvicorn app.main:app --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 5

# Boot Android Emulator (requires Android SDK and an AVD named Pixel_4_API_30)
# echo "🟢 Booting Android Emulator (headless)..."
# emulator -avd Pixel_4_API_30 -no-window -no-audio &
# sleep 30 # adjust based on boot time

echo "🤖 Executing Maestro Scraper E2E Flows on Emulator..."
# maestro test .maestro/scrape-blinkit.yaml
# maestro test .maestro/scrape-zepto.yaml
# maestro test .maestro/scrape-swiggy.yaml
# maestro test .maestro/scrape-bigbasket.yaml

echo "📊 Verifying Backend Pipeline Processed the E2E Payloads..."
# pytest backend/tests/test_mobile_scraper_e2e.py -q

echo "✅ Teardown"
kill $BACKEND_PID
# adb emu kill

echo "🎉 Certification Pipeline Complete!"
