# Architecture Linter

## Purpose

This custom linter enforces two key architectural constraints in the project:

1. **Features Isolation**: Modules within the `features/` directory cannot import other feature modules. This ensures loose coupling between different feature implementations.

2. **Core Module Accessibility**: Modules in the `core/` directory are globally accessible and can be imported from anywhere in the project.

## Usage

### Running the Linter

```bash
python scripts/architecture_linter.py /path/to/project
```

### Integration with CI/CD

You can integrate this linter into your CI/CD pipeline to automatically check architectural constraints during build or pre-merge checks.

### Example CI Configuration (GitHub Actions)

```yaml
name: Architecture Check
on: [push, pull_request]

jobs:
  lint-architecture:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Run Architecture Linter
      run: python scripts/architecture_linter.py .
```

## Violations

If the linter detects any violations, it will:
- Print out detailed violation messages
- Exit with a non-zero status code

### Common Violation Types
- Importing one feature module from another feature module
- Attempting to import a non-core module globally

## Customization

You can modify `architecture_linter.py` to add more sophisticated checks or adjust the existing rules to fit your project's specific architectural needs.
