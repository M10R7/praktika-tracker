# ИС «Практика-Трекер» — Проектная Вики (Wiki)

Добро пожаловать в проектную вики информационной системы «Практика-Трекер».

## Основные разделы:
1. Паспорт проекта и бизнес-цели
2. [Архитектурно-управленческое решение ADR-001](../docs/adr/ADR-001-delivery-model.md)
3. [Командный регламент DoR / DoD](../docs/conventions/team_agreement.md)
4. [Правила ветвления и коммитов](../docs/conventions/branching_and_commits.md)

## Структура доски задач (GitHub Projects)
- **Колонки рабочего процесса:**
  1. Backlog — общий бэклог требований и идей.
  2. Ready for Dev — задачи, удовлетворяющие DoR, запланированные в текущий спринт.
  3. In Progress — задачи в активной разработке (WIP-лимит: 1 задача на разработчика).
  4. In Review / QA — задачи на Code Review и тестировании.
  5. Done — полностью завершенные задачи, соответствующие DoD.

- **Кастомные поля (Custom Fields):**
  - Priority: Single select (P1 - Critical, P2 - Major, P3 - Minor)
  - Story Points: Number (1, 2, 3, 5, 8, 13)
  - Component: Single select (Frontend, Backend, Database, Docs/QA)
  - Sprint: Iteration field (Sprint 1, Sprint 2, Sprint 3, Sprint 4)
  - Assignee: User field
