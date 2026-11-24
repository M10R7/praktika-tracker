"""
Автоматизированный ИИ-ассистент Solo PM для проекта «Практика-Трекер» (ЛЗ 13).
1. Собирает реальные факты из GitHub REST API (коммиты за 2 спринта, CI-запуски, задачи)
   и трекинг возраста открытых задач бэклога (Risk Radar).
2. Очищает данные от ПДн / секретов перед передачей (PII Sanitizer).
3. Генерирует еженедельный статус-отчет через открытую LLM (Ollama или бесплатный API GPT-OSS 20B).
4. Сохраняет исходные факты (raw_github_facts.json) для обязательной ручной верификации PM.

Автор: Сәбитов Азамат (гр. АЖ-47, Solo PM & Developer)
"""

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "docs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

REPO = os.getenv("GITHUB_REPOSITORY", "M10R7/praktika-tracker")
GH_TOKEN = os.getenv("GH_TOKEN", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "")  # Например http://localhost:11434/api/generate

# Открытые задачи и Action Items (из Postmortem INC-2026-001 и ADR-002 Release 2.0) для анализа возраста (Age)
OPEN_BACKLOG_TASKS = [
    {
        "id": "CI-FIX-01",
        "title": "Исправить падения GitHub Actions CI workflow (6 runs failed)",
        "created": "2026-11-03",
        "priority": "Blocker",
        "status": "In Progress",
    },
    {
        "id": "TECH-TASK-41",
        "title": "Вынос генерации DOCX в фоновые задачи BackgroundTasks",
        "created": "2026-11-12",
        "priority": "High",
        "status": "To Do",
    },
    {
        "id": "TECH-TASK-42",
        "title": "Переключение продакшн-стенда с SQLite на PostgreSQL 16",
        "created": "2026-11-12",
        "priority": "High",
        "status": "To Do",
    },
    {
        "id": "AI-01",
        "title": "Интеграция AI Practice Triage + PII-Redactor (Release 2.0)",
        "created": "2026-11-17",
        "priority": "Medium",
        "status": "Planned",
    },
    {
        "id": "US-15",
        "title": "Расширенный личный кабинет студента с архивом за 4 курса",
        "created": "2026-10-06",
        "priority": "Low",
        "status": "Backlog",
    },
]

PM_STATUS_PROMPT = """Ты — ассистент Solo PM проекта «Практика-Трекер» (ФИТ ЕНУ им. Л.Н. Гумилева, г. Астана).
Подготовь лаконичный, структурированный еженедельный статус-отчет для руководителя практики на русском языке
по предоставленным ниже точным фактам за 2 прошедших спринта (Спринт 2: 27.10–09.11.2026 и Спринт 3: 10.11–24.11.2026).

СТРОГИЕ ОГРАНИЧЕНИЯ:
1. Используй ТОЛЬКО переданные факты и цифры. Категорически запрещено выдумывать коммиты, проценты, даты или участников команды.
2. Помни, что проект выполняется индивидуально (Solo PM & Developer: Сәбитов Азамат, гр. АЖ-47). Не выдумывай митинги с несуществующими разработчиками.
3. Обязательно выдели рисковые зоны: статус CI/CD пайплайна и просроченные/зависшие задачи по возрасту (Age > 14 дней).
4. Формат вывода (Markdown):
   - ### 1. Сводка прогресса за 2 спринта (краткий статус: Green / Amber / Red и ключевые инкременты)
   - ### 2. Метрики репозитория и CI/CD (таблица: коммиты по спринтам, прогоны CI, процент успеха)
   - ### 3. Радар рисков и зависшие задачи (по возрасту Age и блокерам)
   - ### 4. План действий на следующую неделю (3 конкретных шага)"""


def sanitize_text(text: str) -> str:
    """Удаляет email, 12-значные ИИН/БИН и телефоны перед передачей во внешнюю LLM."""
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<EMAIL>", text)
    text = re.sub(r"\b\d{12}\b", "<IIN_BIN>", text)
    text = re.sub(r"\+?\d[\d\s\-()]{8,14}\d", "<PHONE>", text)
    return text


def fetch_github_facts() -> dict:
    """Собирает реальные данные о коммитах, CI-прогонах и задачах через GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"

    # 1. Commits
    r_commits = requests.get(
        f"https://api.github.com/repos/{REPO}/commits?per_page=30", headers=headers, timeout=15
    )
    r_commits.raise_for_status()
    raw_commits = r_commits.json()

    sprint2_commits = []  # 2026-10-27 .. 2026-11-09
    sprint3_commits = []  # 2026-11-10 .. 2026-11-24

    for c in raw_commits:
        sha = c["sha"][:7]
        date_str = c["commit"]["author"]["date"][:10]
        msg = sanitize_text(c["commit"]["message"].split("\n")[0])
        entry = {"sha": sha, "date": date_str, "message": msg}
        if "2026-10-27" <= date_str <= "2026-11-09":
            sprint2_commits.append(entry)
        elif date_str >= "2026-11-10":
            sprint3_commits.append(entry)

    # 2. GitHub Actions CI Runs
    r_runs = requests.get(
        f"https://api.github.com/repos/{REPO}/actions/runs?per_page=30", headers=headers, timeout=15
    )
    r_runs.raise_for_status()
    runs_data = r_runs.json().get("workflow_runs", [])

    ci_summary = {
        "total_runs": len(runs_data),
        "success_count": sum(1 for r in runs_data if r.get("conclusion") == "success"),
        "failure_count": sum(1 for r in runs_data if r.get("conclusion") == "failure"),
        "latest_run_status": runs_data[0].get("conclusion") if runs_data else "none",
        "latest_run_date": runs_data[0].get("created_at", "")[:10] if runs_data else "none",
    }

    # 3. GitHub Issues
    r_issues = requests.get(
        f"https://api.github.com/repos/{REPO}/issues?state=all", headers=headers, timeout=15
    )
    r_issues.raise_for_status()
    gh_issues_count = len(r_issues.json())

    # 4. Calculate Age for tracked backlog items relative to report date (2026-11-24)
    now_date = datetime(2026, 11, 24, tzinfo=UTC)
    tracked_tasks = []
    for task in OPEN_BACKLOG_TASKS:
        created_dt = datetime.strptime(task["created"], "%Y-%m-%d").replace(tzinfo=UTC)
        age_days = (now_date - created_dt).days
        tracked_tasks.append(
            {
                **task,
                "age_days": age_days,
                "is_stale": age_days > 14,
            }
        )

    return {
        "repo": REPO,
        "report_date": "2026-11-24",
        "total_repo_commits": len(raw_commits),
        "github_issues_count": gh_issues_count,
        "sprint_2": {
            "period": "2026-10-27 — 2026-11-09",
            "commits_count": len(sprint2_commits),
            "commits": sprint2_commits,
        },
        "sprint_3": {
            "period": "2026-11-10 — 2026-11-24",
            "commits_count": len(sprint3_commits),
            "commits": sprint3_commits,
        },
        "ci_cd": ci_summary,
        "backlog_risk_radar": tracked_tasks,
    }


def generate_report_via_llm(facts: dict) -> tuple[str, float, str]:
    """Отправляет агрегированные факты в LLM (Ollama или бесплатный API GPT-OSS 20B)."""
    facts_str = json.dumps(facts, ensure_ascii=False, indent=2)
    user_prompt = f"Ниже представлены фактические данные проекта за 2 прошедших спринта:\n\n```json\n{facts_str}\n```\n\nСформируй статус-отчет строго по инструкции."

    t0 = time.perf_counter()
    if OLLAMA_URL:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
                "prompt": f"{PM_STATUS_PROMPT}\n\n{user_prompt}",
                "stream": False,
                "options": {"temperature": 0.2, "seed": 42},
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["response"].strip(), time.perf_counter() - t0, "Ollama local"

    # Бесплатный внешний OpenAI-compatible API (GPT-OSS 20B)
    for _ in range(4):
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={
                "model": "openai-fast",
                "messages": [
                    {"role": "system", "content": PM_STATUS_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "seed": 42,
            },
            timeout=45,
        )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            return content, time.perf_counter() - t0, "GPT-OSS 20B (openai-fast)"
        if r.status_code in (402, 429):
            print(f"Rate limit ({r.status_code}), waiting 46s...")
            time.sleep(46)
            continue
        r.raise_for_status()
    raise RuntimeError("Failed to generate report from LLM endpoint")


def main():
    t_start = time.perf_counter()
    print(f"[1/3] Fetching live GitHub API & backlog telemetry for {REPO}...")
    facts = fetch_github_facts()
    t_fetch = time.perf_counter() - t_start

    raw_facts_path = REPORTS_DIR / "raw_github_facts.json"
    with open(raw_facts_path, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    print(f"      Saved verified ground-truth facts -> {raw_facts_path} ({t_fetch:.2f}s)")

    print("[2/3] Generating weekly status report via LLM...")
    report_md, t_llm, provider = generate_report_via_llm(facts)

    report_path = REPORTS_DIR / "weekly_status_sprint2_3.md"
    header = (
        "<!-- СГЕНЕРИРОВАНО ИИ-АССИСТЕНТОМ SOLO PM (ТРЕБУЕТ РУЧНОЙ ВЕРИФИКАЦИИ ПЕРЕД ОТПРАВКОЙ) -->\n"
        f"# Еженедельный статус-отчет: «Практика-Трекер» (Спринты 2–3)\n"
        f"**Дата генерации:** {facts['report_date']} | **Модель:** {provider} | **Время генерации:** {t_llm:.2f} с\n\n---\n\n"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(header + report_md + "\n")

    print(
        f"[3/3] Report saved -> {report_path} (LLM time: {t_llm:.2f}s, Total: {time.perf_counter() - t_start:.2f}s)"
    )


if __name__ == "__main__":
    main()
