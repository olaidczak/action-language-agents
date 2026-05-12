"""
Action Language with Agents Engine module
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Syntax
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Literal:
    """A literal: a fluent name plus a sign. positive=True -> f; positive=False -> ~f."""
    fluent: str
    positive: bool = True

    def negate(self) -> "Literal":
        return Literal(self.fluent, not self.positive)

    def __str__(self) -> str:
        return self.fluent if self.positive else f"~{self.fluent}"


def parse_literal(text: str) -> Literal:
    """Parse one literal: 'f' or '~f'."""
    text = text.strip()
    if not text:
        raise ValueError("Empty literal")
    if text.startswith("~"):
        return Literal(text[1:].strip(), positive=False)
    return Literal(text, positive=True)


def parse_literal_set(text: str) -> set[Literal]:
    """Parse a comma-separated set of literals from text.

    Empty input -> empty set.
    Raises ValueError if both f and ~f appear (consistency).
    """
    text = text.strip()
    if not text:
        return set()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    lits = {parse_literal(p) for p in parts}
    seen: dict[str, bool] = {}
    for l in lits:
        if l.fluent in seen and seen[l.fluent] != l.positive:
            raise ValueError(
                f"Inconsistent literal set: {l.fluent} appears both positively and negatively"
            )
        seen[l.fluent] = l.positive
    return lits


def fluents_of(lits: set[Literal]) -> set[str]:
    """Return fl(L) — the set of fluent symbols occurring in L."""
    return {l.fluent for l in lits}


@dataclass
class ActionEffect:
    """An action effect statement:  A causes E if P by ag."""
    action: str
    effect: set[Literal]
    precondition: set[Literal]
    agent: str

    def __str__(self) -> str:
        e = "{" + ", ".join(str(l) for l in self.effect) + "}" if self.effect else "{}"
        p = "{" + ", ".join(str(l) for l in self.precondition) + "}" if self.precondition else "{}"
        return f"{self.action} causes {e} if {p} by {self.agent}"


@dataclass
class Signature:
    """A signature (F, Ac, Ag, T)."""
    fluents: set[str] = field(default_factory=set)
    actions: set[str] = field(default_factory=set)
    agents: set[str] = field(default_factory=set)
    T: int = 9

    def timepoints(self) -> range:
        return range(0, self.T + 1)


@dataclass
class DomainDescription:
    """Finite collection of action effect statements; at most one per action."""
    statements: dict[str, ActionEffect] = field(default_factory=dict)

    def add(self, stmt: ActionEffect) -> None:
        if stmt.action in self.statements:
            raise ValueError(
                f"Domain description already has a statement for action {stmt.action} (determinism)."
            )
        self.statements[stmt.action] = stmt

    def remove(self, action: str) -> None:
        self.statements.pop(action, None)

    def get(self, action: str) -> Optional[ActionEffect]:
        return self.statements.get(action)


@dataclass
class Observation:
    """(L, t) — set of literals known to hold at timepoint t."""
    literals: set[Literal]
    t: int


@dataclass
class ActionOccurrence:
    """(A, ag, t) — action A performed by agent ag at timepoint t."""
    action: str
    agent: str
    t: int


@dataclass
class Scenario:
    """Sc = (Obs, Acs)."""
    observations: list[Observation] = field(default_factory=list)
    occurrences: list[ActionOccurrence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Semantics
# ---------------------------------------------------------------------------

@dataclass
class Model:
    """A model S = (H, O, E) of (Sc, D)."""
    H: dict[tuple[str, int], int]
    O: dict[tuple[str, int], set[str]]
    E: list[ActionOccurrence]
    sig: Signature

    def holds(self, lits: set[Literal], t: int) -> bool:
        """Check whether every literal in `lits` is true at timepoint t."""
        for l in lits:
            v = self.H.get((l.fluent, t), 0)
            if l.positive and v != 1:
                return False
            if (not l.positive) and v != 0:
                return False
        return True


class InconsistentScenario(Exception):
    """Raised when there is no model of Sc w.r.t. D."""


def build_model(sig: Signature, D: DomainDescription, Sc: Scenario) -> Model:
    """Construct the unique model of (Sc, D), or raise InconsistentScenario."""
    # 1. initial state from observations at t = 0
    H: dict[tuple[str, int], int] = {}
    init_lits: dict[str, int] = {}
    for o in Sc.observations:
        if o.t != 0:
            continue
        for l in o.literals:
            v = 1 if l.positive else 0
            if l.fluent in init_lits and init_lits[l.fluent] != v:
                raise InconsistentScenario(
                    f"Conflicting observations at t=0 for fluent {l.fluent}."
                )
            init_lits[l.fluent] = v
    for f in sig.fluents:
        H[(f, 0)] = init_lits.get(f, 0)

    # occlusion default empty
    O: dict[tuple[str, int], set[str]] = {
        (a, t): set() for a in sig.actions for t in sig.timepoints()
    }

    # index occurrences by timepoint (sequentiality)
    acs_by_t: dict[int, ActionOccurrence] = {}
    for occ in Sc.occurrences:
        if occ.t in acs_by_t:
            raise InconsistentScenario(
                f"Two action occurrences at t={occ.t} — actions must be sequential."
            )
        acs_by_t[occ.t] = occ

    # 2. propagate
    for t in range(0, sig.T):
        occ = acs_by_t.get(t)
        fired = False
        if occ is not None:
            stmt = D.get(occ.action)
            if stmt is not None and stmt.agent == occ.agent:
                pre_ok = True
                for l in stmt.precondition:
                    v = H[(l.fluent, t)]
                    if l.positive and v != 1:
                        pre_ok = False
                        break
                    if (not l.positive) and v != 0:
                        pre_ok = False
                        break
                if pre_ok:
                    # copy then override with effect
                    for f in sig.fluents:
                        H[(f, t + 1)] = H[(f, t)]
                    for l in stmt.effect:
                        H[(l.fluent, t + 1)] = 1 if l.positive else 0
                    O[(occ.action, t + 1)] = fluents_of(stmt.effect)
                    fired = True
        if not fired:
            for f in sig.fluents:
                H[(f, t + 1)] = H[(f, t)]

    model = Model(H=H, O=O, E=list(Sc.occurrences), sig=sig)

    # 3. verify all observations
    for o in Sc.observations:
        if not model.holds(o.literals, o.t):
            obs_str = "{" + ", ".join(str(l) for l in o.literals) + "}"
            raise InconsistentScenario(
                f"Observation {obs_str} at t={o.t} contradicts the computed trajectory."
            )

    return model


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def query_holds(model: Model, lits: set[Literal], t: int) -> bool:
    """Q1:  Sc, D |= holds a at t."""
    return model.holds(lits, t)


def query_involved(model: Model, agent: str) -> bool:
    """Q2:  Sc, D |= involved ag in Sc."""
    for occ in model.E:
        if occ.agent == agent and model.O.get((occ.action, occ.t + 1)):
            return True
    return False
