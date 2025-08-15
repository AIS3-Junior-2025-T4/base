const puppeteer = require("puppeteer");

const FLAG = process.env.FLAG || "flag{wow_you_are_going_to_win}";
const DOMAIN = process.env.DOMAIN || "dev.vincent55.tw";

const sleep = async (s) =>
  new Promise((resolve) => setTimeout(resolve, 1000 * s));
// bot.js


const visit = async (url) => {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ["--disable-gpu", "--no-sandbox"],
    });
    const context = await browser.createIncognitoBrowserContext();
    const page = await context.newPage();
    await sleep(1);

    // --- 修改開始 ---
    // 從傳入的 URL 中動態取得 hostname (網域名稱)
    const pageDomain = new URL(url).hostname;
    // 將 Cookie 設定在 Bot 將要訪問的那個正確的網域上！
    await page.setCookie({ name: "flag", value: FLAG, domain: pageDomain });
    console.log(`[+] Cookie set on domain: ${pageDomain}`);
    // --- 修改結束 ---

    await sleep(1);
    page.goto(url, { waitUntil: 'domcontentloaded' });
    await sleep(1);

    const link = await page.$('#videobtn');
    if (link) {
      const encodedHref = await page.evaluate(el => el.href, link);
      const href = decodeURIComponent(encodedHref);
      if (href.startsWith('javascript:')) {
        await page.evaluate(href.substring(11));
        console.log('[+] Payload executed directly after decoding.');
      }
    } else {
      console.log('[-] Could not find #videobtn to execute payload.');
    }

    await sleep(2);
    await browser.close();
  } catch (e) {
    console.log(e);
  } finally {
    if (browser) await browser.close();
  }
};
module.exports = visit;

if (require.main === module) {
  visit("http://example.com");
}
