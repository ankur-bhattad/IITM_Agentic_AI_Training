# IITM Agentic AI Training

Repository for IITM Emeritus Course In Agentic AI Material

## 📚 Course Overview

This repository contains comprehensive learning materials, assignments, projects, and live session activities for the IITM Emeritus Course in Agentic AI. The course is actively ongoing, with weekly materials released progressively.

**Latest Update**: Expanded course materials now include weeks 1-20+ with advanced topics in agent deployment, observability, production systems, debugging frameworks, and specialized agentic applications.

## 📁 Repository Structure

### 📖 Weekly Resources (`Weekly resources/`)
Curated learning materials for each week of the course covering:
- Course Introduction & Fundamentals (Weeks 1-4)
- Agent Architecture & Design (Weeks 5-8)
- Advanced Techniques & LLM Integration (Weeks 9-12)
- Retrieval-Augmented Generation & Production Systems (Weeks 13-16)
- Advanced Debugging & Agentic Workflows (Weeks 17-20)
- Specialized masterclass materials

Each week contains:
- Jupyter notebooks with interactive code samples
- Conceptual learning resources and reference materials
- Code examples and best practices
- Supporting documentation

### 📝 Assignments (`Assignments/`)
Weekly assignments designed to reinforce learning and build practical skills:
- Weeks 1-20 hands-on coding exercises
- Problem-solving activities aligned with weekly topics
- Progressive complexity building from fundamentals to advanced production patterns
- Assignments for core concepts, agent building, RAG systems, debugging strategies, and deployment strategies

### 🎯 Graded Projects (`Graded Projects/`)
Comprehensive graded projects that assess learning outcomes:

**Recent Projects:**
- **Week 15**: E-Commerce Domain Support Assistant
  - Real Amazon.in customer service documentation (PDF sources)
  - RAG system with FAISS vector store indexing
  - Multi-turn conversation memory and context awareness
  - Streamlit UI bonus implementation
  
- **Week 4, 6, 12**: Various foundational and intermediate projects
- Graded projects involve building end-to-end agentic AI solutions
- Requirements include working code, documentation, and evaluation benchmarks

### 💻 Live Session Activity (`Live Session Activity/`)
Interactive code, exercises, and demonstrations from live sessions organized by week:
- Week-by-week session activities and code walkthroughs
- Advanced topics demonstrations (e.g., operational agents, API design)
- Retrieval masterclass materials
- Week 16 includes:
  - **Operational Agent API**: Production-ready reference implementation demonstrating deployment, monitoring, observability with LangSmith integration, structured logging, and evaluation patterns
- Week 17+ includes:
  - **Industry-Grade IT Support Agent (FastAPI)**: End-to-end agentic workflow with service monitoring, log analysis, and escalation management
  - **Advanced Debugging Frameworks**: Techniques for troubleshooting complex agent workflows
  - **Specialized Agentic Applications**: Domain-specific agent implementations

## 📚 Detailed Weekly Content Summary

| **Week** | **Title** | **Pillar** | **Key Concepts** | **Technologies & Tools** | **Learning Outcomes** |
|----------|-----------|-----------|------------------|------------------------|-----------------------|
| **Week 1** | Getting Started with Python & ChatGPT | Pillar 1: Python Foundations | Python environment setup, ChatGPT & LLMs, Prompt engineering fundamentals, API integration | Python 3.10+, OpenAI API, Jupyter Notebooks, Virtual environments | Set up Python dev environment, Make API calls to ChatGPT, Understand prompt structure, Run & modify code examples |
| **Week 2** | Data Types, Variables, Control Flow & Functions | Pillar 1: Python Foundations | Python data types, Variable assignment, Control flow (if/else, loops), Function definition, Error handling | Python built-ins, List/dict comprehensions, Exception handling | Work with data structures, Write reusable functions, Handle control flow, Implement error handling |
| **Week 3** | Working with Libraries | Pillar 1: Python Foundations | Popular libraries (NumPy, Pandas, Requests), Dependency management, Working with APIs, Data manipulation | NumPy, Pandas, Requests, pip & package management | Install & use external libraries, Perform data manipulation, Make API requests, Work with structured data |
| **Week 4** | Fundamentals of AI & ML | Pillar 1: Python Foundations | ML basics (supervised/unsupervised), Classification & regression, Train-test split, Neural networks intro, Evaluation metrics | Scikit-learn, Model training & evaluation, Hyperparameter tuning | Build & train ML models, Evaluate performance, Understand ML workflow, Apply concepts to real-world problems |
| **Week 5** | Large Language Models (LLMs) | Pillar 2: Core AI Concepts | How LLMs work (transformers), Model scaling & emergence, Tokenization & embeddings, Fine-tuning vs. prompt engineering, Token limits | OpenAI API (GPT-4o-mini, embeddings), Tokenization libraries, Embedding models | Understand LLM capabilities & limitations, Work with embeddings, Optimize prompts, Manage API usage & costs |
| **Week 6** | Embedding Models & Vector Basics | Pillar 2: Core AI Concepts | Vector representations, Semantic similarity, Vector databases & indexing, Similarity search, Dimensionality | OpenAI embeddings, FAISS, Vector similarity metrics, Vector DB basics | Generate & work with embeddings, Implement semantic search, Index large vector datasets, Measure semantic similarity |
| **Week 7** | Agentic Tools in Python | Pillar 3: Introduction to Agentic AI | Tool definition & design, Function calling/tool use, Error handling in tools, Stateless vs. stateful tools, Tool composition | LangChain tool decorators, Tool frameworks, Function schema generation, Tool validation | Define & implement custom tools, Integrate with LLM function calling, Handle errors gracefully, Chain multiple tools |
| **Week 8** | Introduction to Agentic AI | Pillar 3: Introduction to Agentic AI | What is an agent, Agent loop & reasoning cycle, Perception-reasoning-action, Agent vs. chatbot, Design patterns | Agent frameworks, LangChain agents (ReAct), Agent state management, LLM as reasoning engine | Understand agent architecture, Build first autonomous agent, Implement perception-reasoning-action loop, Design workflows |
| **Week 9** | Programming & Frameworks for Agentic Systems | Pillar 3: Introduction to Agentic AI | Agentic frameworks & libraries, Orchestration & workflow design, Agent memory & context, Asynchronous operations, Production considerations | LangChain orchestration, AutoGen, FastAPI, Message queues | Use agentic frameworks, Design complex workflows, Implement memory systems, Deploy at scale |
| **Week 10** | Agent Architectures & Collaboration | Pillar 3: Introduction to Agentic AI | Single-agent architectures (ReAct), Multi-agent systems, Agent specialization & roles, Inter-agent communication, Hierarchical structures | LangChain hierarchical agents, AutoGen, Agent protocols, Supervision patterns | Design single & multi-agent systems, Implement collaboration, Debug interactions, Scale systems |
| **Week 11** | Decision-Making & Planning in Agents | Pillar 4: Advanced Agent Patterns | Goal decomposition & planning, Tree-of-thought & CoT reasoning, Decision trees & state management, Constraint satisfaction, Exploration vs. exploitation | Planning algorithms (BFS, DFS, A*), LLM-based planning, State space exploration, Constraint frameworks | Implement goal decomposition, Use reasoning strategies, Design decision-making systems, Handle complex planning |
| **Week 12** | Memory & Knowledge Retrieval in Agents with MCP | Pillar 4: Advanced Agent Patterns | Short-term vs. long-term memory, Memory types (episodic, semantic, procedural), Knowledge graphs, Information retrieval, Model Context Protocol | Vector stores, Knowledge graphs (Neo4j), MCP servers & clients, Memory optimization | Build memory systems, Integrate knowledge bases, Use MCP for tool integration, Implement efficient retrieval |
| **Week 13** | Prompt Engineering & Adaptive Instructions (Streamlit) | Pillar 4: Advanced Agent Patterns | Advanced prompting techniques, Few-shot & zero-shot, Instruction tuning, Dynamic adaptation, Instruction formatting & CoT | Prompt frameworks, Streamlit, Prompt versioning & testing, Few-shot selection | Master advanced prompting, Create adaptive systems, Build interactive UIs, Evaluate prompt effectiveness |
| **Week 14** | Learning & Adaptation in Agents | Pillar 4: Advanced Agent Patterns | Agent self-improvement, Feedback loops & iterative refinement, Fine-tuning vs. in-context learning, Reinforcement learning from feedback, Continuous evolution | RLHF, Model fine-tuning APIs, Feedback collection, Evaluation metrics | Implement feedback loops, Enable self-improvement, Evaluate & iterate, Deploy continuously improving agents |
| **Week 15** | Advanced Retrieval-Augmented Generation (RAG) | Pillar 5: Advanced Agentic Systems | RAG architecture & workflow, Document chunking & embedding strategies, Retrieval optimization & ranking, Hybrid search (BM25 + semantic), Multi-document reasoning, Domain-specific RAG | FAISS, LangChain RAG chains, Document loaders (PDF, web), Hybrid strategies, Multi-hop retrieval | Build production-grade RAG, Optimize retrieval quality, Handle complex scenarios, Implement multi-turn RAG, Create domain assistants |
| **Week 16** | Deploying & Monitoring Agentic Systems | Pillar 5: Advanced Agentic Systems | Production deployment patterns, API design (FastAPI, REST), Monitoring & observability, Performance metrics & SLAs, Logging & tracing (LangSmith), Cost optimization | FastAPI, LangSmith, Structured logging (JSON), Monitoring dashboards, Docker, Load balancing | Deploy to production, Implement monitoring, Optimize performance, Handle production issues, Scale systems |
| **Week 17** | Agent Evaluation & Debugging | Pillar 5: Advanced Agentic Systems | Agent evaluation metrics, Debugging failures, Tracing & introspection, Error analysis & RCA, Regression testing, Behavior validation | LangSmith debugging, Structured logging, Evaluation frameworks, Unit testing, Integration testing | Evaluate systematically, Debug failures, Implement testing, Monitor health in production, Conduct RCA |
| **Week 18** | Ethics, Safety & Governance in Agentic AI | Pillar 6: Responsible AI & Applications | AI ethics frameworks, Bias detection & mitigation, Safety guardrails & constraints, Transparency & explainability, Responsible AI principles, Regulatory compliance | Safety validation frameworks, Bias detection tools, Adversarial testing, Governance frameworks | Build ethical systems, Implement guardrails, Detect & mitigate bias, Ensure transparency, Manage compliance |
| **Week 19** | Real-World Applications & Case Studies | Pillar 6: Responsible AI & Applications | Industry use cases (customer support, HR, finance, healthcare), Domain-specific design, Real-world constraints, Case study analysis, ROI & business impact | Domain-specific integrations, API connectors (Salesforce, Slack), Industry-specific RAG patterns | Apply to real domains, Design for business needs, Understand constraints, Learn from case studies, Calculate ROI |
| **Week 20** | Low-Code Tools Deep Dive | Pillar 6: Responsible AI & Applications | Low-code platforms, Visual workflow builders, No-code solutions, Integration platforms, Rapid prototyping & deployment | Low-code platforms, Visual builders, Integration marketplaces, Template-based solutions | Use low-code tools, Build without extensive coding, Leverage integrations, Accelerate time-to-market |

---

## 🔧 Technology Stack

The course uses:
- **Python** 3.10+
- **Jupyter Notebooks** (`.ipynb` files) for interactive learning
- **LangChain** - Agent orchestration and RAG frameworks
- **FastAPI** - Production API development
- **FAISS** - Vector indexing and retrieval
- **Streamlit** - Interactive UI development
- **LangSmith** - Observability and tracing
- **OpenAI API** - LLM integration (gpt-4o-mini, embeddings)
- **Various NLP libraries** - Document processing, embeddings, text operations

## 🎓 Learning Outcomes

By completing this course, you will:
- ✅ Understand the fundamentals of Agentic AI and agent design patterns
- ✅ Build and deploy autonomous AI agents using LangChain and AutoGen
- ✅ Implement retrieval-augmented generation (RAG) systems with vector databases
- ✅ Design scalable and production-ready agentic architectures
- ✅ Implement observability and monitoring for AI systems (LangSmith integration)
- ✅ Apply best practices in production environments
- ✅ Evaluate and iterate on agent performance
- ✅ Handle context awareness and multi-turn conversations
- ✅ Debug and troubleshoot complex agentic workflows
- ✅ Build specialized domain-specific agents

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Basic knowledge of Python and machine learning concepts
- OpenAI API key (for LLM access)
- Optional: LangChain API key for observability features

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ankur-bhattad/IITM_Agentic_AI_Training.git
   cd IITM_Agentic_AI_Training
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Study Path**: 
   - Follow materials sequentially by week
   - Start with Weekly Resources for conceptual foundation
   - Work through Assignments to practice skills
   - Complete Graded Projects for comprehensive evaluation

4. **Active Learning**: 
   - Run and modify notebooks to deepen understanding
   - Experiment with code examples
   - Submit graded projects as assigned

## 📚 File Format Guide

- **Jupyter Notebooks** (`.ipynb`): Interactive learning materials with code, explanations, and live demos
- **Python Scripts** (`.py`): Reusable utility functions, helpers, and production code
- **PDF Documents**: Source materials and official documentation (e.g., Amazon customer service guides)
- **Configuration Files** (`.env`): Environment setup for API keys (never committed to version control)
- **Documentation**: README files and guides within subdirectories

## 💡 Best Practices for Success

1. **Keep Up with Weekly Releases**: Check back regularly for new materials each week
2. **Hands-on Practice**: Run notebooks, modify code, and experiment to deepen understanding
3. **Complete Assignments**: Practice makes perfect—work through all exercises
4. **Project Submission**: Submit all graded projects as assigned for evaluation
5. **Review Advanced Sessions**: Study live session activities and masterclass materials for industry best practices
6. **Iterative Learning**: Reference earlier weeks when building on advanced concepts
7. **Observability**: Use provided tools (LangSmith) to monitor and debug your agents
8. **Debug Systematically**: Apply debugging frameworks from later weeks to troubleshoot complex issues

## 🔒 Security Best Practices

- **API Keys**: Never hard-code credentials; use `.env` files (listed in `.gitignore`)
- **Secret Management**: Follow `.env.example` template for safe credential handling
- **Environment Variables**: Use environment variables or Vocareum proxy settings for API access

## 🤝 Contributions & Questions

This is a course material repository maintained for educational purposes. 

For course-related questions or issues:
- Review existing materials and README files first
- Check Week-specific READMEs for detailed project instructions
- Reach out to the repository owner: **@ankur-bhattad**

## 📊 Repository Statistics

- **Language**: Python (Jupyter Notebooks primarily)
- **Repository Size**: ~80 MB
- **License**: See individual project documentation
- **Last Updated**: August 17, 2026

---

**Happy Learning! 🚀**

For detailed instructions on specific projects (e.g., Week 15 E-Commerce Project), refer to the README files within each project directory.
