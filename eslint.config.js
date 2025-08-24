// eslint.config.js
import js from "@eslint/js";

export default [
  // Base JS recommended rules
  js.configs.recommended,

  // Apply to all JS/JSX files
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
      "eqeqeq": ["warn", "always"],
    },
  },

  // Ignore irrelevant/problematic folders
  {
    ignores: [
      "WX51A40D1621/**",
      "net607/**",
      "**/node_modules/**",
      "**/dist/**",
      "venv/**",
      "hunter_env/**",
      "fresh_env/**",
      "**/*.py",
    ],
  },
];
