import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"

def query_rag(text: str, focus: Optional[str] = None):
    payload = {"query": text}
    if focus:
        payload["focus_component"] = focus
    
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    print("=" * 70)
    print("  CHAMUSCA 1920 RAG — Interactive Query Tool")
    print("=" * 70)
    print("\nCommands:")
    print("  • Type a question to ask the RAG")
    print("  • /focus <component_id>  — Set focus for next query")
    print("  • /clear                 — Clear focus")
    print("  • /quit or /exit         — Exit")
    print("\n" + "=" * 70 + "\n")
    
    focus_component = None
    
    while True:
        if focus_component:
            prompt = f"[FOCUS: {focus_component}] > "
        else:
            prompt = "> "
        
        user_input = input(prompt).strip()
        
        if not user_input:
            continue
        
        # Handle commands
        if user_input.startswith("/"):
            cmd_parts = user_input.split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            
            if cmd in ["/quit", "/exit"]:
                print("Goodbye!")
                break
            elif cmd == "/clear":
                focus_component = None
                print("✓ Focus cleared")
                continue
            elif cmd == "/focus":
                if len(cmd_parts) > 1:
                    focus_component = cmd_parts[1]
                    print(f"✓ Focus set to: {focus_component}")
                else:
                    print("Usage: /focus <component_id>")
                continue
            else:
                print(f"Unknown command: {cmd}")
                continue
        
        # Send query
        print("\n⏳ Querying RAG...\n")
        result = query_rag(user_input, focus_component)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}\n")
            continue
        
        # Display answer
        print("📖 ANSWER:")
        print("-" * 70)
        print(result.get("answer", "(no answer)"))
        print("-" * 70)
        
        # Display sources
        sources = result.get("sources", [])
        if sources:
            print(f"\n📚 SOURCES ({len(sources)}):")
            for i, src in enumerate(sources[:5], 1):  # Show top 5
                source_name = src.get('doc_id') or src.get('id') or src.get('source') or src.get('filename') or "Unknown Source"
                score = src.get('score', 0.0)
                print(f"  {i}. {source_name} (score: {score:.3f})")
        
        # Display follow-ups
        follow_ups = result.get("follow_ups", [])
        if follow_ups:
            print(f"\n💡 SUGGESTED FOLLOW-UPS:")
            for i, q in enumerate(follow_ups, 1):
                print(f"  {i}. {q}")
        
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()