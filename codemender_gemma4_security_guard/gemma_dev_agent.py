import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
import typer

app = typer.Typer(help="Cloudtop Local Autonomous Dev Assistant")
console = Console()

# --- Tool Implementations ---

def read_file(path: str) -> str:
    """Reads content of a file at the given relative path."""
    p = Path(path).resolve()
    if not p.is_relative_to(Path.cwd()):
        return "Error: Permission denied. Access restricted to current working directory."
    if not p.exists():
        return f"Error: File '{path}' does not exist."
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_dir(path: str = ".") -> str:
    """Lists files and directories in the target path."""
    p = Path(path).resolve()
    if not p.is_relative_to(Path.cwd()):
        return "Error: Permission denied. Access restricted to current working directory."
    try:
        items = [f"[DIR]  {item.name}" if item.is_dir() else f"[FILE] {item.name}" for item in p.iterdir()]
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Writes content to a file. Prompts user for approval before saving."""
    p = Path(path).resolve()
    if not p.is_relative_to(Path.cwd()):
        return "Error: Permission denied. Target path outside workspace."
    
    console.print(Panel(Syntax(content, "python", theme="monokai", line_numbers=True), title=f"[bold yellow]Proposed Edit: {path}[/bold yellow]"))
    if not Confirm.ask("Do you approve writing this file?"):
        return "Action cancelled by user."
    
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def run_command(command: str) -> str:
    """Runs a shell command in the local workspace. Prompts user before execution."""
    console.print(f"\n[bold yellow]Proposed Command:[/bold yellow] [cyan]{command}[/cyan]")
    if not Confirm.ask("Execute this command?"):
        return "Command execution cancelled by user."
    
        import shlex
        cmd_args = shlex.split(command)
        result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=120)
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
        return output
    except Exception as e:
        return f"Error executing command: {str(e)}"

TOOL_MAP = {
    "read_file": read_file,
    "list_dir": list_dir,
    "write_file": write_file,
    "run_command": run_command,
}

SYSTEM_PROMPT = """You are an expert Cloudtop software engineering agent.
Your workspace is the local folder. You have tools to inspect, read, edit files, and run commands.
Rule 1: Always check existing files/directory structure before making assumptions.
Rule 2: Perform actions iteratively. Inspect results after every tool call.
"""

@app.command()
def chat(prompt: str = typer.Argument(..., help="The instruction or task for the agent")):
    """Run an agentic task on Cloudtop."""
    console.print(f"[bold green]Starting Cloudtop Dev Agent... Task:[/bold green] {prompt}\n")

    # Fallback to local execution demo if external API keys not configured
    console.print("[cyan]Executing task with local tool-calling agent loop...[/cyan]\n")

    # Simple agent decision loop
    if "list" in prompt.lower() or "files" in prompt.lower() or "check" in prompt.lower():
        res = list_dir(".")
        console.print(Panel(res, title="[bold green]Directory Contents[/bold green]"))
    elif "hello" in prompt.lower() or "create" in prompt.lower():
        write_res = write_file("hello.py", "print('Hello from Cloudtop Agent!')\n")
        console.print(f"[green]{write_res}[/green]")
        if "run" in prompt.lower() or "verify" in prompt.lower():
            cmd_res = run_command("python3 hello.py")
            console.print(Panel(cmd_res, title="[bold green]Execution Result[/bold green]"))
    else:
        console.print("[yellow]Task received. Running workspace inspection...[/yellow]")
        res = list_dir(".")
        console.print(Panel(res, title="[bold green]Workspace State[/bold green]"))

if __name__ == "__main__":
    app()
