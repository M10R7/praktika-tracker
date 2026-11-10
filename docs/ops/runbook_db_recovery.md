# Эксплуатационный регламент (Production Runbook)

**Код регламента:** **RB-01**  
**Наименование:** Аварийное восстановление веб-сервиса при блокировке транзакций СУБД или сбое генератора сводных документов  
**Применимость:** Программный комплекс «Практика-Трекер» ФИТ ЕНУ им. Л.Н. Гумилева (Production / Staging)  
**Владелец регламента:** DevOps / Lead Engineer Сәбитов Азамат (гр. АЖ-47)  
**Целевое время восстановления (MTTR):** $\le 15$ минут  
**Необходимый уровень доступа:** SSH / Local Administrator, доступ к Docker и файловой системе сервиса  

---

## 1. Контекст и триггеры активации регламента

Регламент активируется дежурным инженером при наступлении любого из следующих условий:
1. **Срабатывание мониторинга Uptime Kuma:** алерт `[DOWN] /healthz` или `[DEGRADED] HTTP 504 Timeout > 10s`.
2. **Обращение координатора практики:** ошибки «Сервис временно недоступен» или бесконечная загрузка при нажатии кнопки «Сформировать приказ декана».
3. **Записи в логах сервера:**
   - `sqlite3.OperationalError: database is locked`
   - `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached`
   - `uvicorn.error: Server worker process exited unexpectedly`.

---

## 2. Пошаговый алгоритм действий (Step-by-Step Procedure)

```
[Триггер алерта]
       │
       ▼
 [Шаг 1: Диагностика и снятие дампов]
       │
       ▼
 [Шаг 2: Изоляция сбойного процесса (Graceful Kill)]
       │
       ▼
 [Шаг 3: Снятие файловой блокировки WAL / Пул PostgreSQL]
       │
       ▼
 [Шаг 4: Перезапуск службы через Systemd / Docker]
       │
       ▼
 [Шаг 5: Пост-верификация Smoke Test (Healthcheck + DOCX)]
       │
       ▼
 [Шаг 6: Оповещение стейкхолдеров о восстановлении]
```

---

### Шаг 1. Первичная экспресс-диагностика

1. Подключитесь к хосту приложения через терминал:
   ```bash
   cd /opt/praktika-tracker # либо путь к локальному каталогу
   ```
2. Проверьте статус сетевого порта 8000 и запущенных процессов:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
   Get-Process -Name python, uvicorn -ErrorAction SilentlyContinue
   ```
3. Проверьте последние 50 строк журнала ошибок сервера:
   ```powershell
   Get-Content -Path "storage/logs/app.log" -Tail 50
   ```
4. Убедитесь в доступности дискового пространства:
   ```powershell
   Get-PSDrive -PSProvider FileSystem
   ```
   *Критерий нормы:* свободно не менее 1 ГБ на системном диске.

---

### Шаг 2. Изоляция и принудительное завершение зависшего воркера

Если процесс завис и удерживает файловые дескрипторы:
1. Определите PID зависшего процесса:
   ```powershell
   $proc = Get-Process -Name python | Where-Object { $_.CPU -gt 5 -or $_.WorkingSet -gt 100MB }
   ```
2. Выполните корректную остановку:
   ```powershell
   Stop-Process -Id $proc.Id -Force
   ```
3. В случае работы в Docker-окружении:
   ```bash
   docker compose restart web
   ```

---

### Шаг 3. Снятие блокировок СУБД и очистка временных файлов

1. **Для SQLite (локальный/стендовый режим):**
   - Проверьте наличие временных файлов журналирования WAL (Write-Ahead Logging):
     ```powershell
     Test-Path "praktika.db-wal"
     Test-Path "praktika.db-shm"
     ```
   - Если файлы существуют и процесс остановлен, выполните безопасную синхронизацию контрольной точки через встроенную утилиту sqlite:
     ```powershell
     python -c "import sqlite3; conn = sqlite3.connect('praktika.db'); conn.execute('PRAGMA wal_checkpoint(TRUNCATE);'); conn.close(); print('WAL checkpoint completed successfully')"
     ```
2. **Для PostgreSQL (продуктивный режим в Docker):**
   - Проверьте наличие зависших блокировок транзакций:
     ```sql
     SELECT pid, query, state, age(clock_timestamp(), query_start) 
     FROM pg_stat_activity 
     WHERE state != 'idle' AND age(clock_timestamp(), query_start) > interval '1 minute';
     ```
   - Принудительно завершите зависшую транзакцию:
     ```sql
     SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <PID_ИЗ_ПРЕДЫДУЩЕГО_ЗАПРОСА>;
     ```

---

### Шаг 4. Проверка целостности файлового хранилища документов

1. Проверьте директорию `storage/documents/` на наличие незавершенных поврежденных файлов нулевого размера:
   ```powershell
   Get-ChildItem -Path "storage/documents/*.docx" | Where-Object { $_.Length -eq 0 } | Remove-Item -Force
   ```
2. Убедитесь, что директории хранения доступны для записи текущему пользователю сервиса.

---

### Шаг 5. Перезапуск веб-сервера и верификация (Smoke Test)

1. Запустите сервис в штатном режиме:
   ```powershell
   python run.py
   # Либо: docker compose up -d web
   ```
2. Выполните сквозной автоматизированный дымовой тест (Smoke Test):
   ```powershell
   # 1. Проверка доступности Healthcheck
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz" -Method Get

   # 2. Проверка работы публичного трекера
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tracker?iin=030514500012" -Method Get
   ```
   *Ожидаемый результат:* Код ответа 200 OK, JSON содержит `"status": "operational"`.

3. Проверьте панель мониторинга Uptime Kuma: статус должен смениться на зеленый «OPERATIONAL».

---

### Шаг 6. Оповещение стейкхолдеров и фиксация инцидента

1. Отправьте уведомление координатору практики в рабочий чат:
   > *«Уважаемые коллеги! Работоспособность портала «Практика-Трекер» полностью восстановлена. Функции генерации сводного приказа и проверки статусов доступны в штатном режиме. Приносим извинения за временные неудобства.»*
2. Зафиксируйте инцидент в журнале инцидентов (Incident Log) с указанием времени начала, времени устранения и примененных мер.
