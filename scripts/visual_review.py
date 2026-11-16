"""Bind a recorded visual review to tracked inputs, independently of checkpoints."""
import json
from pathlib import Path

def review_state(root, fingerprints):
    path = Path(root) / 'validation' / 'visual-review.json'
    if not path.is_file():
        return 'pending', [], 'No visual-review record; explicit review required'
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
        previous = record['fingerprints']
        if record.get('reviewed') is not True or not isinstance(previous, dict):
            raise ValueError('invalid visual-review record')
    except (OSError, ValueError, KeyError, TypeError):
        return 'pending', [], 'Invalid visual-review record; explicit review required'
    changed = sorted(k for k in set(previous) | set(fingerprints) if previous.get(k) != fingerprints.get(k))
    if changed:
        return 'pending', changed, 'Inputs differ from the visually reviewed version; review is stale'
    return 'passed', [], None
