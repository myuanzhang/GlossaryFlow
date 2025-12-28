/**
 * ProviderSelector Component
 *
 * Allows users to select LLM provider and model
 */

import React, { useEffect, useState } from 'react';
import { Select, Card, Typography, Space, Tag, Alert } from 'antd';
import {
  RobotOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useProviderConfig, useSystemStatus } from '../../stores/translationStore';
import type { ProviderSelectorProps } from '../../types/ui';

const { Title, Text } = Typography;
const { Option } = Select;

// Provider information
const providerInfo: Record<string, { name: string; description: string; color: string }> = {
  deepseek: {
    name: 'DeepSeek',
    description: 'DeepSeek推理模型，擅长复杂逻辑',
    color: '#4D6BFE'
  },
  openai: {
    name: 'OpenAI兼容',
    description: 'OpenAI的LLM模型',
    color: '#10a37f'
  },
  ollama: {
    name: 'Ollama',
    description: '本地运行的开源模型，保护隐私',
    color: '#ff6b35'
  },
  mimo: {
    name: 'Mimo',
    description: '小米Mimo AI模型',
    color: '#FF6900'
  },
  qwen: {
    name: '通义千问',
    description: '阿里云大语言模型服务',
    color: '#FF6A00'
  }
};

const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  disabled = false
}) => {
  const {
    selectedProvider,
    selectedModel,
    fetchProviders,
    fetchProviderStatus,
    setSelectedProvider
  } = useProviderConfig();

  const { systemHealth, checkSystemHealth } = useSystemStatus();

  const [localModel, setLocalModel] = useState(selectedModel);
  const [providerModels, setProviderModels] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);

  // Fetch providers on component mount
  useEffect(() => {
    const initializeComponent = async () => {
      await fetchProviders();
      await checkSystemHealth();

      // Pre-load first available provider's model info only if not already loaded
      if (!providerModels['openai']) {
        try {
          const status = await fetchProviderStatus('openai');
          if (status.success && status.available && status.models && status.models.length > 0) {
            setProviderModels(prev => ({
              ...prev,
              'openai': status.models
            }));
            // Select first model by default
            setSelectedProvider('openai', status.models[0]);
          }
        } catch (error) {
          console.error('Failed to initialize OpenAI provider:', error);
        }
      }
    };

    initializeComponent();
  }, [fetchProviders, checkSystemHealth, fetchProviderStatus, providerModels]); // Add proper dependencies

  // Sync local state with store
  useEffect(() => {
    setLocalModel(selectedModel);
  }, [selectedModel]);

  // Fetch provider models when provider changes
  const fetchProviderModel = async (provider: string) => {
    setLoading(true);
    try {
      const status = await fetchProviderStatus(provider);
      if (status.success && status.available && status.models && status.models.length > 0) {
        setProviderModels(prev => ({
          ...prev,
          [provider]: status.models
        }));
        // Select first model by default, update if provider changed
        const firstModel = status.models[0];
        if (provider !== selectedProvider) {
          setSelectedProvider(provider, firstModel);
        } else {
          // Update local model if current model not in list
          if (!status.models.includes(localModel)) {
            setLocalModel(firstModel);
            setSelectedProvider(provider, firstModel);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch provider models:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (provider: string) => {
    fetchProviderModel(provider);
  };

  const handleModelChange = (model: string) => {
    setLocalModel(model);
    setSelectedProvider(selectedProvider, model);
  };

  const isProviderAvailable = (provider: string) => {
    if (!systemHealth?.provider_status) return false;
    return systemHealth.provider_status[provider] === true;
  };

  const getProviderStatus = (provider: string) => {
    if (!systemHealth?.provider_status) return 'unknown';

    const isAvailable = isProviderAvailable(provider);
    if (isAvailable) return 'available';

    return 'unavailable';
  };

  const getProviderStatusIcon = (provider: string) => {
    const status = getProviderStatus(provider);
    switch (status) {
      case 'available':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'unavailable':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const getProviderStatusText = (provider: string) => {
    const status = getProviderStatus(provider);
    switch (status) {
      case 'available':
        return '可用';
      case 'unavailable':
        return '不可用';
      default:
        return '检查中...';
    }
  };

  return (
    <div className="provider-selector">
      <Card
        title={
          <Space>
            <RobotOutlined />
            <span>翻译服务商配置</span>
          </Space>
        }
        className="provider-card"
      >
        <div className="provider-content">
          {/* Provider Selection */}
          <div className="provider-section">
            <div className="section-label">
              <Title level={5}>选择服务商</Title>
            </div>
            <Select
              value={selectedProvider}
              onChange={handleProviderChange}
              disabled={disabled}
              className="provider-select"
              placeholder="请选择翻译服务商"
              size="large"
              popupMatchSelectWidth={false}
              style={{ minWidth: 450 }}
            >
              {Object.entries(providerInfo).map(([key, info]) => (
                <Option key={key} value={key} disabled={!isProviderAvailable(key)}>
                  <div className="provider-option">
                    <Space>
                      <span className="provider-name">{info.name}</span>
                      <Tag color={info.color}>{key}</Tag>
                      {getProviderStatusIcon(key)}
                    </Space>
                    <div className="provider-description">
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {info.description}
                      </Text>
                    </div>
                    <div className="provider-status">
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        状态：{getProviderStatusText(key)}
                      </Text>
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </div>

          {/* Model Selection */}
          <div className="provider-section">
            <div className="section-label">
              <Title level={5}>选择模型</Title>
            </div>
            <Select
              value={localModel}
              onChange={handleModelChange}
              disabled={disabled || !selectedProvider || loading}
              loading={loading}
              className="model-select"
              placeholder={loading ? "获取模型中..." : "请选择翻译模型"}
              size="large"
              popupMatchSelectWidth={false}
              style={{ minWidth: 450 }}
            >
              {selectedProvider && providerModels[selectedProvider]?.map(model => (
                <Option key={model} value={model}>
                  {model}
                </Option>
              ))}
            </Select>
          </div>

          {/* Provider Status Info */}
          <div className="provider-status-info">
            {selectedProvider && (
              <Alert
                message={
                  <Space>
                    {getProviderStatusIcon(selectedProvider)}
                    <span>
                      {providerInfo[selectedProvider]?.name} - {getProviderStatusText(selectedProvider)}
                    </span>
                  </Space>
                }
                description={
                  getProviderStatus(selectedProvider) === 'unavailable'
                    ? '该服务商当前不可用，请检查配置或选择其他服务商'
                    : providerInfo[selectedProvider]?.description
                }
                type={
                  getProviderStatus(selectedProvider) === 'available' ? 'success' : 'warning'
                }
                showIcon={false}
              />
            )}
          </div>

          {/* System Health Status */}
          {systemHealth && (
            <div className="system-health">
              <Text type="secondary" style={{ fontSize: 12 }}>
                系统状态：{systemHealth.status === 'healthy' ? '正常' : systemHealth.status === 'degraded' ? '降级' : '异常'} |
                可用服务商：{systemHealth.available_providers.length} 个
                {systemHealth.provider_status && (
                  <>
                    {' '}| 总注册：{Object.keys(systemHealth.provider_status).filter(k => k !== 'mock').length} 个
                  </>
                )}
              </Text>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default ProviderSelector;