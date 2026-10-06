"""
Interactive test script for the Socratic Math Tutoring Engine.
Uses Google Gemma (model: gemma-4-31b-it) to guide students through math reasoning.
"""

import sys
import os

# Ensure backend package can be imported directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.socratic_engine import SocraticTutor


def main():
    print("=" * 60)
    print("🎓 Socratic Multimodal Tutor - Math Engine CLI Test")
    print("=" * 60)
    print("Model: gemma-4-31b-it")
    print("Pedagogy: Socratic method (diagnose reasoning -> ask 1 guiding question)")
    print("Type 'exit' to quit.\n")

    try:
        tutor = SocraticTutor(model="gemma-4-31b-it")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Tip: Run 'export GEMINI_API_KEY=\"your_key_here\"' before running this script.")
        return

    print("✅ Socratic Math Tutor initialized! Start by sharing a problem or your reasoning.\n")
    print("Example: 'I'm trying to solve 2(x + 3) = 16. My first step is 2x + 3 = 16.'\n")

    while True:
        try:
            student_message = input("Student: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTutor: Great work today! 👋")
            break

        if not student_message:
            continue

        if student_message.lower() in ("exit", "quit"):
            print("\nTutor: Great work today! Keep practicing! 👋\n")
            break

        print("\nThinking...")
        result = tutor.send_message(student_message)

        print("-" * 50)
        print(f"Tutor: {result['response']}")
        print(f"\n[🏷️ Detected Misconception: {result['misconception']}]")
        print(f"[📊 Status: {result['status']}]")
        print("-" * 50 + "\n")


if __name__ == "__main__":
    main()