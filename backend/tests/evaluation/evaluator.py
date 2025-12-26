"""
Form Extraction Evaluation Framework

Tests the system's ability to accurately extract form questions from PDFs
by comparing generated forms against ground truth annotations.
"""
import json
import os
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import difflib


@dataclass
class QuestionMatch:
    """Represents a match between generated and ground truth question."""
    ground_truth_question: str
    generated_question: str
    similarity_score: float
    is_match: bool
    question_type_correct: bool
    options_match: bool  # For multiple choice
    required_match: bool


@dataclass
class EvaluationResult:
    """Results from evaluating a single PDF."""
    pdf_name: str
    total_ground_truth_questions: int
    total_generated_questions: int
    correctly_identified: int
    missing_questions: int
    extra_questions: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    matches: List[QuestionMatch]
    missing_question_texts: List[str]
    extra_question_texts: List[str]


@dataclass
class AggregateEvaluationResult:
    """Aggregate results across multiple PDFs."""
    total_pdfs: int
    avg_accuracy: float
    avg_precision: float
    avg_recall: float
    avg_f1_score: float
    total_questions: int
    total_correct: int
    total_missing: int
    total_extra: int
    per_pdf_results: List[EvaluationResult]


class FormEvaluator:
    """Evaluates form extraction accuracy against ground truth."""

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize evaluator.

        Args:
            similarity_threshold: Minimum similarity to consider questions matching (0-1)
        """
        self.similarity_threshold = similarity_threshold

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using sequence matcher.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def compare_options(self, ground_truth_options: List[str], generated_options: List[str]) -> bool:
        """
        Compare multiple choice options.

        Args:
            ground_truth_options: Expected options
            generated_options: Generated options

        Returns:
            True if options match (order-independent)
        """
        if not ground_truth_options or not generated_options:
            return False

        # Sort both lists and compare
        gt_sorted = sorted([opt.strip().lower() for opt in ground_truth_options])
        gen_sorted = sorted([opt.strip().lower() for opt in generated_options])

        # Allow for minor differences in option count
        if abs(len(gt_sorted) - len(gen_sorted)) > 1:
            return False

        # Check if most options match
        matches = sum(1 for gt in gt_sorted if any(
            self.calculate_similarity(gt, gen) > 0.9 for gen in gen_sorted
        ))

        return matches >= min(len(gt_sorted), len(gen_sorted)) - 1

    def find_best_match(
        self,
        generated_component: Dict[str, Any],
        ground_truth_components: List[Dict[str, Any]],
        used_indices: set
    ) -> Tuple[int, float]:
        """
        Find the best matching ground truth component for a generated component.

        Args:
            generated_component: Generated component to match
            ground_truth_components: List of ground truth components
            used_indices: Indices already matched

        Returns:
            Tuple of (best_match_index, similarity_score)
        """
        best_match_idx = -1
        best_score = 0.0

        gen_question = generated_component.get("data", {}).get("question", "")

        for idx, gt_component in enumerate(ground_truth_components):
            if idx in used_indices:
                continue

            gt_question = gt_component.get("data", {}).get("question", "")
            score = self.calculate_similarity(gen_question, gt_question)

            if score > best_score:
                best_score = score
                best_match_idx = idx

        return best_match_idx, best_score

    def evaluate_form(
        self,
        generated_schema: Dict[str, Any],
        ground_truth_schema: Dict[str, Any],
        pdf_name: str
    ) -> EvaluationResult:
        """
        Evaluate a generated form against ground truth.

        Args:
            generated_schema: Generated form schema
            ground_truth_schema: Ground truth schema
            pdf_name: Name of the PDF being evaluated

        Returns:
            EvaluationResult with detailed metrics
        """
        gt_components = ground_truth_schema.get("components", [])
        gen_components = generated_schema.get("components", [])

        matches = []
        used_gt_indices = set()

        # For each generated component, find best match in ground truth
        for gen_comp in gen_components:
            best_idx, similarity = self.find_best_match(
                gen_comp, gt_components, used_gt_indices
            )

            if best_idx >= 0 and similarity >= self.similarity_threshold:
                gt_comp = gt_components[best_idx]
                used_gt_indices.add(best_idx)

                # Check if types match
                type_match = gen_comp.get("type") == gt_comp.get("type")

                # Check if options match (for multiple choice)
                options_match = True
                if gt_comp.get("type") == "multiple-choice":
                    gt_options = gt_comp.get("data", {}).get("options", [])
                    gen_options = gen_comp.get("data", {}).get("options", [])
                    options_match = self.compare_options(gt_options, gen_options)

                # Check if required status matches
                gt_required = gt_comp.get("data", {}).get("required", False)
                gen_required = gen_comp.get("data", {}).get("required", False)
                required_match = gt_required == gen_required

                match = QuestionMatch(
                    ground_truth_question=gt_comp.get("data", {}).get("question", ""),
                    generated_question=gen_comp.get("data", {}).get("question", ""),
                    similarity_score=similarity,
                    is_match=True,
                    question_type_correct=type_match,
                    options_match=options_match if gt_comp.get("type") == "multiple-choice" else True,
                    required_match=required_match
                )
                matches.append(match)

        # Identify missing questions (in ground truth but not generated)
        missing_questions = []
        for idx, gt_comp in enumerate(gt_components):
            if idx not in used_gt_indices:
                missing_questions.append(gt_comp.get("data", {}).get("question", ""))

        # Identify extra questions (generated but not in ground truth)
        extra_questions = []
        matched_gen_questions = {m.generated_question for m in matches}
        for gen_comp in gen_components:
            gen_q = gen_comp.get("data", {}).get("question", "")
            if gen_q not in matched_gen_questions:
                extra_questions.append(gen_q)

        # Calculate metrics
        total_gt = len(gt_components)
        total_gen = len(gen_components)
        correct = len(matches)
        missing = len(missing_questions)
        extra = len(extra_questions)

        # Accuracy = correct / total ground truth
        accuracy = (correct / total_gt * 100) if total_gt > 0 else 0

        # Precision = correct / total generated
        precision = (correct / total_gen * 100) if total_gen > 0 else 0

        # Recall = correct / total ground truth
        recall = (correct / total_gt * 100) if total_gt > 0 else 0

        # F1 score
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        return EvaluationResult(
            pdf_name=pdf_name,
            total_ground_truth_questions=total_gt,
            total_generated_questions=total_gen,
            correctly_identified=correct,
            missing_questions=missing,
            extra_questions=extra,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            matches=matches,
            missing_question_texts=missing_questions,
            extra_question_texts=extra_questions
        )

    def evaluate_dataset(
        self,
        ground_truth_dir: Path,
        generated_forms_dir: Path
    ) -> AggregateEvaluationResult:
        """
        Evaluate all forms in a dataset.

        Args:
            ground_truth_dir: Directory containing ground truth JSON files
            generated_forms_dir: Directory containing generated form JSON files

        Returns:
            AggregateEvaluationResult with overall metrics
        """
        results = []

        # Find all ground truth files
        gt_files = list(Path(ground_truth_dir).glob("*.json"))

        for gt_file in gt_files:
            pdf_name = gt_file.stem

            # Load ground truth
            with open(gt_file, 'r') as f:
                ground_truth = json.load(f)

            # Load generated form
            gen_file = Path(generated_forms_dir) / f"{pdf_name}.json"
            if not gen_file.exists():
                print(f"Warning: No generated form found for {pdf_name}")
                continue

            with open(gen_file, 'r') as f:
                generated = json.load(f)

            # Evaluate
            result = self.evaluate_form(generated, ground_truth, pdf_name)
            results.append(result)

        # Calculate aggregate metrics
        if not results:
            return AggregateEvaluationResult(
                total_pdfs=0,
                avg_accuracy=0.0,
                avg_precision=0.0,
                avg_recall=0.0,
                avg_f1_score=0.0,
                total_questions=0,
                total_correct=0,
                total_missing=0,
                total_extra=0,
                per_pdf_results=[]
            )

        total_pdfs = len(results)
        avg_accuracy = sum(r.accuracy for r in results) / total_pdfs
        avg_precision = sum(r.precision for r in results) / total_pdfs
        avg_recall = sum(r.recall for r in results) / total_pdfs
        avg_f1 = sum(r.f1_score for r in results) / total_pdfs
        total_questions = sum(r.total_ground_truth_questions for r in results)
        total_correct = sum(r.correctly_identified for r in results)
        total_missing = sum(r.missing_questions for r in results)
        total_extra = sum(r.extra_questions for r in results)

        return AggregateEvaluationResult(
            total_pdfs=total_pdfs,
            avg_accuracy=avg_accuracy,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_f1_score=avg_f1,
            total_questions=total_questions,
            total_correct=total_correct,
            total_missing=total_missing,
            total_extra=total_extra,
            per_pdf_results=results
        )

    def print_evaluation_report(self, result: EvaluationResult):
        """Print detailed evaluation report for a single PDF."""
        print(f"\n{'='*70}")
        print(f"Evaluation Report: {result.pdf_name}")
        print(f"{'='*70}")
        print(f"\nOverall Metrics:")
        print(f"  Total Ground Truth Questions: {result.total_ground_truth_questions}")
        print(f"  Total Generated Questions:    {result.total_generated_questions}")
        print(f"  Correctly Identified:         {result.correctly_identified}")
        print(f"  Missing Questions:            {result.missing_questions}")
        print(f"  Extra Questions:              {result.extra_questions}")
        print(f"\nPerformance Metrics:")
        print(f"  Accuracy:  {result.accuracy:.2f}%")
        print(f"  Precision: {result.precision:.2f}%")
        print(f"  Recall:    {result.recall:.2f}%")
        print(f"  F1 Score:  {result.f1_score:.2f}%")

        if result.matches:
            print(f"\nMatched Questions ({len(result.matches)}):")
            for i, match in enumerate(result.matches, 1):
                print(f"\n  Match {i}:")
                print(f"    Ground Truth: {match.ground_truth_question}")
                print(f"    Generated:    {match.generated_question}")
                print(f"    Similarity:   {match.similarity_score:.2%}")
                print(f"    Type Correct: {'✓' if match.question_type_correct else '✗'}")
                print(f"    Options OK:   {'✓' if match.options_match else '✗'}")

        if result.missing_question_texts:
            print(f"\nMissing Questions ({len(result.missing_question_texts)}):")
            for q in result.missing_question_texts:
                print(f"  - {q}")

        if result.extra_question_texts:
            print(f"\nExtra Questions ({len(result.extra_question_texts)}):")
            for q in result.extra_question_texts:
                print(f"  + {q}")

    def print_aggregate_report(self, result: AggregateEvaluationResult):
        """Print aggregate evaluation report."""
        print(f"\n{'='*70}")
        print(f"Aggregate Evaluation Report")
        print(f"{'='*70}")
        print(f"\nDataset Overview:")
        print(f"  Total PDFs Evaluated:    {result.total_pdfs}")
        print(f"  Total Questions:         {result.total_questions}")
        print(f"  Correctly Identified:    {result.total_correct}")
        print(f"  Missing:                 {result.total_missing}")
        print(f"  Extra:                   {result.total_extra}")
        print(f"\nAverage Performance:")
        print(f"  Accuracy:  {result.avg_accuracy:.2f}%")
        print(f"  Precision: {result.avg_precision:.2f}%")
        print(f"  Recall:    {result.avg_recall:.2f}%")
        print(f"  F1 Score:  {result.avg_f1_score:.2f}%")

        print(f"\nPer-PDF Results:")
        print(f"  {'PDF Name':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
        print(f"  {'-'*70}")
        for pdf_result in result.per_pdf_results:
            print(f"  {pdf_result.pdf_name:<30} "
                  f"{pdf_result.accuracy:>9.2f}% "
                  f"{pdf_result.precision:>9.2f}% "
                  f"{pdf_result.recall:>9.2f}% "
                  f"{pdf_result.f1_score:>9.2f}%")

    def export_results_to_json(self, result: AggregateEvaluationResult, output_path: Path):
        """Export evaluation results to JSON file."""
        # Convert dataclasses to dicts
        data = asdict(result)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nResults exported to: {output_path}")
