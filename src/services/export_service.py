"""
Export service for Internship Registry (US-10).
Generates CSV format register for Dean's office and Platonus integration.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import csv
import io

from src.database.models import InternshipApplication


def export_applications_to_csv(applications: list[InternshipApplication]) -> str:
    """Exports list of applications to CSV string with UTF-8 BOM encoding for Excel."""
    output = io.StringIO()
    # Write BOM for proper Cyrillic rendering in Microsoft Excel
    output.write("\ufeff")

    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow(
        [
            "№ заявки",
            "ФИО студента",
            "ИИН студента",
            "Группа",
            "Специальность",
            "База практики (Компания)",
            "БИН компании",
            "Вид практики",
            "Дата начала",
            "Дата окончания",
            "Наставник от базы",
            "Руководитель от кафедры",
            "Статус",
            "Причина отклонения",
            "Дата создания",
        ]
    )

    for app in applications:
        student = app.student
        company = app.company
        writer.writerow(
            [
                app.application_number,
                student.full_name if student else "",
                student.iin if student else "",
                student.group_code if student else "",
                student.specialty_code if student else "",
                company.name if company else "",
                company.bin if company else "",
                app.practice_type,
                app.start_date,
                app.end_date,
                app.company_mentor_name,
                app.academic_supervisor_name,
                app.status,
                app.rejection_reason or "",
                app.created_at.strftime("%d.%m.%Y %H:%M") if app.created_at else "",
            ]
        )

    return output.getvalue()
