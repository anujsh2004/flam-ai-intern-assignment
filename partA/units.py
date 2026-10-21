"""Text units used as fertility denominators, plus a clustered bootstrap.

Grapheme clusters use the third-party `regex` module's \\X (UAX #29 extended
grapheme clusters). Which Unicode version it implements matters for Indic
conjuncts -- see decision D-05 and tests/test_units.py.
"""
import random

import regex


def count_words(text: str) -> int:
    """Whitespace-delimited words; runs of whitespace never create empty words."""
    return len(text.split())


def count_codepoints(text: str) -> int:
    return len(text)


def count_bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def count_graphemes(text: str) -> int:
    return len(regex.findall(r"\X", text))


def cluster_bootstrap_ratio(num, den, clusters, n_boot=2000, seed=0, alpha=0.05):
    """Ratio of totals sum(num)/sum(den) with a percentile CI.

    Resamples whole clusters (e.g. FLORES articles) with replacement, because
    sentences from the same article are not independent.
    Returns (point, lo, hi).
    """
    groups = {}
    for n, d, c in zip(num, den, clusters):
        g = groups.setdefault(c, [0.0, 0.0])
        g[0] += n
        g[1] += d
    sums = list(groups.values())
    point = sum(g[0] for g in sums) / sum(g[1] for g in sums)

    rng = random.Random(seed)
    stats = []
    for _ in range(n_boot):
        sample = [sums[rng.randrange(len(sums))] for _ in sums]
        stats.append(sum(g[0] for g in sample) / sum(g[1] for g in sample))
    stats.sort()
    lo = stats[int(alpha / 2 * n_boot)]
    hi = stats[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return point, lo, hi
