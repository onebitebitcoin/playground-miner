import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground_server.settings')
django.setup()

from blocks.views import IntentClassifierAgent

prompt = "비트코인과 대표 자산의 연도별 연말 가격을 알려줘"
quick_requests = []

print(f"Testing Prompt: {prompt}\n")

# 1. Run Intent Classifier
classifier = IntentClassifierAgent()
intent_result, intent_logs = classifier.run(prompt, quick_requests)

print("--- Intent Classifier Result ---")
print(f"Method: {intent_result.get('calculation_method')}")
print("Logs:")
for log in intent_logs:
    print(f"  {log}")
print("\n")
