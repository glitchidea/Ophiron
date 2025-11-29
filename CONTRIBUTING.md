# Contributing to Ophiron

First off, thank you for considering contributing to Ophiron! 🎉

Ophiron is an advanced system monitoring and security management platform, and we welcome contributions from the community. This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How Can I Contribute?](#how-can-i-contribute)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Plugin Development](#plugin-development)
7. [Submitting Changes](#submitting-changes)
8. [Reporting Bugs](#reporting-bugs)
9. [Suggesting Enhancements](#suggesting-enhancements)
10. [Language Translations](#language-translations)
11. [Community](#community)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors. We expect:

- **Respectful Communication**: Treat everyone with respect and professionalism
- **Constructive Feedback**: Provide helpful and constructive criticism
- **Collaborative Spirit**: Work together to improve the project
- **Inclusive Environment**: Welcome contributors of all backgrounds and experience levels

---

## Getting Started

### Before You Start

1. **Check Existing Issues**: Look through [existing issues](https://github.com/glitchidea/Ophiron/issues) to see if your idea or bug has already been reported
2. **Join Discussions**: Participate in [GitHub Discussions](https://github.com/glitchidea/Ophiron/discussions) to get feedback on your ideas
3. **Read Documentation**: Familiarize yourself with the project's [README](README.md) and architecture

### Prerequisites

- **Python 3.10+**: Core application development
- **Go 1.19+**: Plugin SDK development
- **Redis**: Message broker for Celery
- **Linux Environment**: Most features are Linux-specific
- **Git**: Version control

---

## How Can I Contribute?

### 🐛 Bug Reports

Found a bug? Help us fix it by:
1. Searching existing issues to avoid duplicates
2. Creating a detailed bug report with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots or logs if applicable

### ✨ Feature Requests

Have an idea for improvement?
1. Check [existing discussions](https://github.com/glitchidea/Ophiron/discussions)
2. Create a new discussion with:
   - Clear use case description
   - Expected behavior
   - Potential implementation approach
   - Any relevant examples or mockups

### 🔌 Plugin Development

Want to extend Ophiron's functionality?
- Follow our [SDK Plugin Development Guide](MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.en.md)
- Share your plugin in [GitHub Discussions](https://github.com/glitchidea/Ophiron/discussions)
- Consider contributing it to the official plugin repository

### 📖 Documentation Improvements

Documentation is crucial! You can:
- Fix typos or unclear explanations
- Add examples and tutorials
- Improve existing documentation
- Translate documentation to new languages

### 🌍 Translations

Help make Ophiron accessible worldwide:
- Currently supported: Turkish (TR), English (EN), German (DE)
- See [Language Translations](#language-translations) section below

---

## Development Setup

### Quick Setup

1. **Fork and Clone**: Fork the repository on GitHub, then clone your fork
2. **Follow Installation Guide**: See detailed setup instructions in:
   - English: [README.en.md](MD-Document/README/README.en.md#installation)
   - Türkçe: [README.tr.md](MD-Document/README/README.tr.md#kurulum)
   - Deutsch: [README.de.md](MD-Document/README/README.de.md#installation)

### Development Checklist

```bash
# 1. Setup environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Database
python manage.py migrate
python manage.py createsuperuser

# 3. Start services (separate terminals)
docker run -d --name redis -p 6379:6379 redis:latest
celery -A core worker --loglevel=info --pool=solo
python manage.py runserver 0.0.0.0:8000
```

Access: `http://localhost:8000`

---

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all functions, classes, and modules
- Keep functions small and focused (single responsibility principle)
- Maximum line length: 120 characters

**Example:**
```python
def get_system_metrics(include_network: bool = True) -> dict:
    """
    Retrieve current system metrics including CPU, RAM, and disk usage.
    
    Args:
        include_network: Whether to include network statistics
        
    Returns:
        Dictionary containing system metrics
    """
    metrics = {
        'cpu': get_cpu_usage(),
        'ram': get_ram_usage(),
        'disk': get_disk_usage(),
    }
    
    if include_network:
        metrics['network'] = get_network_stats()
    
    return metrics
```

### Go Code Style

- Follow official [Go style guide](https://go.dev/doc/effective_go)
- Use `gofmt` for formatting
- Add comments to exported functions and types
- Handle errors explicitly

### JavaScript/HTML/CSS

- Use 2 spaces for indentation
- Use semantic HTML5 elements
- Follow modern CSS practices (avoid inline styles)
- Use ES6+ features where appropriate
- Add comments for complex logic

### Django Specific

- Use Django's built-in features when possible
- Follow Django's [coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- Use class-based views for complex views
- Use Django ORM instead of raw SQL
- Always use CSRF protection
- Implement proper authentication and authorization

### Git Commit Messages

Write clear and descriptive commit messages:

```bash
# Good examples
feat: Add CVE scanner for Ubuntu packages
fix: Resolve memory leak in process monitor
docs: Update SDK plugin development guide
refactor: Simplify Docker container management logic

# Bad examples
update stuff
fix bug
changes
```

**Commit Message Format:**
```
<type>: <subject>

<optional body>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

---

## Plugin Development

Want to create plugins for Ophiron? We have comprehensive SDK documentation!

### 📚 Complete Plugin Development Guide

**Read the full SDK documentation** (includes installation, architecture, examples, and best practices):

- 🇬🇧 English: [SDK_PLUGIN_DEVELOPMENT.en.md](MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.en.md)
- 🇹🇷 Türkçe: [SDK_PLUGIN_DEVELOPMENT.tr.md](MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.tr.md)
- 🇩🇪 Deutsch: [SDK_PLUGIN_DEVELOPMENT.de.md](MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.de.md)

### Quick Start

```bash
# Install SDK
cd sdk && sudo make install

# Create plugin
cd ../plugins
ophiron-sdk create --name my_plugin --author "Your Name"
```

### Plugin Submission

To submit your plugin for official inclusion:

1. Follow all SDK guidelines
2. Include comprehensive documentation
3. Ensure proper testing
4. Create a PR with clear description and examples

---

## Submitting Changes

### Pull Request Process

1. **Create a Feature Branch**:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

2. **Make Your Changes**:
   - Write clean, documented code
   - Follow coding standards
   - Add tests if applicable
   - Update documentation

3. **Test Your Changes**:
```bash
# Run tests
python manage.py test

# Check for linting issues
flake8 .

# Test in development environment
python manage.py runserver
```

4. **Commit Your Changes**:
```bash
git add .
git commit -m "feat: Add new feature description"
```

5. **Push to Your Fork**:
```bash
git push origin feature/your-feature-name
```

6. **Create Pull Request**:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template with:
     - Clear title and description
     - Related issue numbers (if any)
     - Testing performed
     - Screenshots (if UI changes)

### Pull Request Guidelines

- **One PR per feature/fix**: Keep changes focused
- **Update documentation**: Reflect changes in relevant docs
- **Add tests**: Include tests for new functionality
- **Clean commit history**: Squash unnecessary commits
- **Resolve conflicts**: Rebase on main before submitting
- **Respond to feedback**: Address review comments promptly

### PR Checklist

Before submitting, ensure:

- [ ] Code follows project coding standards
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive data (API keys, passwords) in code
- [ ] Changes are backward compatible (or documented)
- [ ] PR description clearly explains changes

---

## Reporting Bugs

### Bug Report Template

```markdown
**Description**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.11.2]
- Ophiron Version: [e.g., 1.1.0]
- Browser: [e.g., Firefox 120]

**Additional Context**
Add any other context about the problem here.

**Logs**
```
Paste relevant logs here
```
```

### Security Vulnerabilities

**Do not report security vulnerabilities through public GitHub issues.**

For security issues, please email: **info@glitchidea.com**

Include:
- Detailed description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
**Problem Statement**
Describe the problem this enhancement solves.

**Proposed Solution**
Describe your proposed solution.

**Alternatives Considered**
What other approaches did you consider?

**Use Cases**
Who would benefit from this enhancement?

**Implementation Details**
Any technical details or considerations?

**Mockups/Examples**
If applicable, add mockups or examples.
```

---

## Language Translations

We welcome translations to make Ophiron accessible globally!

### Current Languages

-  Turkish (TR) - Complete
-  English (EN) - Complete  
-  German (DE) - Complete

### Adding a New Language

```bash
# 1. Generate translation files
python manage.py makemessages -l <language_code>

# 2. Translate strings in locale/<lang>/LC_MESSAGES/django.po

# 3. Compile translations
python manage.py compilemessages

# 4. Add language to LANGUAGES in core/settings.py

# 5. Test in UI
```

### Guidelines

- Consider UI context and space constraints
- Use consistent terminology
- Keep technical terms recognizable
- Test all translated strings in actual UI

**Resources:** [Django i18n docs](https://docs.djangoproject.com/en/stable/topics/i18n/) • Existing translations in `locale/`

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions and questions
- **Website**: https://ophiron.glitchidea.com/

### Getting Help

- Check the [README](README.md) and documentation
- Search existing issues and discussions
- Join community discussions
- Ask questions in GitHub Discussions

### Recognition

Contributors will be recognized in:
- THANKS.md file
- Release notes
- Project website (for significant contributions)

---

## License and Commercial Use

- **License**: GNU GPL-3.0 (see [LICENSE](LICENSE))
- **Contributing Agreement**: Your contributions will be licensed under GPL-3.0
- **Commercial Use**: Review [license requirements](README.md#license-and-commercial-use) in README

For commercial use inquiries: **info@glitchidea.com**

---

## Questions?

If you have questions about contributing:

1. Check this guide thoroughly
2. Search existing issues and discussions
3. Ask in [GitHub Discussions](https://github.com/glitchidea/Ophiron/discussions)
4. Contact: info@glitchidea.com

---

<div align="center">

## Thank You! 🙏

Every contribution, no matter how small, helps make Ophiron better for everyone.

**Developed with ❤️ by the Ophiron Community**

[Website](https://ophiron.glitchidea.com/) • [Report Issue](https://github.com/glitchidea/Ophiron/issues) • [Discussions](https://github.com/glitchidea/Ophiron/discussions)

</div>

