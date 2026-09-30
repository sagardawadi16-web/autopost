# Contributing to AutoPost

Thank you for your interest in contributing to AutoPost! We welcome improvements, bug fixes, feature requests, and documentation updates.

---

## Code of Conduct

Please maintain a welcoming, respectful, and constructive environment for all contributors.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing issues before creating a new one.
- Provide a clear and descriptive title.
- Include your operating system, Python version, FFmpeg version, and steps to reproduce.
- **Never include API keys or OAuth tokens in bug reports or stack traces!**

### 2. Suggesting Features
- Open an issue describing the proposed feature and why it would be beneficial.
- Outline the expected workflow and any API requirements.

### 3. Submitting Pull Requests
1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. **Install dependencies** in a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. **Make your changes** following PEP 8 conventions.
4. **Test your code** thoroughly:
   ```bash
   python -m src.pipeline --channel english --dry-run
   ```
5. **Commit your changes**:
   ```bash
   git commit -m "feat: add support for custom subtitle transition effects"
   ```
6. **Push to branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request** against the `main` branch.

---

## Code Style & Guidelines

- **Python**: Follow PEP 8 with type annotations (`typing`).
- **Logging**: Use Python's built-in `logging` rather than plain `print()` statements in library code.
- **Error Handling**: Graceful fallbacks are preferred (e.g. Gemini AI fallback when external APIs are unreachable).
