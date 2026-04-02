from langchain.tools import tool
import csv
from tabulate import tabulate

@tool
def csv_reader(input_str: str) -> str:
    """Read and analyze CSV data files. Input format must be 
    'filepath|question' separated by a pipe character. Use this whenever 
    asked about data in a file."""
    try:
        if "|" not in input_str:
            return "Error: Input must be in format 'filepath|question'"
            
        filepath, question = input_str.split("|", 1)
        filepath = filepath.strip()
        question = question.strip()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)
            
        if not data:
            return "Error: CSV file is empty"
            
        headers = data[0]
        rows = data[1:]
        
        table_str = tabulate(rows, headers=headers, tablefmt="grid")
        
        return f"CSV Data:\n{table_str}\n\nQuestion asked: {question}\nNote: To answer the question, look at the data in the table above."
        
    except FileNotFoundError:
        return f"Error: Could not find file {filepath}"
    except Exception as e:
        return f"Error reading CSV: {str(e)}"
