"""
Rich-based logging configuration.

Provides beautiful, colored console output with structured logging
for the PDF Intelligence Extractor application.
"""

import logging
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from app.core.config import settings

# Custom theme for consistent styling
CUSTOM_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "critical": "bold white on red",
        "success": "bold green",
        "debug": "dim",
        "highlight": "bold magenta",
        "path": "blue underline",
        "number": "bold cyan",
    }
)

# Global console instance with custom theme
console = Console(theme=CUSTOM_THEME)


class AppLogger:
    """
    Application logger with Rich formatting.

    Provides structured logging with colored output and
    context-aware formatting for different components.
    """

    def __init__(self, name: str = "pdf-extractor") -> None:
        """
        Initialize the logger.

        Args:
            name: Logger name for identification
        """
        self.name = name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure and return a Rich-enabled logger."""
        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, settings.log_level))

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Rich handler for beautiful console output
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=settings.debug,
            rich_tracebacks=True,
            tracebacks_show_locals=settings.debug,
            markup=True,
        )

        # Set format
        rich_handler.setFormatter(
            logging.Formatter(
                "%(message)s",
                datefmt="[%X]",
            )
        )

        logger.addHandler(rich_handler)

        # Prevent propagation to root logger
        logger.propagate = False

        return logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def success(self, message: str) -> None:
        """Log success message with green styling."""
        console.print(f"[success]✓ {message}[/success]")

    def step(self, step_num: int, total: int, message: str) -> None:
        """Log a processing step."""
        console.print(f"[highlight]Step {step_num}/{total}:[/highlight] {message}")

    def processing(self, filename: str) -> None:
        """Log file processing start."""
        console.print(f"\n[info]📄 Processing:[/info] [path]{filename}[/path]")

    def extraction_result(
        self,
        doc_type: str,
        fields_found: int,
        confidence: float,
        time_ms: int,
    ) -> None:
        """Log extraction results in a formatted way."""
        console.print(
            f"\n[success]✓ Extraction Complete[/success]\n"
            f"  • Document Type: [highlight]{doc_type}[/highlight]\n"
            f"  • Fields Found: [number]{fields_found}[/number]\n"
            f"  • Confidence: [number]{confidence:.2%}[/number]\n"
            f"  • Processing Time: [number]{time_ms}ms[/number]"
        )


def get_logger(name: str = "pdf-extractor") -> AppLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Configured AppLogger instance
    """
    return AppLogger(name)


# Default logger instance
logger = get_logger()


def log_startup_info() -> None:
    """Log application startup information."""
    console.print("\n")
    console.rule("[bold blue]PDF Intelligence Extractor[/bold blue]")
    console.print(f"\n[info]Version:[/info] {settings.app_version}")
    console.print(f"[info]Debug Mode:[/info] {settings.debug}")
    console.print(f"[info]Log Level:[/info] {settings.log_level}")
    console.print(f"[info]LLM Mode:[/info] {settings.llm_mode}")

    if settings.llm_mode == "local":
        console.print(f"[info]Ollama Host:[/info] {settings.ollama_host}")
        console.print(f"[info]Model:[/info] {settings.ollama_model}")
    else:
        console.print("[info]Using Cloud LLM (Groq)[/info]")

    console.print(
        f"\n[success]🚀 Server starting at "
        f"http://{settings.api_host}:{settings.api_port}[/success]\n"
    )
    console.rule()
