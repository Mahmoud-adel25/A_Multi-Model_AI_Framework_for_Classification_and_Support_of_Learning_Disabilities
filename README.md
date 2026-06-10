# Learning Disabilities AI Framework

A child-friendly, accessible Streamlit application for handwriting-based learning-difficulty screening and adaptive learning support. The project combines multiple PyTorch image-classification models with interactive cognitive practice modules, child-safe feedback, and a parent/teacher dashboard for monitoring progress.

> **Important:** This project is a learning-support and research prototype. It is **not** a medical diagnostic tool and should not be used as the sole basis for diagnosing dyslexia or any learning disability. Results should be interpreted by qualified educators, clinicians, or specialists.

## Table of Contents

- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Application Pages](#application-pages)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration and Customization](#configuration-and-customization)
- [Testing and Validation](#testing-and-validation)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [Known Limitations](#known-limitations)
- [License](#license)
- [Contact and Support](#contact-and-support)
- [Additional Resources](#additional-resources)

## Key Features

- **Two user modes**
  - **Child Mode:** playful interface, child registration/selection, progress stars, and safe language.
  - **Teacher/Parent Mode:** dashboard-oriented view for reviewing children, progress, and activity.
- **Handwriting classification**
  - Upload handwriting images through the Streamlit UI.
  - Choose between Custom CNN, MobileNet V3 Large, and EfficientNet-B0 classifiers.
  - Display prediction confidence, probability distribution, recommendations, and classification history.
- **Learning support modules**
  - Attention and focus activities.
  - Visual memory practice.
  - Auditory memory game.
  - Working memory game.
  - Processing speed game.
  - Final assessment flow.
- **Local data persistence**
  - SQLite database stored in `database/learning_support.db`.
  - Tracks child profiles, activity, scores, stars, and learning history.
- **Accessible design direction**
  - Large buttons, high-contrast UI elements, theme toggle support, child-readable instructions, and simplified workflows.

## Project Structure

```text
learning-disabilities-ai-framework/
├── app.py                         # Main Streamlit entry point
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT license
├── README.md                      # Project documentation
├── SYSTEM_ARCHITECTURE_TABS.md    # Architecture notes
├── SYSTEM_DESIGN_IMAGE_PROMPT.md  # Diagram generation prompts
├── assets/                        # Architecture diagram notes/assets
├── database/
│   ├── db_handler.py              # SQLite data access layer
│   └── learning_support.db        # Local application database
├── models/
│   ├── cnn_model.py               # Custom CNN architecture
│   ├── mobilenet_model.py         # MobileNet V3 Large architecture
│   ├── efficientnet_model.py      # EfficientNet-B0 architecture
│   ├── model_loader.py            # Model loading and inference logic
│   └── *.pth                      # Trained PyTorch checkpoint files
├── pages/                         # Streamlit multipage app screens
├── utils/                         # Theme, audio, image, logging, session helpers
├── weights/                       # Weight-file documentation
├── Notebooks/                     # Training/evaluation notebooks and images
└── Paper/                         # Research paper files and generation script
```

## Application Pages

The app uses Streamlit's multipage layout. Each file in `pages/` represents a major user-facing screen or activity.

| Page | File | Primary audience | Purpose |
| --- | --- | --- | --- |
| Upload Handwriting Sample | `pages/1_Upload_Handwriting.py` | Child, Teacher/Parent | Upload a handwriting image, preview it, select a model, and start classification. |
| Classification Results | `pages/2_Classification_Result.py` | Teacher/Parent, supervised child use | Show the analyzed image, prediction result, probability distribution, recommendations, and prior classification history. |
| Learning Support | `pages/3_Learning_Support.py` | Child | Central activity hub with progress, game choices, success tips, recent games, and navigation to support modules. |
| Attention & Focus | `pages/4_Attention_Focus.py` | Child | Target-letter activity with configurable game time, grid size, target letter, results, and next-step navigation. |
| Visual Memory | `pages/5_Visual_Memory.py` | Child | Memory recall game with difficulty selection, timed visual prompts, answer choices, scoring, and follow-up navigation. |
| Auditory Memory | `pages/6_Auditory_Memory.py` | Child, Teacher/Parent | Sound-based memory activities with activity selection, difficulty settings, scoring, and teacher/parent notes. |
| Working Memory | `pages/7_Working_Memory.py` | Child, Teacher/Parent | Number memory game with mode selection, starting sequence length, adaptive play, and teacher/parent notes. |
| Processing Speed | `pages/8_Processing_Speed.py` | Child, Teacher/Parent | Quick-response activities with task selection, difficulty settings, reaction/accuracy tracking, and teacher/parent notes. |
| Final Assessment | `pages/9_Final_Assessment.py` | Child, Teacher/Parent | Combined assessment experience with timing, summary, performance feedback, and teacher/parent notes. |

### Page Flow

1. `app.py` shows the landing experience and lets users choose Child Mode or Teacher/Parent Mode.
2. Child Mode creates or selects a child profile, then routes the child toward handwriting upload and learning activities.
3. `pages/1_Upload_Handwriting.py` stores the uploaded handwriting image and selected model in session state.
4. `pages/2_Classification_Result.py` reads the stored upload/model choice, runs inference, records results, and shows recommendations.
5. `pages/3_Learning_Support.py` acts as the child-friendly activity hub after classification or direct navigation.
6. `pages/4_Attention_Focus.py`, `pages/5_Visual_Memory.py`, `pages/6_Auditory_Memory.py`, `pages/7_Working_Memory.py`, and `pages/8_Processing_Speed.py` provide focused practice modules.
7. `pages/9_Final_Assessment.py` provides a broader final assessment and summary for review.

### Page Design Notes

- **Child-facing pages** should use encouraging language, large controls, visual feedback, and avoid diagnostic labeling.
- **Teacher/parent sections** can include more detailed notes, but should still avoid presenting model output as a clinical diagnosis.
- **Navigation state** is managed through Streamlit session state helpers in `utils/session_manager.py`.
- **Scores and activity records** are persisted through `database/db_handler.py`.
- **Theme controls** are reused through `utils/theme.py`, so new pages should use the existing theme helper instead of duplicating styling logic.

## Requirements

### Runtime

- Python **3.8+** recommended.
- Windows, macOS, or Linux.
- A modern browser for the Streamlit interface.
- CPU is sufficient for local use; GPU is optional if your PyTorch installation supports it.

### Model Checkpoints

The app expects trained PyTorch checkpoints in the `models/` directory:

| Model | Required file |
| --- | --- |
| Custom CNN | `models/cnn_classifier (2).pth` |
| MobileNet V3 Large | `models/mobilenet_v3_large_classifier.pth` |
| EfficientNet-B0 | `models/efficientnet_b0_classifier (1).pth` |

If checkpoints are missing or incompatible, model loading/inference may fail. See `weights/README.md` for supported checkpoint formats and troubleshooting notes.

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd learning-disabilities-ai-framework
```

If you already have the project locally, open a terminal in the project root.

### 2. Create a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Upgrade packaging tools

```bash
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Confirm model files

Verify that the required `.pth` files are present in `models/`.

```bash
ls models
```

On Windows PowerShell:

```powershell
Get-ChildItem .\models
```

## Usage

### Start the application

```bash
streamlit run app.py
```

Streamlit usually opens the app automatically. If it does not, visit:

```text
http://localhost:8501
```

### Typical Child Mode workflow

1. Choose **Child Mode** from the landing screen.
2. Select an existing child profile or create a new one.
3. Open **Upload Handwriting Sample**.
4. Upload a handwriting image.
5. Choose a classification model.
6. Review child-safe feedback and recommendations.
7. Continue with support activities such as attention, visual memory, auditory memory, working memory, or processing speed.

### Typical Teacher/Parent workflow

1. Choose **Teacher / Parent** from the landing screen.
2. Select a child profile.
3. Review available progress, activity, stars, and classification history.
4. Use the insights to guide practice and follow-up support.

### Programmatic model check

You can quickly verify checkpoint availability from Python:

```python
from models.model_loader import ModelLoader

loader = ModelLoader()
print(loader.check_weights_available())
```

## Configuration and Customization

### Model behavior

Edit `models/model_loader.py` to customize:

- `CLASS_LABELS`
- CNN binary conversion behavior.
- Dyslexia probability threshold.
- MobileNet/EfficientNet class-index swapping.
- Checkpoint file paths.

### Model architectures

Edit these files if your trained checkpoints use different layer definitions:

- `models/cnn_model.py`
- `models/mobilenet_model.py`
- `models/efficientnet_model.py`

Keep architecture definitions aligned with the training code used to produce each checkpoint.

### Database

The local SQLite database lives at:

```text
database/learning_support.db
```

Use `database/db_handler.py` for schema and data-access changes. For a clean local demo reset, back up the database first, then replace or recreate it intentionally.

### UI and accessibility

Customize interface behavior in:

- `app.py` for the landing page, mode selection, dashboard, and shared styles.
- `pages/` for individual Streamlit screens.
- `utils/theme.py` for theme-related helpers.
- `utils/audio.py` and `utils/image_processing.py` for media helpers.

### Assets and diagrams

- `assets/README.md` describes model architecture diagrams.
- `SYSTEM_DESIGN_IMAGE_PROMPT.md` contains prompts for regenerating architecture visuals.
- `SYSTEM_ARCHITECTURE_TABS.md` documents the app architecture in tab-oriented form.

## Testing and Validation

This repository currently does not include a dedicated automated test suite or test runner configuration.

Recommended validation steps:

### Syntax check

```bash
python -m py_compile app.py models/*.py pages/*.py database/*.py utils/*.py
```

On Windows PowerShell, if wildcard behavior causes issues:

```powershell
python -m py_compile app.py
python -m py_compile (Get-ChildItem models,pages,database,utils -Filter *.py -Recurse).FullName
```

### Streamlit smoke test

```bash
streamlit run app.py
```

Then verify:

- The landing screen loads.
- Child Mode allows profile creation or selection.
- Teacher/Parent Mode loads the dashboard.
- Handwriting upload accepts an image.
- Each configured model either loads successfully or reports a clear missing/incompatible-checkpoint error.
- Support modules open without crashing.

### Model checkpoint check

```python
from models.model_loader import ModelLoader

loader = ModelLoader()
availability = loader.check_weights_available()
assert all(availability.values()), availability
```

## Dependencies

The core dependencies are pinned in `requirements.txt`:

| Package | Version | Purpose |
| --- | --- | --- |
| `streamlit` | `1.31.0` | Web application framework |
| `torch` | `2.1.2` | Deep learning runtime |
| `torchvision` | `0.16.2` | Vision models/transforms |
| `Pillow` | `10.2.0` | Image loading and manipulation |
| `opencv-python` | `4.9.0.80` | Image processing |
| `numpy` | `1.26.3` | Numerical operations |
| `pandas` | `2.1.4` | Data handling and analytics |
| `python-dateutil` | `2.8.2` | Date/time utilities |

SQLite is included with Python and does not require a separate package.

## Contributing

Contributions are welcome. Please keep changes focused, accessible, and aligned with the child-safe purpose of the project.

### Recommended workflow

1. Fork the repository or create a feature branch.
2. Install the project locally using the steps above.
3. Make a focused change with clear naming and minimal unrelated edits.
4. Run the validation steps in [Testing and Validation](#testing-and-validation).
5. Open a pull request with a concise explanation of the change, screenshots if UI changed, and any known limitations.

### Code standards

- Use readable Python with descriptive function and variable names.
- Keep Streamlit UI copy child-friendly, supportive, and non-diagnostic.
- Avoid hard-coding machine-specific paths.
- Keep model architecture changes compatible with documented checkpoint expectations.
- Do not commit personal data, sensitive child information, or private model artifacts unless intentionally allowed by the project owner.

### Issue reports

When reporting a bug, include:

- Operating system.
- Python version.
- Streamlit version.
- Steps to reproduce.
- Expected behavior.
- Actual behavior.
- Relevant traceback or screenshot.
- Whether model checkpoint files are present.

### Pull request checklist

- [ ] The app starts with `streamlit run app.py`.
- [ ] Updated or added documentation where needed.
- [ ] UI changes remain accessible and child-safe.
- [ ] Model changes document checkpoint compatibility.
- [ ] Database changes include migration/reset notes if relevant.

## Known Limitations

- **Not a diagnosis:** the system supports screening and practice, but it does not replace professional assessment.
- **Transformation sensitivity:** models may classify real handwriting correctly while misclassifying reversed or transformed versions of similar letters. Improving transformed-input performance can reduce normal-input performance.
- **Visual-cue dependence:** current models may rely on orientation, stroke direction, and pixel layout instead of robust transformation-invariant dyslexia indicators.
- **Local database:** data is stored locally in SQLite and is not configured for multi-user production deployment.
- **No formal automated test suite:** validation currently relies on syntax checks, smoke tests, and manual UI/model verification.

## License

This project is licensed under the **MIT License**. See `LICENSE` for the full license text.

## Contact and Support

- Open a GitHub issue for bugs, feature requests, or documentation improvements.
- Include reproduction steps, environment details, screenshots, and logs where possible.
- For research or educational use, document the dataset, training assumptions, and evaluation protocol before interpreting results.

## Additional Resources

- `weights/README.md` — model checkpoint requirements and troubleshooting.
- `assets/README.md` — architecture diagram overview.
- `SYSTEM_ARCHITECTURE_TABS.md` — system architecture documentation.
- `SYSTEM_DESIGN_IMAGE_PROMPT.md` — prompts for regenerating model training diagrams.
- `Notebooks/` — training and evaluation notebooks.
- `Paper/` — research paper artifacts and generation script.
