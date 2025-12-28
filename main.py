#!/usr/bin/env python3
"""
Main CLI Entry Point

统一的 CLI 入口点，支持所有 Agent 功能。
"""

import argparse
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.commands.rewrite import RewriteCommand


def create_main_parser():
    """创建主 CLI 解析器"""
    parser = argparse.ArgumentParser(
        description="Document Translation and Rewrite Toolkit - Multi-Agent 架构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 改写文档
  %(prog)s rewrite input.md output.md --strategy translation_oriented

  # 列出可用策略
  %(prog)s rewrite --list-strategies

  # 获取帮助
  %(prog)s rewrite --help
  %(prog)s <command> --help

更多信息请参考项目文档。
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Document Translation Toolkit v2.0.0 (Multi-Agent)'
    )

    # 子命令
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        metavar='COMMAND'
    )

    # Rewrite 命令
    rewrite_command = RewriteCommand()
    rewrite_parser = subparsers.add_parser(
        'rewrite',
        help='文档改写功能',
        description=rewrite_command.description
    )
    # 这里可以添加 rewrite 特定的参数，但为了简化，我们让 RewriteCommand 自己处理

    return parser, subparsers


def main():
    """主函数"""
    try:
        # 简单的命令检查
        if len(sys.argv) < 2:
            parser, _ = create_main_parser()
            parser.print_help()
            return 1

        command = sys.argv[1]

        if command == 'rewrite':
            # 直接委托给 RewriteCommand 处理
            rewrite_command = RewriteCommand()
            rewrite_args = sys.argv[2:]  # 跳过 'main.py' 和 'rewrite'
            exit_code = rewrite_command.execute(rewrite_args)
            return exit_code
        elif command == '--help' or command == '-h':
            parser, _ = create_main_parser()
            parser.print_help()
            return 0
        elif command == '--version':
            print("Document Translation Toolkit v2.0.0 (Multi-Agent)")
            return 0
        else:
            print(f"未知命令: {command}", file=sys.stderr)
            parser, _ = create_main_parser()
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n用户中断操作", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())