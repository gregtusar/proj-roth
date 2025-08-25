/**
 * Version configuration for the application
 * This file centralizes version management and provides utilities
 * for displaying and checking version information
 */

import packageJson from '../../package.json';

export const APP_VERSION = packageJson.version;
export const APP_NAME = packageJson.name;

/**
 * Get formatted version string for display
 */
export const getVersionDisplay = (): string => {
  return `v${APP_VERSION}`;
};

/**
 * Get full version info including build details
 */
export const getVersionInfo = () => {
  return {
    version: APP_VERSION,
    name: APP_NAME,
    buildTime: process.env.REACT_APP_BUILD_TIME || 'development',
    environment: process.env.NODE_ENV,
  };
};

/**
 * Log version info to console for debugging
 */
export const logVersionInfo = () => {
  console.log(`%c${APP_NAME} ${getVersionDisplay()}`, 'color: #4a90e2; font-weight: bold');
  console.log('Build Info:', getVersionInfo());
};