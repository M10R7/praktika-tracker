"""
Генератор наглядной диаграммы экономии времени и аудита ошибок ИИ-ассистента PM (ЛЗ 13).
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

BASE_DIR = Path(__file__).resolve().parent.parent

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.6), dpi=300)

# Left: Stacked Bar Chart - Time Economics (Manual vs AI + Verification)
categories = ["Ручной процесс\n(Без ИИ)", "ИИ-ассистент +\nВерификация PM"]
x = np.arange(len(categories))
w = 0.48

# Manual components
m_collect = [14.0, 0.0]
m_format = [11.0, 0.0]
m_draft = [10.0, 0.0]

# AI + Verification components
a_run = [0.0, 0.3]
a_verify = [0.0, 4.5]
a_fix = [0.0, 2.5]

ax1.bar(x, m_collect, w, label="Сбор данных вручную (14 мин)", color="#64748b")
ax1.bar(x, m_format, w, bottom=m_collect, label="Расчет Age и верстка (11 мин)", color="#94a3b8")
ax1.bar(
    x,
    m_draft,
    w,
    bottom=np.array(m_collect) + np.array(m_format),
    label="Написание отчета и рисков (10 мин)",
    color="#cbd5e1",
)

ax1.bar(x, a_run, w, label="Автосбор + LLM генерация (0.3 мин)", color="#0284c7")
ax1.bar(x, a_verify, w, bottom=a_run, label="Ручная сверка с JSON (4.5 мин)", color="#10b981")
ax1.bar(
    x,
    a_fix,
    w,
    bottom=np.array(a_run) + np.array(a_verify),
    label="Правка 4 неточностей (2.5 мин)",
    color="#f59e0b",
)

ax1.text(
    0, 36.2, "35.0 мин", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#0f172a"
)
ax1.text(
    1,
    8.5,
    "7.3 мин\n(Чистая экономия:\n+27.7 мин / -79%)",
    ha="center",
    va="bottom",
    fontsize=8.8,
    fontweight="bold",
    color="#047857",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#ecfdf5", edgecolor="#10b981"),
)

ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontsize=9, fontweight="bold")
ax1.set_ylim(0, 43)
ax1.set_ylabel("Трудозатраты PM (минуты на 1 отчет)", fontsize=9, fontweight="bold")
ax1.set_title(
    "Экономика времени Solo PM (1 отчет = 2 спринта)\nС учетом 7 мин обязательной верификации",
    fontsize=10,
    fontweight="bold",
)
ax1.grid(axis="y", linestyle="--", alpha=0.4)
ax1.legend(fontsize=7.0, loc="upper right")

# Right: Verification Audit Breakdown (22 claims checked)
labels = [
    "Точные факты и цифры\n(18 из 22 = 81.8%)",
    "Галлюцинация CI-runs\nи дат (1 = 4.5%)",
    "Ошибка факта по коду\nSprint 3 (1 = 4.5%)",
    "Вредный совет по\nUS-15 (1 = 4.5%)",
    "Сбой верстки и термина\n«Стационарность» (1 = 4.5%)",
]
sizes = [18, 1, 1, 1, 1]
colors = ["#10b981", "#ef4444", "#f97316", "#eab308", "#8b5cf6"]
explode = (0.04, 0.08, 0.08, 0.08, 0.08)

wedges, texts = ax2.pie(
    sizes,
    explode=explode,
    colors=colors,
    startangle=140,
    wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2),
)

ax2.legend(
    wedges,
    labels,
    title="Аудит 22 утверждений ИИ",
    loc="center left",
    bbox_to_anchor=(0.88, 0.5),
    fontsize=7.6,
    title_fontsize=8.5,
)
ax2.text(
    0,
    0,
    "Error Rate:\n18.2%\n(4 / 22)",
    ha="center",
    va="center",
    fontsize=10,
    fontweight="bold",
    color="#b91c1c",
)
ax2.set_title(
    "Журнал ручной верификации отчета LLM\n(GPT-OSS 20B на реальных данных GitHub)",
    fontsize=10,
    fontweight="bold",
)

plt.tight_layout()
plt.savefig(BASE_DIR.parent / "lz13_chart_time_economics.png", bbox_inches="tight")
plt.close()
print("Saved lz13_chart_time_economics.png!")
