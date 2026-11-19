import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const INPUT_PATH = join(BOT_DIR, "POST.json");
const OUTPUT_PATH = join(OUTPUT_DIR, "POST.json");

// A real X post URL, or the placeholder the repo ships with until the
// user posts from their phone and the real URL is filled in.
const URL_PATTERN =
  /^https:\/\/(?:x\.com|twitter\.com)\/(?:[A-Za-z0-9_]+|%3Chandle%3E|<handle>)\/status\/(?:\d+|<id>)$/;

function fail(message: string): never {
  process.stderr.write(`main.ts: ${message}\n`);
  process.exit(1);
}

let raw: Buffer;
try {
  raw = readFileSync(INPUT_PATH);
} catch {
  fail(`cannot read ${INPUT_PATH}: file is missing`);
}

let parsed: unknown;
try {
  parsed = JSON.parse(raw.toString("utf-8"));
} catch {
  fail(`${INPUT_PATH} is not valid JSON`);
}

if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
  fail(`${INPUT_PATH} must contain a JSON object`);
}

const url = (parsed as Record<string, unknown>).url;
if (typeof url !== "string" || !URL_PATTERN.test(url)) {
  fail(
    `${INPUT_PATH} must contain a "url" like https://x.com/<handle>/status/<digits>`,
  );
}

try {
  mkdirSync(OUTPUT_DIR, { recursive: true });
  writeFileSync(OUTPUT_PATH, raw);
  // Verify the copy round-trips byte-for-byte before reporting success.
  if (!readFileSync(OUTPUT_PATH).equals(raw)) {
    fail(`${OUTPUT_PATH} does not match ${INPUT_PATH} after writing`);
  }
} catch (error) {
  if (error instanceof Error && error.message.startsWith("main.ts:")) throw error;
  fail(`cannot write ${OUTPUT_PATH}`);
}
