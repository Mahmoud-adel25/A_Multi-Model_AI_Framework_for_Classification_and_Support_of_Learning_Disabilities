# Model system architecture diagrams

Training pipeline flowcharts for the three classification models. **Design:** black and white only; every arrow connects two elements (no unreachable arrows).

## Diagrams

| Model        | File                         | Description                                                                 |
|-------------|------------------------------|-----------------------------------------------------------------------------|
| **CNN**     | `system_arch_cnn.png`        | Custom CNN: Data → Preprocessing → CNN Layer 1…N → Epochs → Accuracy        |
| **EfficientNet** | `system_arch_efficientnet.png` | EfficientNet-B0: same flow with Stem, MBConv blocks, Head, Classifier   |
| **MobileNet**   | `system_arch_mobilenet.png`   | MobileNet V3 Large: same flow with Stem, Inverted Residual blocks, Classifier |

## Flow (all three)

1. **Data** → **Load Data** → **Resize** (pre processing)
2. **Create Model** (model-specific layers)
3. **Epochs**: Feed Input and labels → Evaluate (calculate the loss)
4. **Reach Acceptable Accuracy?** → Yes: Display Accuracy | No: arrow back to Feed Input and labels

Preprocessing in the notebooks: CNN uses Grayscale, Resize(28×28), Normalize; EfficientNet/MobileNet use Grayscale(3), Resize(224×224), augmentation (train), Normalize. Copy generated images from Cursor project assets or regenerate with prompts in `SYSTEM_DESIGN_IMAGE_PROMPT.md` (section “Model training pipeline diagrams”).
