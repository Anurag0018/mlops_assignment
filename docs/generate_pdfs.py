"""
Automated Markdown to PDF Report Generator
------------------------------------------
Parses Implementation Plan and Walkthrough markdown files into
beautifully styled, publication-ready PDF reports with headers, footers,
formatted tables, and syntax callouts.
"""

import os
import re
import html
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                36, letter[1] - 30,
                "Student Performance & Academic Dropout-Risk Prediction System (MLOps Platform)"
            )
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 34, letter[0] - 36, letter[1] - 34)

        # Running footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 25, page_text)
        self.drawString(36, 25, "Confidential — Academic & Coursework Evaluation")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 35, letter[0] - 36, 35)

        self.restoreState()


def clean_markdown_text(text: str) -> str:
    """Translate basic markdown inline tags to ReportLab HTML tags."""
    # Escape existing xml characters first
    text = html.escape(text, quote=False)

    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic: *text*
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    # Inline code: `text`
    text = re.sub(r"`(.+?)`", r'<font face="Courier" color="#1E293B"><b>\1</b></font>', text)
    # LaTeX expressions: $math$
    text = re.sub(r"\$(.+?)\$", r"<i>\1</i>", text)
    # Markdown links: [text](url) -> text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"<u>\1</u>", text)

    return text


def build_pdf_from_markdown(md_path: Path, output_pdf_path: Path, doc_title: str):
    """Parse markdown file and compile into a styled PDF."""
    if not md_path.exists():
        raise FileNotFoundError(f"Source markdown file not found: {md_path}")

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Custom typography hierarchy
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E1B4B"),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#312E81"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "Heading3_Custom",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        spaceAfter=3,
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E3A8A"),
        leftIndent=12,
        spaceBefore=4,
        spaceAfter=4,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    code_style = ParagraphStyle(
        "CodeStyle",
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0F172A"),
    )

    flowables = []

    # Title
    flowables.append(Paragraph(doc_title, title_style))
    flowables.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#312E81"), spaceAfter=10))

    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            in_table = False
            return

        # Parse markdown table
        rows = []
        is_first = True
        for t_line in table_lines:
            t_line = t_line.strip()
            if not t_line.startswith("|"):
                continue
            cells = [c.strip() for c in t_line.strip("|").split("|")]
            # Skip separator row like |---|---|
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue

            row_cells = []
            for cell in cells:
                c_text = clean_markdown_text(cell)
                if is_first:
                    p = Paragraph(c_text, table_header_style)
                else:
                    p = Paragraph(c_text, table_cell_style)
                row_cells.append(p)
            rows.append(row_cells)
            is_first = False

        if rows:
            col_count = max(len(r) for r in rows)
            avail_width = letter[0] - 72
            col_width = avail_width / max(1, col_count)

            # Pad short rows
            for r in rows:
                while len(r) < col_count:
                    r.append(Paragraph("", table_cell_style))

            t = Table(rows, colWidths=[col_width] * col_count)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312E81")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            flowables.append(Spacer(1, 4))
            flowables.append(t)
            flowables.append(Spacer(1, 6))

        table_lines = []
        in_table = False

    def flush_code():
        nonlocal in_code_block, code_lines
        if code_lines:
            code_text = "\n".join(code_lines)
            p = Preformatted(code_text, code_style)
            t = Table([[p]], colWidths=[letter[0] - 72])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            flowables.append(Spacer(1, 3))
            flowables.append(t)
            flowables.append(Spacer(1, 4))
        code_lines = []
        in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle tables
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        # Headings
        if stripped.startswith("#### "):
            flowables.append(Paragraph(clean_markdown_text(stripped[5:]), h3_style))
        elif stripped.startswith("### "):
            flowables.append(Paragraph(clean_markdown_text(stripped[4:]), h3_style))
        elif stripped.startswith("## "):
            flowables.append(Paragraph(clean_markdown_text(stripped[3:]), h2_style))
        elif stripped.startswith("# "):
            flowables.append(Paragraph(clean_markdown_text(stripped[2:]), h1_style))
        elif stripped.startswith("> "):
            clean_q = clean_markdown_text(stripped[2:])
            flowables.append(Paragraph(f"<b>ℹ Note:</b> {clean_q}", callout_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            flowables.append(Paragraph(f"• {clean_markdown_text(stripped[2:])}", bullet_style))
        elif re.match(r"^\d+\.\s", stripped):
            flowables.append(Paragraph(clean_markdown_text(stripped), bullet_style))
        elif stripped.startswith("---"):
            flowables.append(Spacer(1, 2))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4))
        else:
            flowables.append(Paragraph(clean_markdown_text(stripped), body_style))

    if in_table:
        flush_table()
    if in_code_block:
        flush_code()

    doc.build(flowables, canvasmaker=NumberedCanvas)
    print(f"Generated PDF successfully: {output_pdf_path} ({output_pdf_path.stat().st_size / 1024:.1f} KB)")


def main():
    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Artifact paths
    brain_dir = Path("C:/Users/anura/.gemini/antigravity/brain/0a4635fa-071a-40fa-aa2c-97765a1cba5a")
    plan_md = brain_dir / "implementation_plan.md"
    walk_md = brain_dir / "walkthrough.md"

    out_plan_pdf = docs_dir / "implementation_plan.pdf"
    out_walk_pdf = docs_dir / "walkthrough.pdf"

    if plan_md.exists():
        build_pdf_from_markdown(
            md_path=plan_md,
            output_pdf_path=out_plan_pdf,
            doc_title="MLOps System Architecture & Implementation Plan"
        )

    if walk_md.exists():
        build_pdf_from_markdown(
            md_path=walk_md,
            output_pdf_path=out_walk_pdf,
            doc_title="Part 2: MLOps System Walkthrough & Verification Report"
        )


if __name__ == "__main__":
    main()
