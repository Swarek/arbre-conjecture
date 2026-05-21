"""Scratch space for dynamic-programming experiments on PC-trees.

No DP solver is implemented yet.  This module exists so future checkpoints can
add experiments without overloading ``candidate.py``.
"""

from __future__ import annotations


def not_implemented_status():
    return {
        "implemented": False,
        "reason": "DP state and sufficiency proof obligations are still open",
    }
