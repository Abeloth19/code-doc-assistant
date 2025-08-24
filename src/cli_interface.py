import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog, yes_no_dialog
from prompt_toolkit.formatted_text import HTML
import time
import sys
from typing import Dict, List, Optional
from .utils import Logger
from .config import Config

class BeautifulCLI:
    def __init__(self):
        self.console = Console()
        self.config = Config()
        
    def show_welcome(self):
        title = Text("🤖 Code Documentation Assistant", style="bold cyan")
        subtitle = Text("AI-powered documentation generation and Q&A", style="italic blue")
        
        welcome_panel = Panel(
            f"{title}\n{subtitle}\n\n"
            "✨ Analyze codebases\n"
            "📝 Generate documentation\n" 
            "🤔 Ask questions about code\n"
            "🚀 Built with OpenAI GPT",
            title="Welcome",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(welcome_panel)
        self.console.print("\n")

    def get_repository_input(self) -> tuple[str, str]:
        self.console.print("[bold]Repository Source[/bold]", style="cyan")
        
        choices = [
            ("github", "🌐 GitHub Repository URL"),
            ("local", "📁 Local Directory Path"),
        ]
        
        result = radiolist_dialog(
            title="Repository Source",
            text="How would you like to analyze code?",
            values=choices
        ).run()
        
        if result == "github":
            repo_url = Prompt.ask(
                "\n[cyan]Enter GitHub repository URL[/cyan]",
                default="https://github.com/",
                console=self.console
            )
            return "github", repo_url
        
        elif result == "local":
            local_path = Prompt.ask(
                "\n[cyan]Enter local directory path[/cyan]",
                default=".",
                console=self.console
            )
            return "local", local_path
        
        else:
            self.console.print("[red]Operation cancelled[/red]")
            sys.exit(0)

    def show_analysis_progress(self, total_steps: int = 6):
        steps = [
            "🔍 Analyzing repository structure",
            "📊 Parsing code files", 
            "🧠 Generating documentation",
            "🔗 Building knowledge base",
            "✨ Finalizing analysis",
            "🎉 Complete!"
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=True
        ) as progress:
            
            task = progress.add_task("Starting analysis...", total=total_steps)
            
            for i, step in enumerate(steps):
                progress.update(task, description=step, completed=i)
                time.sleep(0.8)  # Simulate processing
                
            progress.update(task, completed=total_steps)
        
        return True

    def show_analysis_results(self, analysis_results: Dict):
        summary = analysis_results.get('summary', {})
        architecture = analysis_results.get('architecture', {})
        repo_info = analysis_results.get('repo_info', {})
        
        # Create results table
        results_table = Table(title="📊 Analysis Results", box=box.ROUNDED)
        results_table.add_column("Metric", style="cyan", no_wrap=True)
        results_table.add_column("Value", style="green")
        
        results_table.add_row("Project", repo_info.get('name', 'Unknown'))
        results_table.add_row("Files Analyzed", str(len(analysis_results.get('parsed_files', []))))
        results_table.add_row("Languages", ", ".join(summary.get('languages', {}).keys()))
        results_table.add_row("Total Functions", str(summary.get('total_functions', 0)))
        results_table.add_row("Total Classes", str(summary.get('total_classes', 0)))
        results_table.add_row("Test Coverage", architecture.get('test_coverage', {}).get('coverage_level', 'Unknown'))
        
        self.console.print("\n")
        self.console.print(results_table)
        
        # Show language distribution
        if summary.get('languages'):
            self.console.print("\n[bold]Language Distribution:[/bold]")
            lang_columns = []
            for lang, count in summary['languages'].items():
                lang_panel = Panel(
                    f"[bold]{count}[/bold] files",
                    title=f"[cyan]{lang}[/cyan]",
                    border_style="blue",
                    width=15
                )
                lang_columns.append(lang_panel)
            
            self.console.print(Columns(lang_columns, padding=(0, 1)))

    def show_documentation_options(self) -> List[str]:
        self.console.print("\n[bold cyan]📝 Documentation Options[/bold cyan]")
        
        options = {
            "overview": "📖 Project Overview",
            "api": "🔧 API Documentation", 
            "setup": "⚙️ Setup Guide",
            "files": "📁 File Documentation",
            "all": "🎯 Complete Documentation Suite"
        }
        
        choices = [(key, value) for key, value in options.items()]
        
        result = radiolist_dialog(
            title="Documentation Generation",
            text="What documentation would you like to generate?",
            values=choices
        ).run()
        
        if result == "all":
            return list(options.keys())[:-1]  # All except "all"
        elif result:
            return [result]
        else:
            return []

    def show_interactive_qa(self, rag_system) -> bool:
        self.console.print("\n" + "="*60)
        self.console.print("[bold cyan]🤔 Interactive Q&A Session[/bold cyan]")
        self.console.print("Ask questions about the codebase. Type 'quit' to exit.\n")
        
        # Show suggestions
        suggestions = rag_system.get_suggestions()
        if suggestions:
            self.console.print("[dim]💡 Suggested questions:[/dim]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"[dim]{i}. {suggestion}[/dim]")
            self.console.print("")
        
        completer = WordCompleter([
            'functions', 'classes', 'setup', 'install', 'dependencies', 
            'structure', 'architecture', 'tests', 'main', 'entry point',
            'how to', 'what is', 'explain'
        ])
        
        while True:
            try:
                question = prompt(
                    HTML('<cyan><b>🤔 Your question:</b></cyan> '),
                    completer=completer,
                ).strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not question:
                    continue
                
                # Show thinking animation
                with self.console.status("[cyan]🧠 Thinking...[/cyan]", spinner="dots"):
                    result = rag_system.answer_question(question)
                
                # Display answer
                self.show_qa_result(question, result)
                
            except (KeyboardInterrupt, EOFError):
                break
        
        return True

    def show_qa_result(self, question: str, result: Dict):
        answer = result.get('answer', 'No answer available')
        sources = result.get('sources', [])
        confidence = result.get('confidence', 'unknown')
        
        # Confidence indicator
        confidence_colors = {
            'high': 'green',
            'medium': 'yellow', 
            'low': 'red'
        }
        confidence_color = confidence_colors.get(confidence, 'white')
        confidence_emoji = {'high': '✅', 'medium': '⚠️', 'low': '❌'}.get(confidence, '❓')
        
        # Create answer panel
        answer_panel = Panel(
            Markdown(answer),
            title=f"[bold]💬 Answer {confidence_emoji}[/bold]",
            border_style=confidence_color,
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(answer_panel)
        
        # Show sources if available
        if sources:
            sources_table = Table(title="📚 Sources", box=box.SIMPLE)
            sources_table.add_column("Source", style="cyan")
            sources_table.add_column("Type", style="blue")
            sources_table.add_column("Confidence", style="green")
            
            for source in sources[:3]:
                conf_score = f"{source['confidence']:.2f}"
                sources_table.add_row(
                    source['source'],
                    source['type'],
                    conf_score
                )
            
            self.console.print(sources_table)
        
        self.console.print("\n" + "-"*60)

    def show_documentation_generated(self, doc_paths: List[str]):
        self.console.print("\n[bold green]✅ Documentation Generated![/bold green]")
        
        if doc_paths:
            docs_table = Table(title="📄 Generated Files", box=box.ROUNDED)
            docs_table.add_column("File", style="cyan")
            docs_table.add_column("Status", style="green")
            
            for path in doc_paths:
                docs_table.add_row(path, "✓ Created")
            
            self.console.print(docs_table)
        
        self.console.print(f"\n[green]📁 Documentation saved to: ./generated_docs/[/green]")

    def show_completion_summary(self, analysis_results: Dict, documentation_generated: bool = False, qa_sessions: int = 0):
        summary = analysis_results.get('summary', {})
        
        # Create summary panel
        summary_content = f"""
[bold green]✅ Analysis Complete![/bold green]

📊 [bold]Files Processed:[/bold] {len(analysis_results.get('parsed_files', []))}
🔧 [bold]Functions Found:[/bold] {summary.get('total_functions', 0)}
🏗️ [bold]Classes Found:[/bold] {summary.get('total_classes', 0)}
🌐 [bold]Languages:[/bold] {len(summary.get('languages', {}))}

{"📝 [bold green]Documentation Generated[/bold green]" if documentation_generated else ""}
{f"💬 [bold blue]Q&A Sessions:[/bold blue] {qa_sessions}" if qa_sessions > 0 else ""}

[dim]Thank you for using Code Documentation Assistant! 🚀[/dim]
        """
        
        completion_panel = Panel(
            summary_content.strip(),
            title="🎉 Session Summary",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(completion_panel)
        self.console.print("\n")

    def show_error(self, message: str):
        error_panel = Panel(
            f"[red]❌ {message}[/red]",
            title="Error",
            border_style="red"
        )
        self.console.print("\n")
        self.console.print(error_panel)
        self.console.print("\n")

    def show_warning(self, message: str):
        warning_panel = Panel(
            f"[yellow]⚠️ {message}[/yellow]",
            title="Warning",
            border_style="yellow"
        )
        self.console.print("\n")
        self.console.print(warning_panel)

    def confirm_action(self, message: str) -> bool:
        return Confirm.ask(f"\n[cyan]{message}[/cyan]", console=self.console)

    def show_info(self, message: str):
        self.console.print(f"\n[blue]ℹ️ {message}[/blue]")

    def show_success(self, message: str):
        self.console.print(f"\n[green]✅ {message}[/green]")

class CLIFormatter:
    @staticmethod
    def format_code_snippet(code: str, language: str = "python") -> str:
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        return syntax
    
    @staticmethod
    def format_file_list(files: List[Dict], max_files: int = 10) -> Table:
        table = Table(title=f"📁 Analyzed Files (showing {min(len(files), max_files)} of {len(files)})")
        table.add_column("File", style="cyan")
        table.add_column("Language", style="blue")
        table.add_column("Functions", style="green")
        table.add_column("Classes", style="yellow")
        
        for file_data in files[:max_files]:
            table.add_row(
                file_data.get('path', 'Unknown'),
                file_data.get('language', 'Unknown'),
                str(len(file_data.get('functions', []))),
                str(len(file_data.get('classes', [])))
            )
        
        return table
    
    @staticmethod
    def format_recommendations(recommendations: List[str]) -> Panel:
        if not recommendations:
            content = "[dim]No specific recommendations at this time.[/dim]"
        else:
            content = "\n".join(f"• {rec}" for rec in recommendations)
        
        return Panel(
            content,
            title="💡 Recommendations",
            border_style="yellow"
        )