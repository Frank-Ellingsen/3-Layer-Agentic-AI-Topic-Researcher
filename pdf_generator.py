import os
import re
import markdown2
from xhtml2pdf import pisa

DEFAULT_TUFTE_CSS = """
@page {
    size: a4 portrait;
    margin: 20mm 15mm 20mm 15mm;
    @frame header_frame {
        -pdf-frame-content: header_content;
        left: 15mm; width: 180mm; top: 10mm; height: 10mm;
    }
    @frame footer_frame {
        -pdf-frame-content: footer_content;
        left: 15mm; width: 180mm; top: 275mm; height: 10mm;
    }
}

body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    font-size: 10pt;
    line-height: 1.5;
}

#header_content {
    font-size: 8pt;
    color: #666666;
    border-bottom: 0.5pt solid #cccccc;
    padding-bottom: 3px;
}

#footer_content {
    font-size: 8pt;
    color: #666666;
    border-top: 0.5pt solid #cccccc;
    padding-top: 3px;
    text-align: right;
}

h1 {
    font-size: 18pt;
    font-weight: bold;
    color: #0f172a;
    margin-top: 10px;
    margin-bottom: 12px;
    border-bottom: 1.5pt solid #0f172a;
    padding-bottom: 4px;
}

h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1e293b;
    margin-top: 18px;
    margin-bottom: 8px;
    border-bottom: 0.5pt solid #cbd5e1;
    padding-bottom: 2px;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    color: #334155;
    margin-top: 12px;
    margin-bottom: 6px;
}

p {
    margin-top: 0;
    margin-bottom: 8px;
    text-align: justify;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 8px;
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    margin-bottom: 16px;
    font-size: 9pt;
}

th {
    font-weight: bold;
    border-bottom: 1.5pt solid #334155;
    border-top: 1pt solid #334155;
    padding: 6px 8px;
    text-align: left;
    background-color: #f8fafc;
}

td {
    border-bottom: 0.5pt solid #e2e8f0;
    padding: 5px 8px;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #f8fafc;
}

/* Numeric alignment in tables */
td.num, th.num {
    text-align: right;
}

blockquote {
    margin: 10px 0;
    padding: 8px 12px;
    background-color: #f1f5f9;
    border-left: 3pt solid #0284c7;
    font-style: italic;
}

code {
    font-family: "Courier New", Courier, monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    padding: 1px 3px;
}

pre {
    background-color: #f8fafc;
    border: 0.5pt solid #e2e8f0;
    padding: 8px;
    font-size: 8.5pt;
    font-family: "Courier New", Courier, monospace;
    overflow-x: auto;
}

.risk-amber {
    color: #d97706;
    font-weight: bold;
}

.risk-red {
    color: #dc2626;
    font-weight: bold;
}

.metric-highlight {
    color: #0284c7;
    font-weight: bold;
}

img {
    max-width: 100%;
    height: auto;
    margin-top: 10px;
    margin-bottom: 15px;
    border-radius: 4px;
}
"""

def clean_markdown(content: str) -> str:
    """Strips outer markdown/html code block fences if present."""
    content = content.strip()
    if content.startswith("```"):
        # Remove opening fence like ```html or ```markdown
        first_line_end = content.find("\n")
        if first_line_end != -1:
            content = content[first_line_end + 1:]
        if content.endswith("```"):
            content = content[:-3].strip()
    return content

def markdown_to_html(md_content: str, title: str = "Research & Analysis Report") -> str:
    """Converts markdown content to styled HTML document adhering to Tufte Data-Ink principles."""
    cleaned_md = clean_markdown(md_content)
    body_html = markdown2.markdown(
        cleaned_md,
        extras=[
            "tables",
            "fenced-code-blocks",
            "header-ids",
            "def_list",
            "footnotes",
            "task_list",
            "strike"
        ]
    )
    
    html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
    {DEFAULT_TUFTE_CSS}
    </style>
</head>
<body>
    <div id="header_content">
        <span>Project & Decision Intelligence | Executive Report</span>
    </div>
    <div id="footer_content">
        Page <pdf:pagenumber/> of <pdf:pagecount/>
    </div>

    {body_html}
</body>
</html>
"""
    return html_document

def convert_to_pdf(md_content: str, output_pdf_path: str, title: str = "Research & Analysis Report") -> bool:
    """Generates a PDF file from Markdown content using xhtml2pdf."""
    html_content = markdown_to_html(md_content, title=title)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    
    with open(output_pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
    return not pisa_status.err
