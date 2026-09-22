# ИС «Практика-Трекер» — Проектная Вики (Wiki)

Информационная система «Практика-Трекер» (индивидуальный проект).

## Основные разделы:
1. Паспорт проекта и цели
2. [Архитектурно-управленческое решение ADR-001](../docs/adr/ADR-001-delivery-model.md)
3. [Регламент разработки DoR / DoD](../docs/conventions/team_agreement.md)
4. [Правила ветвления и коммитов](../docs/conventions/branching_and_commits.md)

## Структура доски задач (GitHub Projects)
- **Колонки рабочего процесса:**
  1. Backlog — общий бэклог требований и дефектов.
  2. Ready for Dev — декомпозированные задачи, запланированные в текущую итерацию.
  3. In Progress — задача в активной разработке (WIP-лимит: строго 1 задача).
  4. In Review / QA — самопроверка (Self-Review), прогон линтеров и автотестов.
  5. Done — полностью готовый функционал, вошедший в инкремент.

- **Кастомные поля (Custom Fields):**
  - Priority: Single select (P1 - Critical, P2 - Major, P3 - Minor)
  - Story Points: Number (1, 2, 3, 5, 8)
  - Component: Single select (Frontend, Backend, Database, Docs)
  - Sprint: Iteration field (Sprint 1, Sprint 2, Sprint 3, Sprint 4)
  - Assignee: User field (@M10R7 — Азамат)
