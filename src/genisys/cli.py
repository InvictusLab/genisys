"""Console script for genisys."""

import asyncio
import os

import typer
from rich.console import Console

from agent.loop import AgentLoop

app = typer.Typer()
console = Console()


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send to the agent."),
    model: str | None = typer.Option(None, "--model", "-m", help="Override the model name."),
    api_key: str | None = typer.Option(None, "--api-key", help="Override QWEN_API_KEY."),
    base_url: str | None = typer.Option(None, "--base-url", help="Override QWEN_BASE_URL."),
    max_tokens: int = typer.Option(1024, "--max-tokens", help="Maximum tokens to generate."),
    temperature: float = typer.Option(0.7, "--temperature", help="Sampling temperature."),
) -> None:
    """Send one message to the agent and print the response."""
    try:
        resolved_api_key = api_key or os.getenv("QWEN_API_KEY")
        resolved_base_url = base_url or os.getenv("QWEN_BASE_URL")
        loop = AgentLoop(
            message,
            model=model,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response = asyncio.run(loop.run())
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(response or "(no response)")


@app.command()
def agent():
    pass

if __name__ == "__main__":
    app()
