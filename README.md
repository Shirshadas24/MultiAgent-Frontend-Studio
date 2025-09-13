# 🤖 MultiAgent Frontend Studio

**An AI-Powered Multi-Agent Frontend Development System**

AgentCode Frontend is an intelligent, multi-agent system that transforms natural language descriptions into production-ready frontend code. Built with LangGraph and Streamlit, it orchestrates specialized AI agents to enhance prompts, generate code, and validate results through an interactive workflow.

## ✨ Features

- **🧠 Multi-Agent Architecture**: Supervisor, Prompt Enhancer, Code Developer, and Validator agents working in harmony
- **📝 Intelligent Prompt Enhancement**: Automatically clarifies and expands vague requests
- **💻 Complete Frontend Generation**: Generates HTML, CSS, and JavaScript in one go
- **👀 Live Preview**: Real-time preview of generated frontend code
- **🔄 Interactive Feedback Loop**: Review, approve, or request changes seamlessly  
- **💾 Project Persistence**: Save and revisit your projects anytime
- **📁 Easy Export**: Download individual files or complete project packages
- **🗂️ Thread Management**: Multiple conversation threads with automatic naming
##  Demo
<img width="1360" height="593" alt="image" src="https://github.com/user-attachments/assets/ed4caa6a-bd88-4519-923d-1bf821ca3b88" />
<img width="866" height="241" alt="image" src="https://github.com/user-attachments/assets/0f37d0ab-8484-4eba-9325-3e1ba779eac8" />
<img width="1365" height="590" alt="image" src="https://github.com/user-attachments/assets/fff55f2c-5e95-464d-9cfa-d397fb51270e" />
<img width="1363" height="598" alt="image" src="https://github.com/user-attachments/assets/ecdc2982-e22e-43a2-94b5-9829f03e5525" />
<img width="1364" height="600" alt="image" src="https://github.com/user-attachments/assets/a101258a-4c02-4d84-a550-c1c5691a2634" />
<img width="1363" height="598" alt="image" src="https://github.com/user-attachments/assets/b4b2d4c6-cf1f-416a-a11f-c091ad504509" />
<img width="233" height="162" alt="image" src="https://github.com/user-attachments/assets/5489ab39-5e2e-4b13-8d2d-39ffa8f01ffa" />


## 🏗️ Architecture

### Agent Workflow
```
User Request → Supervisor →→ Code Developer → Validator → User Review → If "Ok" files download
              ↑ ↑       ↓                                           ↓
              ↑ Prompt Enhancer                                     ↓
              ↑                                                     ↓
               ←←←←←←←←←←← Feedback Loop (if changes needed) ←←←←←←←←←
```

### Specialized Agents
- **Supervisor**: Routes requests to appropriate agents based on context
- **Prompt Enhancer**: Clarifies ambiguous requests and fills in missing details
- **Code Developer**: Generates clean, production-ready HTML, CSS, and JavaScript
- **Validator**: Ensures code quality and relevance before user review

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API keys for Google Gemini and Cohere

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentcode-frontend.git
   cd agentcode-frontend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   GEMINI_API_KEY=your_gemini_api_key_here
   COHERE_API_KEY=your_cohere_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📋 Requirements

Create a `requirements.txt` file with:
```
streamlit>=1.28.0
langgraph>=0.2.0
langchain-core>=0.2.0
langchain-google-genai>=1.0.0
langchain-cohere>=0.1.0
langchain-groq>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0
sqlite3
ipython
```

## 🎯 Usage Examples

### Simple Landing Page
```
"Create a modern landing page for a tech startup with a hero section, features, and contact form"
```

### Interactive Dashboard
```
"Build a responsive admin dashboard with charts, tables, and a dark mode toggle"
```

### E-commerce Product Page
```
"Design a product showcase page with image gallery, reviews, and add to cart functionality"
```

## 🛠️ Project Structure

```
agentcode-frontend/
├── agent.py              # Multi-agent system logic
├── streamlit_app.py      # Streamlit frontend interface
├── .env                  # Environment variables (not in repo)
├── requirements.txt      # Python dependencies
├── chatbot.db           # SQLite database for persistence
└── README.md            # Project documentation
```

## 🔧 Configuration

The system uses multiple LLM providers for optimal performance:
- **Google Gemini**: Primary code generation and validation
- **Cohere**: Supervisor routing decisions
- **SQLite**: Conversation persistence and thread management

## 🌟 Key Features Explained

### Intelligent Routing
The Supervisor agent analyzes requests and routes them to the most appropriate specialist, ensuring efficient workflow progression.

### Prompt Enhancement
Transforms vague requests like "make a website" into detailed specifications with assumed best practices and modern design principles.

### Code Validation
Multi-layered validation ensures generated code is relevant, functional, and meets the user's requirements before final approval.

### Persistent Sessions
All conversations and projects are saved automatically, allowing users to return to previous work seamlessly.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Powered by [Streamlit](https://streamlit.io/) for the web interface
- Uses Google Gemini and Cohere APIs for AI capabilities

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the documentation
- Review existing discussions

---

**Made with ❤️ for developers who want to turn ideas into code instantly**
