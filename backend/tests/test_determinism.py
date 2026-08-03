"""Determinism tests.

The single most important property in the project. If generation is not
reproducible, no exam can ever be audited and NETI's central claim is
false. See CLAUDE.md invariants.

TODO(role 5): run these on two OS images in CI, and add a golden-hash
test that pins a known seed to a known paper hash across releases.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from app.exam import seeds
from app.generation import generator
from app.generation.blueprint import DEMO
from app.generation.rng import DeterministicRNG

SEED = bytes(range(32))


@pytest.fixture(scope="module")
def bank():
    return generator.load_bank()


def test_rng_stream_is_stable():
    a = DeterministicRNG(SEED)
    b = DeterministicRNG(SEED)
    assert [a.below(1000) for _ in range(50)] == [b.below(1000) for _ in range(50)]


def test_different_seeds_diverge():
    a = DeterministicRNG(SEED)
    b = DeterministicRNG(bytes(range(1, 33)))
    assert [a.below(1000) for _ in range(20)] != [b.below(1000) for _ in range(20)]


def test_same_seed_same_paper(bank):
    first = generator.generate(SEED, bank, DEMO)
    second = generator.generate(SEED, bank, DEMO)
    assert generator.paper_hash(first) == generator.paper_hash(second)


def test_different_candidates_get_different_papers(bank):
    master, pepper = seeds.new_master_seed(), seeds.new_session_pepper()
    hashes = set()
    for roll in range(30):
        pid = seeds.pseudonym(pepper, f"CAND-{roll:04d}")
        seed = seeds.derive_seed(master, "S1", pid)
        hashes.add(generator.paper_hash(generator.generate(seed, bank, DEMO)))
    # A 12-item sample bank collides often; a real bank must not.
    assert len(hashes) > 1


def test_paper_matches_the_blueprint(bank):
    paper = generator.generate(SEED, bank, DEMO)
    assert len(paper["questions"]) == DEMO.total_questions
    for question in paper["questions"]:
        assert len(question["options"]) >= 2
        assert 0 <= question["answer_index"] < len(question["options"])


def test_sealed_paper_hides_the_key(bank):
    paper = generator.generate(SEED, bank, DEMO)
    assert all("answer_index" not in q for q in generator.sealed(paper)["questions"])


def test_deterministic_across_processes(bank):
    """Same seed, fresh interpreter, same hash.

    Catches determinism bugs that a single process hides: hash
    randomisation, dict iteration order, module-level caching.
    """
    expected = generator.paper_hash(generator.generate(SEED, bank, DEMO)).hex()
    script = (
        "from app.generation import generator;"
        "from app.generation.blueprint import DEMO;"
        "print(generator.paper_hash("
        "generator.generate(bytes(range(32)), generator.load_bank(), DEMO)).hex())"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == expected
