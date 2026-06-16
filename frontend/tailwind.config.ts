// Tailwind CSS Configuration
// Extends default config with custom theme values if needed

import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Add custom colors if needed
        'prodoscore-blue': '#0052CC',
        'prodoscore-red': '#EA4335',
      },
      spacing: {
        // Add custom spacing if needed
      },
    },
  },
  plugins: [],
};

export default config;