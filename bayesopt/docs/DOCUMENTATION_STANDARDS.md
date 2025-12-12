# Documentation Standards

This document defines the conventions and standards for all documentation in the BAYESOPT project. Following these standards ensures documentation is maintainable, consistent, and easy to navigate.

## Table of Contents

- [Overview](#overview)
- [File Organization](#file-organization)
- [File Naming](#file-naming)
- [Document Structure](#document-structure)
- [Markdown Formatting](#markdown-formatting)
- [Code Examples](#code-examples)
- [Tables](#tables)
- [Links and Cross-References](#links-and-cross-references)
- [Writing Style](#writing-style)
- [Maintenance](#maintenance)

## Overview

### Purpose

These standards ensure:
- **Consistency** - All docs follow the same patterns
- **Maintainability** - Easy to update and keep current
- **Accessibility** - Easy to find information
- **Professionalism** - High-quality documentation

### When to Use

Follow these standards for:
- User-facing documentation
- Developer guides
- API documentation
- README files
- Contributing guidelines

## File Organization

### Directory Structure

```
BAYESOPT/
├── README.md                          # Project overview and quick start
├── LICENSE                            # License information
│
├── bayesopt/
│   └── docs/                          # All detailed documentation
│       ├── DOCUMENTATION_STANDARDS.md # This file
│       ├── USER_GUIDE.md             # Complete user documentation
│       ├── DEVELOPER_GUIDE.md        # Developer documentation
│       ├── CONTRIBUTING.md           # How to contribute
│       ├── SETUP.md                  # Installation and setup
│       ├── JAVA_INTEGRATION.md       # Java integration guide
│       ├── HOTKEYS.md                # Keyboard shortcuts
│       └── TROUBLESHOOTING.md        # Common issues and solutions
│
├── java-integration/
│   └── README.md                      # Java files documentation
│
└── bayesopt/tuner/tests/
    └── README_TESTS.md                # Test suite documentation
```

### Documentation Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **Overview** | `/README.md` | Project introduction, quick start |
| **User Docs** | `/bayesopt/docs/` | Setup, usage, troubleshooting |
| **Developer Docs** | `/bayesopt/docs/` | Architecture, contributing |
| **Component Docs** | Within component directories | Specific component documentation |

## File Naming

### Rules

1. **Use UPPERCASE for documentation files**
   - ✅ `README.md`
   - ✅ `CONTRIBUTING.md`
   - ✅ `USER_GUIDE.md`
   - ❌ `readme.md`
   - ❌ `user-guide.md`

2. **Use underscores for multi-word names**
   - ✅ `DOCUMENTATION_STANDARDS.md`
   - ✅ `JAVA_INTEGRATION.md`
   - ❌ `documentation-standards.md`
   - ❌ `JavaIntegration.md`

3. **Use `.md` extension for Markdown files**
   - All documentation must be in Markdown format

4. **Be descriptive but concise**
   - ✅ `SETUP.md` - clear and concise
   - ✅ `TROUBLESHOOTING.md` - clear purpose
   - ❌ `GUIDE.md` - too vague
   - ❌ `EVERYTHING_YOU_NEED_TO_KNOW.md` - too long

## Document Structure

### Required Sections

Every documentation file must include:

1. **Title (H1)** - One top-level heading
2. **Brief description** - 1-2 sentences explaining the document
3. **Table of Contents** - For documents longer than 3 sections
4. **Main content** - Organized with clear hierarchy
5. **Related Documents** - Links to related docs (optional but recommended)

### Standard Template

```markdown
# Document Title

Brief description of what this document covers (1-2 sentences).

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)
  - [Subsection 2.1](#subsection-21)
- [Section 3](#section-3)

## Section 1

Content here...

## Section 2

Content here...

### Subsection 2.1

Content here...

## Section 3

Content here...

## See Also

- [Related Doc 1](RELATED_DOC_1.md)
- [Related Doc 2](RELATED_DOC_2.md)
```

### Header Hierarchy

Use headers consistently:

- **H1 (`#`)** - Document title only (use once)
- **H2 (`##`)** - Major sections
- **H3 (`###`)** - Subsections
- **H4 (`####`)** - Sub-subsections (use sparingly)

**Never skip levels:**
- ✅ H1 → H2 → H3
- ❌ H1 → H3 (skipped H2)

### Table of Contents

**When to include:**
- Documents with 4+ H2 sections
- Documents longer than 200 lines
- Documents with nested subsections

**Format:**
```markdown
## Table of Contents

- [Section Name](#section-name)
  - [Subsection Name](#subsection-name)
- [Another Section](#another-section)
```

**Rules:**
- Use lowercase anchor links with hyphens
- Indent subsections with 2 spaces
- List all H2 and H3 headers
- Keep in sync when updating document

## Markdown Formatting

### Emphasis

- **Bold** for important terms: `**bold text**`
- *Italic* for emphasis: `*italic text*`
- `Code` for technical terms: `` `code` ``

**Examples:**
```markdown
The **BayesOpt tuner** uses *Bayesian optimization* to tune `kDragCoefficient`.
```

### Lists

**Unordered lists:**
```markdown
- First item
- Second item
  - Nested item (indent 2 spaces)
  - Another nested item
- Third item
```

**Ordered lists:**
```markdown
1. First step
2. Second step
3. Third step
```

**Best practices:**
- Use unordered lists for items without sequence
- Use ordered lists for steps/procedures
- Keep list items parallel in structure
- Use consistent indentation (2 spaces)

### Code Blocks

**Inline code:**
```markdown
Use the `--verbose` flag to see detailed output.
```

**Code blocks with syntax highlighting:**
````markdown
```python
def example():
    return "Hello, World!"
```
````

**Specify language for syntax highlighting:**
- `python` - Python code
- `java` - Java code
- `bash` - Shell commands
- `json` - JSON data
- `yaml` - YAML data
- `ini` - INI config files

**Command examples:**
```markdown
```bash
# Install dependencies
pip install -r requirements.txt
```
```

**File content examples:**
```markdown
```python
# Example: bayesopt/tuner/main.py
if __name__ == "__main__":
    run_tuner()
```
```

### Quotes and Callouts

**Blockquotes for notes:**
```markdown
> **Note:** This feature requires Python 3.8 or newer.
```

**Status indicators:**
```markdown
✅ Supported
❌ Not supported
⚠️ Warning
💡 Tip
📝 Note
```

## Code Examples

### Guidelines

1. **Always include language identifier**
   ```markdown
   ```python
   # Python code here
   ```
   ```

2. **Add comments to explain non-obvious code**
   ```python
   # Initialize with default values
   config = load_config()
   ```

3. **Keep examples focused and minimal**
   - Show only relevant code
   - Use `...` to indicate omitted code
   - Don't include unnecessary imports

4. **Show complete, runnable examples when possible**
   ```python
   # Complete example
   from bayesopt.tuner import Tuner
   
   tuner = Tuner()
   tuner.start()
   ```

5. **Include expected output**
   ```bash
   $ python run_tests.py
   Ran 116 tests in 2.5s
   
   OK
   ```

### Command-Line Examples

**Format:**
```markdown
```bash
# Description of command
command --flag argument
```
```

**Multi-step commands:**
```markdown
```bash
# Step 1: Navigate to directory
cd /path/to/project

# Step 2: Run command
python script.py
```
```

**Platform-specific commands:**
```markdown
**Windows:**
```cmd
python bayesopt\tuner\main.py
```

**Mac/Linux:**
```bash
python3 bayesopt/tuner/main.py
```
```

## Tables

### When to Use Tables

Tables are ideal for:
- Comparing options
- Listing parameters with descriptions
- Showing configuration values
- Documenting API methods

### Standard Format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

### Alignment

```markdown
| Left-aligned | Center-aligned | Right-aligned |
|:-------------|:--------------:|--------------:|
| Text         | Text           | Text          |
```

### Best Practices

1. **Keep cells concise**
   - Use short descriptions
   - Link to details if needed

2. **Use consistent column ordering**
   - Parameter, Type, Description
   - Name, Location, Purpose

3. **Format consistently**
   - Align column separators
   - Use same header style

**Good example:**
```markdown
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Coefficient name |
| `value` | float | Coefficient value |
```

**Bad example:**
```markdown
| Thing | Stuff |
|---|---|
| A really long description that makes the table hard to read | Value |
```

## Links and Cross-References

### Internal Links

**Link to another document:**
```markdown
See [USER_GUIDE.md](USER_GUIDE.md) for details.
```

**Link to a section in same document:**
```markdown
See [Installation](#installation) for setup instructions.
```

**Link to section in another document:**
```markdown
See [Dashboard Controls](USER_GUIDE.md#dashboard-controls) for details.
```

### External Links

```markdown
Download Python from [python.org](https://www.python.org/).
```

### Best Practices

1. **Use descriptive link text**
   - ✅ `See [Setup Guide](SETUP.md)`
   - ❌ `Click [here](SETUP.md)`

2. **Use relative paths for internal links**
   - ✅ `[USER_GUIDE.md](USER_GUIDE.md)`
   - ❌ `[USER_GUIDE.md](https://github.com/.../USER_GUIDE.md)`

3. **Verify links work**
   - Test links after creating them
   - Update links when moving files

4. **Group related links**
   ```markdown
   ## See Also
   
   - [Setup Guide](SETUP.md)
   - [User Guide](USER_GUIDE.md)
   - [Troubleshooting](TROUBLESHOOTING.md)
   ```

## Writing Style

### Tone

- **Clear and direct** - Get to the point
- **Professional but approachable** - Avoid overly formal language
- **Helpful and supportive** - Guide the reader

### Grammar and Style

1. **Use active voice**
   - ✅ "Run the command to start the tuner"
   - ❌ "The command should be run to start the tuner"

2. **Use present tense**
   - ✅ "The tuner connects to the robot"
   - ❌ "The tuner will connect to the robot"

3. **Be specific**
   - ✅ "Set `autotune_enabled = True` in TUNER_TOGGLES.ini"
   - ❌ "Enable the autotune setting"

4. **Use consistent terminology**
   - Pick one term and stick with it
   - Example: "coefficient" not "parameter" or "value"

5. **Spell out acronyms on first use**
   - ✅ "Field Management System (FMS)"
   - ❌ "FMS" (on first use)

### Formatting Conventions

1. **File paths and names**
   - Use code formatting: `` `bayesopt/config/TUNER_TOGGLES.ini` ``

2. **Commands**
   - Use code blocks: `` ```bash ... ``` ``

3. **Configuration values**
   - Use code formatting: `` `autotune_enabled = True` ``

4. **UI elements**
   - Use code formatting: `` `TunerEnabled` ``
   - Or bold: `**TunerEnabled**`

5. **Keys and shortcuts**
   - Use code formatting: `` `Ctrl+Shift+X` ``

## Maintenance

### Keeping Documentation Current

1. **Update docs when changing code**
   - Documentation is part of the feature
   - Update affected docs in the same PR

2. **Review docs periodically**
   - Check for outdated information
   - Update examples and screenshots
   - Verify links still work

3. **Track documentation todos**
   - Mark incomplete sections with `TODO:`
   - File issues for major doc updates

4. **Version documentation**
   - Note which version docs apply to
   - Update changelogs

### Documentation Checklist

When creating or updating documentation:

- [ ] Title is clear and descriptive
- [ ] Brief description at the top
- [ ] Table of contents for longer docs
- [ ] Headers follow hierarchy (H1 → H2 → H3)
- [ ] Code blocks have language identifiers
- [ ] Examples are complete and tested
- [ ] Links work and use relative paths
- [ ] Terminology is consistent
- [ ] Grammar and spelling checked
- [ ] Follows writing style guidelines
- [ ] Related documents linked

### Common Issues to Avoid

❌ **Don't:**
- Skip header levels (H1 → H3)
- Use absolute URLs for internal links
- Include untested code examples
- Use vague language ("some files", "a few settings")
- Mix terminology (coefficient/parameter/value)
- Include outdated screenshots
- Forget to update cross-references

✅ **Do:**
- Follow the header hierarchy
- Use relative paths for links
- Test all examples
- Be specific and concrete
- Use consistent terminology
- Keep screenshots current
- Update all related documents

## Examples

### Good Documentation Example

```markdown
# Setup Guide

Complete installation instructions for the BayesOpt tuner on all platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Setup](#windows-setup)
- [Mac/Linux Setup](#maclinux-setup)

## Prerequisites

Before you begin, you need:

1. **Python 3.8 or newer** installed on your computer
2. **Git** for cloning the repository
3. **Network connection** to your robot

## Windows Setup

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ⚠️ **Important:** Check "Add Python to PATH"
4. Click "Install Now"

### Step 2: Clone Repository

```bash
git clone https://github.com/Ruthie-FRC/BAYESOPT.git
cd BAYESOPT
```

## See Also

- [User Guide](USER_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
```

### Bad Documentation Example

```markdown
# docs

some documentation about stuff

## section1

You need python. Download it somewhere.

Clone the repo.

## another section

Run these commands:
```
some commands here
```

more stuff...
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-12 | Initial documentation standards |

## Contributing to Documentation

When contributing documentation:

1. Read this standards document
2. Follow the templates and examples
3. Use the checklist before submitting
4. Request review from maintainers

See [CONTRIBUTING.md](CONTRIBUTING.md) for general contribution guidelines.

## Questions?

If you have questions about these standards:
- Open a GitHub issue
- Ask in discussions
- Contact maintainers

Thank you for helping maintain high-quality documentation! 📚
