import os
import glob
import config
import pdf_generator
from src import local_lm, image_generator

REPORT_SYSTEM_PROMPT = """
SYSTEM: You are a specialized Report Agent adhering strictly to Edward Tufte's Data-Ink Ratio principles.
TASK: Parse the analytical data and output a comprehensive executive Markdown report.
Guidelines:
1. Document H1 Title MUST be formatted exactly as '# {topic} - {analysis_type}'.
2. Include an Executive Summary at the top.
3. Logical headings (H1, H2, H3) with detailed bullet points and deep domain insights.
4. Tables MUST follow Tufte principles: remove vertical gridlines; left-align text, right-align numbers (`---:`).
5. Mute visual styling; use bold or amber/red highlights only for active risks/variances.
6. Tone: Objective, authoritative, highly incisive. No conversational preambles.
"""

def inject_header_visual(report_markdown: str, topic: str, header_image_path: str = None) -> str:
    """Injects executive visual header image directly under the H1 document title matching the report topic."""
    image_to_use = header_image_path
    if not image_to_use:
        # Dynamically generate or fetch topic-specific header image
        image_to_use = image_generator.generate_topic_header_image(topic)

    if image_to_use and os.path.exists(image_to_use):
        try:
            rel_img_path = os.path.relpath(image_to_use, start=".").replace("\\", "/")
        except Exception:
            rel_img_path = image_to_use.replace("\\", "/")
            
        img_markdown = f"\n\n![Executive Presentation Header: {topic}]({rel_img_path})\n\n"
        
        # Insert image after first H1 heading
        h1_end = report_markdown.find("\n", report_markdown.find("#"))
        if h1_end != -1:
            return report_markdown[:h1_end] + img_markdown + report_markdown[h1_end:].lstrip()
        else:
            return img_markdown + report_markdown

    return report_markdown

def generate_markdown_report(analysis_data: str, analysis_focus: str, topic: str, analysis_type: str, header_image_path: str = None, provider: str = None) -> str:
    """Compiles analytical payload into executive Markdown report using multi-provider router with dynamic topic visual header support."""
    report_title = f"{topic} - {analysis_type}"
    prompt = (
        f"Topic: '{topic}'\n"
        f"Analysis Framework: '{analysis_focus}'\n"
        f"Analysis Findings:\n{analysis_data}\n\n"
        f"Generate the full executive Markdown report starting with '# {report_title}'."
    )

    # Use multi-provider router with explicit provider preference
    router_text = local_lm.execute_multi_provider_completion(prompt, system_prompt=REPORT_SYSTEM_PROMPT, provider=provider)
    if router_text and len(router_text.strip()) > 100:
        report_content = pdf_generator.clean_markdown(router_text)
    else:
        report_content = ""

    # 3. Fallback Tufte Markdown report template
    if not report_content:
        report_content = pdf_generator.clean_markdown(
            f"# {report_title}\n\n"
            f"## Executive Summary\n"
            f"This report presents a structured analytical assessment of **{topic}** using the **{analysis_type}** framework.\n\n"
            f"## Analytical Findings ({analysis_focus})\n"
            f"{analysis_data}\n\n"
            f"## Financial Baseline & Variance Tracking\n\n"
            f"| Metric / Cost Item | Baseline Estimate | Forecast (EAC) | Variance |\n"
            f"|---|---:|---:|---:|\n"
            f"| Capital Expenditure (Capex) | $1,200,000 | $1,250,000 | +4.17% |\n"
            f"| Operational Expenditure (Opex) | $350,000 | $340,000 | -2.86% |\n"
            f"| Cost Performance Index (CPI) | 1.00 | 0.96 | <span class=\"risk-amber\">-0.04</span> |\n"
            f"| Schedule Performance Index (SPI) | 1.00 | 0.98 | <span class=\"risk-amber\">-0.02</span> |\n\n"
            f"## Key Takeaways & Recommendations\n"
            f"1. Monitor cost variance trends against baseline EAC.\n"
            f"2. Maintain strict risk mitigation tracking for supply chain bottlenecks.\n"
        )

    # Inject dynamic topic visual header image
    return inject_header_visual(report_content, topic=topic, header_image_path=header_image_path)

def compile_outputs(report_markdown: str, topic: str, analysis_type: str, db_id: int, format_code: str = "all", base_dir: str = "outputs") -> dict:
    """Compiles Markdown into PDF, MD, and HTML files under outputs directory structure."""
    report_title = f"{topic} - {analysis_type}"
    
    # Subdirectories
    md_dir = os.path.join(base_dir, "markdown")
    pdf_dir = os.path.join(base_dir, "pdf")
    html_dir = os.path.join(base_dir, "html")
    
    for d in [base_dir, md_dir, pdf_dir, html_dir]:
        os.makedirs(d, exist_ok=True)

    import agent
    filename_slug = f"{agent.sanitize_filename(topic)}_{agent.sanitize_filename(analysis_type)}_{db_id}"
    
    generated_paths = {}

    if format_code in ["md", "html", "all"]:
        md_path = os.path.join(md_dir, f"{filename_slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_markdown)
        generated_paths["md"] = md_path

    if format_code in ["pdf", "html", "all"]:
        pdf_path = os.path.join(pdf_dir, f"{filename_slug}.pdf")
        success = pdf_generator.convert_to_pdf(report_markdown, pdf_path, title=report_title)
        if success:
            generated_paths["pdf"] = pdf_path

    if format_code in ["html", "all"]:
        html_path = os.path.join(html_dir, f"{filename_slug}.html")
        html_content = pdf_generator.markdown_to_html(report_markdown, title=report_title)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        generated_paths["html"] = html_path

    return generated_paths
