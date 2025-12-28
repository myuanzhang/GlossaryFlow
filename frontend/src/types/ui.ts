/**
 * UI Type Definitions
 *
 * TypeScript interfaces for UI components and state management
 */

import { ProviderInfo } from './api';

export interface ErrorInfo {
  code: string;
  message: string;
  details?: any;
}

export interface FileUploadProps {
  accept: string;
  onFileSelect: (file: File) => void;
  placeholder?: string;
  maxSize?: number;
  label: string;
  optional?: boolean;
}

export interface ProgressDisplayProps {
  progress: number;
  status: string;
  currentPhase: string;
  estimatedTimeRemaining: number | null;
  warnings: string[];
  canCancel?: boolean;
  onCancel?: () => void;
}

export interface ProviderSelectorProps {
  disabled?: boolean;
}

export interface ErrorDisplayProps {
  onRetry?: () => void;
  onDismiss?: () => void;
  showRetry?: boolean;
}

// Page Props
export interface DocumentUploadPageProps {}

export interface TranslationProgressPageProps {
  jobId: string;
}

export interface TranslationResultPageProps {
  jobId: string;
}

// Navigation types
export type PageRoute = "/" | "/progress/:jobId" | "/result/:jobId";

// Utility types
export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";
export type TranslationPhase = "validation" | "prompt_building" | "llm_request" | "output_cleaning" | "completed";

// Glossary Upload Types
export interface GlossaryUploadProps {
  onGlossaryReady: (glossary: Record<string, string>) => void;
  maxSize?: number;
  optional?: boolean;
}

export interface GlossaryUploadRef {
  clearGlossary: () => void;
  getGlossary: () => Record<string, string> | null;
}