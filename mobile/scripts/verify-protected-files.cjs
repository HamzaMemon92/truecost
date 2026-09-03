const { createHash } = require('node:crypto');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');

const expected = {
  'components/core/ScraperManager.tsx': '06c6126c206ab8f5a0d599f695e56a5919683f90156ec0cd4435a0db027c6bc8',
  'screens/AgentSearchScreen.tsx': 'b63ca3c864e5bb303dae9efd6dfd52729bb169e2624e7877026c3e9fe6de073f',
};
let failed = false;
for (const [relativePath, expectedHash] of Object.entries(expected)) {
  const actual = createHash('sha256').update(readFileSync(resolve(__dirname, '..', relativePath))).digest('hex');
  if (actual !== expectedHash) {
    failed = true;
    console.error('Protected file changed: ' + relativePath + '\nExpected ' + expectedHash + '\nActual   ' + actual);
  } else {
    console.log('Protected file verified: ' + relativePath);
  }
}
if (failed) process.exit(1);
