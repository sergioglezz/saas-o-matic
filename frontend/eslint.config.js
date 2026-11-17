// @ts-check
const eslint = require('@eslint/js');
const { defineConfig } = require('eslint/config');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');

// Pure modules (spec 005 plan §2): no Angular, no RxJS, testable without a screen.
const PURE_FILES = [
  'src/app/core/api/api-models.ts',
  'src/app/core/rates/rates-snapshot.ts',
  'src/app/shared/format/**/*.ts',
  'src/app/shared/texts.ts',
  'src/app/features/simulator/usage-input.ts',
  'src/app/features/customers/customer-form-errors.ts',
];

module.exports = defineConfig([
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      tseslint.configs.recommended,
      tseslint.configs.stylistic,
      angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      '@angular-eslint/directive-selector': [
        'error',
        {
          type: 'attribute',
          prefix: 'app',
          style: 'camelCase',
        },
      ],
      '@angular-eslint/component-selector': [
        'error',
        {
          type: 'element',
          prefix: 'app',
          style: 'kebab-case',
        },
      ],
      // AGENTS.md: strict TypeScript without `any`; files under 300 lines.
      '@typescript-eslint/no-explicit-any': 'error',
      'max-lines': ['error', { max: 300 }],
    },
  },
  {
    // AGENTS.md: functions under 40 lines. Test files group cases inside `describe`.
    files: ['src/**/*.ts'],
    ignores: ['src/**/*.spec.ts'],
    rules: {
      'max-lines-per-function': ['error', { max: 40 }],
    },
  },
  {
    // AGENTS.md: HTTP calls only from services, which live in core/.
    files: ['src/**/*.ts'],
    ignores: ['src/app/core/**'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: '@angular/common/http',
              importNames: ['HttpClient'],
              message: 'Solo core/ habla con el backend (AGENTS.md).',
            },
          ],
        },
      ],
    },
  },
  {
    files: PURE_FILES,
    ignores: ['src/app/shared/format/format-pipes*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@angular/*', 'rxjs', 'rxjs/*'],
              message: 'Este módulo es puro: sin Angular ni RxJS (plan 005 §2).',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['**/*.html'],
    extends: [angular.configs.templateRecommended, angular.configs.templateAccessibility],
    rules: {},
  },
]);
