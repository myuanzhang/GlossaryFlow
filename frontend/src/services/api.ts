/**
 * API Service Layer
 *
 * Handles all communication with the backend API
 * Follows the contract defined in docs/rest-api-specification.md
 */

import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import type {
  TranslationRequest,
  TranslationOutput,
  JobStatus,
  TranslationStartResponse,
  ErrorResponse,
  ProviderInfo,
  ProvidersResponse,
  HealthResponse
} from '../types/api';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 120 seconds timeout (increased to handle slower providers)
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor for logging
  client.interceptors.request.use(
    (config) => {
      console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('❌ API Request Error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
      return response;
    },
    (error) => {
      console.error('❌ API Response Error:', error);

      // Handle different types of errors
      if (error.response) {
        // Server responded with error status
        const { status, data } = error.response;
        console.error(`API Error ${status}:`, data);
      } else if (error.request) {
        // Request was made but no response received
        console.error('Network Error: No response received');
      } else {
        // Something else happened
        console.error('Unexpected Error:', error.message);
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Create API client instance
const apiClient = createApiClient();

/**
 * Translation API Service
 *
 * Provides methods for all translation-related API calls
 */
export class TranslationAPIService {
  /**
   * Start a new translation job
   */
  async startTranslation(request: TranslationRequest): Promise<TranslationStartResponse> {
    try {
      const response: AxiosResponse<TranslationStartResponse> = await apiClient.post('/translate', request);
      return response.data;
    } catch (error) {
      console.error('Failed to start translation:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Get translation job status
   */
  async getTranslationStatus(jobId: string): Promise<JobStatus> {
    try {
      const response: AxiosResponse<JobStatus> = await apiClient.get(`/translate/${jobId}/status`);
      return response.data;
    } catch (error) {
      console.error('Failed to get job status:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Download translation result as markdown text
   */
  async getTranslationResult(jobId: string): Promise<string> {
    try {
      const response: AxiosResponse<string> = await apiClient.get(`/translate/${jobId}/result`, {
        responseType: 'text',
      });
      return response.data;
    } catch (error) {
      console.error('Failed to download result:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Cancel translation job
   */
  async cancelTranslation(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response: AxiosResponse<{ success: boolean; message: string }> = await apiClient.delete(`/translate/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to cancel translation:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Get available LLM providers
   */
  async getProviders(): Promise<ProvidersResponse> {
    try {
      const response: AxiosResponse<ProvidersResponse> = await apiClient.get('/providers');
      return response.data;
    } catch (error) {
      console.error('Failed to get providers:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Get provider availability status
   */
  async getProviderStatus(providerName: string): Promise<ProviderInfo> {
    try {
      const response: AxiosResponse<ProviderInfo> = await apiClient.get(`/providers/${providerName}/status`);
      return response.data;
    } catch (error) {
      console.error('Failed to get provider status:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Get system health check
   */
  async getSystemHealth(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Failed to get system health:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Handle API errors and convert them to standard format
   *
   * ⚠️ CRITICAL: 处理后端直接返回的错误格式
   * 后端返回: {success: false, error: {code, message, details}}
   */
  private handleApiError(error: any): Error {
    // If it's an Axios error with response data
    if (error.response && error.response.data) {
      const data = error.response.data;

      // 处理我们的标准错误格式
      if (data.success === false && data.error) {
        const errorMessage = data.error.message || 'Unknown API error';
        const errorCode = data.error.code;

        // 构造详细的错误消息
        let fullMessage = errorMessage;
        if (data.error.details && data.error.details.validation_error) {
          fullMessage += ` (${data.error.details.validation_error})`;
        }

        console.error(`API Error [${errorCode}]:`, fullMessage);
        return new Error(fullMessage);
      }

      // 处理其他格式的错误（向后兼容）
      if (data.error && typeof data.error === 'string') {
        return new Error(data.error);
      }

      if (data.message) {
        return new Error(data.message);
      }

      if (data.detail) {
        return new Error(data.detail);
      }

      return new Error('Unknown API error');
    }

    // Network error
    if (error.request) {
      return new Error('Network error: Unable to connect to the API server. Please check your connection.');
    }

    // Other error
    return new Error(error.message || 'Unknown error occurred');
  }

  /**
   * Check if API server is reachable
   */
  async checkConnection(): Promise<boolean> {
    try {
      await this.getSystemHealth();
      return true;
    } catch (error) {
      console.error('API connection check failed:', error.message);
      return false;
    }
  }
}

// Create singleton instance
export const translationAPI = new TranslationAPIService();

// Export singleton as default
export default translationAPI;