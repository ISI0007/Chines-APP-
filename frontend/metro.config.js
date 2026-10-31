const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);

// This app uses hoisted dependencies. Avoid crawling pnpm's duplicate store.
const existing = config.resolver.blockList;
config.resolver.blockList = [
  ...(Array.isArray(existing) ? existing : existing ? [existing] : []),
  /[/\\]node_modules[/\\]\.pnpm[/\\]/,
];
module.exports = config;
