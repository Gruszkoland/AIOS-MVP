#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const REQUIRED_KEYS = [
  "NEXT_PUBLIC_APP_URL",
  "REFERENCE_CONTACT_EMAIL",
  "STRIPE_DASHBOARD_TEST_URL",
  "STRIPE_SECRET_KEY",
  "STRIPE_WEBHOOK_SECRET",
  "STRIPE_PRICE_ID_PRO",
  "STRIPE_PRICE_ID_FOUNDING",
  "STRIPE_LOGIN_EMAIL",
  "STRIPE_LOGIN_PASSWORD",
  "STRIPE_BACKUP_CODE",
];

const SECRET_KEYS = [
  "STRIPE_SECRET_KEY",
  "STRIPE_WEBHOOK_SECRET",
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

const envTemplatePath = path.resolve(process.cwd(), ".env.example");
if (!fs.existsSync(envTemplatePath)) {
  console.error(`Missing env template: ${envTemplatePath}`);
  process.exit(1);
}

const parsed = parseEnv(fs.readFileSync(envTemplatePath, "utf8"));
const missing = REQUIRED_KEYS.filter((key) => !(key in parsed));
if (missing.length > 0) {
  console.error("Missing required keys in .env.example:");
  for (const key of missing) {
    console.error(`- ${key}`);
  }
  process.exit(1);
}

const leakedSecrets = SECRET_KEYS.filter((key) => {
  const value = (parsed[key] || "").trim();
  if (!value) return false;
  return true;
});

if (leakedSecrets.length > 0) {
  console.error("Secret placeholders in .env.example must be empty. Non-empty keys:");
  for (const key of leakedSecrets) {
    console.error(`- ${key}`);
  }
  process.exit(1);
}

console.log(".env.example template is valid and contains no embedded secrets.");
