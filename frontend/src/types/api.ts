/**
 * API Type Definitions
 *
 * TypeScript interfaces that strictly follow the backend API contracts
 * defined in docs/rest-api-specification.md and docs/state-management.md
 */

export interface TranslationRequest {
  source_markdown: string;
  glossary?: Record<string, string>;
  llm_config?: {
    provider: "openai" | "ollama" | "mimo" | "deepseek" | "qwen";
    model: string;
    temperature?: number;
    extra_options?: Record<string, any>;
  };
}

export interface TranslationOutput {
  translated_markdown: string;
  metadata: {
    provider_used: string;
    model_used: string;
    glossary_applied: boolean;
    warnings: string[];
  };
}

export interface JobStatus {
  success: boolean;
  status: "idle" | "validating" | "translating" | "completed" | "error";
  progress: number;
  start_time?: string;
  estimated_completion?: string;
  warnings: string[];
  result?: TranslationOutput;
}

export interface TranslationStartResponse {
  success: boolean;
  job_id: string;
  estimated_duration_ms: number;
}

export interface ProviderInfo {
  success: boolean;
  available: boolean;
  provider: string;
  model?: string;
  configuration_status: string;
}

export interface ProvidersResponse {
  success: boolean;
  providers: string[];
}

export interface HealthResponse {
  success: boolean;
  status: "healthy" | "degraded" | "down";
  available_providers: string[];
  provider_status: Record<string, boolean>;
}

export interface ErrorResponse {
  success: boolean;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

// WebSocket Event Types
export interface ProgressUpdateEvent {
  type: "progress_update";
  job_id: string;
  progress: number;
  phase: string;
  phase_progress: number;
  message?: string;
  timestamp: string;
}

export interface StatusUpdateEvent {
  type: "status_update";
  job_id: string;
  status: string;
  progress: number;
  timestamp: string;
}

export interface WarningEvent {
  type: "warning";
  job_id: string;
  message: string;
  timestamp: string;
}

export interface CompletedEvent {
  type: "completed";
  job_id: string;
  result: TranslationOutput;
  timestamp: string;
}

export interface ErrorEvent {
  type: "error";
  job_id: string;
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export interface CancelledEvent {
  type: "cancelled";
  job_id: string;
  timestamp: string;
}

export interface ProviderStatusResponse {
  success: boolean;
  available: boolean;
  provider: string;
  models: string[];  // Changed from model to models (array)
  configuration_status: string;

  // Backward compatibility
  model?: string;  // Will be derived from first model in models array
}

// Union type for all WebSocket events
export type WebSocketEvent =
  | ProgressUpdateEvent
  | StatusUpdateEvent
  | WarningEvent
  | CompletedEvent
  | ErrorEvent
  | CancelledEvent;