import os
import re
import sys
import uuid
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Local & modular src imports
import config
import database
import pdf_generator
from src import scraper, local_lm, notebook_sync, report_agent, storage_sync

console = Console()

ANALYSIS_OPTIONS = {
    "1": ("SWOT Analysis", "Strengths, Weaknesses, Opportunities, and Threats analysis with strategic recommendations"),
    "2": ("Cost-Benefit & Financial Feasibility", "Capex/Opex breakdown, ROI, Payback Period, and EAC/ETC cost forecasting"),
    "3": ("Risk & Mitigation Tracking", "Risk matrix (Probability vs. Impact), cost/schedule variances, and mitigation strategies"),
    "4": ("Strategic & Competitive Benchmarking", "Market positioning, competitor comparison matrix, and key performance trends"),
    "5": ("PESTEL Analysis", "Political, Economic, Social, Technological, Environmental, and Legal factor evaluation"),
    "6": ("Bottleneck & Operational Efficiency", "Workflow constraints, supply chain risks, process friction, and execution obstacles"),
    "7": ("Project Controlling & Earned Value (EV) Analysis", "CPI/SPI performance indices, Cost Variance (CV), Schedule Variance (SV), and EAC/ETC estimates"),
    "8": ("Comprehensive Multi-Dimensional Analysis", "Integrated analysis combining Financial, Risk, SWOT, and Operational perspectives"),
    "9": ("Custom Analysis", "User-defined custom analytical focus")
}

PROVIDER_OPTIONS = {
    "1": ("OpenAI (GPT-4o / GPT-4o-mini)", "openai"),
    "2": ("Anthropic Claude (Claude 3.5 Sonnet)", "anthropic"),
    "3": ("OpenRouter AI (Auto Multi-Model Router)", "openrouter"),
    "4": ("Google Gemini API (Search Grounded)", "gemini"),
    "5": ("Local Ollama Server (llama3.1 / qwen2.5)", "ollama"),
    "6": ("Auto Failover Network (All Available Providers)", None)
}

FORMAT_OPTIONS = {
    "1": ("HTML Web Page (.html) [Default]", "html"),
    "2": ("PDF Document (.pdf)", "pdf"),
    "3": ("Markdown (.md)", "md"),
    "4": ("All Formats (PDF + Markdown + HTML)", "all")
}

def print_banner():
    console.print(Panel.fit(
        "[bold cyan]ProjectCast — Project Controlling & Decision Intelligence[/bold cyan]\n"
        "[dim]3-Layer Agentic AI for EVM Forecasting, Capex/Opex Analysis & Risk Tracking[/dim]",
        border_style="cyan"
    ))

def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safely used as part of a file name."""
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[\s-]+', '_', clean)

def prompt_user_inputs():
    """Interactively prompts the user for research topic, analysis focus, provider, and output format."""
    print_banner()
    
    # Step 1: Topic definition
    console.print("\n[bold yellow]Step 1: Define Research Topic[/bold yellow]")
    topic = Prompt.ask("What topic or project would you like to research?")
    while not topic.strip():
        topic = Prompt.ask("[red]Topic cannot be empty. Please enter a topic[/red]")

    # Step 2: Analysis Framework Selection
    console.print("\n[bold yellow]Step 2: Choose Analysis Focus / Framework[/bold yellow]")
    
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Option", style="cyan", width=8, justify="right")
    table.add_column("Framework", style="bold white", width=38)
    table.add_column("Description", style="dim")
    
    for key, (name, desc) in ANALYSIS_OPTIONS.items():
        table.add_row(key, name, desc)
        
    console.print(table)
    
    choice = Prompt.ask("Select an analysis framework [1-9]", choices=list(ANALYSIS_OPTIONS.keys()), default="8")
    
    if choice == "9":
        analysis_focus = Prompt.ask("Enter your custom analysis focus")
        while not analysis_focus.strip():
            analysis_focus = Prompt.ask("[red]Custom focus cannot be empty. Please enter instructions[/red]")
        analysis_type = "Custom Analysis"
    else:
        name, desc = ANALYSIS_OPTIONS[choice]
        analysis_type = name
        analysis_focus = f"{name}: {desc}"
        
    console.print(f"[green]Selected Analysis Focus:[/green] {analysis_focus}")

    # Step 3: Provider Selection
    console.print("\n[bold yellow]Step 3: Choose Chat Service & Model Provider[/bold yellow]")
    
    prov_table = Table(show_header=True, header_style="bold magenta", box=None)
    prov_table.add_column("Option", style="cyan", width=8, justify="right")
    prov_table.add_column("Provider Service", style="bold white")
    
    for key, (label, _) in PROVIDER_OPTIONS.items():
        prov_table.add_row(key, label)
        
    console.print(prov_table)
    console.print("[dim yellow]⚠️ Note: Cloud providers require active API key credits. Inactive or uncredited keys will trigger automatic failover to local or offline models, which may increase execution time.[/dim yellow]\n")
    
    prov_choice = Prompt.ask("Select model provider [1-6]", choices=list(PROVIDER_OPTIONS.keys()), default="6")
    provider_label, provider_code = PROVIDER_OPTIONS[prov_choice]
    
    console.print(f"[green]Selected Provider:[/green] {provider_label}")
    
    if provider_code and provider_code != "ollama":
        has_key = False
        if provider_code == "openai" and config.OPENAI_API_KEY: has_key = True
        elif provider_code == "anthropic" and config.ANTHROPIC_KEY: has_key = True
        elif provider_code == "openrouter" and config.OPENROUTER_API_KEY: has_key = True
        elif provider_code == "gemini" and config.GEMINI_API_KEY: has_key = True
        elif provider_code == "huggingface" and config.HF_API_KEY: has_key = True
        
        if not has_key:
            console.print(f"[yellow]⚠️ Warning: Selected provider ({provider_label}) API key is missing. System will attempt failover to local/offline models (which may be slower).[/yellow]")
    elif provider_code == "ollama":
        console.print("[yellow]⚠️ Notice: Running via Local Ollama. Performance depends on local GPU/CPU hardware and may be slower than cloud APIs.[/yellow]")

    # Step 4: Output Format Selection
    console.print("\n[bold yellow]Step 4: Choose Output Format[/bold yellow]")
    
    fmt_table = Table(show_header=True, header_style="bold magenta", box=None)
    fmt_table.add_column("Option", style="cyan", width=8, justify="right")
    fmt_table.add_column("Format Option", style="bold white")
    
    for key, (label, _) in FORMAT_OPTIONS.items():
        fmt_table.add_row(key, label)
        
    console.print(fmt_table)
    
    fmt_choice = Prompt.ask("Select output format [1-4]", choices=list(FORMAT_OPTIONS.keys()), default="1")
    format_label, format_code = FORMAT_OPTIONS[fmt_choice]
    
    console.print(f"[green]Selected Output Format:[/green] {format_label}")
    
    return topic, analysis_type, analysis_focus, provider_code, format_code

def main():
    database.init_db()
    storage_sync.init_telemetry_db()
    
    topic, analysis_type, analysis_focus, provider_code, format_code = prompt_user_inputs()
    report_title = f"{topic} - {analysis_type}"
    run_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Save initial record to db
    db_id = database.save_research(topic, analysis_focus, format_code)
    
    # 1. Research Phase
    console.print("\n[bold green]Executing Phase 1: Ingestion & Web/Local Research...[/bold green]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="Gathering facts and syncing grounded RAG sources...", total=None)
        doc_data = scraper.execute_web_research(topic, provider=provider_code)
        notebook_sync.sync_to_notebook(doc_data)
        raw_research = doc_data["raw_text"]
        grounded_ctx = notebook_sync.query_grounded_context(topic)
        combined_research = f"{raw_research}\n\n{grounded_ctx}"
    database.update_research(db_id, raw_research=combined_research)
    
    # 2. Analysis Phase
    console.print("\n[bold green]Executing Phase 2: Analysing Findings & Running Self-Correction...[/bold green]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="Performing deep reasoning and verification...", total=None)
        raw_analysis = local_lm.perform_deep_reasoning(combined_research, analysis_focus, provider=provider_code)
        validated_analysis = local_lm.run_validation_loop(raw_analysis, combined_research, provider=provider_code)
    database.update_research(db_id, analysis=validated_analysis)
    
    # 3. Report Phase
    console.print("\n[bold green]Executing Phase 3: Generating Tufte-style Report...[/bold green]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="Formatting final document...", total=None)
        report_result = report_agent.generate_markdown_report(
            validated_analysis, analysis_focus, topic, analysis_type, provider=provider_code, sources=doc_data.get("sources")
        )
    
    # 4. Multi-Destination Archiving
    console.print("\n[bold green]Executing Phase 4: Archiving Output Files...[/bold green]")
    output_files = report_agent.compile_outputs(report_result, topic, analysis_type, db_id, format_code=format_code)
    report_paths_str = ", ".join(output_files.values())
    database.update_research(db_id, report_content=report_result, report_path=report_paths_str)
    
    runtime_ms = int((time.time() - start_time) * 1000)
    storage_sync.log_telemetry(
        run_id=run_id,
        topic=topic,
        analysis_type=analysis_type,
        status="SUCCESS",
        runtime_ms=runtime_ms,
        source_count=1,
        insights_extracted=validated_analysis[:500],
        report_paths=report_paths_str
    )
    
    saved_list = "\n".join([f"  - [cyan]{f}[/cyan]" for f in output_files.values()])
    console.print(Panel(
        f"[bold green]Workflow successfully completed![/bold green]\n\n"
        f"Report Title: [bold white]{report_title}[/bold white]\n"
        f"Generated Report Files:\n{saved_list}\n\n"
        f"Database record logged under ID: [yellow]{db_id}[/yellow]\n"
        f"Telemetry log ID: [yellow]{run_id}[/yellow]",
        title="Execution Summary"
    ))

if __name__ == "__main__":
    main()
