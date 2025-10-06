# GitLab Merge Request Review Bot

An AI-powered tool that automatically reviews GitLab Merge Requests using Large Language Models and provides structured feedback in Markdown format.

## Features

- 🤖 **AI-Powered Reviews**: Uses OpenRouter API with GPT-4 for intelligent code analysis
- 🔧 **Configurable Rules**: Bot-level and project-level rule system
- 🔍 **Git Context**: Leverages git history and branch information for better context
- 🐳 **Docker Ready**: Containerized deployment with volume mounting
- 📝 **Markdown Output**: Structured, readable review format
- 🔒 **Security Focus**: Dedicated security analysis and vulnerability detection
- ⚡ **Performance Analysis**: Code efficiency and optimization suggestions

## Quick Start

### Using Docker (Recommended)

```bash
# Build and run the container
docker build -t rbot .
docker run -p 8080:8080 -v /path/to/your/repo:/repo rbot
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENROUTER_API_KEY="your-api-key-here"

# Run the server
python main.py
```

## API Endpoints

- `POST /gitlab` - GitLab webhook endpoint for merge request events
- `GET /health` - Health check endpoint

## Configuration

### Bot-Level Rules

The bot applies default rules for all projects:

```json
{
  "max_file_size": 1000,
  "security_checks": true,
  "performance_checks": true,
  "code_quality_checks": true,
  "language_specific_rules": {
    "python": ["check_imports", "check_docstrings"],
    "javascript": ["check_eslint", "check_async"],
    "java": ["check_annotations", "check_exceptions"]
  }
}
```

### Project-Level Rules

Create an `md.rbot` file in your repository root to override bot-level rules:

```json
{
  "security_checks": true,
  "performance_checks": false,
  "custom_rules": [
    "Check for TODO comments",
    "Verify error handling",
    "Ensure proper logging"
  ]
}
```

## GitLab Webhook Setup

1. Go to your GitLab project settings
2. Navigate to Integrations → Webhooks
3. Add webhook URL: `http://your-server:8080/gitlab`
4. Select "Merge request events"
5. Configure SSL verification as needed

## Review Output Format

The bot generates structured Markdown reviews including:

- **Summary**: High-level overview of changes
- **Quality Score**: 1-10 rating of code quality
- **Issues**: Specific problems found
- **Suggestions**: Actionable improvement recommendations
- **Security Concerns**: Potential vulnerabilities
- **Performance Notes**: Optimization opportunities

## Ideas and Proposed Improvements

### 1. Enhanced Context Analysis

- **Commit Message Analysis**: Parse commit messages for context and intent
- **Related Issues**: Link to GitLab issues and track resolution
- **Dependency Analysis**: Check for outdated or vulnerable dependencies
- **Test Coverage**: Analyze test coverage changes and suggest improvements

### 2. Advanced Rule Engine

- **Language-Specific Rules**: Deep integration with linters (ESLint, Pylint, etc.)
- **Architecture Rules**: Enforce design patterns and architectural decisions
- **Team Standards**: Custom rules based on team coding standards
- **Compliance Checks**: Industry-specific compliance requirements

### 3. Learning and Adaptation

- **Feedback Loop**: Learn from developer responses to improve suggestions
- **Historical Analysis**: Use past MR data to identify patterns
- **Team Preferences**: Adapt to team-specific coding styles and preferences
- **False Positive Reduction**: Improve accuracy over time

### 4. Integration Enhancements

- **IDE Integration**: Real-time feedback in development environments
- **CI/CD Pipeline**: Automated quality gates and deployment decisions
- **Slack/Discord Bots**: Notify teams of review results
- **Jira Integration**: Create tickets for identified issues

### 5. Advanced AI Features

- **Code Generation**: Suggest specific code improvements
- **Refactoring Recommendations**: Identify refactoring opportunities
- **Documentation Generation**: Auto-generate documentation for new code
- **Performance Profiling**: Deep performance analysis and optimization

### 6. Security Enhancements

- **SAST Integration**: Static Application Security Testing
- **Secret Detection**: Scan for exposed credentials and secrets
- **Vulnerability Database**: Integration with CVE databases
- **Compliance Scanning**: GDPR, HIPAA, SOX compliance checks

### 7. Scalability and Performance

- **Caching**: Cache analysis results for unchanged code
- **Parallel Processing**: Analyze multiple files simultaneously
- **Incremental Analysis**: Only analyze changed portions
- **Resource Optimization**: Efficient memory and CPU usage

## Assumptions and Limitations

### Current Assumptions

1. **Repository Access**: The repository is already cloned in the `/repo` directory
2. **Git Operations**: Git commands are available and the repository is accessible
3. **Network Access**: OpenRouter API is accessible from the deployment environment
4. **Webhook Format**: GitLab webhook payload follows standard GitLab webhook format
5. **File Permissions**: The application has read access to the repository files

### Known Limitations

1. **Large Files**: Very large files (>1000 lines) may not be fully analyzed
2. **Binary Files**: Binary files are not analyzed for content
3. **Language Support**: Limited to common programming languages
4. **Context Window**: LLM context limitations may affect very large diffs
5. **Rate Limits**: OpenRouter API rate limits may affect high-volume usage

### Deployment Considerations

1. **Volume Mounting**: Ensure proper volume mounting for repository access
2. **Network Security**: Secure the webhook endpoint appropriately
3. **API Key Management**: Use secure environment variable management
4. **Resource Allocation**: Allocate sufficient CPU and memory for analysis
5. **Monitoring**: Implement logging and monitoring for production use
