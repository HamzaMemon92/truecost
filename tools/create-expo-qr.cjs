const fs = require('fs');
const path = require('path');
const { toQR } = require('../mobile/node_modules/toqr/dist/toqr.js');

const url = process.argv[2] || 'exp://192.168.1.2:8081';
const matrix = toQR(url);
const size = Math.sqrt(matrix.length);
const scale = 14;
const quiet = 4;
const dim = (size + quiet * 2) * scale;

let rects = '';
for (let y = 0; y < size; y += 1) {
  for (let x = 0; x < size; x += 1) {
    if (matrix[y * size + x]) {
      rects += `<rect x="${(x + quiet) * scale}" y="${(y + quiet) * scale}" width="${scale}" height="${scale}"/>`;
    }
  }
}

const svg = [
  `<svg xmlns="http://www.w3.org/2000/svg" width="${dim}" height="${dim + 72}" viewBox="0 0 ${dim} ${dim + 72}">`,
  '<rect width="100%" height="100%" fill="white"/>',
  `<g fill="black">${rects}</g>`,
  `<text x="50%" y="${dim + 34}" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#111">${url}</text>`,
  '</svg>',
].join('');

const out = path.resolve(process.cwd(), 'expo-go-qr.svg');
fs.writeFileSync(out, svg);
console.log(out);
