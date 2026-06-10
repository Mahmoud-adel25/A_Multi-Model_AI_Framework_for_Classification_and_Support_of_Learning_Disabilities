# System Architecture – Support Layer Mapped to Project Tabs

This document maps the **system architecture** (Input → Training → Detection & Classification → **Learning Support** → Analytics) to the **actual Streamlit pages (tabs)** in this project.

---

## 1. Overall flow (top to bottom)

| Architecture layer              | Project implementation                                      |
|---------------------------------|-------------------------------------------------------------|
| **Input & Data**                | Tab: **1 – Upload Handwriting** (handwritten input → preprocessing) |
| **Training Phase**              | Offline (notebooks): Training / Testing / Validation        |
| **Detection & Classification**  | Tab: **2 – Classification Result** (models + optional Grad-CAM)   |
| **Learning Support Layer**      | Tab **3** = hub; Tabs **4–9** = support modules (see below) |
| **Analytics & Tracking**        | Database + Teacher Dashboard (stars, history, export)       |

---

## 2. Learning Support Layer → Tabs (exact mapping)

The **Learning Support** layer in the architecture diagram corresponds to these app tabs:

| Architecture component           | Project tab (page)        | Description |
|----------------------------------|---------------------------|-------------|
| **Learning Support (hub)**       | **3 – Learning Support**  | Central hub: stars, “Choose a Game”, links to all support modules. |
| **Reading Aid (Text-to-Speech)** | *(Optional)*              | Can be added to **2 – Classification Result** or **3 – Learning Support** (e.g. “Read aloud” for feedback). Not yet implemented as a dedicated tab. |
| **Attention / Focus**            | **4 – Attention Focus**   | Focus game: target letter finding, countdown, age-based duration, stars. |
| **Memory Trace Game (visual)**   | **5 – Visual Memory**     | Visual memory: grid of letters/symbols, recall, difficulty levels, stars. |
| **Memory Trace Game (auditory)** | **6 – Auditory Memory**   | Sound memory: listen to sequences, repeat back. |
| **Memory Trace Game (working)**  | **7 – Working Memory**    | Number memory: forward/backward number sequences. |
| **Processing / Speed**           | **8 – Processing Speed**  | Quick think: same/different, color matching, pattern recognition. |
| **Learning Feedback Quiz**       | **9 – Final Assessment**  | Final challenge: combines attention, memory, processing speed. |

---

## 3. Tab order and user flow

```
1_Upload_Handwriting  →  2_Classification_Result  →  3_Learning_Support (hub)
                                                              │
                    ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
                    │             │             │             │             │             │             │
                    ▼             ▼             ▼             ▼             ▼             ▼             ▼
            4_Attention   5_Visual    6_Auditory  7_Working  8_Processing   9_Final
              Focus        Memory      Memory      Memory      Speed       Assessment
```

- **Child flow:** Upload (1) → Result (2) → Learning Support (3) → choose game (4–8) or Final Assessment (9).
- **Teacher flow:** Dashboard / Classification history / export (analytics) use the same backend and DB.

---

## 4. Analytics & Tracking → Project

| Architecture component                    | In project |
|------------------------------------------|------------|
| **Performance Data**                     | `database/db_handler.py`: attention_results, visual_memory_results, classification_results, stars. |
| **Report Export**                        | Teacher dashboard / export (e.g. CSV) as in app design. |
| **Dashboard: Accuracy / Progress Charts** | Stars, “My Progress”, game history in sidebar and Learning Support (3); full dashboard in Teacher mode. |

---

## 5. Summary for diagrams

When drawing the **Support Layer** in a system architecture figure, use these labels so the diagram matches the app tabs:

- **Learning Support Layer** (one box or “hub”) → **Tab 3: Learning Support**
- Under it, as sub-boxes or branches:
  - **Reading Aid (TTS)** – optional/future
  - **Tab 4: Attention Focus**
  - **Tab 5: Visual Memory**
  - **Tab 6: Auditory Memory**
  - **Tab 7: Working Memory**
  - **Tab 8: Processing Speed**
  - **Tab 9: Final Assessment (Learning Feedback Quiz)**

Use this mapping in thesis figures, presentations, and the image prompt in `SYSTEM_DESIGN_IMAGE_PROMPT.md`.
