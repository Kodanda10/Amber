#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const args = require('minimist')(process.argv.slice(2));
const minLines = Number(args.lines || 95);
const minBranches = Number(args.branches || 90);
const summaryPath = path.resolve(args.summary || 'coverage/coverage-summary.json');

if (!fs.existsSync(summaryPath)) {
  console.error(`coverage summary not found at ${summaryPath}`);
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
const totals = data.total || {};
const lines = totals.lines?.pct ?? 0;
const branches = totals.branches?.pct ?? 0;

console.log(`Coverage -> lines: ${lines}%, branches: ${branches}% (targets lines>=${minLines}, branches>=${minBranches})`);
if (lines < minLines || branches < minBranches) {
  console.error('Coverage gate failed');
  process.exit(1);
}
console.log('Coverage gate passed');
