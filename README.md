# Multi-Agent Coding Framework

A fully functional, end-to-end Multi-Agent system that simulates a real-world software development lifecycle using collaborating AI agents. Each agent performs a specific role in a structured pipeline, from requirement analysis to deployment configuration.

## 🤖 Overview

This framework implements a complete software development pipeline using multiple specialized AI agents that collaborate to transform natural language requirements into production-ready code, documentation, tests, and deployment configurations.

## 🏗️ Architecture

The system follows a strict pipeline architecture where agents work sequentially, with the Code Review Agent enforcing quality through iterative feedback loops.

```
User Input → Requirement Analysis → Code Generation → Code Review (with iteration) → Documentation → Test Generation → Deployment Configuration → Output
```

## 👥 Agents

### 1. Requirement Analysis Agent
**Responsibility:** Converts natural-language user input into structured software requirements.

### 2. Coding Agent
**Responsibility:** Converts refined requirements into clean, modular Python code following best practices.

### 3. Code Review Agent (CRITICAL)
**Responsibility:** Reviews generated code for correctness, efficiency, security, and edge cases.

### 4. Documentation Agent
**Responsibility:** Generates clear, structured Markdown documentation.

### 5. Test Case Generation Agent
**Responsibility:** Generates executable pytest test cases.

### 6. Deployment Configuration Agent
**Responsibility:** Generates deployment files and instructions.

### 7. Streamlit UI Agent
**Responsibility:** Provides interactive web interface for the entire workflow.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10 or higher
- OpenAI API key

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Multi-agent-pipeline
   ```

2. **Create a clean virtual environment (recommended to avoid dependency conflicts):**
   ```bash
   python -m venv venv
   ```
   
   **Important:** Using a fresh virtual environment prevents conflicts with other packages (like mcp, mistralai) that may be installed in your system Python.

3. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **Important:** Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## 🎯 Usage

### Running the Streamlit Application

**Option 1: Using the run script (Recommended)**

  ```bash
  ./run.sh
  ```

**Option 2: Manual execution**

1. Activate your virtual environment
2. Run:
   ```bash
   streamlit run app.py
   ```

3. The application will open in your default web browser at `http://localhost:8501`

### Using the Framework

1. **Enter Requirements:** Type your software requirements in natural language in the text area
2. **Generate Code:** Click the "Generate Code" button
3. **Review Outputs:** The system will display outputs from each agent:
   - Refined requirements
   - Generated code
   - Review feedback (with iteration history)
   - Documentation
   - Test cases
   - Deployment instructions
4. **Download Files:** Use the download buttons to save generated files

### Example Input

```
Create a Python calculator that can perform basic arithmetic operations 
(addition, subtraction, multiplication, division) with error handling 
for division by zero. The calculator should accept two numbers and an 
operation as input.
```

## 🧪 Testing

The framework generates test cases for the code it creates. These test cases are included in the output and can be executed using pytest.

**To run the generated test cases:**
1. Save the generated code to a file (e.g., `generated_code.py`)
2. Save the generated test cases to `test_generated_code.py`
3. Run: `pytest test_generated_code.py -v`

The generated test cases include expected execution results in comments, showing what each test should produce when executed.

## 📁 Project Structure

```
Multi-agent-system/
├── agents/
│   ├── __init__.py
│   ├── requirement_agent.py      # Requirement Analysis Agent
│   ├── coding_agent.py            # Code Generation Agent
│   ├── review_agent.py             # Code Review Agent
│   ├── documentation_agent.py     # Documentation Agent
│   ├── test_agent.py              # Test Generation Agent
│   └── deployment_agent.py       # Deployment Configuration Agent
├── utils/
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   └── logger.py                  # Enhanced logging utilities
├── orchestrator.py                # Central pipeline orchestrator
├── app.py                         # Streamlit UI application
├── requirements.txt               # Python dependencies
├── run.sh                         # Run script (Linux/Mac)
├── run.bat                        # Run script (Windows)
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## ⚙️ Configuration

Configuration is managed in `utils/config.py`:

- **MODEL:** OpenAI model to use (default: `gpt-4`)
- **TEMPERATURE:** LLM temperature (default: `0.7`)
- **MAX_ITERATIONS:** Maximum code review iterations (default: `5`)
- **MAX_TOKENS:** Maximum tokens per request (default: `4000`)

## 🔄 Agent Collaboration Rules

1. **Strict Pipeline:** Agents run sequentially in a fixed order
2. **No Skipping:** No agent may skip another
3. **Iterative Review:** Code Review Agent can force re-coding
4. **Central Control:** Orchestrator manages execution flow
5. **Quality Enforcement:** Iteration continues until code passes review

## 📊 Data Flow

```
User Input (Natural Language)
    ↓
Requirement Analysis Agent
    ↓
Structured Requirements (JSON)
    ↓
Coding Agent
    ↓
Generated Code
    ↓
Code Review Agent → [Iteration Loop] → Approved Code
    ↓
Documentation Agent → Markdown Documentation
    ↓
Test Generation Agent → Pytest Test Cases
    ↓
Deployment Agent → Deployment Files
    ↓
Streamlit UI → Display All Outputs
```

## 🛠️ Technology Stack

- **Language:** Python 3.10+
- **Multi-Agent Framework:** AutoGen
- **LLM Provider:** OpenAI GPT-4 family models only
- **UI:** Streamlit
- **Testing:** pytest
- **Documentation:** Markdown

## ⚠️ Important Notes

- **API Key:** Never commit your `.env` file with the API key
- **Model:** Only OpenAI GPT-4 models are supported (no Claude, Mistral, LLaMA)
- **Iterations:** The system will iterate up to 5 times to get code approval
- **Costs:** Be aware of OpenAI API usage costs when running the framework

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

Built using:
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent conversation framework
- [OpenAI](https://openai.com/) - GPT-4 models
- [Streamlit](https://streamlit.io/) - Web application framework
- [pytest](https://pytest.org/) - Testing framework

---
