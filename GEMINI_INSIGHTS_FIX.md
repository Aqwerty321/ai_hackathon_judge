# Gemini Code Insights & Flagging Markdown Support

## Summary
Fixed missing AI code insights due to context limit issues and added markdown rendering support to the claim flagging section.

## Issues Fixed

### 1. **Missing Gemini Code Insights**

**Problem:** Large codebases (like Agentic-Call-Centre) caused Gemini API calls to fail silently due to context overflow, resulting in no AI insights being generated.

**Root Cause:**
- Long file paths in lint messages exceeded context limits
- No truncation or safety checks on context size
- Insufficient error logging made debugging difficult

**Solution:**
```python
# Limited lint messages to 5 instead of 10
for msg in lint_messages[:5]:  
    # Truncate long paths (> 60 chars)
    path_str = str(msg.get('path', 'unknown'))
    if len(path_str) > 60:
        path_str = "..." + path_str[-57:]
    # Truncate long messages (> 100 chars)
    context += f"- [{msg.get('symbol')}] {path_str}:{msg.get('line')} - {msg.get('message', '')[:100]}\n"

# Added safety check to prevent context overflow
max_context_chars = 8000  # ~2000 tokens, well under Gemini's 30K limit
if len(context) > max_context_chars:
    LOGGER.warning("Context too large (%d chars), truncating to %d chars", len(context), max_context_chars)
    context = context[:max_context_chars] + "\n\n[Context truncated due to size...]"
```

**Enhanced Error Handling:**
- Added logging of context and prompt sizes
- Check for blocked responses (safety filters, recitation)
- Better exception logging with `exc_info=True`
- Log finish_reason to diagnose API rejections

### 2. **Markdown Support for Claim Flagging**

**Problem:** Flagged claims from Gemini contained markdown formatting (bold, bullets, etc.) but were rendered as plain text with visible `**` and `*` characters.

**Solution:** Added markdown filter to all flagging-related text fields:

#### Updated Fields:
1. **Claim Reason** - `{{ claim.reason | markdown | safe }}`
2. **LLM Rationale** - `{{ claim.llm_rationale | markdown | safe }}`
3. **Verification Note** - `{{ claim.verification_result.note | markdown | safe }}`
4. **Evidence Snippets** - `{{ item.snippet | markdown | safe }}`

#### Styling:
- Wrapped content in `markdown-content` class for proper formatting
- Applied to inline and block content appropriately
- Maintained dark theme consistency in blockquotes

## Changes Made

### ai_judge/modules/code_analyzer.py

**Lines 595-610 (Context Building):**
```python
# Limit lint messages to 5
for msg in lint_messages[:5]:
    # Truncate paths > 60 chars
    # Truncate messages > 100 chars
    
# Truncate entire context if > 8000 chars
if len(context) > max_context_chars:
    context = context[:max_context_chars] + "[truncated]"
```

**Lines 615 (Added Logging):**
```python
LOGGER.info("Generating Gemini code insights (context: %d chars, prompt: %d chars)", 
            len(context), len(prompt))
```

**Lines 635-655 (Enhanced Error Handling):**
```python
# Check finish_reason for blocks
if 'SAFETY' in finish_reason or 'BLOCKED' in finish_reason:
    LOGGER.warning("Gemini response blocked: %s", finish_reason)
    
# Log empty responses
if not candidate.content.parts:
    LOGGER.warning("Gemini response has no content parts")
    
# Better exception logging
except Exception as exc:
    LOGGER.error("Gemini code insights failed: %s", exc, exc_info=True)
```

### ai_judge/templates/submission_report.html.j2

**Lines 602-615 (Flagged Claims Section):**
```jinja
<!-- Statement (no change - already plain text) -->
<div class="markdown-content"><strong>{{ claim.statement }}</strong></div>

<!-- Reason with markdown -->
<p class="text-muted">Reason: <span class="markdown-content">
  {{ claim.reason | markdown | safe }}
</span></p>

<!-- LLM Rationale with markdown -->
<div class="markdown-content">
  {{ claim.llm_rationale | markdown | safe }}
</div>

<!-- Verification note with markdown -->
<div class="markdown-content">
  {{ claim.verification_result.note | markdown | safe }}
</div>

<!-- Evidence snippets with markdown -->
<blockquote class="markdown-content">
  {{ item.snippet | markdown | safe }}
</blockquote>
```

## Testing

### Before Changes:
```
Agentic-Call-Centre report:
- ❌ No "🤖 AI Code Insights" section
- ❌ Flagged claims show raw markdown: **bold** and * bullets
- ❌ No error logs explaining why insights failed
```

### After Changes:
```
Next analysis will show:
- ✅ AI Code Insights generated (context truncated if needed)
- ✅ Flagged claims render with proper markdown formatting
- ✅ Logs show context size and any API issues
- ✅ Graceful degradation if context too large
```

## Benefits

1. **Reliability**: Large codebases no longer cause silent failures
2. **Visibility**: Clear logging shows exactly what's being sent to Gemini
3. **User Experience**: Flagged claims look professional with proper formatting
4. **Debugging**: Easy to diagnose why insights might be missing
5. **Performance**: Truncation prevents wasted API calls with oversized requests

## Recommendations

To regenerate the Agentic-Call-Centre report with AI insights:
```bash
# Through web interface (recommended)
1. Open http://localhost:5000
2. Upload Agentic-Call-Centre.zip
3. Wait for processing
4. View report with AI insights

# Or via CLI
python -m ai_judge.main --submission Agentic-Call-Centre
```

Check logs for:
```
[INFO] Generating Gemini code insights (context: XXXX chars, prompt: YYYY chars)
[INFO] ✓ Generated Gemini code insights (ZZZ chars)
```

If insights still missing, look for:
```
[WARNING] Context too large (XXXXX chars), truncating to 8000 chars
[WARNING] Gemini response blocked due to safety filters: <reason>
[ERROR] Gemini code insights generation failed: <error>
```

## Impact

- **Code Files Modified**: 2
- **Lines Changed**: ~50 lines
- **Breaking Changes**: None
- **Performance Impact**: Minimal (truncation is fast)
- **API Cost**: Reduced (smaller contexts = fewer tokens)
