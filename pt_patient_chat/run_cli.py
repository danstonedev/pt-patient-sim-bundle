
# Simple CLI runner for quick testing without FastAPI
import json, sys
from engine import load_persona, patient_reply

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cli.py P-0002")
        sys.exit(1)
    pid = sys.argv[1]
    persona = load_persona(pid)
    print(f"Loaded persona for {pid}: {persona['identity']['preferred_name']} / {persona['condition']}")
    state = {}
    while True:
        try:
            user = input("\nYou: ").strip()
        except EOFError:
            break
        if not user or user.lower() in {"quit", "exit"}:
            break
        reply, state, tags = patient_reply(user, persona, state)
        print(f"Patient: {reply}")
        print(f"[tags: {', '.join(tags)}]")

if __name__ == "__main__":
    main()
