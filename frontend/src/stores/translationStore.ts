/**
 * Translation Store
 *
 * Zustand store for managing translation application state
 * Follows the contract defined in docs/rest-api-specification.md
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { translationAPI } from '../services/api';
import type {
  TranslationRequest,
  JobStatus,
  TranslationOutput,
  TranslationStartResponse,
  ProviderInfo,
  ProvidersResponse,
  HealthResponse,
  WebSocketEvent,
  ProviderStatusResponse
} from '../types/api';

// Store state interface
interface TranslationState {
  // Current job state
  currentJobId: string | null;
  jobStatus: JobStatus | null;
  isTranslating: boolean;
  translationResult: TranslationOutput | null;

  // File upload state
  uploadedFile: File | null;
  uploadedFileName: string;
  uploadedContent: string;

  // Glossary state (optional)
  glossaryFile: File | null;
  glossaryData: Record<string, string> | null;
  glossaryFileName: string;

  // Provider configuration
  availableProviders: ProvidersResponse | null;
  selectedProvider: string;
  selectedModel: string;

  // System state
  isConnected: boolean;
  systemHealth: HealthResponse | null;

  // UI state
  errors: string[];
  warnings: string[];

  // WebSocket connection
  wsConnection: WebSocket | null;
}

// Store actions interface
interface TranslationActions {
  // File operations
  setUploadedFile: (file: File | null) => void;
  setUploadedContent: (content: string) => void;
  clearUpload: () => void;

  // Job operations
  startTranslation: (request: TranslationRequest) => Promise<TranslationStartResponse>;
  cancelTranslation: () => Promise<void>;
  fetchJobStatus: (jobId: string) => Promise<void>;
  downloadResult: () => Promise<void>;

  // Provider operations
  fetchProviders: () => Promise<void>;
  fetchProviderStatus: (providerName: string) => Promise<ProviderStatusResponse>;
  setSelectedProvider: (provider: string, model: string) => void;
  checkSystemHealth: () => Promise<void>;

  // WebSocket operations
  connectWebSocket: (jobId: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (event: WebSocketEvent) => void;

  // State management
  setConnected: (connected: boolean) => void;
  addError: (error: string) => void;
  clearErrors: () => void;
  addWarning: (warning: string) => void;
  clearWarnings: () => void;
  resetState: () => void;

  // Glossary operations
  setGlossaryFile: (file: File | null) => void;
  setGlossaryData: (glossary: Record<string, string> | null) => void;
  setGlossaryFileName: (name: string) => void;
  clearGlossary: () => void;
}

// Initial state
const initialState: TranslationState = {
  currentJobId: null,
  jobStatus: null,
  isTranslating: false,
  translationResult: null,

  uploadedFile: null,
  uploadedFileName: '',
  uploadedContent: '',

  glossaryFile: null,
  glossaryData: null,
  glossaryFileName: '',

  availableProviders: null,
  selectedProvider: '',
  selectedModel: '',

  isConnected: false,
  systemHealth: null,

  errors: [],
  warnings: [],

  wsConnection: null,
};

// Create the store
export const useTranslationStore = create<TranslationState & TranslationActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // File operations
      setUploadedFile: (file: File | null) => {
        set({
          uploadedFile: file,
          uploadedFileName: file?.name || '',
          errors: [] // Clear errors when new file is uploaded
        });
      },

      setUploadedContent: (content: string) => {
        set({ uploadedContent: content });
      },

      clearUpload: () => {
        set({
          uploadedFile: null,
          uploadedFileName: '',
          uploadedContent: '',
          errors: [],
          warnings: []
        });
      },

      // Job operations
      startTranslation: async (request: TranslationRequest): Promise<TranslationStartResponse> => {
        const state = get();

        try {
          set({
            isTranslating: true,
            errors: [],
            warnings: [],
            translationResult: null
          });

          // Start translation - this returns immediately with job_id
          const response = await translationAPI.startTranslation(request);

          // ⚠️ CRITICAL: 验证响应包含 job_id
          if (!response || !response.job_id) {
            throw new Error('Invalid response: missing job_id');
          }

          // Update state with job ID
          set({
            currentJobId: response.job_id,
            isTranslating: true
          });

          // Connect WebSocket for real-time updates
          get().connectWebSocket(response.job_id);

          // 返回响应以便调用方验证
          return response;

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to start translation';
          set({
            isTranslating: false,
            errors: [errorMessage],
            currentJobId: null  // ⚠️ 失败时清除 job_id
          });

          // ⚠️ CRITICAL: 重新抛出异常，让调用方处理
          throw error;
        }
      },

      cancelTranslation: async () => {
        const state = get();

        if (!state.currentJobId) {
          return;
        }

        try {
          await translationAPI.cancelTranslation(state.currentJobId);

          // Disconnect WebSocket
          get().disconnectWebSocket();

          // Reset state
          set({
            currentJobId: null,
            jobStatus: null,
            isTranslating: false,
            translationResult: null,
            wsConnection: null
          });

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to cancel translation';
          set({ errors: [errorMessage] });
        }
      },

      fetchJobStatus: async (jobId: string) => {
        try {
          const status = await translationAPI.getTranslationStatus(jobId);

          set({
            jobStatus: status,
            isTranslating: status.status !== 'completed' && status.status !== 'error',
            translationResult: status.result || null
          });

          // Update warnings
          if (status.warnings.length > 0) {
            set({ warnings: status.warnings });
          }

        } catch (error) {
          console.error('Failed to fetch job status:', error);
          const errorMessage = error instanceof Error ? error.message : 'Failed to fetch job status';
          set({ errors: [errorMessage] });
        }
      },

      downloadResult: async () => {
        const state = get();

        if (!state.currentJobId) {
          set({ errors: ['No job to download'] });
          return;
        }

        try {
          const result = await translationAPI.getTranslationResult(state.currentJobId);

          // Create download link
          const blob = new Blob([result], { type: 'text/markdown' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${state.uploadedFileName || 'translated'}.md`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to download result';
          set({ errors: [errorMessage] });
        }
      },

      // Provider operations
      fetchProviders: async () => {
        try {
          const providers = await translationAPI.getProviders();
          set({ availableProviders: providers });
        } catch (error) {
          console.error('Failed to fetch providers:', error);
        }
      },

      fetchProviderStatus: async (providerName: string) => {
        try {
          const response = await translationAPI.getProviderStatus(providerName);
          return response;
        } catch (error) {
          console.error(`Failed to fetch provider status for ${providerName}:`, error);
          throw error;
        }
      },

      setSelectedProvider: (provider: string, model: string) => {
        set({
          selectedProvider: provider,
          selectedModel: model
        });
      },

      checkSystemHealth: async () => {
        try {
          const health = await translationAPI.getSystemHealth();
          set({
            systemHealth: health,
            isConnected: health.status === 'healthy'
          });
        } catch (error) {
          set({
            isConnected: false,
            systemHealth: null
          });
        }
      },

      // WebSocket operations
      connectWebSocket: (jobId: string) => {
        const state = get();

        // Disconnect existing connection
        if (state.wsConnection) {
          state.wsConnection.close();
        }

        try {
          // Create WebSocket connection
          const wsUrl = `ws://localhost:8000/ws/${jobId}`;
          const ws = new WebSocket(wsUrl);

          ws.onopen = () => {
            console.log('WebSocket connected');
            set({ wsConnection: ws });
          };

          ws.onmessage = (event) => {
            try {
              const wsEvent: WebSocketEvent = JSON.parse(event.data);
              get().handleWebSocketMessage(wsEvent);
            } catch (error) {
              console.error('Failed to parse WebSocket message:', error);
            }
          };

          ws.onclose = () => {
            console.log('WebSocket disconnected');
            set({ wsConnection: null });
          };

          ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            // Don't add error for completed jobs - WebSocket might fail gracefully
            // because job is already done
          };

        } catch (error) {
          console.error('Failed to create WebSocket connection:', error);
          set({ errors: ['Failed to create WebSocket connection'] });
        }
      },

      disconnectWebSocket: () => {
        const state = get();

        if (state.wsConnection) {
          state.wsConnection.close();
          set({ wsConnection: null });
        }
      },

      handleWebSocketMessage: (event: WebSocketEvent) => {
        const state = get();

        switch (event.type) {
          case 'progress_update':
            // Update progress in job status
            if (state.jobStatus) {
              set({
                jobStatus: {
                  ...state.jobStatus,
                  progress: event.progress
                }
              });
            }
            break;

          case 'status_update':
            // Update job status
            set({
              jobStatus: {
                success: true,
                status: event.status as any,
                progress: event.progress,
                warnings: []
              }
            });
            break;

          case 'warning':
            // Add warning
            get().addWarning(event.message);
            break;

          case 'completed':
            // Translation completed
            set({
              jobStatus: {
                success: true,
                status: 'completed',
                progress: 100,
                warnings: []
              },
              translationResult: event.result,
              isTranslating: false
            });

            // Disconnect WebSocket
            get().disconnectWebSocket();
            break;

          case 'error':
            // Translation error
            const errorMessage = event.error.message || 'Translation failed';
            set({
              errors: [errorMessage],
              isTranslating: false,
              jobStatus: {
                success: false,
                status: 'error',
                progress: state.jobStatus?.progress || 0,
                warnings: []
              }
            });

            // Disconnect WebSocket
            get().disconnectWebSocket();
            break;

          case 'cancelled':
            // Translation cancelled
            set({
              currentJobId: null,
              jobStatus: null,
              isTranslating: false,
              translationResult: null,
              wsConnection: null
            });
            break;
        }
      },

      // State management
      setConnected: (connected: boolean) => {
        set({ isConnected: connected });
      },

      addError: (error: string) => {
        set(state => ({
          errors: [...state.errors, error]
        }));
      },

      clearErrors: () => {
        set({ errors: [] });
      },

      addWarning: (warning: string) => {
        set(state => ({
          warnings: [...state.warnings, warning]
        }));
      },

      clearWarnings: () => {
        set({ warnings: [] });
      },

      // Glossary operations
      setGlossaryFile: (file: File | null) => {
        set({
          glossaryFile: file,
          glossaryFileName: file?.name || ''
        });
      },

      setGlossaryData: (glossary: Record<string, string> | null) => {
        set({ glossaryData: glossary });
      },

      setGlossaryFileName: (name: string) => {
        set({ glossaryFileName: name });
      },

      clearGlossary: () => {
        set({
          glossaryFile: null,
          glossaryData: null,
          glossaryFileName: ''
        });
      },

      resetState: () => {
        // Disconnect WebSocket
        get().disconnectWebSocket();

        // Reset all state
        set({
          ...initialState,
          // Keep some UI state
          availableProviders: get().availableProviders,
          selectedProvider: get().selectedProvider,
          selectedModel: get().selectedModel
        });
      }
    }),
    {
      name: 'translation-store'
    }
  )
);

// Export selector hooks for common combinations
export const useTranslationJob = () => {
  const store = useTranslationStore();
  return {
    currentJobId: store.currentJobId,
    jobStatus: store.jobStatus,
    isTranslating: store.isTranslating,
    translationResult: store.translationResult,
    progress: store.jobStatus?.progress || 0,
    startTranslation: store.startTranslation,
    cancelTranslation: store.cancelTranslation,
    fetchJobStatus: store.fetchJobStatus,
    downloadResult: store.downloadResult,
    resetState: store.resetState
  };
};

export const useFileUpload = () => {
  const store = useTranslationStore();
  return {
    uploadedFile: store.uploadedFile,
    uploadedFileName: store.uploadedFileName,
    uploadedContent: store.uploadedContent,
    setUploadedFile: store.setUploadedFile,
    setUploadedContent: store.setUploadedContent,
    clearUpload: store.clearUpload
  };
};

export const useProviderConfig = () => {
  const store = useTranslationStore();
  return {
    availableProviders: store.availableProviders,
    selectedProvider: store.selectedProvider,
    selectedModel: store.selectedModel,
    fetchProviders: store.fetchProviders,
    fetchProviderStatus: store.fetchProviderStatus,
    setSelectedProvider: store.setSelectedProvider
  };
};

export const useSystemStatus = () => {
  const store = useTranslationStore();
  return {
    isConnected: store.isConnected,
    systemHealth: store.systemHealth,
    checkSystemHealth: store.checkSystemHealth
  };
};

export const useNotifications = () => {
  const store = useTranslationStore();
  return {
    errors: store.errors,
    warnings: store.warnings,
    addError: store.addError,
    clearErrors: store.clearErrors,
    addWarning: store.addWarning,
    clearWarnings: store.clearWarnings
  };
};

export const useGlossary = () => {
  const store = useTranslationStore();
  return {
    glossaryFile: store.glossaryFile,
    glossaryData: store.glossaryData,
    glossaryFileName: store.glossaryFileName,
    setGlossaryFile: store.setGlossaryFile,
    setGlossaryData: store.setGlossaryData,
    setGlossaryFileName: store.setGlossaryFileName,
    clearGlossary: store.clearGlossary
  };
};