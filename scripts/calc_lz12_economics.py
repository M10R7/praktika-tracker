"""
Расчет стоимости инференса, точки окупаемости Self-Hosted GPU и генерация графиков для ЛЗ 12.
Использует точные замеры токенов из tiktoken (evals/eval_results.json) и официальные прайсы 2026 г.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = BASE_DIR / "evals" / "eval_results.json"

with open(RESULTS_PATH, encoding="utf-8") as f:
    res = json.load(f)

IN_TOK_TRIAGE = res["tokens"]["avg_total_input_tokens"]  # ~764.69
OUT_TOK_TRIAGE = 5.0  # JSON label + confidence

# Extended Assistant mode (RAG context + draft answer)
IN_TOK_RAG = 1500.0
OUT_TOK_RAG = 250.0

PRICES = {
    "GPT-4o-mini (OpenAI)": {"in": 0.15, "out": 0.60},
    "GPT-4.1-mini (OpenAI)": {"in": 0.40, "out": 1.60},
    "Gemini 2.5 Flash (Google)": {"in": 0.30, "out": 2.50},
}

GPU_SELF_HOSTED_VAST_L4 = 160.0  # Vast.ai NVIDIA L4 24GB (~$0.22/hr * 730h)
GPU_SELF_HOSTED_RUNPOD_L4 = 321.0  # RunPod Secure Cloud NVIDIA L4 (~$0.44/hr * 730h)


def calc_cost_per_req(price_dict, in_tok, out_tok):
    return (in_tok * price_dict["in"] + out_tok * price_dict["out"]) / 1_000_000


print("=== COST CALCULATION SUMMARY ===")
print(f"Triage Mode: {IN_TOK_TRIAGE:.1f} input tok + {OUT_TOK_TRIAGE:.1f} output tok")
for name, p in PRICES.items():
    c_req = calc_cost_per_req(p, IN_TOK_TRIAGE, OUT_TOK_TRIAGE)
    c_1500 = c_req * 1500
    c_15000 = c_req * 15000
    be_vast = GPU_SELF_HOSTED_VAST_L4 / c_req
    be_runpod = GPU_SELF_HOSTED_RUNPOD_L4 / c_req
    print(
        f"  {name:26s} | 1.5k/mo=${c_1500:6.3f} | 15k/mo (10x)=${c_15000:6.2f} | Break-even Vast=${be_vast:,.0f} req/mo | RunPod=${be_runpod:,.0f} req/mo"
    )

print(f"\nRAG + Draft Assistant Mode: {IN_TOK_RAG:.0f} input tok + {OUT_TOK_RAG:.0f} output tok")
for name, p in PRICES.items():
    c_req = calc_cost_per_req(p, IN_TOK_RAG, OUT_TOK_RAG)
    c_1500 = c_req * 1500
    c_15000 = c_req * 15000
    be_vast = GPU_SELF_HOSTED_VAST_L4 / c_req
    be_runpod = GPU_SELF_HOSTED_RUNPOD_L4 / c_req
    print(
        f"  {name:26s} | 1.5k/mo=${c_1500:6.2f} | 15k/mo (10x)=${c_15000:6.2f} | Break-even Vast={be_vast:,.0f} req/mo | RunPod={be_runpod:,.0f} req/mo"
    )


# --- Chart 1: Eval Comparison + Confusion Matrix ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=300)

models = [
    "TF-IDF + LinearSVC\n(Classic ML Baseline)",
    "Rules / Regex\n(No-AI Baseline)",
    "GPT-OSS 20B\n(Candidate LLM)",
]
accs = [
    res["models"]["tfidf_linearsvc_cv"]["accuracy"] * 100,
    res["models"]["rule_based"]["accuracy"] * 100,
    res["models"]["llm_gpt_oss_20b"]["accuracy"] * 100,
]
f1s = [
    res["models"]["tfidf_linearsvc_cv"]["macro_f1"] * 100,
    res["models"]["rule_based"]["macro_f1"] * 100,
    res["models"]["llm_gpt_oss_20b"]["macro_f1"] * 100,
]

x = np.arange(len(models))
w = 0.34
b1 = ax1.bar(x - w / 2, accs, w, label="Accuracy (%)", color="#3b82f6", alpha=0.9)
b2 = ax1.bar(x + w / 2, f1s, w, label="Macro-F1 (%)", color="#10b981", alpha=0.9)

ax1.axhline(
    85, color="#dc2626", linestyle="--", linewidth=1.3, label="Порог приемки Macro-F1 (85%)"
)
ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=8.5, fontweight="bold")
ax1.set_ylim(0, 112)
ax1.set_ylabel("Качество (%)", fontsize=9, fontweight="bold")
ax1.set_title(
    "Сравнение моделей на golden-наборе (N=36)\n(RU + KZ + смешанные обращения студентов ЕНУ)",
    fontsize=10.5,
    fontweight="bold",
)
ax1.grid(axis="y", linestyle="--", alpha=0.4)
ax1.legend(fontsize=7.8, loc="upper left")

for bar in b1:
    ax1.text(
        bar.get_x() + w / 2,
        bar.get_height() + 1.8,
        f"{bar.get_height():.1f}%",
        ha="center",
        fontsize=8,
        fontweight="bold",
        color="#1e40af",
    )
for bar in b2:
    ax1.text(
        bar.get_x() + w / 2,
        bar.get_height() + 1.8,
        f"{bar.get_height():.1f}%",
        ha="center",
        fontsize=8,
        fontweight="bold",
        color="#065f46",
    )

# Right: Confusion Matrix
cm = np.array(res["models"]["llm_gpt_oss_20b"]["confusion_matrix"])
short_labels = [
    "CONTRACT\nSIGN",
    "STATUS\nTRACK",
    "COMPANY\nBIN",
    "SCAN\nUPLOAD",
    "ESCALATE\nCOMPLEX",
]
im = ax2.imshow(cm, cmap="Blues", aspect="auto")
ax2.set_xticks(np.arange(len(short_labels)))
ax2.set_yticks(np.arange(len(short_labels)))
ax2.set_xticklabels(short_labels, fontsize=7.5, fontweight="bold")
ax2.set_yticklabels(short_labels, fontsize=7.5, fontweight="bold")
ax2.set_xlabel("Предсказанный класс (Predicted)", fontsize=8.5, fontweight="bold")
ax2.set_ylabel("Истинный класс (True)", fontsize=8.5, fontweight="bold")
ax2.set_title(
    "Матрица ошибок LLM (GPT-OSS 20B)\nAccuracy = 91.7% (33/36), Recall Escalation = 100%",
    fontsize=10.5,
    fontweight="bold",
)

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        val = cm[i, j]
        color = "white" if val > cm.max() / 2 else "#0f172a"
        ax2.text(
            j, i, str(val), ha="center", va="center", color=color, fontsize=10, fontweight="bold"
        )

plt.tight_layout()
plt.savefig(BASE_DIR.parent / "lz12_chart_eval_comparison.png", bbox_inches="tight")
plt.close()

# --- Chart 2: Cost & Break-Even Curve (RAG + Draft Mode & Triage Mode) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=300)

vols_k = np.linspace(1, 450, 200)  # thousands of requests/month (1k .. 450k)
vols = vols_k * 1000

# Plot 1: RAG + Draft Assistant (1500 in / 250 out) - realistic break-even region
for name, col in [
    ("GPT-4o-mini (OpenAI)", "#0284c7"),
    ("GPT-4.1-mini (OpenAI)", "#f59e0b"),
    ("Gemini 2.5 Flash (Google)", "#8b5cf6"),
]:
    c_req = calc_cost_per_req(PRICES[name], IN_TOK_RAG, OUT_TOK_RAG)
    ax1.plot(vols_k, vols * c_req, label=name, color=col, linewidth=2.0)

ax1.axhline(
    GPU_SELF_HOSTED_VAST_L4,
    color="#10b981",
    linestyle="--",
    linewidth=1.8,
    label="Self-Hosted GPU L4 (Vast.ai ~$160/мес)",
)
ax1.axhline(
    GPU_SELF_HOSTED_RUNPOD_L4,
    color="#ef4444",
    linestyle=":",
    linewidth=1.8,
    label="Self-Hosted GPU L4 (RunPod Secure ~$321/мес)",
)
ax1.axvline(1.5, color="#64748b", linestyle="-.", linewidth=1.1)
ax1.axvline(15, color="#0f172a", linestyle="-.", linewidth=1.1)
ax1.text(
    22,
    200,
    "Нагрузка ЕНУ:\n1.5k–15k/мес\n(зона у оси 0)",
    fontsize=7.5,
    color="#334155",
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#94a3b8"),
)

ax1.set_xlim(0, 450)
ax1.set_ylim(0, 480)
ax1.set_xlabel("Объем обращений в месяц (тыс. запросов)", fontsize=8.5, fontweight="bold")
ax1.set_ylabel("Стоимость в месяц (USD)", fontsize=8.5, fontweight="bold")
ax1.set_title(
    "Сценарий «RAG + Черновик ответа» (1500 in / 250 out)\nТочка окупаемости Self-Hosted GPU L4",
    fontsize=10,
    fontweight="bold",
)
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend(fontsize=7.2, loc="upper left")

# Plot 2: Zoom on ENU scale (0 to 25k req/mo) comparing Triage vs RAG API Costs
vols_enu = np.linspace(0.5, 25, 100) * 1000
for name, col in [
    ("GPT-4o-mini (Triage: 765/5 tok)", "#0284c7"),
    ("Gemini 2.5 Flash (Triage: 765/5 tok)", "#8b5cf6"),
]:
    key = name.split(" (")[0]
    full_key = [k for k in PRICES if key in k][0]
    c_req = calc_cost_per_req(PRICES[full_key], IN_TOK_TRIAGE, OUT_TOK_TRIAGE)
    ax2.plot(vols_enu / 1000, vols_enu * c_req, label=name, color=col, linewidth=2.2)

c_rag_4o = calc_cost_per_req(PRICES["GPT-4o-mini (OpenAI)"], IN_TOK_RAG, OUT_TOK_RAG)
ax2.plot(
    vols_enu / 1000,
    vols_enu * c_rag_4o,
    label="GPT-4o-mini (RAG + ответ)",
    color="#10b981",
    linestyle="--",
    linewidth=2.0,
)

ax2.axvline(1.5, color="#64748b", linestyle="-.", linewidth=1.2)
ax2.axvline(15.0, color="#0f172a", linestyle="-.", linewidth=1.2)
ax2.scatter(
    [1.5, 15.0],
    [
        1.5
        * 1000
        * calc_cost_per_req(PRICES["GPT-4o-mini (OpenAI)"], IN_TOK_TRIAGE, OUT_TOK_TRIAGE),
        15.0
        * 1000
        * calc_cost_per_req(PRICES["GPT-4o-mini (OpenAI)"], IN_TOK_TRIAGE, OUT_TOK_TRIAGE),
    ],
    color="#0284c7",
    zorder=5,
)

ax2.text(
    2.0,
    6.2,
    "ФИТ ЕНУ: 1 500 запр/мес\nТриаж GPT-4o-mini = $0.18/мес",
    fontsize=7.5,
    fontweight="bold",
    color="#1e40af",
    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#93c5fd", alpha=0.95),
)
ax2.text(
    15.6,
    0.7,
    "10x масштаб: 15 000 запр/мес\n• Триаж GPT-4o-mini = $1.77/мес\n• RAG + ответ = $5.63/мес",
    fontsize=7.5,
    fontweight="bold",
    color="#065f46",
    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#6ee7b7", alpha=0.95),
)

ax2.set_xlim(0, 26)
ax2.set_ylim(0, 10)
ax2.set_xlabel("Масштаб нагрузки ЕНУ (тыс. запросов/мес)", fontsize=8.5, fontweight="bold")
ax2.set_ylabel("Ежемесячный расход API (USD)", fontsize=8.5, fontweight="bold")
ax2.set_title(
    "Экономика эксплуатации в масштабе ЕНУ (1x vs 10x)\nSelf-Hosted (USD 160–321/мес) убыточен до ~150k–1.3M запр.",
    fontsize=10,
    fontweight="bold",
)
ax2.grid(True, linestyle="--", alpha=0.4)
ax2.legend(fontsize=7.2, loc="upper left")

plt.tight_layout()
plt.savefig(BASE_DIR.parent / "lz12_chart_cost_breakeven.png", bbox_inches="tight")
plt.close()
print("Charts successfully saved to root directory!")
