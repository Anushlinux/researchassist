from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from dotenv import load_dotenv
import logging
import os, json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, ToolMessage

try:
    from langchain.prompts import PromptTemplate
except ImportError:
    from langchain_core.prompts import PromptTemplate

from langchain.tools import tool

from tools.calculator import calculator
from tools.csv_reader import csv_reader

try:
    from langchain.tools import WikipediaQueryRun
except ImportError:
    from langchain_community.tools.wikipedia.tool import WikipediaQueryRun

try:
    from langchain import hub
except ImportError:
    hub = None

try:
    from langchain.agents import create_react_agent, AgentExecutor

    LANGCHAIN_V1 = False
except ImportError:
    from langchain.agents import create_agent

    LANGCHAIN_V1 = True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
    convert_system_message_to_human=True
)


@tool("web_search")
def search(query: str) -> str:
    """Search the internet for current facts, news, or recent data.
    Use this for real-world information that may have changed recently."""
    try:
        search_run = DuckDuckGoSearchRun()
        return search_run.run(query)
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return "Search unavailable, using Wikipedia instead."


wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2))
wiki.name = "wikipedia"
wiki.description = "Get detailed factual background from Wikipedia. Use for history, definitions, concepts, or established facts."

tools = [search, wiki, calculator, csv_reader]

prompt = None
if not LANGCHAIN_V1:
    try:
        if hub is None:
            raise ImportError("langchain hub is unavailable in this LangChain version")
        prompt = hub.pull("hwchase17/react")
    except Exception as exc:
        logger.warning("Falling back to manual ReAct prompt: %s", exc)
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template="""You are a helpful research assistant. Answer the question as best you can.

You have access to the following tools:
{tools}

Use the following format EXACTLY:

Question: the input question you must answer
Thought: think about what to do next
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the complete final answer to the original question

Important rules:
- Always start with a Thought
- Action must be exactly one of the tool names listed
- Never skip the Observation step
- End with "Final Answer:" when done

Begin!

Question: {input}
Thought:{agent_scratchpad}""",
        )


def _create_runtime(debug: bool = False):
    if LANGCHAIN_V1:
        return (
            create_agent(
                model=llm,
                tools=tools,
                system_prompt=(
                    "You are a helpful research assistant. Use tools when needed. "
                    "Prefer web_search for current information, wikipedia for established facts, "
                    "calculator for numeric work, and csv_reader for CSV files."
                ),
                debug=debug,
            ),
            None,
        )

    react_agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=react_agent,
        tools=tools,
        verbose=debug,
        max_iterations=8,
        handle_parsing_errors="Check your output format. Use: Thought/Action/Action Input/Observation",
        return_intermediate_steps=True
    )
    return react_agent, executor


_RUNTIME_CACHE = {}


def _get_runtime(debug: bool = False):
    if debug not in _RUNTIME_CACHE:
        _RUNTIME_CACHE[debug] = _create_runtime(debug=debug)
    return _RUNTIME_CACHE[debug]


def _parse_thought(action_log: str) -> str:
    thought_text = action_log.split("Action:", 1)[0]
    return thought_text.replace("Thought:", "", 1).strip()


def _stringify_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
        return " ".join(parts).strip()
    return str(content)


def _build_steps_from_messages(messages) -> list[dict]:
    steps = []
    pending_steps = []

    for message in messages:
        if isinstance(message, AIMessage):
            thought = _stringify_content(message.content).strip() or "Tool decision made by the agent."
            for tool_call in getattr(message, "tool_calls", []) or []:
                pending_steps.append(
                    {
                        "thought": thought,
                        "action": tool_call.get("name", "unknown"),
                        "action_input": str(tool_call.get("args", "")),
                    }
                )
        elif isinstance(message, ToolMessage) and pending_steps:
            step = pending_steps.pop(0)
            observation_text = _stringify_content(message.content)
            if len(observation_text) > 500:
                observation_text = observation_text[:500] + "..."
            step["observation"] = observation_text
            steps.append(step)

    for step in pending_steps:
        step["observation"] = "No observation captured."
        steps.append(step)

    return steps


def _invoke_agent(query: str, debug: bool = False) -> dict:
    agent_runtime, executor_runtime = _get_runtime(debug=debug)

    if LANGCHAIN_V1:
        result = agent_runtime.invoke({"messages": [{"role": "user", "content": query}]})
        messages = result.get("messages", [])
        steps = _build_steps_from_messages(messages)

        answer = "No answer"
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                content = _stringify_content(message.content).strip()
                if content:
                    answer = content
                    break
        return {"answer": answer, "steps": steps}

    result = executor_runtime.invoke({"input": query})
    raw_steps = result.get("intermediate_steps", [])
    steps = []
    for action, observation in raw_steps:
        observation_text = str(observation)
        if len(observation_text) > 500:
            observation_text = observation_text[:500] + "..."
        steps.append(
            {
                "thought": _parse_thought(action.log),
                "action": action.tool,
                "action_input": str(action.tool_input),
                "observation": observation_text,
            }
        )
    return {"answer": result.get("output", "No answer"), "steps": steps}


def run_agent(query: str, capture_debug: bool = False) -> dict:
    try:
        debug_buffer = StringIO()
        invoke_kwargs = {"query": query, "debug": capture_debug}

        if capture_debug:
            with redirect_stdout(debug_buffer), redirect_stderr(debug_buffer):
                payload = _invoke_agent(**invoke_kwargs)
        else:
            payload = _invoke_agent(**invoke_kwargs)

        steps = payload["steps"]
        result = {
            "query": query,
            "answer": payload["answer"],
            "steps": steps,
            "num_steps": len(steps),
            "debug_trace": debug_buffer.getvalue().strip(),
        }
        return result
    except Exception as exc:
        logger.exception("Agent execution failed")
        return {
            "query": query,
            "answer": "Agent failed to answer the query.",
            "steps": [],
            "num_steps": 0,
            "error": str(exc),
            "debug_trace": debug_buffer.getvalue().strip() if "debug_buffer" in locals() else "",
        }


def format_steps_text(result: dict) -> str:
    lines = []
    for index, step in enumerate(result.get("steps", []), start=1):
        lines.append(f"STEP {index}")
        lines.append(f"Thought: {step['thought']}")
        lines.append(f"Action: {step['action']}")
        lines.append(f"Input: {step['action_input']}")
        lines.append(f"Observation: {step['observation'][:300]}")
        lines.append("")
    if not lines:
        lines.append("No intermediate steps recorded.")
    return "\n".join(lines).strip()


def print_trace(result: dict):
    print("╔══════════════════════════════════════════════════════╗")
    print("║  RESEARCH ASSISTANT AGENT - REASONING TRACE          ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print(f"📋 QUERY: {result.get('query', '')}")
    print()

    steps = result.get("steps", [])
    total_steps = len(steps)
    for index, step in enumerate(steps, start=1):
        observation_preview = step["observation"][:300]
        print("─────────────────────────────────────────────────────")
        print(f"STEP {index} of {total_steps}")
        print("─────────────────────────────────────────────────────")
        print(f"🤔 THOUGHT:   {step['thought']}")
        print(f"🔧 ACTION:    {step['action']}")
        print(f"📥 INPUT:     {step['action_input']}")
        print(f"👁  OBSERVE:  {observation_preview}")
        print()

    tools_used = ", ".join(dict.fromkeys(step["action"] for step in steps)) or "None"
    print("╔══════════════════════════════════════════════════════╗")
    print("║  ✅ FINAL ANSWER                                      ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(result.get("answer", "No answer"))
    if result.get("error"):
        print(f"\nError: {result['error']}")
    print()
    print(f"📊 Stats: {result.get('num_steps', 0)} steps taken | Tools used: {tools_used}")


if __name__ == "__main__":
    print(r"██████╗ ███████╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗")
    print(r"██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║")
    print(r"██████╔╝█████╗  ███████╗█████╗  ███████║██████╔╝██║     ███████║")
    print(r"██╔══██╗██╔══╝  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║")
    print(r"██║  ██║███████╗███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║")
    print("     AGENT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Powered by Gemini 2.5 Flash + LangChain ReAct")
    print("Tools: web_search | wikipedia | calculator | csv_reader")
    print("Type 'exit' to quit\n")

    while True:
        query = input("🔍 Your question: ").strip()
        if query.lower() in ["exit", "quit", ""]:
            break
        result = run_agent(query)
        print_trace(result)
