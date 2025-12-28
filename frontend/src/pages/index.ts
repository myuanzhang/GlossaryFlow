/**
 * Pages Export Index
 *
 * Central export file for all page components
 */

// Page Components
export { default as DocumentUploadPage } from './DocumentUpload';
export { default as TranslationProgressPage } from './TranslationProgress';
export { default as TranslationResultPage } from './TranslationResult';

// Re-export page props types for convenience
export type {
  DocumentUploadPageProps,
  TranslationProgressPageProps,
  TranslationResultPageProps
} from '../types/ui';