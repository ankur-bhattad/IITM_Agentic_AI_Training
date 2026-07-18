# Adaptive Agent with Feedback Memory

## Overview
This project demonstrates an adaptive AI agent that modifies its response style based on user feedback.  
The goal is to simulate a simple learning loop where the agent adapts over time by changing its tone or level of detail according to feedback such as "too short" or "too formal".

---

## Project Structure

```
adaptive_feedback_agent/
│
├── app.py                      ← Main entry point
│
├── core/
│   ├── agent.py                ← AdaptiveAgent class definition
│   ├── feedback.py             ← Feedback rules for adapting style
│   ├── memory.py               ← Persistent feedback memory
│   ├── prompts.py              ← Prompt generation logic
│   └── __init__.py
│
├── config/
│   └── settings.py             ← OpenAI client setup and environment loading
│
├── data/
│   └── feedback_history.json   ← Stores feedback memory
│
├── logs/
│   └── interactions.log        ← Optional logs
│
├── requirements.txt
└── Readme.md
```

---

## Setup Instructions

### 1. Clone or Copy the Repository
```bash
git clone https://github.com/yourusername/adaptive_feedback_agent.git
cd adaptive_feedback_agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create a .env File
In the project root, create a file named `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-yourkey
```

---

## Run the Demo
```bash
python app.py
```

The program will:
1. Generate an initial response.
2. Simulate a sequence of user feedbacks.
3. Adapt the response style based on each feedback.
4. Display the final memory of feedback and style.

---

## Example Output

```
Agent response (initial):
Reinforcement learning is a type of machine learning where agents learn from rewards and penalties.

User feedback: too formal
Agent response (after adapting):
Reinforcement learning is like trial and error – the AI learns by trying actions and seeing what works best.

Feedback memory: ['too formal', 'too short', 'too long', 'too casual']
Final style: formal
```

---

## How It Works

| Step | Component | Function |
|------|------------|-----------|
| 1 | `prompts.py` | Builds dynamic prompts based on style |
| 2 | `feedback.py` | Maps feedback text to a new style |
| 3 | `memory.py` | Saves feedback across sessions |
| 4 | `agent.py` | Controls overall behavior and state |
| 5 | `app.py` | Runs the end-to-end simulation |

---

## Future Extensions

- Add a Streamlit interface for live interaction.  
- Replace rule-based adaptation with a reinforcement model.  
- Store full query-response pairs in logs for analysis.  

---

## License
This project is provided for educational and instructional use.  
You may reuse or modify it freely with attribution.
