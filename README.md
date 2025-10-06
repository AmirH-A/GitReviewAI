# GitLab MR Review Bot

Automated code review tool for GitLab merge requests using AI analysis.

## Overview

This bot integrates with GitLab webhooks to automatically review merge requests and provide detailed feedback on code quality, security, and performance. It uses OpenRouter API with GPT-4 for intelligent code analysis and returns structured Markdown reviews.

## Quick Start

### Docker Deployment

```bash
docker build -t rbot .
docker run -p 8080:8080 -v /repo:/repo rbot
```

### Local Setup

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY="your-api-key"
python main.py
```

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key for LLM access

### Project Rules

Create `md.rbot` in your repository root to customize review rules:

```json
{
  "security_checks": true,
  "performance_checks": true,
  "custom_rules": ["Check for TODO comments", "Verify error handling"]
}
```

## GitLab Integration

1. Go to Project Settings → Integrations → Webhooks
2. Add webhook URL: `http://your-server:8080/gitlab`
3. Select "Merge request events"
4. Configure SSL verification as needed

## API Endpoints

- `POST /gitlab` - GitLab webhook handler
- `GET /health` - Health check
- `POST /test` - Test endpoint for validation

## Review Output

The bot generates comprehensive reviews including:

- **Summary**: Overview of changes and impact
- **Issues**: Specific problems identified
- **Suggestions**: Actionable improvements
- **Security**: Vulnerability analysis
- **Performance**: Optimization recommendations
- **Quality Score**: 1-10 rating with reasoning

## Architecture

The bot consists of several key components:

- **Webhook Handler**: Processes GitLab merge request events
- **Rule Engine**: Manages bot-level and project-level rules
- **Git Operations**: Provides repository context and history
- **LLM Reviewer**: Generates AI-powered code analysis
- **Response Formatter**: Structures output as Markdown

## Future Enhancements

### Planned Features

- **Enhanced Context**: Commit message analysis, issue linking
- **Advanced Rules**: Language-specific linting integration
- **Learning System**: Feedback loop for improved suggestions
- **IDE Integration**: Real-time development feedback
- **Security Scanning**: SAST integration, secret detection
- **Performance Optimization**: Caching, parallel processing

### Technical Improvements

- **Caching**: Store analysis results for unchanged code
- **Rate Limiting**: Handle high-volume usage efficiently
- **Monitoring**: Comprehensive logging and metrics
- **Testing**: Unit tests for critical components
- **Documentation**: Auto-generate code documentation

## Deployment Notes

### Requirements

- Repository cloned in `/repo` directory
- Git commands available
- Network access to OpenRouter API
- Proper file permissions for repository access

### Limitations

- Large files (>1000 lines) may have limited analysis
- Binary files are not processed
- LLM context limits affect very large diffs
- API rate limits may impact high-volume usage

### Security Considerations

- Secure webhook endpoint configuration
- Proper API key management
- Resource allocation for analysis workloads
- Monitor for potential abuse or overuse

## Development

The project uses FastAPI for the web server, GitPython for repository operations, and httpx for API communication. The LLM integration supports both structured responses and fallback parsing for maximum reliability.

## License

This project is available for use in accordance with the job requirements and intended for GitLab merge request automation.
