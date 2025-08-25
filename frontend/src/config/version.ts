/**
 * Version configuration for the application
 * This file centralizes version management and provides utilities
 * for displaying and checking version information
 */

import packageJson from '../../package.json';
import { buildInfo } from '../buildInfo';

export const APP_VERSION = buildInfo.version || packageJson.version;
export const APP_NAME = packageJson.name;
export const BUILD_TIME = buildInfo.buildTime;

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
    buildTime: BUILD_TIME,
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