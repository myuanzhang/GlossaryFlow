#!/usr/bin/env python3
"""
GlossaryFlow CLI Entry Point

This is the main CLI interface for GlossaryFlow.
For web service, use: python run_web.py
For translation CLI, use: python translate.py
"""

import argparse
import sys


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GlossaryFlow - 智能术语表驱动的可控翻译流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动 Web 服务
  %(prog)s web

  # 翻译文档（推荐使用 translate.py）
  python translate.py input.md output.md --provider openai

  # 获取帮助
  %(prog)s --help

更多信息请参考项目文档。
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='GlossaryFlow v1.0.0'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        metavar='COMMAND'
    )

    # Web 服务命令
    web_parser = subparsers.add_parser(
        'web',
        help='启动 Web 服务 (推荐使用 run_web.py)'
    )
    web_parser.description = "启动 FastAPI Web 服务"

    # Translate 命令（委托给 translate.py）
    translate_parser = subparsers.add_parser(
        'translate',
        help='翻译文档 (推荐使用 translate.py)'
    )
    translate_parser.description = "翻译 Markdown 文档"
    translate_parser.add_argument('input_file', help='输入文件')
    translate_parser.add_argument('output_file', help='输出文件')
    translate_parser.add_argument('--provider', help='LLM provider')
    translate_parser.add_argument('--model', help='模型名称')
    translate_parser.add_argument('--glossary', help='术语表文件')

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'web':
        print("🌐 启动 Web 服务...")
        print("💡 建议: 使用 'python run_web.py' 直接启动")
        import uvicorn
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
        return 0

    elif args.command == 'translate':
        # 导入并执行翻译逻辑
        from src.translator.markdown_translator import MarkdownTranslator
        from src.translator.glossary import Glossary

        try:
            glossary = None
            if args.glossary:
                glossary = Glossary.from_file(args.glossary)

            translator = MarkdownTranslator(
                provider_name=args.provider,
                model_name=args.model,
                glossary=glossary
            )

            with open(args.input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"📖 翻译中: {args.input_file}")
            translated = translator.translate(content)

            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(translated)

            print(f"💾 已保存: {args.output_file}")
            return 0

        except Exception as e:
            print(f"❌ 翻译失败: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())