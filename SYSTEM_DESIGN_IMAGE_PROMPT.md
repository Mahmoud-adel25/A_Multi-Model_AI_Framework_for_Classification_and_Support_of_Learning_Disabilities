# System Design Diagram – Image Generation Prompt

Use this prompt with an **image generator** (e.g. DALL·E, Midjourney, Cursor GenerateImage, or similar) to create a **system architecture diagram** for the Learning Disability Detection & Support System.

**Support layer ↔ app tabs:** For a diagram where the **Learning Support** layer matches the project’s pages (tabs), see **Option D** below and the mapping in `SYSTEM_ARCHITECTURE_TABS.md`.

---

## Option A: Short prompt (for most image AI)

```
Professional system architecture diagram, clean flat design, white background. Title at top: "Learning Disability Detection & Support System". Three horizontal layers from top to bottom:

Layer 1 - User: Two boxes side by side: "Child (Play & Practice)" and "Teacher/Parent (Dashboard)".

Layer 2 - Application: One wide box "Streamlit Web App" containing: "Mode selector | Child Home | Upload Handwriting | Classification | Learning Support | Attention Game | Memory Game | Teacher Dashboard".

Layer 3 - Backend: Three boxes in a row: "Model Loader (CNN, MobileNet, EfficientNet)" with arrow from above labeled "handwriting image", "Database Handler (SQLite)" with arrow "users, results, progress", "Session Manager" with arrow "user state".

Bottom: One box "learning_support.db + .pth model files". Arrows flow top to bottom between layers. Minimal colors: blue for app, green for data, gray for storage. No photos, vector diagram style.
```

---

## Option B: Detailed prompt (for best control)

```
Create a single image of a system architecture diagram for a software application. Style: professional, technical diagram, vector or flat design, white or light gray background, suitable for a thesis or presentation.

Layout (top to bottom):

1. TITLE: "Learning Disability Detection & Support System" in bold at the top center.

2. PRESENTATION LAYER (top row): Two rounded rectangles side by side:
   - Left: "Child Mode" with small icons or text: "Register/Select • Check Writing • Practice • Focus Game • Memory Game • Stars"
   - Right: "Teacher/Parent Mode" with text: "Select Child • Progress • Attention/Memory History • Classification History • Export CSV"

3. Arrow down from both boxes to:

4. APPLICATION LAYER (middle): One large rounded rectangle: "Streamlit Web App (app.py + pages/)". Inside or below it, small labels: "Session Manager • Page routing • Accessibility CSS (dyslexia-friendly)".

5. Arrows down from the app box splitting to two groups:

6. BACKEND LAYER (bottom): Two main blocks side by side:
   - Left block: "ML Pipeline" – sub-boxes: "Image Preprocessing" → "Model Loader" → "CNN / MobileNet / EfficientNet" → "Prediction (Non-Dyslexic | Dyslexic)"
   - Right block: "Data Layer" – "Database Handler" → "SQLite (users, parents, classification_results, attention_results, visual_memory_results)"

7. At the very bottom: small storage icons or boxes: "learning_support.db" and ".pth model weights"

Use light blue for user/app boxes, light green for data/DB, light orange or gray for ML/storage. Black or dark gray text. Clear arrows showing data flow. No realistic photos, only diagram elements.
```

---

## Option C: Simple 3-tier diagram (minimal text)

```
System design diagram, 3 tiers, vertical:

Tier 1: "Users" – Child | Teacher/Parent (two small boxes).

Tier 2: "Streamlit App" – one box (Streamlit Web App, multi-page).

Tier 3: "Backend" – two boxes: "Models (CNN, MobileNet, EfficientNet)" and "SQLite Database".

Arrows from Tier 1 to Tier 2, and from Tier 2 to both boxes in Tier 3. Clean, flat, white background, blue and gray colors, professional technical illustration.
```

---

## Option D: Full pipeline with Support Layer (aligned to project tabs)

Use this when the diagram must match the **full pipeline** (Input → Training → Detection → **Learning Support** → Analytics) and the **actual app tabs**. See `SYSTEM_ARCHITECTURE_TABS.md` for the full mapping.

```
Professional system architecture diagram, vertical flow, white or light gray background. Title: "Learning Disability Detection & Support System".

From top to bottom, five layers:

1. INPUT & DATA LAYER (blue): "Handwritten input" → "Dataset" → "Data Preprocessing". Arrows between them.

2. TRAINING PHASE (white box): Three boxes in a row: "Training" | "Testing" | "Validation". Arrow from Data Preprocessing into this phase.

3. DETECTION & CLASSIFICATION (green): One box "Detection & Classification". Inside or below: "Feature Extraction Model", "Decision Layer Model", "Explainable AI (Grad-CAM)". Arrow from Training Phase. Output: "Classification Output".

4. LEARNING SUPPORT LAYER (orange) – aligned to app tabs:
   - Central hub: "Tab 3: Learning Support (Hub)".
   - Branching from it, left to right:
     - "Tab 4: Attention Focus" (focus game)
     - "Tab 5: Visual Memory" (memory game – visual)
     - "Tab 6: Auditory Memory" (sound memory)
     - "Tab 7: Working Memory" (number memory)
     - "Tab 8: Processing Speed" (quick think)
     - "Tab 9: Final Assessment" (learning feedback quiz)
   Optional small box: "Reading Aid (TTS)" – optional/future.
   Arrow from "Classification Output" into the Support Layer.

5. ANALYTICS & TRACKING (orange): One box "Analytics & Tracking". Three outputs: "Performance Data" (chart icon), "Report Export" (spreadsheet icon), "Dashboard: Accuracy / Progress Charts". Arrows from Support Layer into this layer.

Colors: blue = input, green = ML, orange = support and analytics. Arrows connect each layer to the next. No photos, vector/diagram style.
```

**One-line version (Support Layer = tabs):**

```
System architecture: Input & Data → Training (Train/Test/Validation) → Detection & Classification (Grad-CAM) → Learning Support Layer with tabs 3=Hub, 4=Attention, 5=Visual Memory, 6=Auditory, 7=Working Memory, 8=Processing Speed, 9=Final Assessment → Analytics (Performance, Report Export, Dashboard). Vertical flow, flat design, white background.
```

---

## Tips for image generators

- If the AI produces messy text, use **Option C** and add labels in PowerPoint or Google Slides over the image.
- For **Cursor GenerateImage**: use Option A or B; you can say "no text" and add all labels in the slide editor.
- For **presentation use**: generate the image, then place it on a slide and add a title "System Architecture" and a short legend (e.g. "Child/Teacher → Streamlit → Models & DB").

---

## One-line version (for quick paste)

```
System architecture diagram: top "Child & Teacher" users, middle "Streamlit Web App", bottom "Model Loader + SQLite DB" and "learning_support.db + .pth files", arrows between layers, flat design white background, professional.
```

---

## Model training pipeline diagrams (CNN, EfficientNet, MobileNet)

Three system architecture flowcharts for the **training pipeline** of each model. Same flow for all: **Data → Preprocessing → Create Model → Epochs → Evaluate → Reach Acceptable Accuracy? → Display Accuracy (Yes) or loop (No)**.

**Design:** Black and white only; every arrow connects two elements (no unreachable or dangling arrows).

**Preprocessing** (from notebooks): Load Data → Resize; CNN uses Grayscale + 28×28 + Normalize; EfficientNet/MobileNet use Grayscale(3) + 224×224 + RandomRotation/RandomAffine (train) + Normalize. The diagrams use "Load Data" and "Resize" as the main preprocessing block for consistency.

**Generated images** (Cursor GenerateImage): `assets/system_arch_cnn.png`, `assets/system_arch_efficientnet.png`, `assets/system_arch_mobilenet.png`.

### CNN system architecture

```
System architecture flowchart, CNN training pipeline. Black and white only: white background, black rectangular boxes with black borders, black arrows. No colors. Linear vertical flow, every arrow connects exactly one box to the next. Top: cylinder "Data". Single arrow down to box "Load Data". Single arrow down to box "Resize". Both in a group "pre processing". Single arrow down to large box "Create Model" containing: "CNN Layer 1", "CNN Layer 2", "CNN Layer N". Single arrow down from Create Model to box "Feed Input and labels". Single arrow to box "Evaluate (calculate the loss)". Single arrow to diamond "Reach Acceptable Accuracy?". From diamond: one arrow labeled Yes to box "Display Accuracy"; one arrow labeled No going back and connecting directly to "Feed Input and labels". All arrows must touch both source and destination; no dangling or unreachable arrows. Title: CNN System Architecture.
```

### EfficientNet system architecture

```
System architecture flowchart, EfficientNet training pipeline. Black and white only: white background, black rectangular boxes with black borders, black arrows. No colors. Same layout as CNN. Linear vertical flow, every arrow connects exactly one box to the next. Top: cylinder "Data". Single arrow down to box "Load Data". Single arrow down to box "Resize". Group "pre processing". Single arrow down to large box "Create Model" containing: "Stem", "MBConv Block 1", "MBConv Block 2", "MBConv Block N", "Head", "Classifier". Single arrow down to "Feed Input and labels". Single arrow to "Evaluate (calculate the loss)". Single arrow to diamond "Reach Acceptable Accuracy?". Yes arrow to "Display Accuracy"; No arrow connecting back to "Feed Input and labels". All arrows touch source and destination; no unreachable arrows. Title: EfficientNet System Architecture.
```

### MobileNet system architecture

```
System architecture flowchart, MobileNet training pipeline. Black and white only: white background, black rectangular boxes with black borders, black arrows. No colors. Same layout as CNN. Linear vertical flow, every arrow connects exactly one box to the next. Top: cylinder "Data". Single arrow down to box "Load Data". Single arrow down to box "Resize". Group "pre processing". Single arrow down to large box "Create Model" containing: "Stem", "Inverted Residual Block 1", "Inverted Residual Block 2", "Inverted Residual Block N", "Head", "Classifier". Single arrow down to "Feed Input and labels". Single arrow to "Evaluate (calculate the loss)". Single arrow to diamond "Reach Acceptable Accuracy?". Yes arrow to "Display Accuracy"; No arrow connecting back to "Feed Input and labels". All arrows touch source and destination; no unreachable arrows. Title: MobileNet System Architecture.
```
