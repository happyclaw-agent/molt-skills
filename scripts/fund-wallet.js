/**
 * Circle Faucet - Fund Provider Wallet
 * 
 * Run: node scripts/fund-wallet.js
 * 
 * Requirements:
 * 1. npm install playwright
 * 2. npx playwright install chromium
 * 3. Install system deps: libnspr4.so, libnss3.so (sudo apt-get install libnspr4 libnss3)
 */

const { chromium } = require('playwright');

const WALLET_ADDRESS = 'HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B';

(async () => {
  console.log('Opening Circle Faucet...');
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('https://faucet.circle.com');
  await page.waitForLoadState('networkidle');
  
  console.log('Page loaded:', await page.title());
  
  // Select Solana Devnet
  const solanaOption = await page.locator('text=Solana Devnet').first();
  if (await solanaOption.isVisible()) {
    await solanaOption.click();
    console.log('Selected Solana Devnet');
  }
  
  // Select USDC
  const usdcOption = await page.locator('text=USDC').first();
  if (await usdcOption.isVisible()) {
    await usdcOption.click();
    console.log('Selected USDC');
  }
  
  // Enter wallet address
  const addressInput = await page.locator('input[placeholder*="address" i], input[type="text"]').first();
  await addressInput.fill(WALLET_ADDRESS);
  console.log('Entered wallet address');
  
  // Click Send/Claim button
  const claimButton = await page.locator('button:has-text("Send"), button:has-text("Claim"), button[type="submit"]').first();
  await claimButton.click();
  console.log('Clicked Send button');
  
  // Wait for success
  await page.waitForTimeout(2000);
  console.log('Transaction submitted!');
  
  await browser.close();
})();
