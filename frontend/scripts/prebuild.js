const fs = require('fs');
const path = require('path');

// Read package.json to get version
const packageJson = require('../package.json');

// Generate build info
const buildInfo = `// This file is auto-generated at build time
export const buildInfo = {
  version: '${packageJson.version}',
  buildTime: '${new Date().toISOString()}',
};
`;

// Ensure src directory exists
const srcPath = path.join(__dirname, '..', 'src');
if (!fs.existsSync(srcPath)) {
  fs.mkdirSync(srcPath, { recursive: true });
}

// Write to buildInfo.ts
const buildInfoPath = path.join(srcPath, 'buildInfo.ts');
fs.writeFileSync(buildInfoPath, buildInfo);

console.log(`Build info generated: v${packageJson.version} at ${new Date().toISOString()}`);