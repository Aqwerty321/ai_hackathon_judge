# Pylint Isolation Fix

## Problem

The linter was potentially analyzing files from the AI Judge project itself when running on GitHub Actions or analyzing submissions locally. This could cause:

1. **False errors on GitHub**: Pylint errors from the judge's own code appearing in analysis results
2. **Security risk**: Analyzing files outside the submission directory
3. **Performance issues**: Scanning unnecessary directories

## Root Cause

The `CodeAnalyzer._run_pylint()` method accepted a list of Python files but didn't validate that they were actually within the intended code directory. This could happen if:

- File discovery traversed into parent directories
- Symbolic links pointed outside the submission
- Relative paths were mishandled

## Solution Implemented

### 1. Enhanced Skip Directory List

Added more directories to `_SKIP_DIR_NAMES` to prevent scanning common CI/CD and build directories:

```python
_SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".github",  # ✨ NEW: GitHub workflows and configs
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "bin",
    "obj",
    ".tox",  # ✨ NEW
    ".nox",  # ✨ NEW
    "htmlcov",  # ✨ NEW
    "coverage",  # ✨ NEW
    ".eggs",  # ✨ NEW
    "site-packages",  # ✨ NEW
}
```

### 2. File Path Validation in `_run_pylint()`

Added validation to ensure **only** files within the code directory are analyzed:

```python
def _run_pylint(self, code_dir: Path, python_files: Iterable[Path]) -> ...:
    # Validate that all files are within code_dir
    code_dir_resolved = code_dir.resolve()
    validated_files = []
    
    for path in python_files:
        try:
            path_resolved = path.resolve()
            # Only include files actually within the code directory
            if path_resolved.is_relative_to(code_dir_resolved):
                validated_files.append(str(path_resolved))
            else:
                LOGGER.warning("Skipping file outside code directory: %s", path)
        except (ValueError, OSError) as e:
            LOGGER.debug("Failed to validate path %s: %s", path, e)
            continue
    
    if not validated_files:
        return None, {"status": "skipped", "reason": "no valid files"}
    
    # Run pylint only on validated files
    ...
```

### 3. Path Resolution in `_compute_complexity()`

Ensured radon complexity analysis also uses resolved paths:

```python
def _compute_complexity(self, python_files: Iterable[Path]) -> ...:
    for path in python_files:
        try:
            # Resolve path to ensure it's valid
            path = path.resolve()
            text = path.read_text(encoding="utf-8")
        ...
```

## Security Benefits

✅ **Isolation**: Pylint can only analyze files within the submission's code directory  
✅ **Validation**: Symlinks and relative paths are resolved and checked  
✅ **Logging**: Suspicious files are logged with warnings  
✅ **CI Safety**: `.github` workflows are explicitly skipped

## Testing

The changes were validated with existing tests:

```powershell
python -m pytest tests/test_code_analyzer.py -v
```

**Expected behavior**:
- Files outside `code_dir` are skipped with a warning
- Lint status shows "skipped" when no valid files remain
- All security checks pass without errors

## What This Fixes

### Before
```
[Analyzing submission in data/intermediate_outputs/extracted_submissions/project/]
  → Discovers Python files in submission
  → Accidentally finds .github/workflows/ci.yml from parent directory
  → Runs pylint on judge's own code
  → Reports errors from judge's codebase
```

### After
```
[Analyzing submission in data/intermediate_outputs/extracted_submissions/project/]
  → Discovers Python files in submission
  → Validates all paths are within submission directory
  → Skips any files outside with warning
  → Only analyzes submission code
  → Reports only submission's own errors
```

## For Developers

### Running Pylint on Judge's Own Code (CI)

The GitHub workflow correctly runs pylint on the judge's code for quality checks:

```yaml
# .github/workflows/ci.yml
- name: Lint code analyzer
  run: |
    python -m pylint ai_judge/modules/code_analyzer.py \
      --disable=missing-module-docstring,missing-function-docstring
```

This is **separate** from analyzing submissions and is working as intended.

### Debugging Isolation Issues

If you suspect files are being analyzed incorrectly:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Look for warnings like:
# WARNING: Skipping file outside code directory: /path/to/wrong/file.py
```

## Related Files

- `ai_judge/modules/code_analyzer.py` - Main changes
- `.github/workflows/ci.yml` - CI pylint check (unchanged, working correctly)
- `tests/test_code_analyzer.py` - Test suite

---

**Status**: ✅ Fixed  
**Security**: Enhanced  
**GitHub CI**: Working correctly (analyzes judge's code for quality)  
**Submission Analysis**: Now isolated and secure
