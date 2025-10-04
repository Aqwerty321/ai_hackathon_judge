# AI Judge - Summary Generation Architecture

## System Flow with Gemini Priority

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI Judge Pipeline Start                         │
│                                                                     │
│  1. Video Analysis  →  Extract transcript from video/description   │
│  2. Text Analysis   →  Extract project description from README     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 Combined Summary Generation                         │
│                                                                     │
│  Input: Project Description + Video Transcript                     │
│  ├─ "Project Description: {README content}"                        │
│  └─ "Presentation Transcript: {video transcript}"                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  PRIORITY 1: Google Gemini Pro API                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ IF gemini_api_key is set:                            │         │
│  │                                                       │         │
│  │  1. Configure genai.configure(api_key=key)          │         │
│  │  2. Create client = GenerativeModel(model)          │         │
│  │  3. Send prompt with project info                    │         │
│  │  4. Receive summary from Gemini                      │         │
│  │  5. Clean markdown formatting                        │         │
│  │                                                       │         │
│  │  ✅ SUCCESS → Return Gemini summary                  │         │
│  │  ❌ FAILURE → Fall through to Priority 2             │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
│  Configuration:                                                     │
│  • API Key: $env:GEMINI_API_KEY or --gemini-api-key               │
│  • Model: gemini-1.5-pro (default) or --gemini-model              │
│  • Parameters: temp=0.3, top_p=0.8, max_tokens=200                │
│                                                                     │
│  Benefits:                                                          │
│  ⭐ Highest quality (state-of-the-art)                             │
│  ⚡ Fastest (1-2 seconds)                                          │
│  💾 No model download needed                                       │
│  🆓 Free tier: 1,500 requests/day                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ (if Gemini not available)
┌─────────────────────────────────────────────────────────────────────┐
│            PRIORITY 2: Local BART Model (Fallback)                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐         │
│  │ IF transformers library available:                   │         │
│  │                                                       │         │
│  │  1. Load facebook/bart-large-cnn pipeline           │         │
│  │  2. Truncate input to 4096 chars                     │         │
│  │  3. Run local summarization                          │         │
│  │  4. Extract summary_text from result                 │         │
│  │                                                       │         │
│  │  ✅ SUCCESS → Return BART summary                    │         │
│  │  ❌ FAILURE → Return None                            │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
│  Model Details:                                                     │
│  • Model: facebook/bart-large-cnn (~1.6 GB)                        │
│  • Device: CPU/CUDA/MPS (configurable)                             │
│  • Parameters: max_length=150, min_length=40                       │
│                                                                     │
│  Benefits:                                                          │
│  ✅ Works offline                                                  │
│  ✅ No API key needed                                              │
│  ✅ Deterministic results                                          │
│  ⚠️  Slower (2-5 seconds)                                          │
│  ⚠️  Requires model download                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     HTML Report Generation                          │
│                                                                     │
│  Combined summary displayed in prominent section:                  │
│                                                                     │
│  ┌────────────────────────────────────────────────────┐           │
│  │ 🤖 AI-Powered Project Summary                      │           │
│  │ ───────────────────────────────────────────────    │           │
│  │                                                     │           │
│  │ [Generated summary appears here in blue box]       │           │
│  │                                                     │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                     │
│  Output: reports/<submission>_report.html                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Configuration Sources (Priority Order)

```
┌──────────────────────────────────────────────┐
│        Gemini API Key Resolution             │
└──────────────────────────────────────────────┘
              ↓
    1. CLI Argument (--gemini-api-key)
              ↓ (if not provided)
    2. Environment Variable (GEMINI_API_KEY)
              ↓ (if not set)
    3. Config Default (None → use BART fallback)
```

## Error Handling & Fallback Chain

```
┌─────────────────────────────────────────────┐
│     Attempt Gemini Pro API                  │
│                                             │
│  • Check if API key exists                 │
│  • Check if genai library available        │
│  • Make API call with retry logic          │
└─────────────────────────────────────────────┘
         ↓ SUCCESS              ↓ FAILURE
    ✅ Return                    ↓
    Gemini Summary    ┌─────────────────────────────────┐
                      │  LOG: "Gemini API failed: {err}" │
                      │  Fall through to BART            │
                      └─────────────────────────────────┘
                                 ↓
                      ┌─────────────────────────────────┐
                      │     Attempt Local BART          │
                      │                                 │
                      │  • Check if pipeline available  │
                      │  • Load/use cached model        │
                      │  • Run local inference          │
                      └─────────────────────────────────┘
                           ↓ SUCCESS    ↓ FAILURE
                          ✅ Return      ❌ Return
                          BART Summary   None
```

## Comparison Matrix

```
┌─────────────────────┬─────────────────┬──────────────────┐
│      Feature        │   Gemini Pro    │   Local BART     │
├─────────────────────┼─────────────────┼──────────────────┤
│  Quality            │  ⭐⭐⭐⭐⭐      │  ⭐⭐⭐⭐         │
│  Speed              │  1-2 seconds    │  2-5 seconds     │
│  Setup              │  API key only   │  1.6GB download  │
│  Memory             │  ~0 MB          │  ~2 GB           │
│  Cost               │  ~$0.001/req    │  Free            │
│  Offline Support    │  ❌             │  ✅              │
│  API Limits         │  1,500/day      │  Unlimited       │
│  Context Length     │  ~1M tokens     │  4,096 chars     │
│  Priority           │  🥇 HIGHEST     │  🥈 Fallback     │
└─────────────────────┴─────────────────┴──────────────────┘
```

## Example Outputs

### Gemini Pro Summary (Typical Output)
```
This Student Management System is a Java-based application designed 
to manage student records through CRUD operations. It features a 
command-line interface for adding, updating, deleting, and searching 
student information, with optional file-based persistence. The project 
demonstrates core OOP concepts including encapsulation and inheritance.
```
**Characteristics:**
- More detailed and structured
- Better context understanding
- Natural flow between concepts
- Technical terminology used appropriately

### Local BART Summary (Typical Output)
```
A simple Student Management System built in Java to manage student 
records including adding, updating, deleting, and displaying student 
details. This project demonstrates the core concepts of object-oriented 
programming (OOP) and file handling in Java.
```
**Characteristics:**
- Concise and factual
- Good extraction of key points
- Sometimes more generic phrasing
- Reliable fallback option

## Deployment Scenarios

### Scenario 1: Production with API Key
```
User sets GEMINI_API_KEY
       ↓
Pipeline uses Gemini for all summaries
       ↓
Fast, high-quality results
       ↓
Cost: ~$0.50 per 1,000 submissions
```

### Scenario 2: Development/Testing without API Key
```
No GEMINI_API_KEY set
       ↓
Pipeline uses local BART model
       ↓
Slower but works offline
       ↓
Cost: Free (uses local compute)
```

### Scenario 3: Hybrid (API Failure Handling)
```
GEMINI_API_KEY set but API fails
       ↓
Pipeline attempts Gemini
       ↓
Gemini fails (quota/network/etc)
       ↓
Automatic fallback to BART
       ↓
System continues without interruption
```

## Integration Points

```
ai_judge/
├── config.py
│   ├── gemini_api_key: str | None       ← API key config
│   └── gemini_model: str                 ← Model selection
│
├── main.py
│   ├── CLI args: --gemini-api-key       ← User input
│   ├── CLI args: --gemini-model         ← Model override
│   └── Env check: GEMINI_API_KEY        ← Environment
│
├── modules/
│   └── text_analyzer.py
│       ├── _generate_combined_summary() ← Entry point
│       ├── _generate_summary_with_gemini() ← Priority 1
│       ├── _summarizer (BART pipeline)  ← Priority 2
│       └── _merge_texts()               ← Text preparation
│
└── templates/
    └── submission_report.html.j2
        └── {% if text.combined_summary %} ← Display
```

## Monitoring & Logging

```
[INFO] Generated combined summary using Gemini Pro API
       ↳ Success: Gemini was used

[WARNING] Gemini API summary generation failed: [error]
       ↳ Gemini failed, falling back

[INFO] Generated combined summary using local BART model
       ↳ Using BART (either no key or Gemini failed)

[DEBUG] Combined summary generation failed: [error]
       ↳ Both methods failed, no summary
```

## Summary

This architecture ensures:
1. **Best quality first** - Gemini Pro gets priority
2. **Reliable fallback** - BART always available
3. **Easy configuration** - Environment variable or CLI
4. **Graceful degradation** - No failures, just fallbacks
5. **Full transparency** - Clear logging of which method used

**Result: Production-ready summarization with cloud intelligence and local reliability!** 🚀
