require('ts-node').register({ transpileOnly: true });
const { sanitizeCapture } = require('./lib/scraperCertification/sanitizeCapture.ts');
const fs = require('fs');

const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
const output = sanitizeCapture(input);
console.log(JSON.stringify(output));
