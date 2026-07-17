# Summarize GitHub Repositories for Resume

This tool automatically fetches all your GitHub repositories (including public, private, and organizational ones) using the `gh` CLI credentials, retrieves their READMEs, and utilizes an OpenAI-compatible LLM to summarize each repository specifically tailored for software engineering resumes.

For each repository, the LLM extracts:
1. A concise 2-3 sentence project summary.
2. 3-4 key technical achievements, library usage, architectural highlights, or complex feature implementations.
3. A strong, action-verb-oriented resume bullet point (e.g., "Architected...", "Developed...").

---

## Features

- **GitHub CLI Integration:** Leverages your existing local `gh` auth credentials securely.
- **Organization & Private Repo Support:** Retrieves all repositories accessible by your GitHub account.
- **LLM Summarization:** Connects to any OpenAI-compatible API (e.g., OpenAI, DeepSeek, Gemini, etc.) to perform analysis.
- **Dry-Run Mode:** Includes a simulator that runs mock data through the LLM pipeline without calling the GitHub API.
- **Resilient Output:** Flushes output in real-time to a Markdown file (`repo_summaries.md`).

---

## Prerequisites

1. **GitHub CLI:** Install the GitHub CLI (`gh`) and authenticate:
   ```bash
   brew install gh # macOS
   gh auth login
   ```
2. **Python 3:** Ensure Python 3 is installed.

---

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tripasect/SummerizeGitHub4Resume.git
   cd SummerizeGitHub4Resume
   ```

2. **Set up virtual environment & install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   LLM_API_KEY=your_api_key_here
   LLM_BASE_URL=https://api.openai.com/v1 # or your provider's endpoint
   LLM_MODEL=gpt-4o # or whichever model you prefer
   ```

---

## Usage

### 1. Dry Run / Cold Run
Test your LLM API configuration and see example outputs using mock repository data:
```bash
python3 extract_repos.py --dry-run
```
This generates `dry_run_summaries.md`.

### 2. Full Run
Fetch all your actual GitHub repositories, download their READMEs, and generate summaries:
```bash
python3 extract_repos.py
```
This generates `repo_summaries.md` containing all summaries.

#### Limiting Repository Counts
If you have a large number of repositories and want to run a quick test on a subset, use the `--limit` flag:
```bash
python3 extract_repos.py --limit 5
```

---

## Output Format

The generated Markdown output files (`repo_summaries.md` and `dry_run_summaries.md`) look like this:

```markdown
## owner/repo-name (Python)
**Private:** False | **Stars:** 12 | **Forks:** 2
**URL:** https://github.com/owner/repo-name

[A concise 2-3 sentence project summary detailing the primary purpose and features.]

- Key tech achievement 1 (e.g., FastAPI backend with Asyncpg)
- Key tech achievement 2 (e.g., Integrated JWT authentication flow)
- Key tech achievement 3 (e.g., Designed CI/CD workflow with GitHub Actions)

* Developed a scalable RESTful API utilizing FastAPI and PostgreSQL, reducing latency by 15% through async database queries.
```
