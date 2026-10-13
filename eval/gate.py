"""Eval gate: run the bot on the golden set, score it with Ragas, block if a score drops.

Exit codes:
  0  every metric at or above its threshold
  1  a metric below its threshold: quality regression, the PR is blocked
  2  the judge could not score (quota or rate limit): not a quality verdict

Only scores are printed. Ghost's documentation is not openly licensed, so no
excerpt of it ever reaches a public CI log.
"""
import argparse
import json
import math
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ragas import EvaluationDataset, evaluate  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import Faithfulness, LLMContextRecall  # noqa: E402
from ragas.run_config import RunConfig  # noqa: E402

from bot.answer import ask  # noqa: E402
from bot.corpus import DOCS_SHA  # noqa: E402
from bot.llm import chat_model, model_name  # noqa: E402

HERE = Path(__file__).resolve().parent
THRESHOLDS = json.loads((HERE / "thresholds.json").read_text())
QUOTA_HINTS = ("429", "rate limit", "quota", "capacity")


def ask_with_retry(question, sabotage, attempts=5, wait=30):
    """Mistral's free tier sometimes answers "not enough capacity". Wait and retry before giving up."""
    for attempt in range(1, attempts + 1):
        try:
            return ask(question, sabotage=sabotage)
        except Exception as e:  # noqa: BLE001
            if attempt == attempts or not any(h in str(e).lower() for h in QUOTA_HINTS):
                raise
            print(f"  judge busy, retrying in {wait * attempt}s ({attempt}/{attempts - 1})")
            time.sleep(wait * attempt)


def load_cases(limit):
    lines = (HERE / "dataset.jsonl").read_text().splitlines()
    cases = [json.loads(l) for l in lines if l.strip()]
    return cases[:limit] if limit else cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sabotage", action="store_true", help="break the bot on purpose: the gate must go red")
    parser.add_argument("--limit", type=int, default=0, help="score only the first N cases")
    args = parser.parse_args()

    print(f"judge and bot: {model_name()}" + ("  [SABOTAGED BOT]" if args.sabotage else ""))
    print(f"docs: TryGhost/Docs@{DOCS_SHA[:7]}")
    samples = []
    try:
        for case in load_cases(args.limit):
            out = ask_with_retry(case["user_input"], args.sabotage)
            samples.append({
                "user_input": case["user_input"],
                "response": out["answer"],
                "retrieved_contexts": out["contexts"],
                "reference": case["reference"],
            })
        result = evaluate(
            EvaluationDataset.from_list(samples),
            metrics=[Faithfulness(), LLMContextRecall()],
            llm=LangchainLLMWrapper(chat_model()),
            run_config=RunConfig(max_workers=1, max_retries=6, timeout=300),
            show_progress=False,
        )
    except Exception as e:  # noqa: BLE001
        if any(h in str(e).lower() for h in QUOTA_HINTS):
            print(f"JUDGE UNAVAILABLE (quota or rate limit): {e}")
            sys.exit(2)
        raise

    table = result.to_pandas()
    failed = {}
    for metric, threshold in THRESHOLDS["mean"].items():
        values = [v for v in table[metric] if not math.isnan(v)]
        if len(values) < len(table) / 2:
            print(f"JUDGE UNAVAILABLE: {metric} scored only {len(values)} of {len(table)} cases")
            sys.exit(2)
        mean = sum(values) / len(values)
        mark = "ok  " if mean >= threshold else "FAIL"
        print(f"{mark} {metric:<15} {mean:.2f}  (threshold {threshold}, {len(values)}/{len(table)} scored)")
        if mean < threshold:
            failed[metric] = round(mean, 2)

    # A mean can hide one answer that was invented outright: every case has a floor too.
    for metric, floor in THRESHOLDS["case_floor"].items():
        below = [i + 1 for i, v in enumerate(table[metric]) if not math.isnan(v) and v < floor]
        mark = "ok  " if not below else "FAIL"
        print(f"{mark} {metric:<15} no case below {floor}" + (f": cases {below}" if below else ""))
        if below:
            failed[f"{metric} floor"] = below

    for i, row in table.iterrows():
        print(f"  case {i + 1:>2}: " + "  ".join(f"{m}={row[m]:.2f}" for m in THRESHOLDS["mean"]))

    if failed:
        print(f"GATE RED: {failed}")
        sys.exit(1)
    print("GATE GREEN")


if __name__ == "__main__":
    main()
