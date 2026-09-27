
import json
import os

from ollama import Client

from tools import search_course, check_schedule, register_course
from harness import execute_tool, MAX_TOOL_CALLS

# Configuration 
OLLAMA_BASE_URL =  "http://localhost:11434"
LLM_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are a Student Assistant agent for a university course system.

You can help users search for courses, check course schedules/seat availability,
and register students into courses, by calling the tools provided to you.

Rules you must follow:
- Only call a tool when it is actually needed to answer the request.
- Use the exact numeric course id returned by a previous tool result when
  calling another tool -- never invent, guess, or reuse a placeholder value.
- Use the result of one tool call to decide whether another tool call is needed.
- If a tool result has status "error", explain the problem to the user in plain
  language instead of retrying the same call blindly.
- Some actions may be denied by the application due to permissions -- if that
  happens, tell the user clearly that they don't have permission, don't try to
  work around it.
- When you have enough information, give a final plain-text answer with no
  further tool calls.

"""

tools = [search_course, check_schedule, register_course]

# Names allowed to be proposed by the model. Anything else is rejected.
ALLOWED_TOOL_NAMES = {"search_course", "check_schedule", "register_course"}


class StudentAssistantAgent:
    def __init__(self, role: str, verbose: bool = True):
        self.role = role
        self.verbose = verbose
        self.client = Client(host=OLLAMA_BASE_URL)

    def run(self, user_request: str) -> str:
        """
        Runs the agent loop for a single user request:
        user request -> LLM proposes tool call -> harness executes ->
        result observed -> LLM decides again -> ... -> final answer,
        bounded by MAX_TOOL_CALLS.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request},
        ]

        call_count = 0
        final_text = ""

        for step in range(MAX_TOOL_CALLS + 1):
            if self.verbose:
                print(f"\n===== AGENT STEP {step + 1} =====")

            response = self.client.chat(
                model=LLM_MODEL,
                messages=messages,
                tools=tools,
            )

            message = response.message
            messages.append(message)

            if not message.tool_calls:
                final_text = message.content or ""
                if self.verbose:
                    print("\n[Agent] Final answer:")
                    print(final_text)
                break

            for call in message.tool_calls:
                call_count += 1
                tool_name = call.function.name
                arguments = dict(call.function.arguments)

                if self.verbose:
                    print(f"\n[Agent] Proposes tool call #{call_count}: "
                          f"{tool_name}({json.dumps(arguments)})  [role={self.role}]")

                if tool_name not in ALLOWED_TOOL_NAMES:
                    # Fail closed: reject anything not explicitly known,
                    # even before it reaches the permission table.
                    result = {"status": "error", "error_code": "UNKNOWN_TOOL",
                              "message": f"Tool '{tool_name}' is not an allowed tool."}
                else:
                    # *** Application decides here: iteration limit, permission,
                    # validation, controlled execution -- never the raw function. ***
                    result = execute_tool(tool_name, arguments, self.role, call_count)

                if self.verbose:
                    print("[Tool result]", result)

                messages.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(result),
                })
        else:
            final_text = ("[Stopped: reached the maximum tool-call limit "
                           f"({MAX_TOOL_CALLS}) for this run before a final answer was given.]")
            if self.verbose:
                print(f"\nAgent stopped: maximum iterations reached ({MAX_TOOL_CALLS}).")

        return final_text