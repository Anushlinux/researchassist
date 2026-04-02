import os
from datetime import datetime
from tabulate import tabulate
from agent import run_agent, print_trace

def log_session(result: dict):
    log_file = "logs/session.log"
    os.makedirs("logs", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write(f"QUERY: {result['query']}\n")
        f.write("STEPS:\n")
        for i, step in enumerate(result["steps"], 1):
            f.write(f"  Step {i} - Action: {step['action']} | Input: {step['action_input']} | Observation: {step['observation']}\n")
        f.write(f"FINAL ANSWER: {result['answer']}\n")
        f.write("============================================================\n\n")

if __name__ == "__main__":
    queries = [
        "What is India's current GDP in 2024 and how many times larger is the US GDP compared to India? Calculate the exact ratio.",
        "Search Wikipedia for the history of artificial intelligence. What year was the term 'Artificial Intelligence' coined and by whom?",
        "Read the file data/sample_data.csv. Which country has the highest GDP growth rate? Also calculate the average GDP across all 5 countries in the CSV."
    ]
    
    summary_data = []
    
    for i, q in enumerate(queries, 1):
        print(f"\n--- Running Demo Query {i} ---")
        result = run_agent(q)
        print_trace(result)
        log_session(result)
        
        used_tools = ", ".join(list(set([s["action"] for s in result["steps"]])))
        status = "✅" if not result["answer"].startswith("Error running agent") else "❌"
        summary_data.append([
            i,
            q[:47] + "..." if len(q) > 50 else q,
            used_tools,
            result["num_steps"],
            status
        ])
    
    print("\n\n--- SUMMARY ---")
    headers = ["Query #", "Query Preview (50 chars)", "Tools Used", "Steps", "Status (✅ or ❌)"]
    print(tabulate(summary_data, headers=headers, tablefmt="fancy_grid"))
