const puppeteer = require('puppeteer');

(async () => {
  try {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    // Simulate iPhone 13 Pro viewport
    await page.setViewport({ width: 390, height: 844, isMobile: true });
    
    console.log("Navigating to Expo Web App...");
    await page.goto('http://127.0.0.1:8082', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise(r => setTimeout(r, 4000));
    
    // Screenshot 1: Welcome Screen
    await page.screenshot({ path: 'screenshot_1_welcome.png' });
    console.log(`Saved screenshot_1_welcome.png`);

    // Click "Continue as guest"
    console.log("Clicking Continue as guest...");
    const guestButtons = await page.$x("//div[contains(text(), 'Continue as guest')]");
    if (guestButtons.length > 0) {
        await guestButtons[0].click();
        await new Promise(r => setTimeout(r, 4000));
        
        // Screenshot 2: Home Dashboard
        await page.screenshot({ path: 'screenshot_2_dashboard.png' });
        console.log(`Saved screenshot_2_dashboard.png`);
        
        // Click on "Profile" or "Settings" tab in the bottom bar
        const profileTabs = await page.$x("//div[contains(text(), 'Profile')]");
        if (profileTabs.length > 0) {
            await profileTabs[0].click();
            await new Promise(r => setTimeout(r, 3000));
            // Screenshot 3: Profile
            await page.screenshot({ path: 'screenshot_3_profile.png' });
            console.log(`Saved screenshot_3_profile.png`);
        }
    }

    await browser.close();
  } catch (error) {
    console.error("Error taking screenshot:", error);
    process.exit(1);
  }
})();
