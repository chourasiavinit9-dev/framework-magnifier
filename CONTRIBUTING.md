# Contributing to Framework Magnifier

Thank you for your interest in contributing! Here's how to get started.

## Getting Started

1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/framework-magnifier.git
   cd framework-magnifier
   ```

2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key** for local testing:
   ```bash
   cp .env.example .env
   # Fill in your GEMINI_API_KEY in .env
   export GEMINI_API_KEY="your_key"
   ```

## Running Tests

```bash
python -m unittest discover tests/
```

All tests must pass before opening a pull request.

## Pull Request Guidelines

- Keep PRs focused and small — one feature or fix per PR.
- Add tests for any new functionality in `tests/`.
- Update the `README.md` if you add a new command or supported dependency manager.
- Use clear commit messages:
  - `feat: add support for pyproject.toml`
  - `fix: handle AccessDenied on Windows port scan`
  - `docs: update README usage examples`

## Code Style

- Follow PEP 8 for Python code.
- Functions should have a short docstring if the purpose is not obvious.

## Reporting Issues

Open a GitHub Issue with:
- Your OS (Windows / macOS / Linux)
- Python version (`python --version`)
- The command you ran and the error output.
