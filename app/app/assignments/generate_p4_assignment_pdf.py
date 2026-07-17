from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "P4_MQTT_IoT_Telemetry_Assignment_Reguler_3SKS.md"
OUTPUT = ROOT / "P4_MQTT_IoT_Telemetry_Assignment_Reguler_3SKS.pdf"


def setup_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSub",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=11,
            leading=16,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading1Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeCustom",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=5,
            spaceAfter=8,
            backColor=colors.HexColor("#F4F6F8"),
            borderColor=colors.HexColor("#D7DEE8"),
            borderWidth=0.5,
            borderPadding=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=8,
            textColor=colors.HexColor("#566070"),
        )
    )
    return styles


def clean_inline(text):
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    parts = escaped.split("`")
    for idx in range(1, len(parts), 2):
        parts[idx] = f'<font name="Courier">{parts[idx]}</font>'
    return "".join(parts)


def flush_list(story, list_items, styles):
    if not list_items:
        return
    flowables = [
        ListItem(Paragraph(clean_inline(item), styles["BodyCustom"]), leftIndent=14)
        for item in list_items
    ]
    story.append(ListFlowable(flowables, bulletType="1", start="1", leftIndent=18))
    story.append(Spacer(1, 4))
    list_items.clear()


def table_from_rows(rows, styles):
    data = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        data.append([Paragraph(clean_inline(cell), styles["BodyCustom"]) for cell in cells])

    usable_width = A4[0] - 3.2 * cm
    col_count = max(len(row) for row in data)
    col_widths = [usable_width / col_count] * col_count
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1F8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#182333")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C3D0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_story(markdown, styles):
    lines = markdown.splitlines()
    story = []
    list_items = []
    table_rows = []
    code_lines = []
    in_code = False
    cover_done = False

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["CodeCustom"]))
                code_lines = []
                in_code = False
            else:
                flush_list(story, list_items, styles)
                if table_rows:
                    story.append(table_from_rows(table_rows, styles))
                    story.append(Spacer(1, 8))
                    table_rows = []
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("|") and line.endswith("|"):
            if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue
            flush_list(story, list_items, styles)
            table_rows.append(line)
            continue

        if table_rows:
            story.append(table_from_rows(table_rows, styles))
            story.append(Spacer(1, 8))
            table_rows = []

        if not line.strip():
            flush_list(story, list_items, styles)
            continue

        if line.startswith("# "):
            flush_list(story, list_items, styles)
            story.append(Spacer(1, 2.8 * cm))
            story.append(Paragraph(clean_inline(line[2:]), styles["CoverTitle"]))
            continue

        if line.startswith("## MQTT"):
            story.append(Paragraph(clean_inline(line[3:]), styles["CoverTitle"]))
            continue

        if line.startswith("Mata kuliah:") or line.startswith("Program studi:") or line.startswith("Kelas:") or line.startswith("Bobot:") or line.startswith("Pertemuan:") or line.startswith("Sifat tugas:") or line.startswith("Estimasi pengerjaan:"):
            story.append(Paragraph(clean_inline(line), styles["CoverSub"]))
            continue

        if line.startswith("## "):
            flush_list(story, list_items, styles)
            if not cover_done:
                story.append(PageBreak())
                cover_done = True
            story.append(Paragraph(clean_inline(line[3:]), styles["Heading1Custom"]))
            continue

        if line.startswith("### "):
            flush_list(story, list_items, styles)
            story.append(Paragraph(clean_inline(line[4:]), styles["Heading2Custom"]))
            continue

        if line[:3].strip().endswith(".") and line.split(".", 1)[0].isdigit():
            list_items.append(line.split(".", 1)[1].strip())
            continue

        if line.startswith("- "):
            list_items.append(line[2:].strip())
            continue

        flush_list(story, list_items, styles)
        story.append(Paragraph(clean_inline(line), styles["BodyCustom"]))

    flush_list(story, list_items, styles)
    if table_rows:
        story.append(table_from_rows(table_rows, styles))

    return story


def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#566070"))
    page_text = f"Communication Protocols - P4 MQTT Assignment | Page {doc.page}"
    canvas.drawCentredString(A4[0] / 2, 0.75 * cm, page_text)
    canvas.restoreState()


def main():
    markdown = SOURCE.read_text(encoding="utf-8")
    styles = setup_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.4 * cm,
        title="P4 MQTT IoT Telemetry Assignment",
        author="Communication Protocols",
    )
    doc.build(build_story(markdown, styles), onFirstPage=add_footer, onLaterPages=add_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()

