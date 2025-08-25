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

// Write to buildInfo.ts
const buildInfoPath = path.join(__dirname, '..', 'src', 'buildInfo.ts');
fs.writeFileSync(buildInfoPath, buildInfo);

console.log(`Build info generated: v${packageJson.version} at ${new Date().toISOString()}`);