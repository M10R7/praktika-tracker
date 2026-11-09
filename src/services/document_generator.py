"""
Official DOCX 3-Party Contract Document Generator.
Standard Form No. 107 of the Ministry of Education and Science of the Republic of Kazakhstan.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from datetime import datetime
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt

from src.core.config import settings


def generate_contract_docx(
    contract_number: str,
    student_fullname: str,
    student_iin: str,
    student_group: str,
    specialty_code: str,
    company_name: str,
    company_bin: str,
    company_address: str,
    company_director: str,
    mentor_fullname: str,
    academic_supervisor: str,
    start_date: str,
    end_date: str,
    output_dir: Path = settings.DOCUMENTS_DIR,
) -> str:
    """
    Generates an official three-sided internship agreement in DOCX format.
    """
    doc = docx.Document()

    # Set 2 cm margins
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

    # Header / Title
    p_num = add_p(align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=2)
    r_form = p_num.add_run("Типовая форма МОН РК № 107\nПриложение к приказу № 107")
    set_font(r_form, size=8.5, italic=True)

    p_title = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    r_t1 = p_title.add_run("ТИПОВОЙ ДОГОВОР № " + contract_number)
    set_font(r_t1, size=12, bold=True)

    p_sub = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    r_sub = p_sub.add_run("на проведение профессиональной практики обучающихся")
    set_font(r_sub, size=11, bold=True)

    # City and Date Table
    p_meta = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
    p_meta.add_run("г. Алматы").bold = True
    p_meta.add_run("\t\t\t\t\t\t\t\t\t\t")
    cur_date = datetime.now().strftime("%d.%m.%Y")
    p_meta.add_run(f"«___» _________ 2026 г. (Рег. дата: {cur_date})").bold = True

    # Preamble
    p_pre = add_p()
    p_pre.add_run("Республиканское государственное предприятие на праве хозяйственного ведения ")
    p_pre.add_run(f"«{settings.UNIVERSITY_NAME_RU}»").bold = True
    p_pre.add_run(", именуемое в дальнейшем «Университет», в лице декана ")
    p_pre.add_run(f"{settings.FACULTY_NAME_RU} {settings.DEAN_NAME}").bold = True
    p_pre.add_run(", действующего на основании Доверенности и Устава, с одной стороны,\n")

    p_pre.add_run(f"Организация (Предприятие) «{company_name}»").bold = True
    p_pre.add_run(f", БИН {company_bin}, именуемое в дальнейшем «Предприятие», в лице ")
    p_pre.add_run(f"{company_director or 'первого руководителя'}").bold = True
    p_pre.add_run(", действующего на основании Устава, со второй стороны, и\n")

    p_pre.add_run(f"Обучающийся (студент) {student_fullname}").bold = True
    p_pre.add_run(f", ИИН {student_iin}, обучающийся по специальности {specialty_code}, ")
    p_pre.add_run(
        f"академическая группа {student_group}, именуемый в дальнейшем «Обучающийся», с третьей стороны, "
    )
    p_pre.add_run("совместно именуемые «Стороны», заключили настоящий Договор о нижеследующем:")

    # Section 1
    p_h1 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    set_font(p_h1.add_run("1. Предмет Договора"), size=10.5, bold=True)

    p_1 = add_p()
    p_1.add_run(
        f"1.1. Университет направляет, а Предприятие принимает Обучающегося для прохождения "
        f"производственной практики в период с «{start_date}» по «{end_date}» в структурных подразделениях Предприятия.\n"
        f"1.2. Профессиональная практика проводится в соответствии с утвержденным рабочим учебным планом, "
        f"академическим календарем и программой практики по специальности {specialty_code}."
    )

    # Section 2
    p_h2 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    set_font(p_h2.add_run("2. Обязанности и права Сторон"), size=10.5, bold=True)

    p_2_1 = add_p()
    p_2_1.add_run("2.1. Университет обязуется:\n").bold = True
    p_2_1.add_run(
        f"2.1.1. Назначить руководителем практики от кафедры квалифицированного преподавателя ({academic_supervisor});\n"
        "2.1.2. Обеспечить Обучающегося утвержденной программой практики, методическими указаниями и формой дневника-отчета;\n"
        "2.1.3. Принимать участие в расследовании несчастных случаев, если таковые произойдут с Обучающимся в период практики."
    )

    p_2_2 = add_p()
    p_2_2.add_run("2.2. Предприятие обязуется:\n").bold = True
    p_2_2.add_run(
        f"2.2.1. Предоставить Обучающемуся рабочее место и назначить квалифицированного наставника ({mentor_fullname});\n"
        "2.2.2. Обеспечить безопасные условия труда, провести обязательный инструктаж по технике безопасности и охране труда;\n"
        "2.2.3. Создать условия для освоения практических навыков по специальности, не допуская использования Обучающегося на работах, не предусмотренных программой;\n"
        "2.2.4. По окончании практики составить отзыв-характеристику с оценкой результатов и заверить печатью дневник-отчет."
    )

    p_2_3 = add_p()
    p_2_3.add_run("2.3. Обучающийся обязуется:\n").bold = True
    p_2_3.add_run(
        "2.3.1. Строго соблюдать правила внутреннего трудового распорядка Предприятия, режим труда и требования охраны труда;\n"
        "2.3.2. Бережно относиться к имуществу Предприятия, сохранять служебную и коммерческую тайну;\n"
        "2.3.3. Регулярно вести дневник производственной практики и предоставить итоговый отчет на кафедру в установленный срок."
    )

    # Section 3
    p_h3 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    set_font(
        p_h3.add_run("3. Ответственность Сторон и порядок разрешения споров"), size=10.5, bold=True
    )

    p_3 = add_p()
    p_3.add_run(
        "3.1. За неисполнение или ненадлежащее исполнение обязательств Стороны несут ответственность в соответствии с законодательством Республики Казахстан.\n"
        "3.2. Все споры и разногласия, возникающие в связи с исполнением настоящего Договора, разрешаются путем взаимных переговоров Сторон."
    )

    # Section 4: Signatures Table
    p_h4 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    set_font(
        p_h4.add_run("4. Юридические адреса, реквизиты и подписи Сторон"), size=10.5, bold=True
    )

    table = doc.add_table(rows=2, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(2.4), Inches(2.4), Inches(2.2)]

    # Style table borders
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

    headers = ["Университет", "Предприятие (База практики)", "Обучающийся (Студент)"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = widths[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, size=9.5, bold=True)

    # Fill details
    row1 = table.rows[1]
    for i in range(3):
        row1.cells[i].width = widths[i]

    # University
    c0 = row1.cells[0].paragraphs[0]
    c0.paragraph_format.line_spacing = 1.05
    c0.add_run(
        f"РГП на ПХВ «{settings.UNIVERSITY_NAME_RU}»\n"
        f"{settings.FACULTY_NAME_RU}\n"
        "г. Алматы, пр. аль-Фараби, 71\n"
        "БИН 990140001157\n\n"
        f"Декан: {settings.DEAN_NAME}\n\n"
        "Подпись: ________________\n"
        "М.П."
    )
    set_font(c0.runs[0], size=8.5)

    # Company
    c1 = row1.cells[1].paragraphs[0]
    c1.paragraph_format.line_spacing = 1.05
    c1.add_run(
        f"«{company_name}»\n"
        f"Адрес: {company_address}\n"
        f"БИН: {company_bin}\n\n"
        f"Руководитель: {company_director or mentor_fullname}\n\n"
        "Подпись: ________________\n"
        "М.П."
    )
    set_font(c1.runs[0], size=8.5)

    # Student
    c2 = row1.cells[2].paragraphs[0]
    c2.paragraph_format.line_spacing = 1.05
    c2.add_run(
        f"ФИО: {student_fullname}\n"
        f"ИИН: {student_iin}\n"
        f"Группа: {student_group}\n"
        f"Специальность: {specialty_code[:7]}\n\n"
        "Подпись: ________________\n"
        f"Дата: {cur_date}"
    )
    set_font(c2.runs[0], size=8.5)

    filename = f"Contract_{contract_number.replace('/', '_')}.docx"
    filepath = output_dir / filename
    doc.save(str(filepath))
    return str(filepath)
