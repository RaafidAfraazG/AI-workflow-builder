# AI Workflow Builder

A **No-Code Intelligent Workflow Builder** that empowers users to create sophisticated AI applications through a visual drag-and-drop interface. Connect intelligent components to build custom AI workflows that combine document knowledge, Large Language Models, and web search - all without writing code.

## 🎯 Use Cases

Create specialized AI assistants tailored to your needs: **Customer Support Chatbots**, **Document Q&A Systems**, **Research Assistants**, **FAQ Automation**, **Knowledge Management Solutions**, **Content Analysis Workflows**, **Technical Documentation Helpers**, **Learning Companions**, and more.

## 📸 Screenshots

<img width="960" height="415" alt="image" src="https://github.com/user-attachments/assets/f982cdc3-0521-4651-9a02-9d90f1046e2c" />

## 🌟 Key Features

- **🎨 Visual Drag & Drop Builder** - Intuitive React Flow interface for workflow creation
- **🧩 Smart Components** - Pre-built User Query, Knowledge Base, LLM Engine, and Output modules  
- **📄 Document Intelligence** - Upload and process PDFs, extract text, generate semantic embeddings
- **🤖 Multi-LLM Integration** - Support for OpenAI GPT, Google Gemini with customizable parameters
- **🔍 Real-time Web Search** - Built-in search capabilities via SerpAPI for up-to-date information
- **💬 Interactive Chat Interface** - Responsive chat UI with conversation history and rich formatting
- **✅ Smart Validation** - Real-time workflow validation and execution monitoring
- **🔄 Context Management** - Maintain conversation context across multi-turn interactions

## 🛠️ Technology Stack

**Frontend**
- React.js with modern hooks architecture
- React Flow for visual workflow building
- Tailwind CSS for responsive design
- Axios for seamless API communication

**Backend**
- FastAPI for high-performance REST APIs
- Asyncio for concurrent request handling
- Pydantic for robust data validation
- SQLAlchemy ORM for database operations

**AI & Machine Learning**
- OpenAI GPT models for natural language generation
- Google Gemini for advanced AI capabilities
- ChromaDB for vector storage and similarity search
- PyMuPDF for intelligent document processing
- Sentence Transformers for text embeddings

**Infrastructure**
- PostgreSQL for reliable data persistence
- Redis for caching and session management
- Docker support for easy deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL database
- Git

### Installation Steps

**Clone Repository**
```bash
git clone https://github.com/RaafidAfraazG/AI-workflow-builder.git
cd AI-workflow-builder
```

**Backend Setup**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend Setup**
```bash
cd frontend
npm install
npm start
```

## 💡 How It Works

**1. Design Phase**
- Drag components from the palette onto the canvas
- Connect components to define your AI workflow
- Configure each component's parameters and settings

**2. Validation & Testing**
- Click "Build" to validate component connections
- Use "Test Workflow" to run sample queries
- Debug and refine your workflow logic

**3. Deploy & Use**
- Launch your AI assistant with "Chat with Stack"
- Share workflows with team members
- Monitor usage and performance metrics

## 🌟 Why Choose AI Builder?

- **No Programming Required** - Visual interface eliminates coding barriers
- **Rapid Prototyping** - Build and test AI workflows in minutes
- **Enterprise Ready** - Scalable architecture with robust data handling
- **Flexible Integration** - Connect multiple AI services and data sources
- **Cost Effective** - Reduce development time and resources significantly

## 🤝 Contributing

We welcome contributions! Feel free to:
- Report bugs and suggest features via GitHub Issues
- Submit pull requests for improvements
- Share workflow templates with the community
- Contribute to documentation and tutorials
