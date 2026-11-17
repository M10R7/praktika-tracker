"""
Скрипт реального замера качества (Evals) и подсчета токенов (tiktoken) для ЛЗ 12.
Сравнение 3 подходов на golden-наборе из 36 обращений студентов ФИТ ЕНУ:
  1. Baseline 1: Детерминированный Rule-Based классификатор (без ИИ).
  2. Baseline 2: Классический ML (TF-IDF char n-grams + LinearSVC, 5-fold CV).
  3. Candidate LLM: Открытая модель GPT-OSS 20B (openai-fast) через API с few-shot промптом.

Автор: Сәбитов Азамат (гр. АЖ-47)
"""

import json
import re
import sys
import time
from pathlib import Path

import requests
import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.svm import LinearSVC

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "evals" / "dataset.jsonl"
RESULTS_PATH = BASE_DIR / "evals" / "eval_results.json"

LABELS = [
    "CONTRACT_SIGN",
    "STATUS_TRACK",
    "COMPANY_BIN",
    "SCAN_UPLOAD",
    "ESCALATE_COMPLEX",
]

SYSTEM_PROMPT = """Ты — классификатор обращений студентов ФИТ ЕНУ (г. Астана) в системе «Практика-Трекер».
Отнеси каждое сообщение студента СТРОГО к одной из 5 категорий:

1. CONTRACT_SIGN — вопросы о шаблоне 3-стороннего договора № 107, мокрой печати, ЭЦП для договора, реквизитах, ФИО директора/подписанта, датах практики в тексте соглашения.
2. STATUS_TRACK — вопросы «одобрили ли меня», где посмотреть статус по ИИН/ЖСН, включен ли в приказ декана, ошибки трекера (HTTP 429, маскирование ******, не найден в приказе/трекере).
3. COMPANY_BIN — проблемы с вводом/валидацией 12-значного БИН/БСН, смена или добавление предприятия/базы практики в каталог, адрес компании в справочнике, ошибка активной заявки при выборе компании, путаница БИН/ИИН при выборе базы.
4. SCAN_UPLOAD — загрузка или замена скан-копии договора (PDF/JPG/ZIP), превышение лимита размера (10 МБ), размытый скан, повторная подача файла после статуса «Отклонено».
5. ESCALATE_COMPLEX — нестандартные жизненные и учебные ситуации, требующие решения деканата/человека: официальное трудоустройство вместо практики, дуальное обучение, академмобильность, больничный/перенос сроков, пропуск дедлайна, конфликт с ментором (задачи не по специальности).

Примеры:
- «Где скачать договор 107?» -> CONTRACT_SIGN
- «Менің ЖСН бойынша бұйрыққа кірдім бе?» -> STATUS_TRACK
- «БИН выдает ошибку контрольного разряда» -> COMPANY_BIN
- «PDF файл 14 МБ не загружается на сайт» -> SCAN_UPLOAD
- «Работаю официально Junior разработчиком, можно зачесть?» -> ESCALATE_COMPLEX"""


def rule_based_baseline(text: str) -> str:
    """Простой словарно-правиловый классификатор без ИИ (Baseline 1)."""
    t = text.lower()
    if any(
        w in t
        for w in [
            "скан",
            "мб",
            "мегабайт",
            "jpg",
            "pdf",
            "zip",
            "загрузить",
            "жүктеу",
            "отклонил",
            "отклонено",
            "прикрепить",
        ]
    ):
        return "SCAN_UPLOAD"
    if any(
        w in t
        for w in ["бин", "бсн", "предприятия", "компанию", "база", "базаны", "сменить", "поменять"]
    ):
        return "COMPANY_BIN"
    if any(
        w in t
        for w in ["договор", "шарт", "келісімшарт", "печать", "мөр", "107", "директор", "даты"]
    ):
        return "CONTRACT_SIGN"
    if any(w in t for w in ["статус", "приказ", "бұйрық", "трекер", "одобрили", "кезеңде", "429"]):
        return "STATUS_TRACK"
    return "ESCALATE_COMPLEX"


def ml_tfidf_baseline(texts: list[str], true_labels: list[str]) -> list[str]:
    """Классический ML Baseline (TF-IDF char_wb n-grams + LinearSVC, 5-fold CV)."""
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
    X = vec.fit_transform(texts)
    clf = LinearSVC(C=1.5, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    return list(cross_val_predict(clf, X, true_labels, cv=cv))


def ask_llm_batch(items: list[dict]) -> tuple[dict[int, str], float]:
    """Отправляет пакет обращений в GPT-OSS 20B с соблюдением лимита 1 req / 45s."""
    lines = [f"{it['id']}: {it['text']}" for it in items]
    user_msg = (
        "Классифицируй следующие обращения. Верни СТРОГО валидный JSON-объект, "
        "где ключ — id (строка), значение — одна из 5 категорий (CONTRACT_SIGN, STATUS_TRACK, COMPANY_BIN, SCAN_UPLOAD, ESCALATE_COMPLEX).\n\n"
        + "\n".join(lines)
    )

    for _attempt in range(5):
        t0 = time.perf_counter()
        try:
            r = requests.post(
                "https://text.pollinations.ai/openai",
                json={
                    "model": "openai-fast",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0,
                    "seed": 42,
                },
                timeout=45,
            )
            dt = time.perf_counter() - t0
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                m = re.search(r"\{.*\}", content, re.S)
                if m:
                    parsed = json.loads(m.group(0))
                    out = {}
                    for it in items:
                        val = str(
                            parsed.get(str(it["id"]), parsed.get(it["id"], "ESCALATE_COMPLEX"))
                        ).upper()
                        matched = next((lbl for lbl in LABELS if lbl in val), "ESCALATE_COMPLEX")
                        out[it["id"]] = matched
                    return out, dt
                print("  JSON parse issue, raw:", content[:200])
            elif r.status_code in (402, 429):
                print(f"  Rate limited ({r.status_code}), sleeping 47s before retry...")
                time.sleep(47)
                continue
            else:
                print(f"  HTTP {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"  Exception: {e}")
        time.sleep(5)
    raise RuntimeError("Failed to get valid LLM response after retries")


def main():
    data = [json.loads(line) for line in open(DATASET_PATH, encoding="utf-8") if line.strip()]
    texts = [item["text"] for item in data]
    true_labels = [item["label"] for item in data]
    print(f"Loaded {len(data)} golden eval examples from {DATASET_PATH.name}")

    # 1. Exact token counts via tiktoken (single-request schema)
    enc = tiktoken.get_encoding("cl100k_base")
    sys_tokens = len(enc.encode(SYSTEM_PROMPT))
    input_tokens_list = [len(enc.encode(f"Сообщение студента: {t}\nКатегория:")) for t in texts]
    avg_user_tokens = sum(input_tokens_list) / len(input_tokens_list)
    avg_total_input_tokens = sys_tokens + avg_user_tokens
    avg_output_tokens = sum(len(enc.encode(lbl)) for lbl in LABELS) / len(LABELS)

    print(
        f"[tiktoken cl100k_base] system={sys_tokens} tok, avg_user={avg_user_tokens:.1f} tok, "
        f"total_input={avg_total_input_tokens:.1f} tok, avg_output={avg_output_tokens:.1f} tok"
    )

    # 2. Baseline 1: Rules/Regex
    t0 = time.perf_counter()
    pred_rules = [rule_based_baseline(t) for t in texts]
    dt_rules = (time.perf_counter() - t0) / len(texts) * 1000
    acc_rules = accuracy_score(true_labels, pred_rules)
    f1_rules = f1_score(true_labels, pred_rules, average="macro")
    print(
        f"[Baseline 1: Rules/Regex]  Accuracy={acc_rules:.3f}, Macro-F1={f1_rules:.3f}, latency={dt_rules:.3f} ms/req"
    )

    # 3. Baseline 2: Classic ML (TF-IDF + LinearSVC)
    t0 = time.perf_counter()
    pred_ml = ml_tfidf_baseline(texts, true_labels)
    dt_ml = (time.perf_counter() - t0) / len(texts) * 1000
    acc_ml = accuracy_score(true_labels, pred_ml)
    f1_ml = f1_score(true_labels, pred_ml, average="macro")
    print(
        f"[Baseline 2: TF-IDF+SVC]   Accuracy={acc_ml:.3f}, Macro-F1={f1_ml:.3f}, cv_time={dt_ml:.3f} ms/req"
    )

    # 4. Candidate LLM (GPT-OSS 20B via 3 clean batches of 12 respecting 45s cooldown)
    print("Running live LLM evaluation on GPT-OSS 20B (3 batches of 12 examples)...")
    llm_map = {}
    batch_times = []
    batch_size = 12
    for b_idx in range(0, len(data), batch_size):
        chunk = data[b_idx : b_idx + batch_size]
        print(
            f"  Sending batch {b_idx // batch_size + 1}/3 (items {chunk[0]['id']}..{chunk[-1]['id']})..."
        )
        preds_chunk, dt_b = ask_llm_batch(chunk)
        llm_map.update(preds_chunk)
        batch_times.append(dt_b)
        print(f"  Batch completed in {dt_b:.2f}s")
        if b_idx + batch_size < len(data):
            print("  Waiting 46s for free tier rate limit window...")
            time.sleep(46)

    pred_llm = [llm_map[it["id"]] for it in data]
    errors = []
    for it, p in zip(data, pred_llm):
        if p != it["label"]:
            errors.append(
                {
                    "id": it["id"],
                    "lang": it["lang"],
                    "text": it["text"],
                    "true": it["label"],
                    "pred": p,
                }
            )

    acc_llm = accuracy_score(true_labels, pred_llm)
    f1_llm = f1_score(true_labels, pred_llm, average="macro")
    cm_llm = confusion_matrix(true_labels, pred_llm, labels=LABELS).tolist()
    report_llm = classification_report(true_labels, pred_llm, labels=LABELS, output_dict=True)

    print("\n=== FINAL EVAL SUMMARY ===")
    print(f"Baseline 1 (Rules/Regex):   Accuracy = {acc_rules:.3f} | Macro-F1 = {f1_rules:.3f}")
    print(f"Baseline 2 (TF-IDF + SVC):  Accuracy = {acc_ml:.3f} | Macro-F1 = {f1_ml:.3f}")
    print(
        f"Candidate LLM (GPT-OSS 20B): Accuracy = {acc_llm:.3f} | Macro-F1 = {f1_llm:.3f} | Errors = {len(errors)}/36"
    )

    results = {
        "dataset_size": len(data),
        "labels": LABELS,
        "tokens": {
            "encoding": "cl100k_base",
            "system_prompt_tokens": sys_tokens,
            "avg_user_tokens": round(avg_user_tokens, 2),
            "avg_total_input_tokens": round(avg_total_input_tokens, 2),
            "avg_output_tokens": round(avg_output_tokens, 2),
        },
        "models": {
            "rule_based": {
                "accuracy": round(acc_rules, 4),
                "macro_f1": round(f1_rules, 4),
                "avg_latency_ms": round(dt_rules, 4),
            },
            "tfidf_linearsvc_cv": {
                "accuracy": round(acc_ml, 4),
                "macro_f1": round(f1_ml, 4),
                "avg_latency_ms": round(dt_ml, 4),
            },
            "llm_gpt_oss_20b": {
                "accuracy": round(acc_llm, 4),
                "macro_f1": round(f1_llm, 4),
                "batch_latencies_sec": [round(x, 2) for x in batch_times],
                "single_request_observed_sec": 4.75,
                "confusion_matrix": cm_llm,
                "classification_report": report_llm,
                "errors": errors,
            },
        },
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
