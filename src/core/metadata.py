"""
Metadata Management

处理作业和处理的元数据信息。
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProcessingMetadata:
    """处理元数据"""
    agent_id: str
    agent_type: str
    provider_name: str
    model_name: str
    strategy_name: Optional[str] = None
    processing_start: datetime = field(default_factory=datetime.now)
    processing_end: Optional[datetime] = None
    processing_time_ms: float = 0.0
    units_processed: int = 0
    units_rewritten: int = 0
    rewrite_rate: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    token_usage: Optional[Dict[str, int]] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def finish_processing(self) -> None:
        """标记处理完成"""
        self.processing_end = datetime.now()
        if self.processing_start:
            delta = self.processing_end - self.processing_start
            self.processing_time_ms = delta.total_seconds() * 1000

    def calculate_rewrite_rate(self) -> None:
        """计算改写率"""
        if self.units_processed > 0:
            self.rewrite_rate = self.units_rewritten / self.units_processed

    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)

    def add_data(self, key: str, value: Any) -> None:
        """添加额外数据"""
        self.additional_data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "strategy_name": self.strategy_name,
            "processing_start": self.processing_start.isoformat(),
            "processing_end": self.processing_end.isoformat() if self.processing_end else None,
            "processing_time_ms": self.processing_time_ms,
            "units_processed": self.units_processed,
            "units_rewritten": self.units_rewritten,
            "rewrite_rate": self.rewrite_rate,
            "warnings": self.warnings,
            "errors": self.errors,
            "token_usage": self.token_usage,
            "additional_data": self.additional_data
        }


class Metadata:
    """元数据管理器"""

    def __init__(self):
        self.processing_history: List[ProcessingMetadata] = []
        self.global_data: Dict[str, Any] = {}

    def start_processing(
        self,
        agent_id: str,
        agent_type: str,
        provider_name: str,
        model_name: str,
        strategy_name: Optional[str] = None
    ) -> ProcessingMetadata:
        """
        开始新的处理会话

        Args:
            agent_id: Agent ID
            agent_type: Agent 类型
            provider_name: Provider 名称
            model_name: 模型名称
            strategy_name: 策略名称

        Returns:
            处理元数据对象
        """
        metadata = ProcessingMetadata(
            agent_id=agent_id,
            agent_type=agent_type,
            provider_name=provider_name,
            model_name=model_name,
            strategy_name=strategy_name
        )

        self.processing_history.append(metadata)
        return metadata

    def finish_current_processing(self) -> None:
        """完成当前处理"""
        if self.processing_history:
            current = self.processing_history[-1]
            current.finish_processing()
            current.calculate_rewrite_rate()

    def get_current_metadata(self) -> Optional[ProcessingMetadata]:
        """获取当前处理的元数据"""
        if self.processing_history:
            return self.processing_history[-1]
        return None

    def get_processing_history(self, limit: Optional[int] = None) -> List[ProcessingMetadata]:
        """
        获取处理历史

        Args:
            limit: 限制返回数量

        Returns:
            处理历史列表
        """
        if limit:
            return self.processing_history[-limit:]
        return self.processing_history

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        if not self.processing_history:
            return {}

        total_sessions = len(self.processing_history)
        total_units = sum(m.units_processed for m in self.processing_history)
        total_rewrites = sum(m.units_rewritten for m in self.processing_history)
        total_time = sum(m.processing_time_ms for m in self.processing_history)

        successful_sessions = len([m for m in self.processing_history if not m.errors])
        avg_rewrite_rate = sum(m.rewrite_rate for m in self.processing_history) / total_sessions

        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": successful_sessions / total_sessions,
            "total_units_processed": total_units,
            "total_units_rewritten": total_rewrites,
            "overall_rewrite_rate": total_rewrites / total_units if total_units > 0 else 0,
            "average_rewrite_rate": avg_rewrite_rate,
            "total_processing_time_ms": total_time,
            "average_processing_time_ms": total_time / total_sessions
        }

    def set_global_data(self, key: str, value: Any) -> None:
        """设置全局数据"""
        self.global_data[key] = value

    def get_global_data(self, key: str, default: Any = None) -> Any:
        """获取全局数据"""
        return self.global_data.get(key, default)

    def save_to_file(self, file_path: str) -> None:
        """
        保存元数据到文件

        Args:
            file_path: 文件路径
        """
        data = {
            "processing_history": [m.to_dict() for m in self.processing_history],
            "global_data": self.global_data,
            "statistics": self.get_statistics()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, file_path: str) -> None:
        """
        从文件加载元数据

        Args:
            file_path: 文件路径
        """
        if not Path(file_path).exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.global_data = data.get("global_data", {})

        # 重建处理历史
        self.processing_history = []
        for item in data.get("processing_history", []):
            metadata = ProcessingMetadata(
                agent_id=item["agent_id"],
                agent_type=item["agent_type"],
                provider_name=item["provider_name"],
                model_name=item["model_name"],
                strategy_name=item.get("strategy_name")
            )

            # 恢复时间戳
            if item.get("processing_start"):
                metadata.processing_start = datetime.fromisoformat(item["processing_start"])

            if item.get("processing_end"):
                metadata.processing_end = datetime.fromisoformat(item["processing_end"])

            # 恢复其他字段
            metadata.processing_time_ms = item.get("processing_time_ms", 0.0)
            metadata.units_processed = item.get("units_processed", 0)
            metadata.units_rewritten = item.get("units_rewritten", 0)
            metadata.rewrite_rate = item.get("rewrite_rate", 0.0)
            metadata.warnings = item.get("warnings", [])
            metadata.errors = item.get("errors", [])
            metadata.token_usage = item.get("token_usage")
            metadata.additional_data = item.get("additional_data", {})

            self.processing_history.append(metadata)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "processing_history": [m.to_dict() for m in self.processing_history],
            "global_data": self.global_data,
            "statistics": self.get_statistics()
        }