# Contributing to GPX Track Analyzer

Thank you for your interest in contributing to GPX Track Analyzer! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues
- Use the GitHub Issues tab to report bugs or request features
- Provide clear, detailed descriptions of the issue
- Include steps to reproduce bugs
- Mention your operating system and Python version

### Submitting Changes
1. **Fork the repository**
   - Click the "Fork" button on the GitHub repository page
   - Clone your fork locally: `git clone https://github.com/amarcuss/gpx-track-analyzer.git`

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style and conventions
   - Add comments for complex logic
   - Update documentation if needed

4. **Test thoroughly**
   - Run the test script: `python3 test_gpx_parser.py`
   - Test with various GPX files
   - Ensure all features work as expected

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Submit a pull request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Provide a clear description of your changes

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Keep functions focused and modular
- Add docstrings for new functions

### Testing
- Test your changes with various GPX files
- Ensure backward compatibility
- Test error handling paths
- Use the included test script for quick validation

### Documentation
- Update README.md if adding new features
- Update help text and examples
- Add comments for complex algorithms
- Update version information if applicable

## Types of Contributions Welcome

### Bug Fixes
- Fix parsing errors
- Improve error handling
- Resolve compatibility issues

### New Features
- Additional output formats (JSON, CSV, KML)
- More statistical calculations
- Performance optimizations
- Integration with mapping services

### Documentation
- Improve README clarity
- Add usage examples
- Create tutorials or guides
- Fix typos and formatting

### Testing
- Add test cases
- Improve test coverage
- Test with different GPX formats
- Performance testing

## Code of Conduct

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Focus on the technical merits of contributions
- Maintain a positive and inclusive environment

## Getting Help

If you need help or have questions:
- Check the README.md for usage instructions
- Review existing issues for similar problems
- Open a new issue with the "question" label
- Review the code comments for technical details

## Recognition

Contributors will be acknowledged in the project documentation. Significant contributions may be recognized in release notes.

Thank you for helping make GPX Track Analyzer better!
