# Understanding Pylint in GitHub Actions

## Two Different Uses of Pylint

### 1. CI Quality Check (`.github/workflows/ci.yml`)

This runs pylint **on the AI Judge's own code** to ensure code quality:

```yaml
- name: Lint code analyzer
  run: >-
    python -m pylint
    ai_judge/modules/code_analyzer.py
    --disable=missing-module-docstring,missing-function-docstring,too-many-locals,too-few-public-methods
```

**Purpose**: Quality assurance for the judge's codebase  
**Target**: `ai_judge/modules/code_analyzer.py`  
**Status**: ✅ This is correct and should remain

### 2. Submission Analysis (Runtime)

This runs pylint **on submitted hackathon projects** during evaluation:

```python
# In CodeAnalyzer.analyze()
lint_score, lint_details = self._run_pylint(code_dir, python_files)
```

**Purpose**: Evaluate quality of submitted code  
**Target**: Files in `data/intermediate_outputs/extracted_submissions/<project>/`  
**Status**: ✅ Now isolated and secure (see PYLINT_ISOLATION_FIX.md)

## Why You See Pylint Errors on GitHub

If you're seeing pylint errors in GitHub Actions, they are likely from **CI quality checks** (#1 above), not from analyzing submissions.

### Example: Seeing Errors on GitHub

```
Run python -m pylint ai_judge/modules/code_analyzer.py
************* Module ai_judge.modules.code_analyzer
ai_judge/modules/code_analyzer.py:234: C0301: Line too long (105/100) (line-too-long)

Your code has been rated at 9.45/10
```

This is **expected** and **good**! It means:
- ✅ GitHub is checking YOUR code quality
- ✅ It's finding minor style issues in the judge's code
- ✅ This helps you maintain high code quality

## What Changed with Our Fix

### Before Fix
- **Risk**: Submission analysis might scan judge's own files
- **Symptom**: Pylint errors from `ai_judge/` appearing in submission reports
- **Security**: Files outside submission could be analyzed

### After Fix
- **Protection**: Path validation ensures only submission files are analyzed
- **Isolation**: `.github`, `tests`, `ai_judge` directories are skipped
- **Logging**: Warnings when files outside submission are attempted

## How to Handle CI Pylint Errors

If you see pylint errors in GitHub Actions:

### Option 1: Fix the Code Quality Issues
```bash
# Run locally to see issues
python -m pylint ai_judge/modules/code_analyzer.py

# Fix the issues (e.g., shorten long lines, add docstrings)
```

### Option 2: Disable Specific Warnings
```yaml
# In .github/workflows/ci.yml
- name: Lint code analyzer
  run: |
    python -m pylint ai_judge/modules/code_analyzer.py \
      --disable=missing-module-docstring,missing-function-docstring,line-too-long
```

### Option 3: Set Score Threshold
```yaml
# Fail only if score is below threshold
- name: Lint code analyzer
  run: |
    python -m pylint ai_judge/modules/code_analyzer.py \
      --disable=missing-module-docstring,missing-function-docstring \
      --fail-under=8.0
```

## Verification

To confirm everything is working correctly:

### 1. Check CI is Linting Judge's Code Only
```bash
# In .github/workflows/ci.yml, this should analyze judge's code:
python -m pylint ai_judge/modules/code_analyzer.py
```

### 2. Check Submissions are Isolated
```bash
# Run analysis on a test submission
python -m ai_judge.main --submission test_project

# Check logs - should NOT see files from ai_judge/ or tests/
# Should ONLY see files from data/intermediate_outputs/extracted_submissions/
```

### 3. Verify Skip Directories Work
```python
# These directories should be automatically skipped:
.git, .github, __pycache__, node_modules, venv, .venv, tests, .pytest_cache
```

## Summary

| Context | What Gets Analyzed | Why | Status |
|---------|-------------------|-----|--------|
| **GitHub Actions CI** | Judge's own code (`ai_judge/`) | Quality checks | ✅ Correct |
| **Submission Analysis** | Only submission files | Evaluate projects | ✅ Fixed (now isolated) |
| **Local Development** | Whatever you run pylint on | Developer choice | ✅ Working |

The pylint errors you see on GitHub are **from checking the judge's code quality**, not from analyzing submissions. This is intentional and helps maintain code quality! 🎯

---

**Next Steps**:
1. If seeing CI errors, check which file has the issue
2. If it's `ai_judge/modules/code_analyzer.py`, fix the code or adjust `--disable` flags
3. If submission analysis seems wrong, check logs for path validation warnings
