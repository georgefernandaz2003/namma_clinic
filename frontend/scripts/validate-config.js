/**
 * validate-config.js
 * 
 * Verifies that when VITE_API_BASE_URL is configured (e.g. staging or production),
 * the Vite bundle uses the configured base URL and does NOT fall back to localhost.
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');
const distAssetsDir = path.join(frontendDir, 'dist', 'assets');

const STAGING_URL = 'https://staging.nammaclinic.karnataka.gov.in/api/';

console.log('--- Validating Frontend Configuration Contract ---');
console.log(`Building with VITE_API_BASE_URL=${STAGING_URL}...`);

// 1. Build with custom staging URL
execSync('npm run build', {
  cwd: frontendDir,
  env: { ...process.env, VITE_API_BASE_URL: STAGING_URL },
  stdio: 'inherit'
});

// 2. Inspect output JS files
const files = fs.readdirSync(distAssetsDir);
const jsFiles = files.filter(f => f.endsWith('.js'));
let foundStagingUrl = false;
let foundLocalhost = false;

for (const jsFile of jsFiles) {
  const content = fs.readFileSync(path.join(distAssetsDir, jsFile), 'utf-8');
  if (content.includes(STAGING_URL)) {
    foundStagingUrl = true;
  }
  if (content.includes('http://localhost:8000/api/')) {
    foundLocalhost = true;
  }
}

if (!foundStagingUrl) {
  console.error(`FAILED: Expected staging URL ${STAGING_URL} was NOT found in dist bundle.`);
  process.exit(1);
}

if (foundLocalhost) {
  console.error('FAILED: Found hardcoded localhost:8000 URL in dist bundle even when VITE_API_BASE_URL was set.');
  process.exit(1);
}

console.log('SUCCESS: Configured VITE_API_BASE_URL is active in bundle and localhost is excluded.');

// 3. Clean rebuild with default local development settings
console.log('Restoring default build...');
execSync('npm run build', {
  cwd: frontendDir,
  env: { ...process.env, VITE_API_BASE_URL: '' },
  stdio: 'inherit'
});
console.log('--- Configuration Contract Validation Passed! ---');
