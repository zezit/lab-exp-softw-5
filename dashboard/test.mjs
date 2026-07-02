import { chromium } from 'playwright';

(async () => {
  console.log("Starting browser...");
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let errors = 0;

  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error(`Browser console error: ${msg.text()}`);
      errors++;
    } else if (msg.type() === 'warning') {
      console.warn(`Browser console warning: ${msg.text()}`);
    } else {
      console.log(`Browser console: ${msg.text()}`);
    }
  });

  // Listen for uncaught exceptions
  page.on('pageerror', exception => {
    console.error(`Uncaught exception: ${exception}`);
    errors++;
  });

  console.log("Navigating to http://localhost:3000...");
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 30000 });
    
    // Wait for a bit so React can render and fetch the CSV
    await page.waitForTimeout(5000);
    
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);
    
    // Check if the specific elements are visible
    const cardTitle = await page.locator('text=Medições Totais').isVisible();
    console.log(`Medições Totais card visible: ${cardTitle}`);

    if (errors > 0) {
      console.log(`Found ${errors} errors in the browser.`);
      process.exit(1);
    } else if (!cardTitle) {
      console.log("Error: Expected elements are not visible.");
      process.exit(1);
    } else {
      console.log("Success! No errors found and UI rendered properly.");
    }
  } catch (err) {
    console.error("Navigation failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
