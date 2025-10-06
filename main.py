import os
import json
import git
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GitLab MR Review Bot", version="1.0.0")

# Configuration
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "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",
)
REPO_PATH = "./repo"
BOT_CONFIG_FILE = "md.rbot"


class GitLabWebhook(BaseModel):
    object_kind: str
    project: Dict[str, Any]
    object_attributes: Dict[str, Any]
    changes: Optional[Dict[str, Any]] = None


class CodeReview(BaseModel):
    """AI-powered code review with structured feedback"""

    summary: str
    issues: list[str]
    suggestions: list[str]
    security_concerns: list[str]
    performance_notes: list[str]
    code_quality_score: int  # 1-10 scale


class RuleEngine:
    """Handles bot-level and project-level rules"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.bot_rules = self._load_bot_rules()
        self.project_rules = self._load_project_rules()

    def _load_bot_rules(self) -> Dict[str, Any]:
        """Load bot-level rules from environment or config"""
        return {
            "max_file_size": 1000,  # lines
            "security_checks": True,
            "performance_checks": True,
            "code_quality_checks": True,
            "language_specific_rules": {
                "python": ["check_imports", "check_docstrings"],
                "javascript": ["check_eslint", "check_async"],
                "java": ["check_annotations", "check_exceptions"],
            },
        }

    def _load_project_rules(self) -> Dict[str, Any]:
        """Load project-specific rules from md.rbot file"""
        rbot_file = Path(self.repo_path) / BOT_CONFIG_FILE
        if rbot_file.exists():
            try:
                with open(rbot_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def get_effective_rules(self) -> Dict[str, Any]:
        """Combine bot and project rules with project rules taking precedence"""
        rules = self.bot_rules.copy()
        rules.update(self.project_rules)
        return rules


class GitLabClient:
    """Handles GitLab API interactions"""

    def __init__(self, project_id: str, access_token: Optional[str] = None):
        self.project_id = project_id
        self.access_token = access_token
        self.base_url = "https://gitlab.com/api/v4"

    async def get_merge_request(self, mr_iid: int) -> Dict[str, Any]:
        """Fetch merge request details"""
        async with httpx.AsyncClient() as client:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = await client.get(
                f"{self.base_url}/projects/{self.project_id}/merge_requests/{mr_iid}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_merge_request_diff(self, mr_iid: int) -> str:
        """Fetch merge request diff"""
        async with httpx.AsyncClient() as client:
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            response = await client.get(
                f"{self.base_url}/projects/{self.project_id}/merge_requests/{mr_iid}/diffs",
                headers=headers,
            )
            response.raise_for_status()
            return response.text


class GitOperations:
    """Handles git operations for better context"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def checkout_branch(self, branch_name: str):
        """Checkout to specific branch"""
        self.repo.git.checkout(branch_name)

    def get_commit_context(self, commit_hash: str):
        """Get context around a specific commit"""
        return self.repo.git.show(commit_hash, "--stat")

    def get_file_history(self, file_path: str, limit: int = 5):
        """Get recent history of a file"""
        return self.repo.git.log(f"-{limit}", "--oneline", file_path)


class LLMReviewer:
    """Handles LLM-based code review"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def review_code(
        self, diff: str, rules: Dict[str, Any], context: str = ""
    ) -> CodeReview:
        """Generate AI-powered code review using ai-pydantic for structured responses"""

        system_prompt = f"""
        You are an expert code reviewer with extensive experience in software engineering.
        Review the provided code changes with focus on:
        
        1. **Correctness**: Logic errors, edge cases, potential bugs
        2. **Security**: Vulnerabilities, unsafe practices, data exposure
        3. **Performance**: Efficiency, resource usage, scalability
        4. **Code Quality**: Readability, maintainability, best practices
        5. **Architecture**: Design patterns, separation of concerns
        
        Rules to apply:
        {json.dumps(rules, indent=2)}
        
        Additional context:
        {context}
        
        Provide a structured review with:
        - Summary of changes
        - Specific issues found
        - Actionable suggestions
        - Security concerns
        - Performance notes
        - Overall quality score (1-10)
        """

        user_prompt = f"""
        Please review the following code changes and provide a structured analysis:
        
        ```diff
        {diff}
        ```
        """

        # Use fallback method since ai-pydantic is not available
        return await self._fallback_review(diff, rules, context)

    async def _fallback_review(
        self, diff: str, rules: Dict[str, Any], context: str = ""
    ) -> CodeReview:
        """Fallback method using traditional API calls"""
        system_prompt = f"""
        You are an expert code reviewer with extensive experience in software engineering.
        Review the provided code changes with focus on:
        
        1. **Correctness**: Logic errors, edge cases, potential bugs
        2. **Security**: Vulnerabilities, unsafe practices, data exposure
        3. **Performance**: Efficiency, resource usage, scalability
        4. **Code Quality**: Readability, maintainability, best practices
        5. **Architecture**: Design patterns, separation of concerns
        
        Rules to apply:
        {json.dumps(rules, indent=2)}
        
        Additional context:
        {context}
        
        IMPORTANT: You MUST format your response EXACTLY as follows:
        
        ## Summary
        [Provide a detailed summary of the changes and overall assessment]
        
        ## Issues
        - [List specific issues found, one per line starting with -]
        - [Another issue if found]
        
        ## Suggestions
        - [List actionable suggestions, one per line starting with -]
        - [Another suggestion if applicable]
        
        ## Security
        - [List security concerns, one per line starting with -]
        - [Another security issue if found]
        
        ## Performance
        - [List performance notes, one per line starting with -]
        - [Another performance note if applicable]
        
        ## Quality Score
        [Provide a number from 1-10]
        """

        user_prompt = f"""
        Please review the following code changes:
        
        ```diff
        {diff}
        ```
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "openai/gpt-4-turbo-preview",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        response = await self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM API error")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return self._parse_review_response(content)

    def _parse_review_response(self, content: str) -> CodeReview:
        """Parse LLM response into structured CodeReview object"""
        print(f"DEBUG: AI Response Content:\n{content}\n" + "=" * 50)

        lines = content.split("\n")

        summary = ""
        issues = []
        suggestions = []
        security_concerns = []
        performance_notes = []
        code_quality_score = 7  # default

        current_section = None

        for line in lines:
            line = line.strip()
            if (
                line.startswith("## Summary")
                or line.startswith("**Summary**")
                or line.startswith("### Summary")
                or "Summary of Changes" in line
            ):
                current_section = "summary"
            elif (
                line.startswith("## Issues")
                or line.startswith("**Issues**")
                or line.startswith("### Issues")
                or "Specific Issues Found" in line
            ):
                current_section = "issues"
            elif (
                line.startswith("## Suggestions")
                or line.startswith("**Suggestions**")
                or line.startswith("### Suggestions")
                or "Actionable Suggestions" in line
            ):
                current_section = "suggestions"
            elif (
                line.startswith("## Security")
                or line.startswith("**Security**")
                or line.startswith("### Security")
                or "Security Concerns" in line
            ):
                current_section = "security"
            elif (
                line.startswith("## Performance")
                or line.startswith("**Performance**")
                or line.startswith("### Performance")
                or "Performance Notes" in line
            ):
                current_section = "performance"
            elif (
                line.startswith("## Quality Score")
                or line.startswith("**Quality Score**")
                or line.startswith("### Quality Score")
                or "Overall Quality Score" in line
            ):
                current_section = "score"
            elif (
                line.startswith("- ")
                or line.startswith("1. ")
                or line.startswith("2. ")
                or line.startswith("3. ")
                or line.startswith("4. ")
                or line.startswith("5. ")
            ) and current_section:
                # Extract content from different bullet formats
                if line.startswith("- "):
                    item = line[2:].strip()
                else:
                    item = line[3:].strip()  # Remove "1. ", "2. ", etc.

                if current_section == "issues":
                    issues.append(item)
                elif current_section == "suggestions":
                    suggestions.append(item)
                elif current_section == "security":
                    security_concerns.append(item)
                elif current_section == "performance":
                    performance_notes.append(item)
            elif (
                current_section == "summary"
                and line
                and not line.startswith("#")
                and not line.startswith("###")
            ):
                summary += line + " "
            elif current_section == "score" and (line.isdigit() or "Score:" in line):
                # Extract score from various formats
                if line.isdigit():
                    code_quality_score = int(line)
                elif "Score:" in line:
                    try:
                        score_part = line.split("Score:")[1].strip()
                        if "/" in score_part:
                            code_quality_score = int(score_part.split("/")[0].strip())
                        else:
                            code_quality_score = int(score_part)
                    except:
                        pass

        return CodeReview(
            summary=summary.strip() or "Code review completed",
            issues=issues,
            suggestions=suggestions,
            security_concerns=security_concerns,
            performance_notes=performance_notes,
            code_quality_score=code_quality_score,
        )


@app.post("/gitlab")
async def handle_gitlab_webhook(request: Request):
    """Handle GitLab merge request webhook"""
    try:
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON payload: {str(e)}"
            )

        try:
            webhook = GitLabWebhook(**payload)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid webhook format: {str(e)}"
            )

        if webhook.object_kind != "merge_request":
            return {"message": "Not a merge request event"}

        mr_data = webhook.object_attributes
        mr_iid = mr_data.get("iid")
        project_id = webhook.project.get("id")

        if not mr_iid or not project_id:
            raise HTTPException(status_code=400, detail="Missing MR IID or Project ID")

        try:
            rule_engine = RuleEngine(REPO_PATH)
            gitlab_client = GitLabClient(str(project_id))
            git_ops = GitOperations(REPO_PATH)
            llm_reviewer = LLMReviewer(OPENROUTER_API_KEY)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize components: {str(e)}"
            )

        rules = rule_engine.get_effective_rules()

        try:
            mr_details = await gitlab_client.get_merge_request(mr_iid)
            diff = await gitlab_client.get_merge_request_diff(mr_iid)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch MR details: {str(e)}"
            )

        source_branch = mr_data.get("source_branch")
        target_branch = mr_data.get("target_branch")

        context = ""
        if source_branch:
            try:
                git_ops.checkout_branch(source_branch)
                recent_commits = git_ops.repo.git.log("-5", "--oneline")
                context += f"Recent commits on {source_branch}:\n{recent_commits}\n\n"
            except Exception as e:
                context += f"Could not checkout branch {source_branch}: {str(e)}\n"

        try:
            review = await llm_reviewer.review_code(diff, rules, context)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate review: {str(e)}"
            )

        markdown_response = format_review_as_markdown(review)

        return {"review": markdown_response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error processing webhook: {str(e)}"
        )


def format_review_as_markdown(review: CodeReview) -> str:
    """Format the review as Markdown"""
    md = f"""# 🤖 AI Code Review

## 📋 Summary
{review.summary}

## 🎯 Quality Score: {review.code_quality_score}/10

"""

    if review.issues:
        md += "## ⚠️ Issues Found\n"
        for issue in review.issues:
            md += f"- {issue}\n"
        md += "\n"

    if review.suggestions:
        md += "## 💡 Suggestions\n"
        for suggestion in review.suggestions:
            md += f"- {suggestion}\n"
        md += "\n"

    if review.security_concerns:
        md += "## 🔒 Security Concerns\n"
        for concern in review.security_concerns:
            md += f"- {concern}\n"
        md += "\n"

    if review.performance_notes:
        md += "## ⚡ Performance Notes\n"
        for note in review.performance_notes:
            md += f"- {note}\n"
        md += "\n"

    return md


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gitlab-mr-review-bot"}


@app.post("/test")
async def test_webhook():
    """Test endpoint for webhook functionality"""
    try:
        # Test with more complex sample diff
        sample_diff = """
        diff --git a/auth.py b/auth.py
        index 1234567..abcdefg 100644
        --- a/auth.py
        +++ b/auth.py
        @@ -1,10 +1,15 @@
         import os
         import hashlib
         
         def authenticate_user(username, password):
        -    # Simple authentication
        -    if username == "admin" and password == "password":
        -        return True
        -    return False
        +    # Enhanced authentication with hashing
        +    stored_hash = get_user_hash(username)
        +    if stored_hash:
        +        password_hash = hashlib.sha256(password.encode()).hexdigest()
        +        return password_hash == stored_hash
        +    return False
        +
        +def get_user_hash(username):
        +    # Get user hash from database
        +    return os.environ.get(f"USER_{username.upper()}_HASH")
        """

        rule_engine = RuleEngine(REPO_PATH)
        llm_reviewer = LLMReviewer(OPENROUTER_API_KEY)

        rules = rule_engine.get_effective_rules()
        review = await llm_reviewer.review_code(sample_diff, rules, "Test context")

        return {
            "status": "success",
            "review": format_review_as_markdown(review),
            "raw_review": {
                "summary": review.summary,
                "issues": review.issues,
                "suggestions": review.suggestions,
                "security_concerns": review.security_concerns,
                "performance_notes": review.performance_notes,
                "code_quality_score": review.code_quality_score,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"Test failed: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
