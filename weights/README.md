# Model Weights Directory

This directory should contain your trained model weight files for the Learning Disability Detection System.

## Required Files

Your trained model weights are loaded from the **`models/`** folder (same folder as the Python model files):

| Model | Filename | Description |
|-------|----------|-------------|
| Custom CNN | `cnn_classifier (2).pth` | Custom CNN trained weights |
| MobileNet V3 Large | `mobilenet_v3_large_classifier.pth` | Fine-tuned MobileNetV3 Large weights |
| EfficientNet-B0 | `efficientnet_b0_classifier (1).pth` | Fine-tuned EfficientNet-B0 weights |

## File Format

The weight files should be PyTorch state dictionaries saved using one of these formats:

### Option 1: Direct state dict
```python
torch.save(model.state_dict(), 'weights/custom_cnn_weights.pth')
```

### Option 2: With metadata
```python
torch.save({
    'model_state_dict': model.state_dict(),
    'epoch': epoch,
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss,
}, 'weights/custom_cnn_weights.pth')
```

### Option 3: Using 'state_dict' key
```python
torch.save({
    'state_dict': model.state_dict(),
    'config': model_config,
}, 'weights/custom_cnn_weights.pth')
```

The model loader (`models/model_loader.py`) automatically handles all three formats.

## Architecture Requirements

### Custom CNN (`models/cnn_model.py`)
- Input: Grayscale images (1 channel)
- Default input size: 224x224
- Output: 3 classes (Normal, Reversal, Dyslexia Indicator)

**If your architecture differs**, modify `models/cnn_model.py` to match your training architecture.

### MobileNet (`models/mobilenet_model.py`)
- Input: RGB images (3 channels)
- Default input size: 224x224
- Output: 3 classes

**If your classifier head differs**, modify the `classifier` Sequential block in `models/mobilenet_model.py`.

### EfficientNet (`models/efficientnet_model.py`)
- Input: RGB images (3 channels)
- Default input size: 224x224
- Output: 3 classes

**If your classifier head differs**, modify the `classifier` Sequential block in `models/efficientnet_model.py`.

## Class Labels

Default class labels (modify in `models/model_loader.py` if different):

```python
CLASS_LABELS = {
    0: "Normal",
    1: "Reversal",
    2: "Dyslexia Indicator"
}
```

## Troubleshooting

### "Model architecture mismatch" error
The weight file's architecture doesn't match the model definition. Ensure:
1. The model class in `models/` matches your training architecture
2. Number of classes matches
3. Input channels match (grayscale vs RGB)

### "Missing keys" or "Unexpected keys" warnings
Some layers were added/removed. Check:
1. Classifier head structure matches
2. Feature extraction layers match
3. Consider using `strict=False` in load_state_dict if needed

### Device issues
The loader automatically handles CPU/GPU placement using `map_location`.

## Testing Weights

After placing weights, test with:

```python
from models import ModelLoader

loader = ModelLoader()
print(loader.check_weights_available())  # Shows which weights are found

# Test loading
loader.load_model('cnn')  # Should load without errors
```

## Note for Evaluation

If weights are not available, the models will initialize with random weights for demonstration purposes. This allows the system to run and show the complete workflow even without trained models.
