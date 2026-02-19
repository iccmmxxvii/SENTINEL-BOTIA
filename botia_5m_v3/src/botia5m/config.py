from __future__ import annotations

import os
from pathlib import Path


def _parse_yaml_like(path: Path) -> dict:
    if not path.exists():
        return {}
    root: dict = {}
    stack = [(0, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if ":" not in line:
            continue
        k, v = [p.strip() for p in line.split(":", 1)]
        if not v:
            node = {}
            parent[k] = node
            stack.append((indent + 2, node))
            continue
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        elif v.lower() in {"true", "false"}:
            v = v.lower() == "true"
        else:
            try:
                v = int(v) if "." not in v else float(v)
            except ValueError:
                pass
        parent[k] = v
    return root


def deep_get(cfg: dict, path: str, default=None):
    node = cfg
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def load_config(base_dir: Path) -> dict:
    cfg = _parse_yaml_like(base_dir / "config.yml")
    runtime = cfg.setdefault("runtime", {})
    runtime["loop_seconds"] = int(os.getenv("BOTIA_LOOP_SECONDS", runtime.get("loop_seconds", 5)))
    return cfg
