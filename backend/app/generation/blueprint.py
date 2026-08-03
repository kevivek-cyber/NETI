"""Paper blueprints.

A blueprint is the shape of a paper: how many questions come from where.
Config, not code, so a pattern change never touches the generator.

Owner: ML (role 2) tunes the weightage and difficulty targets.
See docs/AI_PIPELINE.md section 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..ledger.canonical import Domain, hash_object


@dataclass(frozen=True)
class Section:
    subject: str
    count: int
    marks_correct: int = 4
    marks_incorrect: int = -1


@dataclass(frozen=True)
class Blueprint:
    name: str
    duration_minutes: int
    sections: tuple[Section, ...] = field(default_factory=tuple)

    @property
    def total_questions(self) -> int:
        return sum(s.count for s in self.sections)

    @property
    def total_marks(self) -> int:
        return sum(s.count * s.marks_correct for s in self.sections)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "sections": [
                {
                    "subject": s.subject,
                    "count": s.count,
                    "marks_correct": s.marks_correct,
                    "marks_incorrect": s.marks_incorrect,
                }
                for s in self.sections
            ],
        }

    def hash(self) -> bytes:
        """Committed in the genesis block so the shape cannot change later."""
        return hash_object(Domain.BLOCK, self.as_dict())


# Real thing. Needs a bank of a few thousand items before it can be used.
# Verify against the current NTA bulletin each cycle; this pattern has
# changed twice in recent years.
NEET_UG = Blueprint(
    name="NEET-UG",
    duration_minutes=180,
    sections=(
        Section("physics", 45),
        Section("chemistry", 45),
        Section("botany", 45),
        Section("zoology", 45),
    ),
)

# What the walking skeleton actually runs on, sized to the sample bank.
DEMO = Blueprint(
    name="DEMO",
    duration_minutes=20,
    sections=(
        Section("physics", 3),
        Section("chemistry", 2),
        Section("botany", 2),
        Section("zoology", 1),
    ),
)

BLUEPRINTS = {b.name: b for b in (NEET_UG, DEMO)}
