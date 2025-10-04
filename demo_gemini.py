"""
Demo script showing Gemini Pro API integration for AI Judge.

This script demonstrates how to:
1. Set up Gemini API key
2. Run the pipeline with Gemini
3. Compare Gemini vs BART outputs
"""

import os
import sys

def main():
    print("=" * 70)
    print("🤖 AI Judge - Gemini Pro Integration Demo")
    print("=" * 70)
    print()
    
    # Check if API key is set
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        print("✅ GEMINI_API_KEY found in environment")
        print(f"   Key: {gemini_key[:10]}...{gemini_key[-4:]}")
        print()
    else:
        print("❌ GEMINI_API_KEY not found in environment")
        print()
        print("To use Gemini Pro API, set your API key:")
        print()
        print("Windows (PowerShell):")
        print('  $env:GEMINI_API_KEY="your-api-key-here"')
        print()
        print("Linux/Mac:")
        print('  export GEMINI_API_KEY="your-api-key-here"')
        print()
        print("Get your API key: https://makersuite.google.com/app/apikey")
        print()
        print("The pipeline will fall back to local BART model if no key is set.")
        print()
    
    print("-" * 70)
    print("📋 Usage Examples:")
    print("-" * 70)
    print()
    
    print("1. Run with Gemini (if API key is set via environment):")
    print("   python -m ai_judge.main --submission project_alpha")
    print()
    
    print("2. Run with Gemini (API key via CLI):")
    print('   python -m ai_judge.main --submission project_alpha --gemini-api-key "your-key"')
    print()
    
    print("3. Use different Gemini model:")
    print('   python -m ai_judge.main --submission project_alpha --gemini-model gemini-1.5-flash')
    print()
    
    print("4. Force regeneration (bypass cache):")
    print("   python -m ai_judge.main --submission project_alpha --no-cache")
    print()
    
    print("-" * 70)
    print("🔍 How to Verify Gemini is Being Used:")
    print("-" * 70)
    print()
    print("Look for this in the output:")
    print('  [INFO] Generated combined summary using Gemini Pro API')
    print()
    print("If you see this instead:")
    print('  [INFO] Generated combined summary using local BART model')
    print()
    print("Then Gemini wasn't used (check your API key).")
    print()
    
    print("-" * 70)
    print("💡 Benefits of Gemini Pro:")
    print("-" * 70)
    print()
    print("  ✓ Better quality summaries (state-of-the-art language understanding)")
    print("  ✓ Faster performance (~1-2s vs 2-5s for BART)")
    print("  ✓ No model download needed (saves 1.6GB+)")
    print("  ✓ Lower memory usage (0MB vs ~2GB for BART)")
    print("  ✓ Free tier: 1,500 requests/day, 1M tokens/day")
    print()
    
    print("-" * 70)
    print("📊 Priority Order:")
    print("-" * 70)
    print()
    print("  1. 🥇 Google Gemini Pro API (if API key provided) ← HIGHEST PRIORITY")
    print("  2. 🥈 Local BART Model (facebook/bart-large-cnn fallback)")
    print()
    
    print("-" * 70)
    print("🚀 Quick Start:")
    print("-" * 70)
    print()
    print("Step 1: Get API key from https://makersuite.google.com/app/apikey")
    print("Step 2: Set environment variable:")
    if sys.platform == "win32":
        print('        $env:GEMINI_API_KEY="your-key-here"')
    else:
        print('        export GEMINI_API_KEY="your-key-here"')
    print("Step 3: Run pipeline normally:")
    print('        python -m ai_judge.main --submission Student-Management-System-main.zip')
    print()
    
    print("=" * 70)
    print("For detailed documentation, see: GEMINI_INTEGRATION.md")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
