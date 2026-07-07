#!/usr/bin/env python3
"""Convert agents-cli traces to Hermes ATIF format.

Usage:
    python hermes/convert_traces_to_atif.py traces.json scores.json output.jsonl
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def convert_agents_cli_to_atif(traces_file: Path, scores_file: Path) -> List[Dict[str, Any]]:
    """
    Convert agents-cli traces + scores to Hermes ATIF format.

    Args:
        traces_file: agents-cli traces JSON (eval generate output)
        scores_file: agents-cli scores JSON (eval grade output)

    Returns:
        List of ATIF trajectory dicts
    """
    with open(traces_file) as f:
        traces_data = json.load(f)
    with open(scores_file) as f:
        scores_data = json.load(f)

    scores_by_id = {}
    for result in scores_data.get('eval_results', []):
        case_id = result.get('eval_case_id')
        for metric in result.get('eval_metric_results', []):
            if metric.get('metric_name') == 'final_response_quality_v1':
                scores_by_id[case_id] = metric.get('score', 0.0)
                break

    atif_trajectories = []
    for case in traces_data.get('eval_cases', []):
        case_id = case.get('eval_case_id', 'unknown')
        turns_raw = case.get('agent_data', {}).get('turns', [])

        atif_turns = []
        for turn in turns_raw:
            role = turn.get('role')
            text_content = "".join(p.get('text', '') for p in turn.get('parts', []))

            if role == 'user':
                atif_turns.append({"role": "user", "content": text_content})
            elif role == 'model':
                actions = [
                    {"tool": tc.get('name', 'unknown'), "arguments": tc.get('arguments', {})}
                    for tc in turn.get('tool_calls', [])
                ]
                atif_turns.append({"role": "assistant", "content": text_content, "actions": actions})

        score = scores_by_id.get(case_id, 0.0)
        atif_trajectories.append({
            "session_id": case_id,
            "turns": atif_turns,
            "outcome": "success" if score >= 0.7 else "failure",
            "metadata": {
                "score": score,
                "category": case.get('metadata', {}).get('category', 'unknown')
            }
        })

    return atif_trajectories


def main():
    if len(sys.argv) != 4:
        print("Usage: convert_traces_to_atif.py <traces.json> <scores.json> <output.jsonl>")
        sys.exit(1)

    traces_file, scores_file, output_file = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    trajectories = convert_agents_cli_to_atif(traces_file, scores_file)

    with open(output_file, 'w') as f:
        for t in trajectories:
            f.write(json.dumps(t) + '\n')

    print(f"✅ Wrote {len(trajectories)} ATIF trajectories to {output_file}")
    print(f"   Success: {sum(1 for t in trajectories if t['outcome'] == 'success')}")
    print(f"   Failure: {sum(1 for t in trajectories if t['outcome'] == 'failure')}")


if __name__ == '__main__':
    main()
