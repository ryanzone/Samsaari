# Samsaari Rice Disease Detection Model — Final Results (Old)

## Model Details

| Parameter                | Value                                                 |
| ------------------------ | ----------------------------------------------------- |
| Model                    | MobileNetV3-Large                                     |
| Dataset 1                | `techharry/paddy_disease_classification`              |
| Dataset 2                | `Project-AgML/rice_leaf_disease_classification_india` |
| Total Images             | 16,339                                                |
| Training Images          | 13,071                                                |
| Validation Images        | 3,268                                                 |
| Number of Classes        | 10                                                    |
| Image Size               | 224 × 224                                             |
| GPU                      | NVIDIA GeForce RTX 4060 Laptop GPU                    |
| Peak GPU Memory          | 2.74 GB                                               |
| Best Validation Accuracy | **97.49%**                                            |

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

## Classification Report

| Class                    | Precision | Recall | F1-Score | Support |
| ------------------------ | --------: | -----: | -------: | ------: |
| Bacterial Leaf Blight    |      0.99 |   0.99 |     0.99 |     413 |
| Bacterial Leaf Streak    |      0.95 |   0.99 |     0.97 |      76 |
| Bacterial Panicle Blight |      0.98 |   0.94 |     0.96 |      67 |
| Blast                    |      0.98 |   0.97 |     0.97 |     636 |
| Brown Spot               |      0.99 |   0.98 |     0.99 |     513 |
| Dead Heart               |      0.99 |   0.99 |     0.99 |     288 |
| Downy Mildew             |      0.90 |   0.94 |     0.92 |     124 |
| Hispa                    |      0.97 |   0.95 |     0.96 |     319 |
| Normal                   |      0.96 |   0.97 |     0.97 |     353 |
| Tungro                   |      0.97 |   0.98 |     0.98 |     479 |

## Overall Metrics

- **Accuracy:** 0.9749
- **Macro Precision:** 0.97
- **Macro Recall:** 0.97
- **Macro F1-Score:** 0.97
- **Weighted F1-Score:** 0.97
- **Validation Samples:** 3,268

## Best Performing Classes

- Bacterial Leaf Blight — **F1: 0.99**
- Brown Spot — **F1: 0.99**
- Dead Heart — **F1: 0.99**
- Tungro — **F1: 0.98**

## Lowest Performing Class

- Downy Mildew — **F1: 0.92**

## Model Output

The trained model is saved as:

```text
rice_disease_mobilenetv3.pth
```
