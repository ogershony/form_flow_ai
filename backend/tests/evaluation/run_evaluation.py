#!/usr/bin/env python3
"""
Evaluation Runner Script

Runs form extraction evaluations against ground truth datasets.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.mcp_service import get_mcp_service
from app.services.document_service import get_document_service
from tests.evaluation.evaluator import FormEvaluator


def generate_form_from_pdf(pdf_path: Path, user_id: str = "eval_user") -> dict:
    """
    Generate a form from a PDF file using the MCP service.

    Args:
        pdf_path: Path to PDF file
        user_id: User ID for form generation

    Returns:
        Generated form schema
    """
    print(f"Generating form from: {pdf_path}")

    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    # Convert to base64
    import base64
    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

    # Process document
    doc_service = get_document_service()
    documents = [{
        "name": pdf_path.name,
        "type": "pdf",
        "content": pdf_base64
    }]

    try:
        document_text = doc_service.process_documents(documents)
        print(f"Extracted {len(document_text)} characters from PDF")

        # Generate form using MCP service
        mcp_service = get_mcp_service()
        context = f"Create a form based on this document:\n\n{document_text}"

        schema = mcp_service.create_form(context, user_id)
        print(f"Generated form with {len(schema.get('components', []))} questions")

        return schema

    except Exception as e:
        print(f"Error generating form: {e}")
        raise


def evaluate_single_pdf(args):
    """Evaluate a single PDF against ground truth."""
    pdf_path = Path(args.pdf)
    gt_path = Path(args.ground_truth)

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    if not gt_path.exists():
        print(f"Error: Ground truth file not found: {gt_path}")
        return 1

    # Load ground truth
    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)

    # Generate form from PDF
    try:
        generated_schema = generate_form_from_pdf(pdf_path)
    except Exception as e:
        print(f"Failed to generate form: {e}")
        return 1

    # Save generated form
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gen_output_path = output_dir / f"{pdf_path.stem}_generated.json"
    with open(gen_output_path, 'w') as f:
        json.dump(generated_schema, f, indent=2)
    print(f"Generated form saved to: {gen_output_path}")

    # Evaluate
    evaluator = FormEvaluator(similarity_threshold=args.threshold)
    result = evaluator.evaluate_form(
        generated_schema=generated_schema,
        ground_truth_schema=ground_truth,
        pdf_name=pdf_path.stem
    )

    # Print report
    evaluator.print_evaluation_report(result)

    # Export results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = results_dir / f"evaluation_{pdf_path.stem}_{timestamp}.json"

    from dataclasses import asdict
    with open(result_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    print(f"\nResults saved to: {result_path}")

    return 0


def evaluate_dataset(args):
    """Evaluate a dataset of PDFs."""
    gt_dir = Path(args.ground_truth_dir)
    gen_dir = Path(args.generated_dir)

    if not gt_dir.exists():
        print(f"Error: Ground truth directory not found: {gt_dir}")
        return 1

    # If generated directory doesn't exist, we need to generate forms
    if not gen_dir.exists():
        print(f"Generated forms directory not found. Will generate forms from PDFs.")
        gen_dir.mkdir(parents=True, exist_ok=True)

        # Find PDFs matching ground truth files
        pdf_dir = Path(args.pdf_dir) if args.pdf_dir else Path(".")
        gt_files = list(gt_dir.glob("*.json"))

        for gt_file in gt_files:
            pdf_name = gt_file.stem
            pdf_path = pdf_dir / f"{pdf_name}.pdf"

            if not pdf_path.exists():
                print(f"Warning: No PDF found for {pdf_name}, skipping")
                continue

            # Generate form
            try:
                schema = generate_form_from_pdf(pdf_path)
                gen_output = gen_dir / f"{pdf_name}.json"
                with open(gen_output, 'w') as f:
                    json.dump(schema, f, indent=2)
                print(f"Generated: {gen_output}")
            except Exception as e:
                print(f"Failed to generate form for {pdf_name}: {e}")

    # Run evaluation
    evaluator = FormEvaluator(similarity_threshold=args.threshold)
    aggregate_result = evaluator.evaluate_dataset(gt_dir, gen_dir)

    # Print reports
    evaluator.print_aggregate_report(aggregate_result)

    # Print individual reports if requested
    if args.verbose:
        for result in aggregate_result.per_pdf_results:
            evaluator.print_evaluation_report(result)

    # Export results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = results_dir / f"evaluation_dataset_{timestamp}.json"
    evaluator.export_results_to_json(aggregate_result, result_path)

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate form extraction accuracy against ground truth"
    )

    parser.add_argument(
        '--dataset',
        action='store_true',
        help='Evaluate entire dataset instead of single PDF'
    )

    parser.add_argument(
        '--pdf',
        type=str,
        default='pdf/test.pdf',
        help='Path to PDF file (for single PDF evaluation)'
    )

    parser.add_argument(
        '--ground-truth',
        type=str,
        default='ground_truth/test.json',
        help='Path to ground truth JSON file (for single PDF evaluation)'
    )

    parser.add_argument(
        '--ground-truth-dir',
        type=str,
        default='ground_truth',
        help='Directory containing ground truth JSON files (default: ground_truth/)'
    )

    parser.add_argument(
        '--generated-dir',
        type=str,
        default='test_forms',
        help='Directory containing generated forms (default: test_forms/)'
    )

    parser.add_argument(
        '--pdf-dir',
        type=str,
        help='Directory containing PDF files (for dataset evaluation)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='test_forms',
        help='Directory to save generated forms (default: test_forms/)'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.8,
        help='Similarity threshold for matching questions (0-1, default: 0.8)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed reports for each PDF'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.dataset:
        return evaluate_dataset(args)
    else:
        if not args.pdf or not args.ground_truth:
            parser.error("--pdf and --ground-truth are required for single PDF evaluation")
        return evaluate_single_pdf(args)


if __name__ == "__main__":
    sys.exit(main())
