# Learning Disability Detection & Support System

A child-friendly, accessible multi-model AI system for detecting learning disabilities from handwriting and providing adaptive learning support.

## Features

### Two Operating Modes

1. **Child Mode** - Practice-focused, playful UI
2. **Teacher/Parent Mode** - Progress analytics

### Core Modules

#### Handwriting Classification
- Upload handwriting images
- Classification using CNN, MobileNet V3 Large, or EfficientNet-B0
- Child-safe feedback (no diagnostic labels shown to children)

**Known limitation (transformation invariance):** When models correctly classify real handwriting images, they often misclassify reversed or transformed versions of the same letters. When adjusted to classify reversed letters correctly, they can misclassify normal handwriting. Improving performance on one type of input tends to degrade performance on the other. The models tend to rely on low-level visual cues (orientation, stroke direction, pixel layout) rather than learning transformation-invariant, dyslexia-related writing patterns.

#### Attention & Focus Module
- Age-based focus duration, countdown timer, target letter finding task

#### Visual Memory Module
- Configurable display duration, recall questions, difficulty levels

## Project Structure

```
Grad project/
├── app.py
├── requirements.txt
├── README.md
├── models/
│   ├── cnn_model.py
│   ├── mobilenet_model.py
│   ├── efficientnet_model.py
│   ├── model_loader.py
│   └── *.pth
├── pages/
│   ├── 1_Upload_Handwriting.py
│   ├── 2_Classification_Result.py
│   └── ...
├── database/
├── utils/
└── weights/
```

## Installation

1. Create virtual environment and activate it.
2. Install dependencies: `pip install -r requirements.txt`
3. Place model weights in `models/`: `cnn_classifier (2).pth`, `mobilenet_v3_large_classifier.pth`, `efficientnet_b0_classifier (1).pth`

## Running the Application

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`
