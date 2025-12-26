# Form Extraction Evaluation Framework

This framework evaluates the accuracy of form generation from PDFs by comparing generated forms against ground truth annotations.

## Directory Structure

```
evaluation/
├── evaluator.py                 # Main evaluation framework
├── run_evaluation.py            # Evaluation runner script
├── ground_truth/                # Ground truth form schemas
│   └── example_contact_form.json
├── test_forms/                  # Generated forms to evaluate (created during evaluation)
└── results/                     # Evaluation results (created during evaluation)
```

## Ground Truth Format

Ground truth files are JSON files matching the FormFlow schema format:

```json
{
  "title": "Form Title",
  "description": "Form description",
  "components": [
    {
      "id": "comp_1",
      "type": "short-answer",
      "data": {
        "question": "Question text",
        "required": true
      }
    },
    {
      "id": "comp_2",
      "type": "multiple-choice",
      "data": {
        "question": "Question text",
        "options": ["Option 1", "Option 2", "Option 3"],
        "required": false
      }
    }
  ]
}
```

## Creating Ground Truth Files

1. Manually annotate a PDF by identifying all form questions
2. Create a JSON file in `ground_truth/` directory
3. Name it matching the PDF filename (e.g., `contact_form.json` for `contact_form.pdf`)
4. Include all questions with correct types, options, and required status

## Running Evaluations

### Evaluate a Single PDF

```bash
python run_evaluation.py --pdf path/to/form.pdf --ground-truth ground_truth/form.json
```

### Evaluate a Dataset

```bash
python run_evaluation.py --dataset --ground-truth-dir ground_truth/ --generated-dir test_forms/
```

### With Custom Similarity Threshold

```bash
python run_evaluation.py --dataset --threshold 0.85
```

## Evaluation Metrics

The framework calculates the following metrics:

### Per-PDF Metrics

- **Accuracy**: (Correct / Total Ground Truth) × 100
- **Precision**: (Correct / Total Generated) × 100
- **Recall**: (Correct / Total Ground Truth) × 100
- **F1 Score**: Harmonic mean of precision and recall

### Question Matching

Questions are matched based on:
- Text similarity (configurable threshold, default 0.8)
- Question type (short-answer vs multiple-choice)
- Options (for multiple choice questions)
- Required status

### Aggregate Metrics

When evaluating multiple PDFs:
- Average accuracy, precision, recall, F1 across all PDFs
- Total questions, correct identifications, missing, and extra questions

## Output

### Console Report

```
====================================================================
Evaluation Report: contact_form
====================================================================

Overall Metrics:
  Total Ground Truth Questions: 5
  Total Generated Questions:    5
  Correctly Identified:         4
  Missing Questions:            1
  Extra Questions:              1

Performance Metrics:
  Accuracy:  80.00%
  Precision: 80.00%
  Recall:    80.00%
  F1 Score:  80.00%

Matched Questions (4):
  Match 1:
    Ground Truth: What is your full name?
    Generated:    What is your name?
    Similarity:   92.31%
    Type Correct: ✓
    Options OK:   ✓

Missing Questions (1):
  - What is your phone number?

Extra Questions (1):
  + What is your address?
```

### JSON Export

Results are automatically exported to `results/evaluation_TIMESTAMP.json` with full details including all matches, missing questions, and metrics.

## Using in Tests

```python
from evaluation.evaluator import FormEvaluator

evaluator = FormEvaluator(similarity_threshold=0.8)

# Evaluate single form
result = evaluator.evaluate_form(
    generated_schema=generated_form,
    ground_truth_schema=ground_truth,
    pdf_name="contact_form"
)

# Evaluate dataset
aggregate_result = evaluator.evaluate_dataset(
    ground_truth_dir=Path("ground_truth"),
    generated_forms_dir=Path("test_forms")
)

# Print reports
evaluator.print_evaluation_report(result)
evaluator.print_aggregate_report(aggregate_result)

# Export to JSON
evaluator.export_results_to_json(aggregate_result, Path("results/eval.json"))
```

## Best Practices

1. **Consistent Naming**: Use the same base name for PDFs and ground truth files
2. **Complete Annotation**: Include all questions from the PDF, even optional ones
3. **Exact Text**: Use the exact question text as it appears in the PDF
4. **Option Order**: List multiple choice options in the same order as the PDF
5. **Regular Testing**: Run evaluations regularly to track improvements

## Interpreting Results

- **High Accuracy (>90%)**: System correctly identifies most questions
- **Low Precision (<70%)**: System generates too many extra questions
- **Low Recall (<70%)**: System misses many questions from the PDF
- **High F1 (>85%)**: Good balance between precision and recall
