#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from dotenv import load_dotenv
import httpx
from openai import OpenAI
from tqdm import tqdm

# Load environment variables from .env
load_dotenv()

def get_gh_token():
    """Retrieve GitHub token using the gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        if not token:
            raise ValueError("Token returned by 'gh auth token' is empty.")
        return token
    except Exception as e:
        print(f"Error retrieving GitHub token using 'gh auth token': {e}", file=sys.stderr)
        # Fallback to GITHUB_TOKEN environment variable if available
        fallback = os.environ.get("GITHUB_TOKEN")
        if fallback:
            print("Using fallback GITHUB_TOKEN environment variable.", file=sys.stderr)
            return fallback
        print("Please make sure you are logged in using 'gh auth login' or have GITHUB_TOKEN set.", file=sys.stderr)
        sys.exit(1)

def get_all_repositories(token):
    """Retrieve all repositories for the authenticated user, including private and org repos."""
    print("Fetching repositories list from GitHub...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    repos = []
    url = "https://api.github.com/user/repos"
    params = {
        "per_page": 100,
        "type": "all",
        "sort": "updated",
        "direction": "desc"
    }
    
    while url:
        response = httpx.get(url, headers=headers, params=params if url.endswith("/repos") else None)
        if response.status_code != 200:
            print(f"Error listing repositories: {response.status_code} - {response.text}", file=sys.stderr)
            sys.exit(1)
        
        repos.extend(response.json())
        
        # Check for pagination link header
        link_header = response.headers.get("Link")
        url = None
        if link_header:
            parts = link_header.split(",")
            for part in parts:
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip("<> ")
                    break

    return repos

def get_repo_readme(owner, repo_name, token):
    """Retrieve the raw content of README.md if it exists."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def summarize_repo_llm(client, model, repo_info, readme_content):
    """Summarize repository using the configured LLM for a resume-focused description."""
    prompt = f"""
You are an expert resume writer and technical career coach.
Summarize the following repository to extract its core essence ("the soul of the creation") for a professional software engineer resume.

Repository Details:
- Name: {repo_info['name']}
- Owner: {repo_info['owner']}
- Description: {repo_info.get('description') or 'No description provided.'}
- Primary Language: {repo_info.get('language') or 'Not specified'}
- Private: {repo_info.get('private', False)}
- Stars: {repo_info.get('stargazers_count', 0)}
- Forks: {repo_info.get('forks_count', 0)}

README Content (excerpt):
{readme_content[:3000] if readme_content else "No README content available."}

Instructions:
1. Provide a concise 2-3 sentence summary of the project, explaining what it is and the primary problem it solves.
2. List 3-4 bullet points highlighting key technical achievements, libraries/tools used, architecture patterns, or complex features implemented.
3. Write a one-liner resume bullet point starting with an action verb (e.g., "Architected...", "Developed...", "Designed...") that captures the highlight of this repository.
4. Keep the output clean, highly professional, and structured in Markdown.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional assistant summarizing software engineering projects for a resume."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary using LLM: {e}"

def run_dry_run(client, model):
    """Simulate execution using mock data to verify API and LLM functionality."""
    print("=== STARTING COLD-RUN / DRY-RUN ===")
    mock_repos = [
        {
            "name": "resume-builder-ai",
            "owner": "tripasect",
            "description": "An agentic AI app that automatically styles and customizes resumes based on job descriptions.",
            "language": "Python",
            "private": True,
            "stargazers_count": 12,
            "forks_count": 2,
            "mock_readme": """# Resume Builder AI
An AI-powered tool to automatically build tailored resumes.

## Features
- Integrates with Gemini/OpenAI API
- Uses FastAPI backend and Streamlit frontend
- Implements Retrieval-Augmented Generation (RAG) to scan PDFs
- Automatically formats output as LaTeX and PDF

## Tech Stack
- Python, FastAPI, Streamlit, LangChain, PyPDF, Weaviate
"""
        },
        {
            "name": "distributed-kv-store",
            "owner": "tech-org",
            "description": "High-performance distributed key-value store with Raft consensus implementation.",
            "language": "Go",
            "private": False,
            "stargazers_count": 150,
            "forks_count": 18,
            "mock_readme": """# Distributed KV Store
A lightweight distributed key-value store implementing the Raft consensus algorithm.

## Features
- Leader election and log replication
- Dynamic cluster membership changes
- gRPC communication layer
- Persistent storage using LSM-tree
"""
        }
    ]

    print(f"Mocked {len(mock_repos)} repositories for dry-run.")
    summaries = []
    
    for repo in mock_repos:
        print(f"\nSummarizing mock repository: {repo['owner']}/{repo['name']}...")
        summary = summarize_repo_llm(client, model, repo, repo["mock_readme"])
        summaries.append((repo, summary))
        
    # Write dry run summaries to console and file
    output_file = "dry_run_summaries.md"
    with open(output_file, "w") as f:
        f.write("# Dry Run: Repository Summaries\n\n")
        for repo, summary in summaries:
            header = f"## {repo['owner']}/{repo['name']} ({repo['language'] or 'Unknown'})\n"
            f.write(header)
            f.write(f"**Private:** {repo['private']} | **Stars:** {repo['stargazers_count']}\n\n")
            f.write(summary)
            f.write("\n\n---\n\n")
            
            # Print preview to console
            print("=" * 40)
            print(f"{repo['owner']}/{repo['name']}")
            print("=" * 40)
            print(summary)
            print("\n")

    print(f"=== DRY-RUN COMPLETED SUCCESSFULLY. Output saved to {output_file} ===")

def main():
    parser = argparse.ArgumentParser(description="Summarize GitHub repositories using an LLM.")
    parser.add_argument("--dry-run", action="store_true", help="Run a dry run with mock data to test the API and pipeline.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of repositories to process.")
    args = parser.parse_args()

    # Verify LLM config
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL", "auto")

    if not api_key:
        print("Error: LLM_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Initialize OpenAI-compatible client
    client = OpenAI(api_key=api_key, base_url=base_url)

    if args.dry_run:
        run_dry_run(client, model)
        return

    # Normal "hot-run" (disabled/warned as per instructions, but available when they run it manually later)
    token = get_gh_token()
    repos = get_all_repositories(token)
    
    print(f"Found {len(repos)} repositories.")
    if args.limit:
        print(f"Limiting run to the first {args.limit} repositories.")
        repos = repos[:args.limit]
    
    # Filter or process
    summaries = []
    
    output_file = "repo_summaries.md"
    print(f"Generating summaries and saving to {output_file}...")
    
    with open(output_file, "w") as f:
        f.write("# My GitHub Repositories Summaries\n")
        f.write("Generated automatically for resume optimization.\n\n")
        
        for repo in tqdm(repos, desc="Summarizing repositories"):
            owner = repo["owner"]["login"]
            name = repo["name"]
            
            readme = get_repo_readme(owner, name, token)
            
            # Simple repo dict for summary function
            repo_info = {
                "name": name,
                "owner": owner,
                "description": repo.get("description"),
                "language": repo.get("language"),
                "private": repo.get("private"),
                "stargazers_count": repo.get("stargazers_count"),
                "forks_count": repo.get("forks_count")
            }
            
            summary = summarize_repo_llm(client, model, repo_info, readme)
            
            f.write(f"## {owner}/{name} ({repo_info['language'] or 'Unknown'})\n")
            f.write(f"**Private:** {repo_info['private']} | **Stars:** {repo_info['stargazers_count']} | **Forks:** {repo_info['forks_count']}\n")
            f.write(f"**URL:** {repo.get('html_url')}\n\n")
            f.write(summary)
            f.write("\n\n---\n\n")
            f.flush()
            
    print(f"Done! Summaries saved to {output_file}.")

if __name__ == "__main__":
    main()
