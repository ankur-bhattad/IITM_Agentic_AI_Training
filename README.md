# IITM Agentic AI Training

Repository for IITM Emeritus Course In Agentic AI Material

## 📚 Course Overview

This repository contains comprehensive learning materials, assignments, projects, and live session activities for the IITM Emeritus Course in Agentic AI. The course is actively ongoing, with weekly materials covering fundamentals through advanced production systems.

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

### **Pillar 1: Python Foundations (Weeks 1-3)**

#### **Week 1: Getting Started with Python & ChatGPT**
- **Key Concepts:**
  - Python environment setup and basics
  - Introduction to ChatGPT and Large Language Models
  - Prompt engineering fundamentals
  - API integration with ChatGPT
  
- **Technologies & Tools:**
  - Python 3.10+
  - OpenAI API
  - Jupyter Notebooks for interactive learning
  - Virtual environments and package management
  
- **Learning Outcomes:**
  - Set up Python development environment
  - Make your first API call to ChatGPT
  - Understand basic prompt structure and best practices
  - Run and modify simple code examples

#### **Week 2: Data Types, Variables, Control Flow & Functions**
- **Key Concepts:**
  - Python data types (strings, lists, dictionaries, tuples)
  - Variable assignment and naming conventions
  - Control flow (if/else, loops)
  - Function definition and usage
  - Error handling basics
  
- **Technologies & Tools:**
  - Python built-in functions and methods
  - List/dictionary comprehensions
  - Exception handling
  
- **Learning Outcomes:**
  - Work with different data structures effectively
  - Write reusable functions and modules
  - Handle control flow in complex programs
  - Implement error handling strategies

#### **Week 3: Working with Libraries**
- **Key Concepts:**
  - Popular Python libraries (NumPy, Pandas, Requests)
  - Library installation and dependency management
  - Working with external APIs
  - Data manipulation and processing
  
- **Technologies & Tools:**
  - NumPy for numerical computing
  - Pandas for data analysis
  - Requests for HTTP calls
  - pip and package management
  
- **Learning Outcomes:**
  - Install and use external libraries
  - Perform data manipulation operations
  - Make and handle API requests
  - Work with structured data

---

### **Week 4: Fundamentals of AI & ML**
- **Key Concepts:**
  - Machine Learning basics (supervised, unsupervised learning)
  - Classification and regression tasks
  - Train-test split and model evaluation
  - Introduction to neural networks
  - Basic evaluation metrics
  
- **Technologies & Tools:**
  - Scikit-learn for ML models
  - Model training and evaluation
  - Hyperparameter tuning basics
  
- **Learning Outcomes:**
  - Build and train basic ML models
  - Evaluate model performance
  - Understand ML workflow end-to-end
  - Apply ML concepts to real-world problems

---

### **Week 5: Large Language Models (LLMs)**
- **Key Concepts:**
  - How LLMs work (transformer architecture overview)
  - Model scaling and emergence
  - Tokenization and embeddings
  - Fine-tuning vs. prompt engineering trade-offs
  - Token limits and context windows
  
- **Technologies & Tools:**
  - OpenAI API (GPT-4o-mini, text-embedding-3-small)
  - Tokenization libraries
  - Embedding models
  - LLM cost considerations
  
- **Learning Outcomes:**
  - Understand LLM capabilities and limitations
  - Work with embeddings for semantic search
  - Optimize prompts for better responses
  - Manage API usage and costs

#### **Week 6: Embedding Models & Vector Basics**
- **Key Concepts:**
  - Vector representations of text
  - Semantic similarity and cosine distance
  - Vector databases and indexing
  - Similarity search techniques
  - Dimensionality and computational efficiency
  
- **Technologies & Tools:**
  - OpenAI embeddings
  - FAISS for vector indexing
  - Vector similarity metrics
  - Vector database basics
  
- **Learning Outcomes:**
  - Generate and work with text embeddings
  - Implement semantic search
  - Index and query large vector datasets
  - Measure semantic similarity

---

### **Pillar 3: Introduction to Agentic AI (Weeks 7-9)**

#### **Week 7: Agentic Tools in Python**
- **Key Concepts:**
  - Tool definition and design
  - Function calling / tool use
  - Error handling in tool execution
  - Stateless vs. stateful tools
  - Tool composition patterns
  
- **Technologies & Tools:**
  - LangChain tool decorators
  - Tool definition frameworks
  - Function schema generation
  - Tool validation
  
- **Learning Outcomes:**
  - Define and implement custom tools
  - Integrate tools with LLM function calling
  - Handle tool errors gracefully
  - Chain multiple tools together

#### **Week 8: Introduction to Agentic AI**
- **Key Concepts:**
  - What is an agent? (Autonomous decision-making systems)
  - Agent loop and reasoning cycle
  - Perception, reasoning, and action
  - Agent vs. traditional chatbot
  - Agent design patterns
  
- **Technologies & Tools:**
  - Agent frameworks overview
  - LangChain agents (ReAct pattern)
  - Agent state management
  - LLM as the reasoning engine
  
- **Learning Outcomes:**
  - Understand agent architecture principles
  - Build your first autonomous agent
  - Implement the perception-reasoning-action loop
  - Design agent workflows

#### **Week 9: Programming & Frameworks for Agentic Systems**
- **Key Concepts:**
  - Agentic AI frameworks and libraries
  - Orchestration and workflow design
  - Agent memory and context management
  - Asynchronous operations in agents
  - Production considerations
  
- **Technologies & Tools:**
  - LangChain for agent orchestration
  - AutoGen for multi-agent systems
  - FastAPI for agent APIs
  - Message queues for agent communication
  
- **Learning Outcomes:**
  - Use agentic frameworks effectively
  - Design and build complex agent workflows
  - Implement agent memory systems
  - Deploy agents at scale

---

### **Week 10: Agent Architectures & Collaboration**
- **Key Concepts:**
  - Single-agent architectures (ReAct, Tool-using)
  - Multi-agent systems and collaboration
  - Agent specialization and roles
  - Inter-agent communication patterns
  - Hierarchical agent structures
  
- **Technologies & Tools:**
  - LangChain hierarchical agents
  - AutoGen multi-agent framework
  - Agent message protocols
  - Supervision patterns
  
- **Learning Outcomes:**
  - Design both single and multi-agent systems
  - Implement agent collaboration
  - Debug multi-agent interactions
  - Scale agent systems

---

### **Pillar 4: Advanced Agent Patterns (Weeks 11-14)**

#### **Week 11: Decision-Making & Planning in Agents**
- **Key Concepts:**
  - Goal decomposition and planning
  - Tree-of-thought and chain-of-thought reasoning
  - Decision trees and state management
  - Constraint satisfaction in agent planning
  - Exploration vs. exploitation trade-offs
  
- **Technologies & Tools:**
  - Planning algorithms (BFS, DFS, A*)
  - LLM-based planning
  - State space exploration
  - Constraint frameworks
  
- **Learning Outcomes:**
  - Implement goal decomposition
  - Use advanced reasoning strategies
  - Design decision-making systems
  - Handle complex planning scenarios

#### **Week 12: Memory & Knowledge Retrieval in Agents with MCP**
- **Key Concepts:**
  - Short-term vs. long-term memory
  - Memory types (episodic, semantic, procedural)
  - Knowledge graph integration
  - Information retrieval from memory
  - Model Context Protocol (MCP) for tool integration
  
- **Technologies & Tools:**
  - Vector stores for semantic memory
  - Knowledge graphs (Neo4j, etc.)
  - MCP servers and clients
  - Memory optimization techniques
  
- **Learning Outcomes:**
  - Build memory systems for agents
  - Integrate knowledge bases
  - Use MCP for standardized tool integration
  - Implement efficient retrieval

#### **Week 13: Prompt Engineering & Adaptive Instructions (Streamlit)**
- **Key Concepts:**
  - Advanced prompt engineering techniques
  - Few-shot and zero-shot prompting
  - Instruction tuning without fine-tuning
  - Dynamic prompt adaptation
  - Instruction formatting and chain-of-thought
  
- **Technologies & Tools:**
  - Prompt engineering frameworks
  - Streamlit for interactive demos
  - Prompt versioning and testing
  - Few-shot example selection
  
- **Learning Outcomes:**
  - Master advanced prompting techniques
  - Create adaptive instruction systems
  - Build interactive prompt testing UIs
  - Evaluate prompt effectiveness

#### **Week 14: Learning & Adaptation in Agents**
- **Key Concepts:**
  - Agent self-improvement mechanisms
  - Feedback loops and iterative refinement
  - Fine-tuning vs. in-context learning
  - Reinforcement learning from feedback
  - Continuous agent evolution
  
- **Technologies & Tools:**
  - RLHF (Reinforcement Learning from Human Feedback)
  - Model fine-tuning APIs
  - Feedback collection mechanisms
  - Evaluation metrics for agent performance
  
- **Learning Outcomes:**
  - Implement feedback loops in agents
  - Enable agent self-improvement
  - Evaluate and iterate on agent behavior
  - Deploy continuously improving agents

---

### **Pillar 5: Advanced Agentic Systems (Weeks 15-17)**

#### **Week 15: Advanced Retrieval-Augmented Generation (RAG)**
- **Key Concepts:**
  - RAG architecture and workflow
  - Document chunking and embedding strategies
  - Retrieval optimization and ranking
  - Hybrid search (BM25 + semantic)
  - Handling multi-document reasoning
  - RAG for domain-specific knowledge
  
- **Technologies & Tools:**
  - FAISS for vector indexing
  - LangChain RAG chains
  - Document loaders (PDF, web, etc.)
  - Hybrid retrieval strategies
  - Multi-hop retrieval
  
- **Learning Outcomes:**
  - Build production-grade RAG systems
  - Optimize retrieval quality
  - Handle complex document scenarios
  - Implement multi-turn RAG interactions
  - Create domain-specific assistants

#### **Week 16: Deploying & Monitoring Agentic Systems**
- **Key Concepts:**
  - Production deployment patterns
  - API design for agents (FastAPI, REST)
  - Monitoring and observability
  - Performance metrics and SLAs
  - Logging and tracing (LangSmith)
  - Cost optimization in production
  
- **Technologies & Tools:**
  - FastAPI for production APIs
  - LangSmith for observability and tracing
  - Structured logging (JSON)
  - Monitoring dashboards
  - Container deployment (Docker)
  - Load balancing and scaling
  
- **Learning Outcomes:**
  - Deploy agents to production
  - Implement comprehensive monitoring
  - Optimize agent performance
  - Handle production issues
  - Scale agent systems

#### **Week 17: Agent Evaluation & Debugging**
- **Key Concepts:**
  - Agent evaluation metrics
  - Debugging agent failures
  - Tracing and introspection
  - Error analysis and root cause analysis
  - Regression testing for agents
  - Agent behavior validation
  
- **Technologies & Tools:**
  - LangSmith debugging tools
  - Structured logging for analysis
  - Evaluation frameworks
  - Unit testing for agents
  - Integration testing patterns
  
- **Learning Outcomes:**
  - Evaluate agent performance systematically
  - Debug complex agent failures
  - Implement comprehensive testing
  - Monitor agent health in production
  - Conduct root cause analysis

---

### **Pillar 6: Responsible AI & Applications (Weeks 18-20)**

#### **Week 18: Ethics, Safety & Governance in Agentic AI**
- **Key Concepts:**
  - AI ethics frameworks
  - Bias detection and mitigation
  - Safety guardrails and constraints
  - Transparency and explainability
  - Responsible AI principles
  - Regulatory compliance (GDPR, etc.)
  
- **Technologies & Tools:**
  - Safety validation frameworks
  - Bias detection tools
  - Adversarial testing
  - Governance frameworks
  
- **Learning Outcomes:**
  - Build ethical AI systems
  - Implement safety guardrails
  - Detect and mitigate bias
  - Ensure transparency
  - Manage compliance

#### **Week 19: Real-World Applications & Case Studies**
- **Key Concepts:**
  - Industry use cases (customer support, HR, finance, healthcare)
  - Domain-specific agent design
  - Real-world constraints and considerations
  - Case study analysis and lessons learned
  - ROI and business impact
  
- **Technologies & Tools:**
  - Domain-specific integrations
  - API connectors (Salesforce, Slack, etc.)
  - Industry-specific RAG patterns
  
- **Learning Outcomes:**
  - Apply agentic AI to real domains
  - Design for specific business needs
  - Understand domain constraints
  - Learn from industry case studies
  - Calculate ROI and impact

#### **Week 20: Low-Code Tools Deep Dive**
- **Key Concepts:**
  - Low-code platforms for agent building
  - Visual workflow builders
  - No-code solutions for non-developers
  - Integration platforms
  - Rapid prototyping and deployment
  
- **Technologies & Tools:**
  - Low-code agent platforms
  - Visual workflow builders
  - Integration marketplaces
  - Template-based solutions
  
- **Learning Outcomes:**
  - Use low-code tools for rapid development
  - Build agents without extensive coding
  - Leverage pre-built integrations
  - Accelerate time-to-market

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

## 📅 Current Progress

**Course Status**: Actively ongoing (20+ weeks completed)

The course covers:
- **Weeks 1-4**: Fundamentals & Core Concepts
- **Weeks 5-8**: Agent Architectures (LangChain, AutoGen)
- **Weeks 9-12**: Advanced Agent Patterns & RAG Implementation
- **Weeks 13-16**: Production Systems, Observability, and Deployment
- **Weeks 17-20**: Advanced Debugging, Agentic Workflows, and Specialized Applications

Materials are progressively released week by week as the course advances.

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
