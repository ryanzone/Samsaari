# Samsaari Rice Disease Detection Model — Final Results (V2)

## Model Details

| Parameter | Value |
|---|---|
| Model | MobileNetV3-Large |
| Dataset | Rice disease classification dataset |
| Number of Classes | 10 |
| Image Size | 224 × 224 |
| Normalization | ImageNet |
| Uncertainty Threshold | 70% |
| Best Validation Accuracy | **97.06%** |
| Macro F1-Score | **0.9626** |
| Model Checkpoint | `rice_disease_mobilenetv3_v2.pth` |

## Classes

1. Bacterial Leaf Blight
2. Bacterial Leaf Streak
3. Bacterial Panicle Blight
4. Blast
5. Brown Spot
6. Dead Heart
7. Downy Mildew
8. Hispa
9. Normal
10. Tungro

## Overall Metrics

- **Validation Accuracy:** 97.06%
- **Macro F1-Score:** 0.9626

## External Validation — Roboflow

The model was additionally evaluated on the validation split of the external **Paddy Field** dataset from Roboflow.

Dataset:

`paddy-field-1`

Source:

https://universe.roboflow.com/wheat-egsai/paddy-field-trpyn

### Evaluation Results

| Metric | Result |
|---|---:|
| Labeled Images | **2,060** |
| Correct Predictions | **2,017** |
| Incorrect Predictions | **43** |
| Accuracy | **97.91%** |

Unlabeled samples were excluded from the evaluation.

### Per-Class External Accuracy

| Class | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Bacterial Leaf Blight | 94 | 94 | **100%** |
| Bacterial Leaf Streak | 76 | 76 | **100%** |
| Bacterial Panicle Blight | 67 | 67 | **100%** |
| Blast | 331 | 345 | **95.9%** |
| Brown Spot | 187 | 191 | **97.9%** |
| Dead Heart | 286 | 286 | **100%** |
| Downy Mildew | 119 | 123 | **96.7%** |
| Hispa | 313 | 318 | **98.4%** |
| Normal | 340 | 344 | **98.8%** |
| Tungro | 204 | 216 | **94.4%** |

## Uncertainty Handling

Samsaari uses a **70% confidence threshold** to prevent low-confidence disease predictions from directly triggering disease-specific actions.

```text
Confidence >= 70%
        ↓
Prediction accepted
        ↓
Gemini decision pipeline

Confidence < 70%
        ↓
Uncertain prediction
        ↓
WAIT
        ↓
Request a clearer crop image
