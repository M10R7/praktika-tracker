"""
Database seeding module with realistic FIT ENU data (Astana).
Pre-populates accredited partner companies, students, applications, and audit logs.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.database.models import (
    Company,
    InternshipApplication,
    StatusAuditLog,
    Student,
)
from src.services.document_generator import generate_contract_docx

COMPANIES_SEED = [
    {
        "bin": "081240012740",
        "name": "АО «Kaspi Bank»",
        "legal_form": "АО",
        "address": "г. Алматы, ул. Наурызбай батыра, 154",
        "director_name": "Лоresource Михаил",
        "contact_person": "Смагулов Берик (HR Tech)",
        "contact_phone": "+7 (727) 356-34-34",
        "contact_email": "tech-internship@kaspi.kz",
        "is_partner": True,
    },
    {
        "bin": "941240000193",
        "name": "АО «Казахтелеком»",
        "legal_form": "АО",
        "address": "г. Алматы, ул. Панфилова, 129",
        "director_name": "Мусин Багдат Батырбекович",
        "contact_person": "Алиева Жанар (Департамент ИТ)",
        "contact_phone": "+7 (727) 258-71-11",
        "contact_email": "hr@telecom.kz",
        "is_partner": True,
    },
    {
        "bin": "091040006374",
        "name": "ТОО «Kolesa Group»",
        "legal_form": "ТОО",
        "address": "г. Алматы, пр. Шевченко, 157/4",
        "director_name": "Богатырев Николай",
        "contact_person": "Сергеева Елена (DevRel)",
        "contact_phone": "+7 (727) 345-00-11",
        "contact_email": "internship@kolesa.team",
        "is_partner": True,
    },
    {
        "bin": "180540018590",
        "name": "ТОО «BTS Digital»",
        "legal_form": "ТОО",
        "address": "г. Астана, ул. Достык, 16 / г. Алматы Hub",
        "director_name": "Нуриев Нурали",
        "contact_person": "Кенесова Диана (Talent Lead)",
        "contact_phone": "+7 (7172) 79-55-00",
        "contact_email": "jobs@btsdigital.kz",
        "is_partner": True,
    },
    {
        "bin": "940140000385",
        "name": "АО «Народный Банк Казахстана» (Halyk Bank)",
        "legal_form": "АО",
        "address": "г. Астана, пр. Туран, 18",
        "director_name": "Шаяхметова Умут Болатхановна",
        "contact_person": "Искаков Азат (Центр ИТ-разработки)",
        "contact_phone": "+7 (727) 259-07-77",
        "contact_email": "praktika@halykbank.kz",
        "is_partner": True,
    },
    {
        "bin": "931240001157",
        "name": "РГП «Национальный Банк Республики Казахстан»",
        "legal_form": "РГП",
        "address": "г. Алматы, мкр. Коктем-3, 21",
        "director_name": "Сулейменов Тимур Муратович",
        "contact_person": "Байжанов Марат (Управление цифровизации)",
        "contact_phone": "+7 (727) 270-45-55",
        "contact_email": "it-dept@nationalbank.kz",
        "is_partner": True,
    },
    {
        "bin": "200540001235",
        "name": "ТОО «KazTech Innovations»",
        "legal_form": "ТОО",
        "address": "г. Алматы, пр. Жибек Жолы, 135",
        "director_name": "Ибраев Серик Канатович",
        "contact_person": "Касымов Арман",
        "contact_phone": "+7 (727) 292-14-14",
        "contact_email": "info@kaztech.kz",
        "is_partner": True,
    },
]

STUDENTS_SEED = [
    {
        "iin": "030514500012",
        "full_name": "Сәбитов Азамат Ерланович",
        "email": "azamat.sabitov@enu.kz",
        "phone": "+7 (707) 812-44-55",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "АЖ-47",
        "course": 4,
    },
    {
        "iin": "030822600023",
        "full_name": "Смагулова Динара Болатовна",
        "email": "dinara.smagulova@enu.kz",
        "phone": "+7 (701) 334-21-90",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "АЖ-47",
        "course": 4,
    },
    {
        "iin": "031110500039",
        "full_name": "Касымов Бахтияр Даниярович",
        "email": "bakhtiyar.kassymov@enu.kz",
        "phone": "+7 (777) 112-99-88",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06102 - Вычислительная техника и ПО",
        "group_code": "ВТиПО-42",
        "course": 4,
    },
    {
        "iin": "030219600045",
        "full_name": "Омарова Асель Сериковна",
        "email": "asel.omarova@enu.kz",
        "phone": "+7 (705) 556-78-12",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "ИС-41",
        "course": 4,
    },
    {
        "iin": "030704500055",
        "full_name": "Ахметов Дамир Муратович",
        "email": "damir.akhmetov@enu.kz",
        "phone": "+7 (702) 890-12-34",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06103 - Кибербезопасность",
        "group_code": "ИБ-43",
        "course": 4,
    },
    {
        "iin": "030915500062",
        "full_name": "Жолдасов Нурлан Кайратович",
        "email": "nurlan.zholdasov@enu.kz",
        "phone": "+7 (747) 441-23-77",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "АЖ-47",
        "course": 4,
    },
    {
        "iin": "031201600076",
        "full_name": "Ибрагимова Зарина Тимуровна",
        "email": "zarina.ibragimova@enu.kz",
        "phone": "+7 (708) 991-33-45",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "ИС-41",
        "course": 4,
    },
    {
        "iin": "030412500088",
        "full_name": "Токтаров Руслан Берикович",
        "email": "ruslan.toktarov@enu.kz",
        "phone": "+7 (775) 678-90-21",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06102 - Вычислительная техника и ПО",
        "group_code": "ВТиПО-42",
        "course": 4,
    },
    {
        "iin": "031025500097",
        "full_name": "Маратов Айдар Касымович",
        "email": "aidar.maratov@enu.kz",
        "phone": "+7 (701) 456-11-22",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06103 - Кибербезопасность",
        "group_code": "ИБ-43",
        "course": 4,
    },
    {
        "iin": "030618500107",
        "full_name": "Кенесов Ербол Сакенович",
        "email": "erbol.kenesov@enu.kz",
        "phone": "+7 (771) 234-56-78",
        "faculty": "Факультет информационных технологий",
        "specialty_code": "6B06101 - Информационные системы",
        "group_code": "АЖ-47",
        "course": 4,
    },
]


def seed_database(db: Session):
    """Checks if database is empty and seeds initial data."""
    if db.query(Company).count() > 0:
        return

    # 1. Seed Companies
    companies_map = {}
    for c_data in COMPANIES_SEED:
        c = Company(**c_data)
        db.add(c)
        db.flush()
        companies_map[c.bin] = c

    # 2. Seed Students
    students_list = []
    for s_data in STUDENTS_SEED:
        st = Student(**s_data)
        db.add(st)
        db.flush()
        students_list.append(st)

    db.commit()

    # 3. Seed Applications in realistic states
    apps_seed_config = [
        # Student 0: Azamat Sabitov -> Kaspi Bank (Approved & Generated DOCX)
        {
            "student_idx": 0,
            "company_bin": "081240012740",
            "mentor": "Смагулов Берик (Senior Python Architect)",
            "status": "approved",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
        # Student 1: Dinara Smagulova -> Kolesa Group (Approved & Generated DOCX)
        {
            "student_idx": 1,
            "company_bin": "091040006374",
            "mentor": "Сергеева Елена (Team Lead Data Engineering)",
            "status": "approved",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
        # Student 2: Bakhtiyar Kassymov -> Казахтелеком (In Order)
        {
            "student_idx": 2,
            "company_bin": "941240000193",
            "mentor": "Алиева Жанар (Ведущий инженер)",
            "status": "in_order",
            "supervisor": "Шаяхметова А. К.",
        },
        # Student 3: Asel Omarova -> BTS Digital (In Order)
        {
            "student_idx": 3,
            "company_bin": "180540018590",
            "mentor": "Кенесова Диана (Product Analyst)",
            "status": "in_order",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
        # Student 4: Damir Akhmetov -> Halyk Bank (Approved)
        {
            "student_idx": 4,
            "company_bin": "940140000385",
            "mentor": "Искаков Азат (Руководитель отдела ИБ)",
            "status": "approved",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
        # Student 5: Nurlan Zholdasov -> Kaspi Bank (Under Review)
        {
            "student_idx": 5,
            "company_bin": "081240012740",
            "mentor": "Турсунов Марат (Mobile Lead)",
            "status": "under_review",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
        # Student 6: Zarina Ibragimova -> Национальный Банк РК (Under Review)
        {
            "student_idx": 6,
            "company_bin": "931240001157",
            "mentor": "Байжанов Марат (Главный специалист)",
            "status": "under_review",
            "supervisor": "Шаяхметова А. К.",
        },
        # Student 7: Ruslan Toktarov -> KazTech (Rejected with reason - US-06)
        {
            "student_idx": 7,
            "company_bin": "200540001235",
            "mentor": "Касымов Арман",
            "status": "rejected",
            "rejection_reason": "Несоответствие профиля деятельности компании учебной программе специальности 6B06102",
            "supervisor": "Самбетбаева Мадина Аралбаевна",
        },
    ]

    for idx, cfg in enumerate(apps_seed_config, start=1):
        st = students_list[cfg["student_idx"]]
        comp = companies_map[cfg["company_bin"]]
        app_num = f"ПР-2026-FIT-{idx:04d}"

        # If approved, generate real official DOCX contract
        docx_path = None
        if cfg["status"] in ("approved", "in_order"):
            try:
                docx_path = generate_contract_docx(
                    contract_number=f"Д-2026-FIT-{idx:04d}",
                    student_fullname=st.full_name,
                    student_iin=st.iin,
                    student_group=st.group_code,
                    specialty_code=st.specialty_code,
                    company_name=comp.name,
                    company_bin=comp.bin,
                    company_address=comp.address,
                    company_director=comp.director_name,
                    mentor_fullname=cfg["mentor"],
                    academic_supervisor=cfg["supervisor"],
                    start_date="2026-06-01",
                    end_date="2026-07-15",
                )
            except Exception:
                docx_path = None

        app = InternshipApplication(
            application_number=app_num,
            student_id=st.id,
            company_id=comp.id,
            practice_type="Өндірістік практика / Производственная практика",
            start_date="2026-06-01",
            end_date="2026-07-15",
            company_mentor_name=cfg["mentor"],
            academic_supervisor_name=cfg["supervisor"],
            status=cfg["status"],
            rejection_reason=cfg.get("rejection_reason"),
            contract_file_path=docx_path,
            created_at=datetime.utcnow() - timedelta(days=12 - idx),
        )
        db.add(app)
        db.flush()

        # Add initial audit log entry (SEC-02)
        audit_1 = StatusAuditLog(
            application_id=app.id,
            old_status=None,
            new_status="under_review",
            changed_by="Система (Подача заявки студентом)",
            comment="Первичная регистрация заявления через веб-портал",
            ip_address="192.168.1.45",
            created_at=app.created_at,
        )
        db.add(audit_1)

        if cfg["status"] != "under_review":
            audit_2 = StatusAuditLog(
                application_id=app.id,
                old_status="under_review",
                new_status=cfg["status"],
                changed_by="Координатор практики ФИТ ЕНУ",
                comment=cfg.get("rejection_reason")
                or "Согласовано кафедрой ИС после проверки документов",
                ip_address="172.16.10.12",
                created_at=app.created_at + timedelta(hours=3),
            )
            db.add(audit_2)

    db.commit()
