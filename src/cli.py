"""Command Line Interface for Document Translation"""

import argparse
import sys
import os
from pathlib import Path
from .agents import TranslationAgent, TranslationInput, LLMConfig, DocumentOrchestrator, OrchestratorConfig, DocumentContext
from .translator.glossary_loader import glossary_loader
from .config import config

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Translate Markdown documents from Chinese to English"
    )

    parser.add_argument(
        "input_file",
        help="Input markdown file path"
    )

    parser.add_argument(
        "output_file",
        help="Output markdown file path"
    )

    parser.add_argument(
        "--provider",
        choices=["openai", "ollama"],
        help=f"LLM provider to use (default: {config.provider})"
    )

    parser.add_argument(
        "--glossary",
        help="Path to glossary file (JSON or YAML) for terminology control"
    )

    parser.add_argument(
        "--enable-rewrite",
        action="store_true",
        help="Enable pre-translation rewriting to improve clarity and translation quality"
    )

    parser.add_argument(
        "--rewrite-output-dir",
        default="rewritten_docs",
        help="Output directory for rewritten documents (default: rewritten_docs)"
    )

    args = parser.parse_args()

    try:
        # Validate input file exists
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
            sys.exit(1)

        # Read input file
        print(f"Reading from: {args.input_file}")
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()

        if not input_content.strip():
            print("Warning: Input file is empty.", file=sys.stderr)
            # Still create empty output file

        # Load glossary if specified
        glossary_dict = None
        if args.glossary:
            print(f"Loading glossary from: {args.glossary}")
            glossary = glossary_loader.load_glossary(args.glossary)
            if glossary and not glossary.is_empty():
                glossary_dict = glossary.get_terms()
                print(f"Loaded {glossary.get_term_count()} terminology terms")
            else:
                print("Warning: Glossary is empty or failed to load", file=sys.stderr)

        # Build LLM configuration
        llm_config = None
        if args.provider:
            # Use specified provider with default model from config
            if args.provider == "openai":
                model = config.openai_model
            else:  # ollama
                model = config.ollama_model
            llm_config = LLMConfig(provider=args.provider, model=model)

        # Create document context for better rewriting
        print("DEBUG: Creating document context...")
        document_context = DocumentContext(
            intent="技术文档",
            target_audience="技术用户",
            tone="professional",
            domain="根据内容推断"
        )
        print("DEBUG: Document context created successfully")

        # Process document with or without rewrite
        if args.enable_rewrite:
            # Use DocumentOrchestrator for rewrite + translation
            print("Using DocumentOrchestrator with rewrite enabled...")
            print("DEBUG: Creating orchestrator config...")

            print("DEBUG: Creating OrchestratorConfig instance...")
            orchestrator_config = OrchestratorConfig(
                enable_rewrite=True,
                enable_rewrite_persistence=True,  # Enable persistence for CLI
                rewrite_output_dir=args.rewrite_output_dir,
                rewrite_fallback_to_original=True,
                rewrite_llm_config=llm_config,
                translation_llm_config=llm_config
            )
            print("DEBUG: OrchestratorConfig created successfully")

            print("DEBUG: Creating DocumentOrchestrator...")
            orchestrator = DocumentOrchestrator(orchestrator_config)
            print("DEBUG: DocumentOrchestrator created successfully")

            # Process document
            provider_name = args.provider or config.provider
            glossary_info = f" with {len(glossary_dict) if glossary_dict else 0} terms" if glossary_dict else ""
            print(f"Processing document using {provider_name} provider{glossary_info}...")
            print("DEBUG: Starting orchestrator.process_document...")

            result = orchestrator.process_document(
                source_markdown=input_content,
                glossary=glossary_dict,
                document_context=document_context
            )
            print("DEBUG: orchestrator.process_document completed")

            translated_content = result.translated_markdown

            # Display metadata
            metadata = result.metadata
            print(f"Provider used: {metadata.provider_used} ({metadata.model_used})")
            if metadata.glossary_applied:
                print("Glossary applied: Yes")
            if metadata.rewrite_applied:
                print("Rewrite applied: Yes")
                if metadata.rewrite_metadata:
                    rewrite_meta = metadata.rewrite_metadata
                    print(f"Rewrite stats: {rewrite_meta.get('sentences_rewritten', 0)}/{rewrite_meta.get('sentences_processed', 0)} sentences rewritten")
            else:
                print("Rewrite applied: No")

            # Show persistence info
            if args.enable_rewrite:
                print(f"Rewrite documents saved to: {args.rewrite_output_dir}/")

        else:
            # Use original TranslationAgent for translation only
            print("Using TranslationAgent (rewrite disabled)...")

            agent = TranslationAgent()

            # Build translation input
            translation_input = TranslationInput(
                source_markdown=input_content,
                glossary=glossary_dict,
                llm_config=llm_config
            )

            # Translate content
            provider_name = args.provider or config.provider
            glossary_info = f" with {len(glossary_dict) if glossary_dict else 0} terms" if glossary_dict else ""
            print(f"Translating using {provider_name} provider{glossary_info}...")

            result = agent.translate(translation_input)
            translated_content = result.translated_markdown

            # Display metadata
            metadata = result.metadata
            print(f"Provider used: {metadata.provider_used} ({metadata.model_used})")
            if metadata.glossary_applied:
                print("Glossary applied: Yes")

        if metadata.warnings:
            for warning in metadata.warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        # Create output directory if needed
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        print(f"Writing to: {args.output_file}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        print("Translation completed successfully!")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()