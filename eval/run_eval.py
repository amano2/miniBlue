"""Comprehensive Evaluation Harness for Agentic HR Assistant & RightAction Governance.

Scores:
1. Policy Q&A Groundedness & Refusal Correctness (eval/test_questions.json)
2. RightAction Governance Compliance & Violation Detection (eval/test_actions.json)
3. Orchestrator Intent Routing Accuracy
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.pipeline import process_message
from src.generate import REFUSAL_RESPONSE


def run_qa_evaluation(eval_file: Path = ROOT_DIR / "eval" / "test_questions.json") -> dict:
    """Evaluates Policy Q&A groundedness and refusal guardrails."""
    if not eval_file.exists():
        raise FileNotFoundError(f"QA evaluation dataset not found at {eval_file}")

    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print("\n" + "=" * 80)
    print("TEST SUITE 1: POLICY Q&A & GROUNDED CITATION EVALUATION")
    print("=" * 80)

    in_scope_total = 0
    in_scope_passed = 0
    out_of_scope_total = 0
    out_of_scope_passed = 0
    retrieval_hits = 0

    for item in test_cases:
        qid = item["id"]
        query = item["query"]
        is_in_scope = item["is_in_scope"]
        expected_src = item.get("expected_source")
        expected_keywords = item.get("expected_keywords", [])

        start_t = time.perf_counter()
        res = process_message(query, session_id=f"eval-qa-{qid}")
        latency = time.perf_counter() - start_t

        answer = res["response"]
        refused = res["refused"]
        sources = res["sources"]

        top_source_files = [s.get("source_file") for s in sources]
        source_matched = (expected_src in top_source_files) if (is_in_scope and expected_src) else False
        if source_matched:
            retrieval_hits += 1

        test_passed = False
        if is_in_scope:
            in_scope_total += 1
            kw_match = any(kw.lower() in answer.lower() for kw in expected_keywords)
            if not refused and (source_matched or kw_match):
                test_passed = True
                in_scope_passed += 1
            status = "[PASS]" if test_passed else "[FAIL]"
        else:
            out_of_scope_total += 1
            if refused or REFUSAL_RESPONSE.lower() in answer.lower():
                test_passed = True
                out_of_scope_passed += 1
            status = "[PASS] (Refusal Triggered)" if test_passed else "[FAIL]"

        print(f"[{status}] Q{qid:02d} ({'In-Scope' if is_in_scope else 'Out-of-Scope'}): {query[:60]}... ({latency:.2f}s)")

    in_scope_acc = (in_scope_passed / in_scope_total * 100) if in_scope_total else 0.0
    out_of_scope_acc = (out_of_scope_passed / out_of_scope_total * 100) if out_of_scope_total else 0.0
    retrieval_acc = (retrieval_hits / in_scope_total * 100) if in_scope_total else 0.0

    print(f"\n--> Q&A In-Scope Accuracy:    {in_scope_passed}/{in_scope_total} ({in_scope_acc:.1f}%)")
    print(f"--> Q&A Refusal Accuracy:     {out_of_scope_passed}/{out_of_scope_total} ({out_of_scope_acc:.1f}%)")
    print(f"--> Q&A Retrieval Precision:  {retrieval_hits}/{in_scope_total} ({retrieval_acc:.1f}%)")

    return {
        "in_scope_accuracy": in_scope_acc,
        "refusal_accuracy": out_of_scope_acc,
        "retrieval_accuracy": retrieval_acc,
    }


def run_governance_evaluation(eval_file: Path = ROOT_DIR / "eval" / "test_actions.json") -> dict:
    """Evaluates RightAction governance compliance, violation catching, and routing."""
    if not eval_file.exists():
        raise FileNotFoundError(f"Action evaluation dataset not found at {eval_file}")

    with open(eval_file, "r", encoding="utf-8") as f:
        action_cases = json.load(f)

    print("\n" + "=" * 80)
    print("TEST SUITE 2: RIGHTACTION GOVERNANCE & VIOLATION DETECTION EVALUATION")
    print("=" * 80)

    total_actions = len(action_cases)
    decision_matches = 0
    intent_matches = 0
    violations_caught = 0
    total_violations = sum(1 for a in action_cases if a.get("is_violation", False))

    for item in action_cases:
        aid = item["id"]
        scenario = item["scenario"]
        message = item["message"]
        expected_intent = item["intent"]
        expected_decision = item["expected_decision"]
        is_violation = item.get("is_violation", False)

        start_t = time.perf_counter()
        res = process_message(message, session_id=f"eval-act-{aid}")
        latency = time.perf_counter() - start_t

        actual_intent = res["intent"]
        actual_decision = res.get("governance_decision", "UNKNOWN")
        agent_used = res.get("agent_used", "Unknown")

        intent_correct = actual_intent == expected_intent
        decision_correct = actual_decision == expected_decision

        if intent_correct:
            intent_matches += 1
        if decision_correct:
            decision_matches += 1

        if is_violation and actual_decision in ["FLAG_FOR_REVIEW", "BLOCK"]:
            violations_caught += 1

        pass_status = "[PASS]" if decision_correct else f"[FAIL (Exp: {expected_decision}, Got: {actual_decision})]"
        print(f"{pass_status} {aid} ({scenario}): Decision -> {actual_decision} | Agent: {agent_used} ({latency:.2f}s)")

    gov_accuracy = (decision_matches / total_actions * 100) if total_actions else 0.0
    intent_accuracy = (intent_matches / total_actions * 100) if total_actions else 0.0
    violation_catch_rate = (violations_caught / total_violations * 100) if total_violations else 0.0

    print(f"\n--> Governance Decision Accuracy: {decision_matches}/{total_actions} ({gov_accuracy:.1f}%)")
    print(f"--> Intent Routing Accuracy:      {intent_matches}/{total_actions} ({intent_accuracy:.1f}%)")
    print(f"--> Violation Catch Rate:         {violations_caught}/{total_violations} ({violation_catch_rate:.1f}%)")

    return {
        "governance_accuracy": gov_accuracy,
        "intent_accuracy": intent_accuracy,
        "violation_catch_rate": violation_catch_rate,
    }


def run_all_evaluations() -> None:
    """Runs complete end-to-end evaluation benchmark."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n" + "#" * 80)
    print("BLUEVERSE AGENTIC HR ASSISTANT — MASTER BENCHMARK RUNNER")
    print(f"LLM Model: {config.OPENROUTER_MODEL} | Embedding: {config.EMBEDDING_MODEL_NAME}")
    print("#" * 80)

    qa_res = run_qa_evaluation()
    gov_res = run_governance_evaluation()

    print("\n" + "=" * 80)
    print("📊 OVERALL AGENTIC SYSTEM SCORECARD")
    print("=" * 80)
    print(f"1. Policy Q&A Groundedness:       {qa_res['in_scope_accuracy']:.1f}%")
    print(f"2. Out-of-Scope Refusal Accuracy: {qa_res['refusal_accuracy']:.1f}%")
    print(f"3. Orchestrator Intent Routing:   {gov_res['intent_accuracy']:.1f}%")
    print(f"4. RightAction Governance Score:  {gov_res['governance_accuracy']:.1f}%")
    print(f"5. Violation Detection Rate:      {gov_res['violation_catch_rate']:.1f}%")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_evaluations()
