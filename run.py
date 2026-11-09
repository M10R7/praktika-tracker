"""
Launch script for Praktika-Tracker MVP.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import uvicorn

from src.core.config import settings

if __name__ == "__main__":
    print("============================================================")
    print(f"🎓 Запуск веб-сервиса «{settings.PROJECT_NAME}»")
    print(f"📍 Главная страница: http://127.0.0.1:{settings.PORT}/")
    print(f"📝 Подача заявки:     http://127.0.0.1:{settings.PORT}/apply")
    print(f"🔍 Трекер статуса:    http://127.0.0.1:{settings.PORT}/tracker")
    print(f"📊 Кабинет деканата:  http://127.0.0.1:{settings.PORT}/coordinator")
    print(f"📚 Документация API:  http://127.0.0.1:{settings.PORT}/docs")
    print("============================================================")
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=False,
    )
