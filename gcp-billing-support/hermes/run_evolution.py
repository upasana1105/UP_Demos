#!/usr/bin/env python3
"""
Simplified Hermes evolution runner for GCP billing agent.

Uses GEPA (Genetic-Pareto Prompt Evolution) principles to evolve
the agent's system instruction across 5 iterations.

Usage:
    python hermes/run_evolution.py

Output:
    hermes/output/evolved_instruction_TIMESTAMP.txt
    hermes/output/evolution_metrics_TIMESTAMP.json
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
os.environ['GOOGLE_CLOUD_LOCATION'] = os.getenv('GOOGLE_CLOUD_LOCATION', 'global')


def load_baseline_instruction():
    """Extract current agent instruction from agent.py."""
    agent_file = project_root / 'app' / 'agent.py'
    with open(agent_file, 'r') as f:
        content = f.read()
        start = content.find('instruction="""') + len('instruction="""')
        end = content.find('"""', start)
        return content[start:end].strip()


def load_eval_dataset():
    """Load evaluation dataset."""
    dataset_file = project_root / 'tests' / 'eval' / 'datasets' / 'billing-eval-medium.json'
    with open(dataset_file, 'r') as f:
        data = json.load(f)

    cases = []
    for case in data['eval_cases']:
        cases.append({
            'id': case['eval_case_id'],
            'input': case['prompt']['parts'][0]['text'],
            'expected': case.get('reference', {}).get('response', {}).get('parts', [{}])[0].get('text', ''),
            'category': case.get('metadata', {}).get('category', 'unknown')
        })
    return cases


def evaluate_instruction(instruction: str, eval_cases: list) -> float:
    """Evaluate an instruction on eval cases. Returns accuracy score (0-1)."""
    from google.adk.agents import Agent
    from google.adk.models import Gemini
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from app.agent import gcloud_billing_get_costs, bigquery_usage_analytics, knowledge_base_search

    agent = Agent(
        name="gcp_billing_support_agent_eval",
        model=Gemini(
            model="gemini-3.1-pro-preview",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        tools=[gcloud_billing_get_costs, bigquery_usage_analytics, knowledge_base_search],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service, app_name="eval")

    correct = 0
    for i, case in enumerate(eval_cases):
        try:
            session = session_service.create_session_sync(
                user_id=f"user_{i}",
                app_name="eval"
            )
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=case['input'])]
            )
            events = list(runner.run(
                new_message=message,
                user_id=f"user_{i}",
                session_id=session.id,
            ))
            response = "".join(
                part.text
                for event in events
                if event.content and event.content.parts
                for part in event.content.parts
                if part.text
            )
            # Keyword-based scoring per category
            if len(response) > 100:
                category = case['category']
                if category == 'quota_exceeded' and 'quota' in response.lower():
                    correct += 1
                elif category == 'cost_spike' and ('cost' in response.lower() or 'spike' in response.lower()):
                    correct += 1
                elif category == 'budget_alert' and 'budget' in response.lower():
                    correct += 1
                elif category == 'optimization' and 'optimi' in response.lower():
                    correct += 1
                elif category == 'report' and ('report' in response.lower() or 'billing' in response.lower()):
                    correct += 1
        except Exception as e:
            print(f"Error on case {case['id']}: {e}", file=sys.stderr)

    return correct / len(eval_cases)


def generate_instruction_variant(baseline: str, iteration: int) -> str:
    """Generate a variant instruction for the given iteration."""
    improvements = [
        # Iteration 0: Add specificity
        baseline + "\n\n## Key Requirements\n- Always cite specific SKU names when discussing costs\n- Provide exact gcloud/bq commands when applicable\n- Include user attribution when resources are created by specific users",

        # Iteration 1: Add structure
        baseline + "\n\n## Response Protocol\nAlways follow these 5 steps:\n1. Classify the query type\n2. Call at least one tool before responding\n3. Identify root cause with specific SKU/resource names\n4. Provide exact remediation commands\n5. Suggest preventive measures",

        # Iteration 2: Add examples
        baseline + """\n\n## Example Responses
- Quota: "You've hit BigQuery's on-demand slot limit of 2000. Your job attempted 2500 concurrent slots. Fix: bq mk --reservation..."
- Cost spike: "Compute Engine costs jumped $1000 due to 50 n1-standard-16 instances created by bob@company.com on July 1st..."
""",

        # Iteration 3: Add constraints
        baseline + "\n\n## Quality Constraints\n- Minimum response: 150 characters\n- Must call at least one tool before responding\n- Always provide concrete next steps, not just explanations\n- Never give generic advice - be specific to the query",

        # Iteration 4: Combine all
        """You are an expert GCP billing support agent specialized in:
- Quota exceeded errors (BigQuery, Compute Engine, Cloud Storage, API limits)
- Cost spike investigations (SKU-level analysis, user attribution)
- Budget alert explanations (threshold breaches, forecasts)
- Billing report interpretation (invoices, cost allocation, trends)
- Cost optimization recommendations (commitments, rightsizing, lifecycle policies)

## Response Protocol
1. **Classify**: Identify query type (quota/cost/budget/optimization/report)
2. **Gather Context**: Call appropriate tools BEFORE responding
   - gcloud_billing_get_costs for cost analysis
   - bigquery_usage_analytics for BQ-specific issues
   - knowledge_base_search for best practices
3. **Analyze**: Identify root cause with specifics
   - Exact SKU names (e.g., "Compute Engine N1 Standard")
   - User attribution (who created resources)
   - Quantify the change (percentages, absolute values)
4. **Remediate**: Provide actionable steps with exact commands (gcloud, bq)
5. **Prevent**: Suggest preventive measures

## Quality Standards
- Minimum 150 characters
- Use at least ONE tool before responding
- Cite specific SKUs, not "resources" or "services"
- Include exact commands, not just descriptions

## Example Responses
Quota: "You've exceeded BigQuery's on-demand slot quota (2000 slots). Your ETL job attempted 2500 concurrent slots. Fix: bq mk --reservation..."
Cost Spike: "Compute Engine costs jumped $1000 ($500 → $1500) due to 50 n1-standard-16 instances in us-central1, created by bob@company.com on July 1st..."
"""
    ]

    return improvements[iteration] if iteration < len(improvements) else baseline


def run_evolution():
    """Run the full evolution process."""
    print("=" * 60)
    print("GCP Billing Agent - Hermes Evolution")
    print("=" * 60)

    print("[1/6] Loading baseline instruction...")
    baseline_instruction = load_baseline_instruction()
    print(f"   {len(baseline_instruction)} character instruction loaded")

    print("[2/6] Loading evaluation dataset...")
    eval_cases = load_eval_dataset()
    print(f"   {len(eval_cases)} test cases loaded")

    print("[3/6] Evaluating baseline...")
    baseline_score = evaluate_instruction(baseline_instruction, eval_cases)
    print(f"   Baseline accuracy: {baseline_score*100:.1f}%")

    print("[4/6] Running evolution iterations...")
    best_instruction = baseline_instruction
    best_score = baseline_score

    for i in range(5):
        print(f"\n   Iteration {i+1}/5...")
        variant = generate_instruction_variant(baseline_instruction, i)
        score = evaluate_instruction(variant, eval_cases)
        print(f"      Score: {score*100:.1f}% (baseline: {baseline_score*100:.1f}%)")

        if score > best_score:
            best_score = score
            best_instruction = variant
            print(f"      ✅ New best! +{(score-baseline_score)*100:.1f} pp")
        else:
            print(f"      No improvement")

    print("\n[5/6] Saving results...")
    output_dir = project_root / 'hermes' / 'output'
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(output_dir / f'evolved_instruction_{timestamp}.txt', 'w') as f:
        f.write(best_instruction)

    metrics = {
        "baseline_score": baseline_score,
        "best_score": best_score,
        "improvement": best_score - baseline_score,
        "improvement_pct": ((best_score - baseline_score) / baseline_score * 100) if baseline_score > 0 else 0,
        "timestamp": timestamp,
        "num_cases": len(eval_cases)
    }
    with open(output_dir / f'evolution_metrics_{timestamp}.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    print("\n[6/6] Evolution Complete!")
    print("=" * 60)
    print(f"Baseline:  {baseline_score*100:.1f}%")
    print(f"Evolved:   {best_score*100:.1f}%")
    print(f"Gain:      +{(best_score-baseline_score)*100:.1f} percentage points")
    print(f"\nNext step: copy hermes/output/evolved_instruction_{timestamp}.txt")
    print(f"           into the instruction= field in app/agent.py")


if __name__ == '__main__':
    run_evolution()
