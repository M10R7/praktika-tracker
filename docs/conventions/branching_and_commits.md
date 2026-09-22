# Соглашения команды по веткам и коммитам (Branching & Commit Conventions)

## 1. Стратегия ветвления (Git Branching Model)
В проекте используется модель **Trunk-based / GitHub Flow**:
- main — защищенная стабильная ветка (Production-ready). Прямые коммиты запрещены, изменения вносятся только через Pull Request.
- develop — ветка интеграции и тестирования (Staging).
- Рабочие ветки создаются от develop по единому шаблону:
  <type>/<issue-id>-<short-description>

Примеры:
- Новая функциональность: eat/PT-12-auth-bin-validation
- Исправление ошибки: ix/PT-25-pdf-margin-overflow
- Документация: docs/PT-02-adr-delivery-model
- Техническая задача / Spike: spike/PT-09-fastapi-pdf-generation

## 2. Стандарт коммитов (Conventional Commits v1.0.0)
Коммиты пишутся на английском языке с семантическим префиксом:
<type>(<scope>): <description>

Основные префиксы:
- eat: — новая пользовательская функциональность (например, eat(auth): add bin validation)
- ix: — исправление ошибки (например, ix(contract): fix company head field layout)
- docs: — изменения в документации (например, docs(adr): add ADR-001 delivery model)
- 
efactor: — переработка кода без изменения логики
- 	est: — добавление или исправление тестов
- chore: — обновление зависимостей и сборки
