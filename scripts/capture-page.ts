#!/usr/bin/env node
import { chromium } from 'playwright';

type Options = {
  url: string;
  output: string;
  viewport: string;
  waitMs: number;
  fullPage: boolean;
};

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const options: Options = {
    url: '',
    output: 'artifacts/actual.png',
    viewport: '1440x900',
    waitMs: 500,
    fullPage: false,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const next = args[index + 1];
    if (arg === '--url') {
      options.url = next;
      index += 1;
    } else if (arg === '--output') {
      options.output = next;
      index += 1;
    } else if (arg === '--viewport') {
      options.viewport = next;
      index += 1;
    } else if (arg === '--wait-ms') {
      options.waitMs = Number(next);
      index += 1;
    } else if (arg === '--full-page') {
      options.fullPage = true;
    }
  }

  if (!options.url) {
    throw new Error('Missing required --url');
  }
  return options;
}

async function main() {
  const options = parseArgs();
  const [width, height] = options.viewport.split('x').map(Number);
  if (!width || !height) {
    throw new Error(`Invalid --viewport: ${options.viewport}`);
  }

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(options.url, { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    if ('fonts' in document) {
      await (document as Document & { fonts: FontFaceSet }).fonts.ready;
    }
  });
  await page.waitForTimeout(options.waitMs);
  await page.screenshot({ path: options.output, fullPage: options.fullPage });
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
