#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const REQUIRED = [
  "STRIPE_SECRET_KEY",
  "STRIPE_WEBHOOK_SECRET",
  "STRIPE_PRICE_ID_PRO",
  "STRIPE_PRICE_ID_FOUNDING",
  "STRIPE_LOGIN_EMAIL",
  "STRIPE_LOGIN_PASSWORD",
  "STRIPE_BACKUP_CODE",
];

function parseEnv(content) {
  const values = {};
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const idx = line.indexOf("=");
    if (idx <= 0) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    values[key] = value;
  }
  return values;
}

const root = path.resolve(process.cwd());
const envPath = path.join(root, ".env.local");

if (!fs.existsSync(envPath)) {
  console.error(`Missing ${envPath}. Copy .env.example -> .env.local first.`);
  process.exit(1);
}

const parsed = parseEnv(fs.readFileSync(envPath, "utf8"));
const missing = REQUIRED.filter((key) => !parsed[key]);

console.log(`Loaded local env: ${envPath}`);
if (missing.length > 0) {
  console.error("Missing required secret placeholders:");
  for (const key of missing) {
    console.error(`- ${key}`);
  }
  console.error("Set values in .env.local or via your password manager sync process.");
  process.exit(1);
}

console.log("All required secrets are set in .env.local.");
console.log("Secret values are intentionally not printed.");
