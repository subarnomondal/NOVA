import sys
import os
# Add the project root to sys.path
sys.path.append(os.getcwd())

from skills.natural_events import cmd_natural_events

class MockDispatcher:
    def register(self, keyword, handler):
        print(f"Registered: {keyword}")

def test_skill():
    dispatcher = MockDispatcher()
    import skills.natural_events as ne
    ne.register(dispatcher)
    
    print("\n--- Testing Natural Events Command ---")
    result = cmd_natural_events("show natural events")
    print("\nResponse:")
    if isinstance(result, dict):
        print(result.get('response', result))
        print("\nData (Events):")
        for event in result.get('data', {}).get('events', []):
            print(f"- {event.get('title')} ({event.get('lat')}, {event.get('lon')})")
    else:
        print(result)

if __name__ == "__main__":
    test_skill()
