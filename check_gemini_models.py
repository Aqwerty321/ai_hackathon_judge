"""
Quick test script to check available Gemini models with your API key.
"""
import os
import sys

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai not installed")
    print("Run: pip install google-generativeai")
    sys.exit(1)

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not set")
    print()
    print("Set it with:")
    print('  $env:GEMINI_API_KEY="your-key-here"')
    sys.exit(1)

print("=" * 70)
print("🔍 Checking Available Gemini Models")
print("=" * 70)
print()
print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print()

try:
    # Configure API
    genai.configure(api_key=api_key)
    
    print("Listing all available models...")
    print()
    
    # List all models
    models = genai.list_models()
    
    generation_models = []
    for model in models:
        # Check if model supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            generation_models.append(model.name)
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Methods: {', '.join(model.supported_generation_methods)}")
            print()
    
    print("=" * 70)
    print("📋 Summary")
    print("=" * 70)
    print()
    
    if generation_models:
        print(f"Found {len(generation_models)} models that support generateContent:")
        for model_name in generation_models:
            print(f"  • {model_name}")
        print()
        
        # Recommend which to use
        if any('gemini-1.5-flash' in m for m in generation_models):
            recommended = next(m for m in generation_models if 'gemini-1.5-flash' in m)
            print(f"✨ RECOMMENDED for free tier: {recommended}")
        elif any('gemini-pro' in m for m in generation_models):
            recommended = next(m for m in generation_models if 'gemini-pro' in m)
            print(f"✨ RECOMMENDED for free tier: {recommended}")
        else:
            recommended = generation_models[0]
            print(f"✨ RECOMMENDED: {recommended}")
        
        print()
        print("To use with AI Judge:")
        print(f'  python -m ai_judge.main --submission your-project --gemini-model "{recommended}"')
        
    else:
        print("❌ No models found that support generateContent")
        print("   Your API key might not have access to Gemini models")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("Possible issues:")
    print("  1. Invalid API key")
    print("  2. API not enabled")
    print("  3. Network connectivity issue")
    print()
    print("Get a new API key: https://makersuite.google.com/app/apikey")

print()
print("=" * 70)
