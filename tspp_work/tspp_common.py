"""Shared helpers for Track 2 («Технології створення програмних продуктів») report generators."""
import re
import sys

COURSE = "Технології створення програмних продуктів"
CITE = re.compile(r"\[(@\w+(?:;\s*@\w+)*)\]")


def number_citations(blocks, ref_keys):
    """Replace [@key; @key] in every string of `blocks` with [n; m] numbered by order of first mention
    (ПР3 rule, applied to all practicals). Aborts on unknown keys or uncited sources. Returns keys in order."""
    order = []

    def rep(m):
        ks = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        for k in ks:
            if k not in ref_keys:
                sys.exit(f"Unknown reference key {k}")
            if k not in order:
                order.append(k)
        return "[" + "; ".join(str(n) for n in sorted(order.index(k) + 1 for k in ks)) + "]"

    def walk(v):
        if isinstance(v, str):
            return CITE.sub(rep, v)
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        return v

    blocks[:] = walk(blocks)
    missing = [k for k in ref_keys if k not in order]
    if missing:
        sys.exit(f"Sources never cited: {missing}")
    return order


def block_helpers(B, rel):
    """Short constructors for report.yaml blocks (h1 always starts a new page)."""
    return dict(
        h1=lambda t: B.append({"h1": t, "new_page": True}),
        h2=lambda t: B.append({"h2": t}),
        h3=lambda t: B.append({"h3": t}),
        p=lambda t: B.append({"p": t}),
        bl=lambda items: B.append({"bullets": items}),
        nl=lambda items: B.append({"numbered": items}),
        tab=lambda **kw: B.append({"table": {"font": 12, **kw}}),
        fig=lambda src, cap, fid, **kw: B.append({"figure": {"id": fid, "src": f"{rel}/{src}", "caption": cap, **kw}}),
    )
