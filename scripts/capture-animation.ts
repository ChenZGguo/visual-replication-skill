#!/usr/bin/env node
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

type Options = {
  url: string;
  outputDir: string;
  viewport: string;
  durationMs: number;
  fps: number;
};

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const options: Options = {
    url: '',
    outputDir: 'artifacts/frames',
    viewport: '1440x900',
    durationMs: 3000,
    fps: 10,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const next = args[index + 1];
    if (arg === '--url') {
      options.url = next;
      index += 1;
    } else if (arg === '--output-dir') {
      options.outputDir = next;
      index += 1;
    } else if (arg === '--viewport') {
      options.viewport = next;
      index += 1;
    } else if (arg === '--duration-ms') {
      options.durationMs = Number(next);
      index += 1;
    } else if (arg === '--fps') {
      options.fps = Number(next);
      index += 1;
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
  if (!Number.isFinite(options.durationMs) || options.durationMs <= 0) {
    throw new Error(`Invalid --duration-ms: ${options.durationMs}`);
  }
  if (!Number.isFinite(options.fps) || options.fps <= 0) {
    throw new Error(`Invalid --fps: ${options.fps}`);
  }

  await fs.mkdir(options.outputDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(options.url, { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    if ('fonts' in document) {
      await (document as Document & { fonts: FontFaceSet }).fonts.ready;
    }
  });

  const frameCount = Math.max(1, Math.ceil((options.durationMs / 1000) * options.fps));
  const frameDelay = 1000 / options.fps;
  for (let frame = 0; frame < frameCount; frame += 1) {
    await page.screenshot({ path: path.join(options.outputDir, `frame-${String(frame).padStart(4, '0')}.png`) });
    await page.waitForTimeout(frameDelay);
  }

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
