#!/usr/bin/env python3
"""
Document Translation CLI Tool

Usage:
    python translate.py input.md output.md
    python translate.py input.md output.md --provider openai
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.translator.markdown_translator import MarkdownTranslator
from src.translator.glossary import Glossary
import argparse
import sys

def main():
    """Main translation function"""
    parser = argparse.ArgumentParser(
        description="Translate Markdown documents using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.md output.md
  %(prog)s input.md output.md --provider openai
  %(prog)s input.md output.md --provider ollama
  %(prog)s input.md output.md --glossary terms.json
        """
    )

    parser.add_argument('input_file', help='Input markdown file path')
    parser.add_argument('output_file', help='Output markdown file path')
    parser.add_argument('--provider', help='LLM provider (openai, ollama)')
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--glossary', help='Glossary file path (JSON or YAML)')

    args = parser.parse_args()

    try:
        # Load glossary if provided
        glossary = None
        if args.glossary:
            glossary = Glossary.from_file(args.glossary)

        # Create translator
        translator = MarkdownTranslator(
            provider_name=args.provider,
            model_name=args.model,
            glossary=glossary
        )

        # Read input file
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"📖 Reading from: {args.input_file}")
        print(f"📄 File size: {len(content)} characters")
        print(f"🤖 Using AI provider: {translator.provider.get_name()}")
        print("✨ Starting translation...")

        # Translate
        translated_content = translator.translate(content)

        # Write output file
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        print(f"💾 Writing to: {args.output_file}")
        print("✅ Translation completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()