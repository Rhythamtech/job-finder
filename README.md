# 🚀 JobFinder: Intelligent AI Job Search Agent

JobFinder is a powerful, LangGraph-driven conversational agent designed to streamline your job search. By combining the reasoning capabilities of LLMs with specialized scrapers for major job boards, JobFinder automates the tedious process of finding and filtering job listings based on your specific requirements.

## ✨ Features

- **🗣️ Conversational Interface**: Provide your job preferences (profile, location, experience, etc.) in natural language.
- **🧠 LLM-Powered Parsing**: Automatically extracts and structures your requirements using advanced language models.
- **🔍 Multi-Source Scraping**: Fetches the latest job listings from **Naukri** and **Hirist**.
- **🔄 Intelligent Workflow**: Managed by **LangGraph**, ensuring a robust, state-managed execution flow with human-in-the-loop capabilities.
- **💾 Persistent Sessions**: Uses **Redis** to save search states and thread history, allowing you to resume searches anytime.
- **📊 Refined Results**: Automatically cleanses, sorts, and formats job data for easy reading.

## 🛠️ Tech Stack

- **Core**: Python 3.12+
- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **AI Framework**: [LangChain](https://github.com/langchain-ai/langchain) & OpenAI SDK
- **Database**: Redis (for state check-pointing)
- **Scraping**: `requests`, `cloudscraper`
- **Environment**: `python-dotenv`

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher.
- A running Redis instance.
- API Access for your preferred LLM (OpenAI-compatible).

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd JobFinder
   ```

2. **Install dependencies**:
   It is recommended to use `uv` for lightning-fast dependency management:
   ```bash
   uv sync
   ```
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   # LLM Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o  # or your preferred model
   OPENAI_BASE_URL=https://api.openai.com/v1 # Optional

   # Database Configuration
   REDIS_URI=redis://localhost:6379

   # Scraper-Specific Config (if required)
   NAUKRI_NKPARAM=your_naukri_nkparam
   ```

### Running the Agent

Launch the main script to start the conversational search process:

```bash
python main.py
```

## 🧠 Workflow Visualization

The agent follows a structured graph-based workflow:

1. **Initialise**: Sets up the agent state.
2. **Collect Requirements**: Greets the user and asks for job preferences.
3. **Prepare Query**: LLM generates optimized search queries for different platforms.
4. **Scrape Jobs**: Multi-board parallelized scraping (Naukri, Hirist).
5. **Refine Data**: Cleans and sorts job postings based on relevance and experience.
6. **Format & Share**: Presents the curated list to the user.

*(You can find the workflow diagram in `graph_xray.png`)*

## 📂 Project Structure

- `main.py`: The entry point and LangGraph workflow definition.
- `scraper.py`: Contains specialized classes for scraping Naukri and Hirist.
- `utils.py`: Utility functions for LLM interaction and data parsing.
- `pyproject.toml`: Dependency management via `uv`.

---
Made with ❤️ for developers searching for their next adventure.
