/**
 * Circle Faucet - Fund Provider Wallet
 */

const { chromium } = require('playwright');

const WALLET_ADDRESS = 'HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B';

(async () => {
  console.log('Opening Circle Faucet...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://faucet.circle.com');
  await page.waitForTimeout(5000);
  
  console.log('Page title:', await page.title());
  
  // Fill wallet address
  await page.evaluate((addr) => {
    const inputs = document.querySelectorAll('input');
    for (const input of inputs) {
      if (input.placeholder && input.placeholder.toLowerCase().includes('wallet')) {
        input.value = addr;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        break;
      }
    }
  }, WALLET_ADDRESS);
  
  console.log('Filled wallet address');
  
  // Check for CAPTCHA or login requirement
  const captchaCheck = await page.evaluate(() => {
    const body = document.body.innerHTML;
    return {
      hasCaptcha: body.includes('captcha') || body.includes('reCAPTCHA'),
      hasChallenge: body.includes('challenge') || body.includes('checkbox'),
    };
  });
  
  console.log('CAPTCHA check:', captchaCheck);
  
  // Check submit button state
  const buttonState = await page.evaluate(() => {
    const btn = document.querySelector('button[type="submit"]');
    return {
      exists: !!btn,
      disabled: btn?.disabled,
      text: btn?.textContent?.substring(0, 100),
    };
  });
  
  console.log('Submit button:', JSON.stringify(buttonState));
  
  // Check for any error messages or alerts
  const alerts = await page.evaluate(() => {
    const alerts = document.querySelectorAll('[role="alert"], .alert, .error');
    return Array.from(alerts).map(a => a.textContent?.substring(0, 100));
  });
  
  console.log('Alerts:', alerts);
  
  await browser.close();
  console.log('Done');
})();
