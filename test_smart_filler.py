"""
Test the SmartFormFiller with candidate profiles
Run this to verify the human-in-loop system
"""

import yaml
import os
import sys
from bot.application.smart_form_filler import SmartFormFiller

# Set stdout encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def load_candidates():
    """Load candidates from YAML with fallback to example"""
    candidates_file = 'config/candidates.yaml'
    if not os.path.exists(candidates_file):
        candidates_file = 'config/candidates.example.yaml'
    with open(candidates_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['candidates']

def test_profile_matching():
    """Test keyword matching with profile data"""
    candidates = load_candidates()
    candidate = candidates[0]  # First candidate
    
    print("=" * 70)
    print(f"Testing profile: {candidate['name']}")
    print("=" * 70)
    
    # Create a mock page object (we won't actually use it for this test)
    class MockPage:
        pass
    
    filler = SmartFormFiller(MockPage(), candidate)
    
    # Test keyword matching
    test_questions = [
        "What is your email address?",
        "How many years of Python experience do you have?",
        "Do you require visa sponsorship?",
        "Are you willing to relocate?",
        "What is your phone number?",
        "Phone country code",
    ]
    
    print("\nTesting keyword matching:")
    print("-" * 70)
    for question in test_questions:
        answer = filler._match_keywords(question.lower())
        print(f"Q: {question}")
        print(f"A: {answer or 'WOULD ASK HUMAN'}")
        print()
    
    print("=" * 70)
    print("✅ Profile matching test complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_profile_matching()
