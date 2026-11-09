"""
Official Dean's Order DOCX Generator (US-11, WBS 1.3.4).
Aggregates approved students by enterprise in alphabetical order and formats formal order.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from collections import defaultdict
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt

from src.core.config import settings


def generate_dean_order_docx(
    order_number: str,
    order_date: str,
    academic_year: str,
    faculty_name: str,
    specialty_name: str,
    approved_applications: list[dict],
    all_students_in_cohort: list[dict],
    output_dir: Path = settings.DOCUMENTS_DIR,
) -> tuple[str, list[str]]:
    """
    Generates an official Faculty Dean's Order in DOCX format.
    Groups students by enterprise in alphabetical order.

    Returns:
        (file_path: str, unassigned_students_list: List[str])
    """
    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    def set_font(run, size=10, bold=False, italic=False, name="Times New Roman"):
        run.font.name = name
        run.font.size = Pt(size)
        run.bold = bold
        run.font.italic = italic

    def add_p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=3, line_spacing=1.15):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        return p

    # Header / University Crest Text
    p_top = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=1)
    r1 = p_top.add_run("ҚАЗАҚСТАН РЕСПУБЛИКАСЫ ҒЫЛЫМ ЖӘНЕ ЖОҒАРЫ БІЛІМ МИНИСТРЛІГІ\n")
    set_font(r1, size=9.5, bold=True)
    r2 = p_top.add_run(f"«{settings.UNIVERSITY_NAME_KZ.upper()}» КЕАҚ\n")
    set_font(r2, size=11, bold=True)
    r3 = p_top.add_run(f"{settings.FACULTY_NAME_KZ.upper()}\n")
    set_font(r3, size=10.5, bold=True)

    p_divider = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    p_divider.add_run("____________________________________________________________________")

    # Order Title
    p_order = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    r_ord = p_order.add_run("БҰЙРЫҚ / ПРИКАЗ")
    set_font(r_ord, size=14, bold=True)

    p_meta = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
    p_meta.add_run(f"«{order_date}»").bold = True
    p_meta.add_run("\t\t\t\t\t\t\tг. Астана\t\t\t\t\t\t")
    p_meta.add_run(f"{order_number}").bold = True

    # Subject
    p_subj = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6)
    r_subj = p_subj.add_run(
        "О направлении студентов 4 курса очной формы обучения\n"
        f"{faculty_name} на производственную практику в {academic_year} учебном году"
    )
    set_font(r_subj, size=10.5, bold=True)

    # Preambule
    p_pre = add_p()
    p_pre.add_run(
        "В соответствии с Академической политикой университета, Государственным общеобязательным "
        "стандартом высшего образования и рабочими учебными планами образовательных программ факультета, "
        "а также заключенными трехсторонними договорами на проведение профессиональной практики,\n\n"
        "ПРИКАЗЫВАЮ:\n\n"
        "1. Направить студентов 4 курса бакалавриата на производственную практику с отрывом от учебных занятий "
        "согласно нижеследующему распределению по базам практики:\n"
    )

    # Group students by enterprise
    grouped: dict[str, list[dict]] = defaultdict(list)
    approved_student_iins = set()

    for app in approved_applications:
        company_key = app.get("company_name", "Прочие организации")
        grouped[company_key].append(app)
        approved_student_iins.add(app.get("student_iin"))

    # Sort companies alphabetically
    sorted_companies = sorted(grouped.keys())

    # Build Table per company or unified table
    total_count = 0
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(0.4), Inches(2.2), Inches(0.9), Inches(1.2), Inches(1.3), Inches(1.2)]

    # Borders
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(tblBorders)

    headers = [
        "№",
        "ФИО обучающегося",
        "Группа",
        "Сроки практики",
        "База практики (Предприятие)",
        "Руководитель от кафедры",
    ]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = widths[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size=8.5, bold=True)

    seq_num = 1
    for comp in sorted_companies:
        for app in grouped[comp]:
            row = table.add_row()
            cells = row.cells
            for idx, w in enumerate(widths):
                cells[idx].width = w

            # No
            cells[0].paragraphs[0].add_run(str(seq_num))
            cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(cells[0].paragraphs[0].runs[0], size=8.0)

            # Fullname + IIN
            p_st = cells[1].paragraphs[0]
            p_st.add_run(app.get("student_fullname", ""))
            set_font(p_st.runs[0], size=8.5, bold=True)
            p_st.add_run(f"\nИИН: {app.get('student_iin', '')}")
            set_font(p_st.runs[1], size=7.5, italic=True)

            # Group
            cells[2].paragraphs[0].add_run(app.get("student_group", "АЖ-47"))
            cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(cells[2].paragraphs[0].runs[0], size=8.0)

            # Dates
            dates_str = (
                f"{app.get('start_date', '01.06.2026')}\nпо {app.get('end_date', '15.07.2026')}"
            )
            cells[3].paragraphs[0].add_run(dates_str)
            cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(cells[3].paragraphs[0].runs[0], size=8.0)

            # Company + Mentor
            p_cp = cells[4].paragraphs[0]
            p_cp.add_run(f"{comp}\n(БИН: {app.get('company_bin', '')})")
            set_font(p_cp.runs[0], size=8.0, bold=True)
            p_cp.add_run(f"\nНаставник: {app.get('mentor_fullname', '')}")
            set_font(p_cp.runs[1], size=7.5, italic=True)

            # Academic Supervisor
            cells[5].paragraphs[0].add_run(app.get("academic_supervisor", settings.DEAN_NAME))
            cells[5].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(cells[5].paragraphs[0].runs[0], size=8.0)

            seq_num += 1
            total_count += 1

    # Additional Order Clauses
    doc.add_paragraph().paragraph_format.space_before = Pt(8)
    p_c2 = add_p()
    p_c2.add_run(
        "2. Руководителям практики от кафедр обеспечить контроль за своевременным прибытием обучающихся "
        "на базы практики, выполнением программы и сдачей отчетов.\n"
        "3. Контроль за исполнением настоящего приказа возложить на заместителя декана по учебной и воспитательной работе.\n\n"
    )

    # Dean Signature
    p_sign = add_p(space_after=20)
    p_sign.add_run(f"Декан {settings.FACULTY_NAME_RU}\t\t\t\t\t{settings.DEAN_NAME}\n\n")
    p_sign.runs[0].bold = True
    p_sign.add_run("М.П.\t\t\t\t\t\t\t\tПодпись: _______________")

    # Find unassigned students (US-11 criteria)
    unassigned = []
    for st in all_students_in_cohort:
        if st.get("iin") not in approved_student_iins:
            unassigned.append(
                f"{st.get('full_name')} (гр. {st.get('group_code')}, ИИН {st.get('iin')})"
            )

    filename = (
        f"Dean_Order_{order_number.replace('№', '').replace(' ', '_').replace('/', '_')}.docx"
    )
    filepath = output_dir / filename
    doc.save(str(filepath))

    return str(filepath), unassigned
