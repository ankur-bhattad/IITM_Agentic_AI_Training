# IITM Agentic AI Training

Repository for IITM Emeritus Course In Agentic AI Material

## 📚 Course Overview

This repository contains comprehensive learning materials, assignments, projects, and live session activities for the IITM Emeritus Course in Agentic AI. The course is actively ongoing, with weekly materials and advanced topics covered throughout the curriculum.

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

| **Week** | **Title** | **Key Concepts** | **Technologies & Tools** | **Learning Outcomes** |
|----------|-----------|-----------------|-------------------------|----------------------|
| **Week 1** | Getting Started with Python & ChatGPT | - Python environment setup<br>- ChatGPT & LLMs fundamentals<br>- Prompt engineering basics<br>- API integration | - Python 3.10+<br>- OpenAI API<br>- Jupyter Notebooks<br>- pip & virtual environments | - Set up Python development environment<br>- Understand LLM capabilities and limitations<br>- Write effective prompts<br>- Integrate OpenAI API into Python scripts |
| **Week 2** | Data Types, Variables, Control Flow & Functions | - Python data types (int, float, str, list, dict, tuple)<br>- Variable assignment and scoping<br>- Control flow (if/else, loops)<br>- Function definition and parameters<br>- Error handling basics | - Python standard library<br>- Jupyter Notebooks<br>- IDE/Text editor<br>- Python debugger (pdb) | - Master Python data structures<br>- Write clean, reusable functions<br>- Implement robust error handling<br>- Debug Python code effectively |
| **Week 3** | Working with Libraries | - Popular libraries (NumPy, Pandas, Requests)<br>- Dependency management and pip<br>- Working with APIs<br>- Data manipulation and analysis<br>- File I/O operations | - NumPy<br>- Pandas<br>- Requests<br>- pip & requirements.txt<br>- JSON/CSV file formats | - Leverage NumPy for numerical computing<br>- Manipulate data with Pandas<br>- Make API requests with Requests<br>- Manage project dependencies effectively |
| **Week 4** | Fundamentals of AI & ML | - Supervised vs. unsupervised learning<br>- Classification & regression tasks<br>- Train-test split<br>- Neural networks introduction<br>- Evaluation metrics (accuracy, precision, recall, F1) | - scikit-learn<br>- TensorFlow/Keras<br>- Matplotlib for visualization<br>- NumPy & Pandas<br>- ML workflow tools | - Understand ML fundamentals<br>- Build and evaluate classification models<br>- Implement train-test split correctly<br>- Understand neural network basics |
| **Week 5** | Large Language Models (LLMs) | - How LLMs work (transformers architecture)<br>- Model scaling and emergence<br>- Tokenization and embeddings<br>- Fine-tuning vs. prompt engineering<br>- Token limits and cost optimization | - OpenAI API (GPT-4, GPT-3.5)<br>- Hugging Face Transformers<br>- Tokenizers<br>- TensorFlow/PyTorch<br>- LangChain | - Understand transformer architecture fundamentals<br>- Work with embeddings effectively<br>- Optimize prompts for LLMs<br>- Calculate and manage token usage<br>- Understand fine-tuning trade-offs |
| **Week 6** | Embedding Models & Vector Basics | - Vector representations of text<br>- Semantic similarity concepts<br>- Vector databases and indexing<br>- Similarity search algorithms<br>- Dimensionality reduction | - OpenAI Embeddings API<br>- FAISS (Facebook AI Similarity Search)<br>- Pinecone<br>- Weaviate<br>- NumPy for vector operations | - Create embeddings for text<br>- Understand vector similarity metrics<br>- Build vector databases<br>- Implement semantic search<br>- Optimize vector indexing |
| **Week 7** | Agentic Tools in Python | - Tool definition and design patterns<br>- Function calling and tool use<br>- Error handling in tool execution<br>- Stateless vs. stateful tools<br>- Tool composition and chaining | - Python functions & decorators<br>- Type hints & pydantic<br>- LangChain Tools<br>- FastAPI for tool APIs<br>- JSON schema validation | - Design reusable tools<br>- Implement proper error handling<br>- Create tool interfaces with type safety<br>- Chain tools together<br>- Document tools effectively |
| **Week 8** | Introduction to Agentic AI | - What is an agent?<br>- Agent loop and reasoning cycle<br>- Perception-reasoning-action paradigm<br>- Agent vs. chatbot differences<br>- Common design patterns | - LangChain Agents<br>- AutoGen<br>- LLMs (GPT-4, Claude)<br>- Agent frameworks<br>- Logging and debugging tools | - Understand agent architecture<br>- Implement basic agent loops<br>- Distinguish agents from chatbots<br>- Apply common agent design patterns<br>- Debug agent behavior |
| **Week 9** | Programming & Frameworks for Agentic Systems | - Agentic frameworks & libraries<br>- Orchestration and workflow design<br>- Agent memory and context management<br>- Asynchronous programming for agents<br>- State management | - LangChain<br>- AutoGen<br>- Crew AI<br>- FastAPI<br>- AsyncIO & concurrent.futures<br>- Redis for state management | - Select and use appropriate frameworks<br>- Design agent workflows<br>- Implement agent memory systems<br>- Write async agent code<br>- Manage agent state effectively |
| **Week 10** | Agent Architectures & Collaboration | - Single-agent architectures (ReAct)<br>- Multi-agent systems<br>- Agent specialization and roles<br>- Inter-agent communication<br>- Collaboration patterns | - LangChain Agent architectures<br>- AutoGen multi-agent systems<br>- Message passing systems<br>- Pub-Sub patterns<br>- Agent communication protocols | - Design single and multi-agent systems<br>- Implement agent roles<br>- Enable agent communication<br>- Handle inter-agent coordination<br>- Scale agent systems |
| **Week 11** | Decision-Making & Planning in Agents | - Goal decomposition and planning<br>- Tree-of-thought reasoning<br>- Chain-of-thought (CoT) reasoning<br>- Decision trees and state machines<br>- Constraint satisfaction | - LangChain planning chains<br>- Tree-of-thought libraries<br>- Decision tree frameworks<br>- State machine libraries<br>- Constraint programming | - Implement planning algorithms<br>- Use reasoning frameworks effectively<br>- Handle complex decision-making<br>- Decompose goals hierarchically<br>- Apply constraints to agent decisions |
| **Week 12** | Memory & Knowledge Retrieval in Agents with MCP | - Short-term vs. long-term memory<br>- Memory types (episodic, semantic, procedural)<br>- Knowledge graphs<br>- Model Context Protocol (MCP)<br>- Information retrieval techniques | - LangChain Memory modules<br>- FAISS & vector databases<br>- Neo4j for knowledge graphs<br>- Model Context Protocol (MCP)<br>- LangSmith for memory management | - Implement memory systems<br>- Use knowledge graphs effectively<br>- Integrate MCP for context<br>- Build retrieval systems<br>- Manage memory efficiency |
| **Week 13** | Prompt Engineering & Adaptive Instructions (Streamlit) | - Advanced prompting techniques<br>- Few-shot and zero-shot learning<br>- Instruction tuning<br>- Dynamic prompt adaptation<br>- Prompt templates and versioning | - Streamlit<br>- Prompt templates (LangChain)<br>- LLMs (GPT-4, Claude)<br>- Jinja2 templating<br>- Prompt management tools | - Write effective system prompts<br>- Apply few-shot learning<br>- Create dynamic prompts<br>- Build interactive prompt tools<br>- Version and test prompts |
| **Week 14** | Learning & Adaptation in Agents | - Agent self-improvement<br>- Feedback loops and iterative refinement<br>- Fine-tuning vs. in-context learning<br>- Reinforcement learning basics<br>- Online learning strategies | - LangChain feedback loops<br>- LangSmith for evaluation<br>- Fine-tuning APIs<br>- Reinforcement learning libraries<br>- Experiment tracking tools | - Implement feedback mechanisms<br>- Build iterative improvement systems<br>- Choose between fine-tuning approaches<br>- Apply reinforcement learning<br>- Track agent improvements |
| **Week 15** | Advanced Retrieval-Augmented Generation (RAG) | - RAG architecture and workflow<br>- Document chunking strategies<br>- Embedding strategies<br>- Retrieval optimization and ranking<br>- Evaluation metrics for RAG | - LangChain RAG chains<br>- FAISS & Pinecone<br>- Document loaders (PyMuPDF)<br>- Embedding models (OpenAI, Ollama)<br>- Streamlit for UI<br>- Evaluation frameworks | - Build end-to-end RAG systems<br>- Optimize document retrieval<br>- Implement hybrid search<br>- Evaluate RAG performance<br>- Handle multi-document queries |
| **Week 16** | Deploying & Monitoring Agentic Systems | - Production deployment patterns<br>- API design (FastAPI, REST)<br>- Monitoring and observability<br>- Performance metrics<br>- Scaling strategies | - FastAPI<br>- Docker<br>- LangSmith for observability<br>- Logging frameworks<br>- Monitoring tools (Prometheus, Grafana)<br>- Cloud deployment (AWS, GCP, Azure) | - Deploy agents to production<br>- Design scalable APIs<br>- Implement observability<br>- Monitor agent performance<br>- Scale systems effectively |
| **Week 17** | Agent Evaluation & Debugging | - Agent evaluation metrics<br>- Debugging failures and issues<br>- Tracing and introspection<br>- Error analysis and root cause analysis (RCA)<br>- Regression testing | - LangSmith tracing<br>- Custom evaluation frameworks<br>- Logging and debugging tools<br>- Error analysis tools<br>- Testing frameworks (pytest)<br>- Visualization tools | - Evaluate agent performance<br>- Debug complex agent issues<br>- Implement tracing systems<br>- Perform root cause analysis<br>- Build regression test suites |
| **Week 18** | Ethics, Safety & Governance in Agentic AI | - AI ethics frameworks<br>- Bias detection and mitigation<br>- Safety guardrails and constraints<br>- Transparency and explainability<br>- Regulatory compliance | - AI ethics toolkits<br>- Bias detection libraries<br>- Safety guardrail frameworks<br>- Audit logging systems<br>- Compliance tools | - Apply ethics frameworks<br>- Detect and mitigate bias<br>- Implement safety guardrails<br>- Ensure transparency<br>- Meet regulatory requirements |
| **Week 19** | Real-World Applications & Case Studies | - Industry use cases (customer support, HR, finance, healthcare)<br>- Domain-specific design<br>- Real-world challenges and solutions<br>- Case study analysis<br>- Lessons learned | - Domain-specific APIs<br>- Integration platforms<br>- Industry tools and frameworks<br>- Case study resources<br>- Real-world datasets | - Apply agents to real domains<br>- Solve domain-specific challenges<br>- Analyze real-world case studies<br>- Design domain-specific agents<br>- Handle production edge cases |
| **Week 20** | Low-Code Tools Deep Dive | - Low-code platforms and tools<br>- Visual workflow builders<br>- No-code solutions<br>- Integration platforms<br>- Rapid prototyping and deployment | - Low-code platforms (Make.com, Zapier)<br>- Visual builders (Flowise, n8n)<br>- No-code tools<br>- Integration APIs<br>- Rapid deployment frameworks | - Use low-code platforms effectively<br>- Build workflows visually<br>- Integrate systems easily<br>- Prototype quickly<br>- Deploy without coding |

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
