#!/usr/bin/env python3
"""Hermes evaluation adapter for ADK agents."""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def load_agent_with_custom_instruction(instruction: str):
    """Load ADK agent with a custom instruction (for eval/evolution)."""
    from google.adk.agents import Agent
    from google.adk.models import Gemini
    from app.agent import gcloud_billing_get_costs, bigquery_usage_analytics, knowledge_base_search

    return Agent(
        name="gcp_billing_support_agent",
        model=Gemini(
            model="gemini-3.1-pro-preview",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        tools=[gcloud_billing_get_costs, bigquery_usage_analytics, knowledge_base_search],
    )


def evaluate_agent(instruction: str, eval_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate agent with given instruction on eval cases.

    Returns dict with 'score' (0-1) and 'num_correct'.
    """
    agent = load_agent_with_custom_instruction(instruction)
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service, app_name="hermes_eval")

    correct = 0
    for i, case in enumerate(eval_cases):
        try:
            session = session_service.create_session_sync(
                user_id=f"hermes_user_{i}",
                app_name="hermes_eval"
            )
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=case['input'])]
            )
            events = list(runner.run(
                new_message=message,
                user_id=f"hermes_user_{i}",
                session_id=session.id,
            ))
            response_text = "".join(
                part.text
                for event in events
                if event.content and event.content.parts
                for part in event.content.parts
                if part.text
            )
            expected = case.get('expected_output', '').lower()
            response_lower = response_text.lower()

            key_terms = []
            if 'quota' in expected or 'limit' in expected:
                key_terms.extend(['quota', 'limit'])
            if 'cost' in expected or 'spike' in expected:
                key_terms.extend(['cost', 'spike'])
            if 'budget' in expected or 'alert' in expected:
                key_terms.extend(['budget', 'alert'])

            if not key_terms:
                score = 1.0 if len(response_text) > 50 else 0.0
            else:
                terms_found = sum(1 for term in key_terms if term in response_lower)
                score = terms_found / len(key_terms)

            if score >= 0.7:
                correct += 1
        except Exception as e:
            print(f"Error evaluating case {i}: {e}", file=sys.stderr)

    return {
        "score": correct / len(eval_cases) if eval_cases else 0.0,
        "num_correct": correct,
        "num_total": len(eval_cases)
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: adk_evaluator.py <instruction_file> <eval_dataset_json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        instruction = f.read()
    with open(sys.argv[2]) as f:
        dataset = json.load(f)

    eval_cases = [
        {
            'input': case['prompt']['parts'][0]['text'],
            'expected_output': case.get('reference', {}).get('response', {}).get('parts', [{}])[0].get('text', '')
        }
        for case in dataset.get('eval_cases', [])
    ]

    results = evaluate_agent(instruction, eval_cases)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
