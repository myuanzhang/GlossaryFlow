"""Glossary Loading and Management"""

import os
from typing import Optional, Union
from pathlib import Path
from .glossary import Glossary
from ..config import config

class GlossaryLoader:
    """
    Handles loading and management of glossary files with fallback support
    """

    def __init__(self):
        self._default_glossary = None

    def load_glossary(self, glossary_path: Optional[Union[str, Path]] = None) -> Glossary:
        """
        Load glossary from file with graceful fallback

        Args:
            glossary_path: Path to glossary file. If None, uses config default.

        Returns:
            Glossary instance (empty if loading fails)
        """
        # Determine which path to use
        target_path = None
        if glossary_path:
            target_path = Path(glossary_path)
        elif config.default_glossary_path:
            target_path = Path(config.default_glossary_path)

        # If no path specified, return empty glossary
        if not target_path:
            return Glossary()

        # Try to load the glossary file
        try:
            return Glossary.from_file(target_path)
        except FileNotFoundError:
            print(f"Warning: Glossary file not found: {target_path}", file=os.sys.stderr)
            print("Proceeding without glossary.", file=os.sys.stderr)
            return Glossary()
        except ValueError as e:
            print(f"Warning: Invalid glossary file {target_path}: {str(e)}", file=os.sys.stderr)
            print("Proceeding without glossary.", file=os.sys.stderr)
            return Glossary()
        except Exception as e:
            print(f"Warning: Failed to load glossary {target_path}: {str(e)}", file=os.sys.stderr)
            print("Proceeding without glossary.", file=os.sys.stderr)
            return Glossary()

    def load_default_glossary(self) -> Glossary:
        """
        Load default glossary from environment configuration

        Returns:
            Glossary instance (cached, empty if not configured)
        """
        if self._default_glossary is None:
            self._default_glossary = self.load_glossary(config.default_glossary_path)
        return self._default_glossary

    def create_sample_glossary(self, file_path: Union[str, Path], format_type: str = "json") -> None:
        """
        Create a sample glossary file for demonstration

        Args:
            file_path: Path where to create the sample file
            format_type: "json" or "yaml"
        """
        file_path = Path(file_path)

        sample_terms = {
            "虚拟私有云": "Virtual Private Cloud",
            "可用区": "Availability Zone",
            "实例": "Instance",
            "负载均衡器": "Load Balancer",
            "子网": "Subnet",
            "路由表": "Route Table",
            "安全组": "Security Group",
            "弹性IP": "Elastic IP",
            "对象存储": "Object Storage",
            "内容分发网络": "Content Delivery Network"
        }

        try:
            if format_type.lower() == "yaml":
                import yaml
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(sample_terms, f, default_flow_style=False, allow_unicode=True)
            else:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(sample_terms, f, ensure_ascii=False, indent=2)

            print(f"Sample glossary created: {file_path}")

        except ImportError:
            if format_type.lower() == "yaml":
                raise ValueError("PyYAML is required for YAML format. Install with: pip install PyYAML")
            else:
                raise
        except Exception as e:
            raise ValueError(f"Failed to create sample glossary: {str(e)}")

# Global glossary loader instance
glossary_loader = GlossaryLoader()