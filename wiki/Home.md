# «Практика-Трекер» ақпараттық жүйесі — Жобалық Вики (Wiki)

Қош келдіңіз! Бұл вики «Практика-Трекер» жобасының негізгі регламенттері мен сәулеттік шешімдерін қамтиды.

## Негізгі бөлімдер:
1. [Жоба паспорты және мақсаттары](Home.md#жоба-паспорты)
2. [Жеткізу моделі (ADR-001)](../docs/adr/ADR-001-delivery-model.md)
3. [Командалық келісім және сапа критерийлері (DoR / DoD)](../docs/conventions/team_agreement.md)
4. [Кодпен жұмыс істеу және бұтақтау ережелері](../docs/conventions/branching_and_commits.md)
5. [Тапсырмалар тақтасының құрылымы (GitHub Projects)](Home.md#жоба-тақтасы)

## Жоба тақтасының баптаулары (GitHub Projects Configuration)
- **Бағандар (Columns / Workflow):**
  1. Backlog — Барлық тіркелген пайдаланушы оқиғалары мен идеялар.
  2. Ready for Dev — DoR талаптарына сай бағаланған, орындауға дайын тапсырмалар.
  3. In Progress — Әзірлеуші орындап жатқан тапсырмалар (WIP limit: адам басына 1 тапсырма).
  4. In Review / QA — Тестілеудегі немесе Pull Request тексерісіндегі тапсырмалар.
  5. Done — DoD талаптары толық орындалған, өндіріске дайын тапсырмалар.

- **Теңшелетін өрістер (Custom Fields):**
  - Priority: Single select (P1 - Critical, P2 - Major, P3 - Minor)
  - Story Points: Number (1, 2, 3, 5, 8, 13)
  - Component: Single select (Frontend, Backend, Database, Docs/QA)
  - Sprint: Iteration field (Sprint 1, Sprint 2, Sprint 3, Sprint 4)
  - Assignee: User field
