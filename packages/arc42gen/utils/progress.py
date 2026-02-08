"""
Rich-based progress tracking for arc42gen documentation generation.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProgressStep:
    """A single step in the generation pipeline."""
    name: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    details: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        if self.start_time:
            return time.time() - self.start_time
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "duration": round(self.duration, 2) if self.duration else None,
            "details": self.details,
            "error": self.error,
        }


@dataclass
class LLMCallRecord:
    """Record of a single LLM API call."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    duration: float
    cost: Optional[float] = None

    @property
    def tokens_per_second(self) -> float:
        if self.duration > 0:
            return self.output_tokens / self.duration
        return 0.0


class ProgressTracker:
    """
    Tracks progress of the documentation generation pipeline.

    Prints step-by-step status to the console using Rich,
    and writes a JSON status file for external monitoring.
    """

    def __init__(self, output_dir: str = ".", verbose: bool = True):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.console = Console(stderr=True)
        self.steps: list[ProgressStep] = []
        self.llm_calls: list[LLMCallRecord] = []
        self.current_step: Optional[ProgressStep] = None
        self.start_time = time.time()

        # Aggregate metrics
        self.files_analyzed: int = 0
        self.total_loc: int = 0
        self.total_tokens_in: int = 0
        self.total_tokens_out: int = 0
        self.total_cost: float = 0.0
        self.errors: list[str] = []

    def start_step(self, name: str, details: Optional[dict] = None) -> None:
        """Start a new pipeline step."""
        step = ProgressStep(
            name=name,
            status=StepStatus.RUNNING,
            start_time=time.time(),
            details=details or {},
        )
        self.steps.append(step)
        self.current_step = step

        if self.verbose:
            self.console.print(f"[bold blue]>[/] {name}...", highlight=False)

        self._update_status_file()

    def complete_step(self, details: Optional[dict] = None) -> None:
        """Mark the current step as complete."""
        if not self.current_step:
            return

        self.current_step.status = StepStatus.COMPLETE
        self.current_step.end_time = time.time()
        if details:
            self.current_step.details.update(details)

        if self.verbose:
            dur = self.current_step.duration
            dur_str = f" ({dur:.1f}s)" if dur else ""
            self.console.print(
                f"  [green]\u2713[/] {self.current_step.name}{dur_str}",
                highlight=False,
            )

        self.current_step = None
        self._update_status_file()

    def fail_step(self, error: str) -> None:
        """Mark the current step as failed."""
        if not self.current_step:
            return

        self.current_step.status = StepStatus.FAILED
        self.current_step.end_time = time.time()
        self.current_step.error = error
        self.errors.append(f"{self.current_step.name}: {error}")

        if self.verbose:
            self.console.print(
                f"  [red]\u2717[/] {self.current_step.name}: {error}",
                highlight=False,
            )

        self.current_step = None
        self._update_status_file()

    def log_file_analysis(self, path: str, loc: int) -> None:
        """Track a file being analyzed."""
        self.files_analyzed += 1
        self.total_loc += loc

    def log_llm_call(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration: float = 0.0,
        cost: Optional[float] = None,
    ) -> None:
        """Track an LLM API call."""
        record = LLMCallRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration=duration,
            cost=cost,
        )
        self.llm_calls.append(record)
        self.total_tokens_in += input_tokens
        self.total_tokens_out += output_tokens
        if cost:
            self.total_cost += cost

        if self.verbose:
            tok_s = f"{record.tokens_per_second:.0f} tok/s" if duration > 0 else ""
            tokens_str = ""
            if input_tokens or output_tokens:
                tokens_str = f" [{input_tokens}in/{output_tokens}out]"
            self.console.print(
                f"    [dim]LLM {provider}/{model}: {duration:.1f}s{tokens_str} {tok_s}[/]",
                highlight=False,
            )

    def show_summary(self) -> None:
        """Display a Rich summary table at the end of generation."""
        if not self.verbose:
            return

        total_duration = time.time() - self.start_time
        self.console.print()

        # Summary table
        table = Table(title="Generation Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")

        table.add_row("Total time", f"{total_duration:.1f}s")
        table.add_row("Steps completed", str(sum(1 for s in self.steps if s.status == StepStatus.COMPLETE)))
        table.add_row("Steps failed", str(sum(1 for s in self.steps if s.status == StepStatus.FAILED)))
        table.add_row("Files analyzed", str(self.files_analyzed))
        table.add_row("Total LOC", f"{self.total_loc:,}")
        table.add_row("LLM calls", str(len(self.llm_calls)))
        table.add_row("Tokens (in/out)", f"{self.total_tokens_in:,} / {self.total_tokens_out:,}")

        if self.total_cost > 0:
            table.add_row("Estimated cost", f"${self.total_cost:.4f}")

        self.console.print(table)

        # Step breakdown tree
        if self.steps:
            tree = Tree("[bold]Pipeline Steps[/]")
            for step in self.steps:
                dur = f" ({step.duration:.1f}s)" if step.duration else ""
                if step.status == StepStatus.COMPLETE:
                    icon = "[green]\u2713[/]"
                elif step.status == StepStatus.FAILED:
                    icon = "[red]\u2717[/]"
                elif step.status == StepStatus.RUNNING:
                    icon = "[yellow]\u25cb[/]"
                else:
                    icon = "[dim]\u25cb[/]"
                tree.add(f"{icon} {step.name}{dur}")
            self.console.print(tree)

        # Errors
        if self.errors:
            self.console.print()
            self.console.print("[bold red]Errors:[/]")
            for err in self.errors:
                self.console.print(f"  - {err}")

    def _update_status_file(self) -> None:
        """Write current status to .arc42gen-status.json for external monitoring."""
        try:
            status = {
                "status": "running" if self.current_step else "idle",
                "current_step": self.current_step.name if self.current_step else None,
                "elapsed": round(time.time() - self.start_time, 1),
                "steps": [s.to_dict() for s in self.steps],
                "metrics": {
                    "files_analyzed": self.files_analyzed,
                    "total_loc": self.total_loc,
                    "llm_calls": len(self.llm_calls),
                    "tokens_in": self.total_tokens_in,
                    "tokens_out": self.total_tokens_out,
                    "errors": len(self.errors),
                },
            }
            status_path = self.output_dir / ".arc42gen-status.json"
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(json.dumps(status, indent=2))
        except Exception:
            pass  # Don't fail the pipeline for status file issues

    def get_status_dict(self) -> dict:
        """Return current status as a dictionary (for API use)."""
        return {
            "status": "running" if self.current_step else "idle",
            "current_step": self.current_step.name if self.current_step else None,
            "elapsed": round(time.time() - self.start_time, 1),
            "steps_completed": sum(1 for s in self.steps if s.status == StepStatus.COMPLETE),
            "steps_total": len(self.steps),
            "llm_calls": len(self.llm_calls),
            "errors": len(self.errors),
        }


class ProgressBar:
    """Thin wrapper around rich.progress.Progress for file-level iteration."""

    def __init__(self, description: str = "Processing", total: Optional[int] = None, verbose: bool = True):
        self.description = description
        self.total = total
        self.verbose = verbose
        self._progress: Optional[Progress] = None
        self._task_id = None

    def __enter__(self):
        if self.verbose:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=Console(stderr=True),
            )
            self._progress.__enter__()
            self._task_id = self._progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, *args):
        if self._progress:
            self._progress.__exit__(*args)

    def advance(self, amount: int = 1) -> None:
        if self._progress and self._task_id is not None:
            self._progress.advance(self._task_id, amount)

    def update(self, description: Optional[str] = None, total: Optional[int] = None) -> None:
        if self._progress and self._task_id is not None:
            kwargs = {}
            if description is not None:
                kwargs["description"] = description
            if total is not None:
                kwargs["total"] = total
            self._progress.update(self._task_id, **kwargs)
