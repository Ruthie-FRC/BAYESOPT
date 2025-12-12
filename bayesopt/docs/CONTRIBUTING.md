# Contributing to BayesOpt

Thanks for contributing! This is an open source project made by one high schooler, so please be patient if code reviews or responses take some time.

## Quick Workflow

1. **Fork and clone** the repository
2. **Create a branch** - Use naming convention: `feat/feature-name` or `fix/bug-name`
3. **Make focused commits** - One logical change per commit
4. **Run tests and linters** locally before pushing
5. **Push your branch** and open a Pull Request
6. **Address review feedback** - Rebase/squash if requested

## Before Contributing

- Search existing issues to avoid duplicates
- For major changes, open an issue first to discuss
- Keep changes small and focused
- Write tests for new functionality
- Update documentation for user-facing changes

## Commit Message Format

Use this format for commit messages:

```
<type>(scope): short imperative summary

Body (optional):
- Explain what changed and why
- Include "from X → Y" for value changes
- Note testing and compatibility
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, no logic change)
- `refactor` - Code change that neither fixes bug nor adds feature
- `perf` - Performance improvement
- `test` - Adding or updating tests
- `chore` - Maintenance (dependencies, build, etc.)

### Examples

**Good commit:**
```
feat(optimizer): reduce default learning_rate 0.01 → 0.001

Changed Adam (adaptive moment estimate) default learning_rate in 
bayesopt/optimizer.py from 0.01 → 0.001.

Why: Reduced overshooting and improved stability on noisy datasets.
Testing: Updated tests/test_optimizer.py::test_default_lr to assert new default.
Files: bayesopt/optimizer.py, tests/test_optimizer.py
```

**Bad commit:**
```
fix stuff
```

## Pull Request Guidelines

### PR Checklist

Before submitting, ensure:

- [ ] Branch follows naming convention
- [ ] All tests pass locally
- [ ] Linter passes (if applicable)
- [ ] Documentation updated for user-facing changes
- [ ] Commit messages follow format
- [ ] PR description is clear and complete

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- List specific changes made
- Use "from X → to Y" format for value changes
- Explain why changes were needed

## Testing
- Describe how you tested
- Include relevant test output
- Note any manual testing performed

## Related Issues
- Closes #123
- Relates to #456
```

### Good PR Example

**Title:** `feat(optimizer): improve convergence detection`

**Description:**
```markdown
## Summary
Improves convergence detection by adding standard deviation threshold check.

## Changes
- Added `std_threshold` parameter to optimizer convergence check
- Changed convergence from "no improvement in 5 iterations" to 
  "no improvement in 5 iterations AND std < threshold"
- Default std_threshold = 0.01

Why: Previous method sometimes detected false convergence on noisy data.

## Testing
- Updated tests/test_optimizer.py::test_convergence
- Ran manual test with noisy synthetic data
- Verified convergence is more stable

## Related Issues
Closes #42
```

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use meaningful variable names
- Add docstrings to public functions/classes
- Keep functions focused and small
- Use type hints where appropriate

**Example:**
```python
def calculate_score(hit: bool, distance: float) -> float:
    """
    Calculate shot score based on hit result and distance.
    
    Args:
        hit: Whether shot hit target
        distance: Distance to target in meters
        
    Returns:
        Score value (0.0 to 1.0)
    """
    if hit:
        return 1.0
    return max(0.0, 1.0 - distance / 10.0)
```

### Java Style

- Follow WPILib conventions
- Use `m_` prefix for member variables
- Use `k` prefix for constants
- Use `s_` prefix for static fields
- Add Javadoc comments

### Running Linters

```bash
# Python
black bayesopt/tuner/
flake8 bayesopt/tuner/

# Check formatting without changing
black --check bayesopt/tuner/
```

## Testing

### Running Tests

```bash
# All tests
cd bayesopt/tuner
python run_tests.py

# Specific test
python -m pytest tests/test_optimizer.py -v

# With coverage
python -m pytest --cov=. --cov-report=html tests/
```

### Writing Tests

- Write tests for new features
- Update tests when changing behavior
- Mock external dependencies (NetworkTables)
- Use descriptive test names

**Example:**
```python
def test_optimizer_clamps_to_bounds():
    """Test that optimizer suggestions are clamped to configured bounds."""
    config = CoefficientConfig(min=0.0, max=1.0, default=0.5)
    optimizer = BayesianOptimizer(config)
    
    suggestion = optimizer.suggest_next_value()
    
    assert suggestion >= 0.0
    assert suggestion <= 1.0
```

## Documentation

### When to Update Docs

Update documentation when:
- Adding new features
- Changing configuration options
- Modifying public APIs
- Fixing user-visible bugs

### Documentation Files

| File | Update When |
|------|-------------|
| README.md | Overview or quick start changes |
| docs/SETUP.md | Setup process changes |
| docs/USER_GUIDE.md | Feature or configuration changes |
| docs/JAVA_INTEGRATION.md | Java API changes |
| docs/TROUBLESHOOTING.md | New common issues discovered |
| docs/DEVELOPER_GUIDE.md | Architecture or code structure changes |

### Documentation Style

- Use clear, concise language
- Include examples
- Provide context for why, not just what
- Use tables for comparisons
- Use code blocks for commands/config

## Reporting Issues

### Before Reporting

1. Search existing issues
2. Check documentation
3. Try troubleshooting steps
4. Verify with latest version

### Issue Template

```markdown
## Description
Clear description of the issue.

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- Python version: 
- OS: 
- BayesOpt version/commit:
- NetworkTables version:

## Logs
Relevant log output or error messages.

## Additional Context
Any other relevant information.
```

## Code Review Process

### What to Expect

1. Maintainer reviews your PR
2. Feedback provided as comments
3. You address feedback with new commits
4. Once approved, PR is merged

### Review Criteria

- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility
- Performance impact

### Responding to Feedback

- Be respectful and constructive
- Ask questions if feedback is unclear
- Explain your reasoning if you disagree
- Make requested changes in new commits
- Mark conversations as resolved when addressed

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the project

### Ask Questions

- Don't assume - ask for clarification
- Explain your reasoning
- Provide context for your questions
- Be patient waiting for responses

### Help Others

- Answer questions when you can
- Share your knowledge
- Point to relevant documentation
- Be supportive of new contributors

## Getting Help

### Where to Ask

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and discussion
- **Pull Request comments** - Questions about specific code

### What to Include

When asking for help:
1. What you're trying to do
2. What you've tried
3. Relevant error messages
4. Your environment details
5. Minimal reproducible example (if applicable)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Attribution

Contributors are credited in:
- Git commit history
- GitHub contributors page
- Project acknowledgments (for significant contributions)

## Questions?

If you have questions about contributing:
- Open a GitHub issue
- Check existing documentation
- Ask in GitHub Discussions

Thank you for contributing to BayesOpt! 🎉

## See Also

- **Developer Guide:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Architecture and code structure
- **Documentation Standards:** [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - Documentation conventions
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md) - Complete feature documentation
- **Setup Guide:** [SETUP.md](SETUP.md) - Installation instructions
- **Main README:** [README.md](../../README.md) - Project overview
