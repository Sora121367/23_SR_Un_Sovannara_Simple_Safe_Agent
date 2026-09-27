

import argparse
import sys

from agent import StudentAssistantAgent


def main():
    parser = argparse.ArgumentParser(description="Student Assistant Agent (LangGraph + local Ollama llama3.2)")
    parser.add_argument("request", type=str, help="The user's request in natural language.")
    parser.add_argument("--role", type=str, default="student", choices=["student", "admin"],
                         help="Role of the current user (default: student).")
    args = parser.parse_args()

    print(f"=== Student Assistant Agent ===")
    print(f"Role: {args.role}")
    print(f"User request: {args.request}\n")

    agent = StudentAssistantAgent(role=args.role)
    agent.run(args.request)


if __name__ == "__main__":
    sys.exit(main())