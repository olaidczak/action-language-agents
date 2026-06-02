"""
Action Language with Agents - reasoning engine.

This version supports:
* many `causes` statements for the same action/agent,
* observations at arbitrary timepoints (future observations constrain the
  admissible initial states, so backward reasoning works),
* deterministic sequential actions,
* inertia: only fluents in the minimal occlusion set may change,
* inconsistency caused by contradictory observations or conflicting effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
import re
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Syntax
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class Literal:
    """A literal: a fluent name plus a sign. positive=True -> f; positive=False -> ~f."""

    fluent: str
    positive: bool = True

    def negate(self) -> "Literal":
        return Literal(self.fluent, not self.positive)

    def __str__(self) -> str:
        return self.fluent if self.positive else f"~{self.fluent}"


def parse_literal(text: str) -> Literal:
    """Parse one literal.

    Accepted negation forms: ~f, -f, !f, not f, ¬f.
    """

    text = text.strip()
    if not text:
        raise ValueError("Empty literal")

    lower = text.lower()
    for prefix in ("not ", "not\t"):
        if lower.startswith(prefix):
            fluent = text[len(prefix) :].strip()
            if not fluent:
                raise ValueError("Negation without a fluent name")
            return Literal(fluent, positive=False)

    if text[0] in {"~", "-", "!", "¬"}:
        fluent = text[1:].strip()
        if not fluent:
            raise ValueError("Negation without a fluent name")
        return Literal(fluent, positive=False)

    return Literal(text, positive=True)


def _split_literal_text(text: str) -> list[str]:
    """Split a literal list written as `f, ~g`, `{f;~g}`, or `f ~g`."""

    text = text.strip()
    if not text:
        return []
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    if not text or text in {"∅", "{}"}:
        return []

    if any(sep in text for sep in [",", ";"]):
        return [p.strip() for p in re.split(r"[,;]", text) if p.strip()]

    # Space-separated input is convenient in the GUI, but `not f` must remain one literal.
    tokens = text.split()
    parts: list[str] = []
    i = 0
    while i < len(tokens):
        if tokens[i].lower() == "not":
            if i + 1 >= len(tokens):
                raise ValueError("`not` must be followed by a fluent name")
            parts.append(f"not {tokens[i + 1]}")
            i += 2
        else:
            parts.append(tokens[i])
            i += 1
    return parts


def parse_literal_set(text: str) -> set[Literal]:
    """Parse a set of literals.

    Empty input, `{}`, or `∅` -> empty set. Raises ValueError if both f and ~f occur.
    """

    parts = _split_literal_text(text)
    lits = {parse_literal(p) for p in parts}
    _check_literal_set_consistent(lits, where="literal set")
    return lits


def _check_literal_set_consistent(lits: Iterable[Literal], where: str = "literal set") -> None:
    seen: dict[str, bool] = {}
    for lit in lits:
        old = seen.get(lit.fluent)
        if old is not None and old != lit.positive:
            raise ValueError(
                f"Inconsistent {where}: fluent {lit.fluent!r} occurs both positively and negatively."
            )
        seen[lit.fluent] = lit.positive


def fluents_of(lits: set[Literal]) -> set[str]:
    """Return fl(L) — the set of fluent symbols occurring in L."""

    return {lit.fluent for lit in lits}


def literal_set_to_str(lits: Iterable[Literal]) -> str:
    items = sorted(str(lit) for lit in lits)
    return "{" + ", ".join(items) + "}" if items else "{}"


@dataclass
class ActionEffect:
    """An action effect statement: A by ag causes E if P."""

    action: str
    effect: set[Literal]
    precondition: set[Literal] = field(default_factory=set)
    agent: Optional[str] = None

    def __post_init__(self) -> None:
        _check_literal_set_consistent(self.effect, where=f"effect of {self.action}")
        _check_literal_set_consistent(self.precondition, where=f"precondition of {self.action}")

    def __str__(self) -> str:
        ag = self.agent if self.agent is not None else "<unspecified>"
        return (
            f"{self.action} by {ag} causes {literal_set_to_str(self.effect)} "
            f"if {literal_set_to_str(self.precondition)}"
        )


@dataclass
class Signature:
    """A signature (F, Ac, Ag, T)."""

    fluents: set[str] = field(default_factory=set)
    actions: set[str] = field(default_factory=set)
    agents: set[str] = field(default_factory=set)
    T: int = 9

    def __post_init__(self) -> None:
        if self.T < 1:
            raise ValueError("T must be at least 1.")

    def timepoints(self) -> range:
        return range(0, self.T + 1)

    def action_start_timepoints(self) -> range:
        # An action executed at t lasts one unit and terminates at t+1, so t must be < T.
        return range(0, self.T)


@dataclass
class DomainDescription:
    """Finite collection of action effect statements.

    Multiple statements for the same action are allowed. This is needed for examples such as:
        a by ag causes f if g
        a by ag causes ~f if h
    If both rules fire in one state, the scenario is inconsistent because H cannot assign
    two values to the same fluent at the next timepoint.
    """

    statements: list[ActionEffect] = field(default_factory=list)

    def add(self, stmt: ActionEffect) -> None:
        self.statements.append(stmt)

    def remove_at(self, index: int) -> None:
        del self.statements[index]

    def remove(self, action: str) -> None:
        self.statements = [stmt for stmt in self.statements if stmt.action != action]

    def matching(self, action: str, agent: str) -> list[ActionEffect]:
        return [
            stmt
            for stmt in self.statements
            if stmt.action == action and stmt.agent == agent
        ]

    def get(self, action: str) -> list[ActionEffect]:
        """Compatibility helper: return all statements with a given action."""
        return [stmt for stmt in self.statements if stmt.action == action]


@dataclass
class Observation:
    """(L, t) — set of literals known to hold at timepoint t."""

    literals: set[Literal]
    t: int


@dataclass(frozen=True)
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
    """One model S = (H, O, E) of (Sc, D)."""

    H: dict[tuple[str, int], int]
    O: dict[tuple[str, int], set[str]]
    E: list[ActionOccurrence]
    sig: Signature

    def holds(self, lits: set[Literal], t: int) -> bool:
        _validate_time(self.sig, t, allow_action_start=False)
        for lit in lits:
            v = self.H[(lit.fluent, t)]
            if lit.positive and v != 1:
                return False
            if not lit.positive and v != 0:
                return False
        return True

    def state_at(self, t: int) -> dict[str, int]:
        return {f: self.H[(f, t)] for f in self.sig.fluents}


@dataclass
class ModelSet:
    """All admissible models for a scenario and a domain description."""

    models: list[Model]
    sig: Signature

    def __len__(self) -> int:
        return len(self.models)

    @property
    def H(self) -> dict[tuple[str, int], int]:
        """Representative history, kept for old GUI code that expected one model."""
        return self.representative.H

    @property
    def O(self) -> dict[tuple[str, int], set[str]]:
        """Representative occlusion, kept for old GUI code that expected one model."""
        return self.representative.O

    @property
    def E(self) -> list[ActionOccurrence]:
        return self.representative.E

    @property
    def representative(self) -> Model:
        if not self.models:
            raise InconsistentScenario("No model exists.")
        return self.models[0]

    def possible_values(self, fluent: str, t: int) -> set[int]:
        return {model.H[(fluent, t)] for model in self.models}

    def common_value(self, fluent: str, t: int) -> Optional[int]:
        values = self.possible_values(fluent, t)
        return next(iter(values)) if len(values) == 1 else None

    def holds_count(self, lits: set[Literal], t: int) -> int:
        return sum(1 for model in self.models if model.holds(lits, t))

    def involved_count(self, agent: str) -> int:
        return sum(1 for model in self.models if _agent_involved_in_model(model, agent))


class InconsistentScenario(Exception):
    """Raised when there is no model of Sc w.r.t. D."""


class _TransitionConflict(Exception):
    """Internal exception: an initial state produces a conflicting transition."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_time(sig: Signature, t: int, *, allow_action_start: bool) -> None:
    if allow_action_start:
        if not (0 <= t < sig.T):
            raise ValueError(f"Action time t must be in [0, {sig.T - 1}] because actions terminate at t+1.")
    else:
        if not (0 <= t <= sig.T):
            raise ValueError(f"Timepoint t must be in [0, {sig.T}].")


def _validate_literal_symbols(sig: Signature, lits: Iterable[Literal], where: str) -> None:
    for lit in lits:
        if lit.fluent not in sig.fluents:
            raise ValueError(f"Unknown fluent {lit.fluent!r} in {where}.")


def _validate_inputs(sig: Signature, D: DomainDescription, Sc: Scenario) -> None:
    if not sig.fluents:
        raise ValueError("Signature must contain at least one fluent.")
    if not sig.actions:
        raise ValueError("Signature must contain at least one action.")
    if not sig.agents:
        raise ValueError("Signature must contain at least one agent.")

    for stmt in D.statements:
        if stmt.action not in sig.actions:
            raise ValueError(f"Unknown action {stmt.action!r} in domain description.")
        if stmt.agent is None:
            raise ValueError(
                f"Statement for action {stmt.action!r} has no designated agent. "
                "In this implementation, omit the statement to model empty effect for all agents."
            )
        if stmt.agent not in sig.agents:
            raise ValueError(f"Unknown agent {stmt.agent!r} in domain description.")
        _validate_literal_symbols(sig, stmt.effect, f"effect of {stmt.action}")
        _validate_literal_symbols(sig, stmt.precondition, f"precondition of {stmt.action}")

    seen_occ_times: dict[int, ActionOccurrence] = {}
    for occ in Sc.occurrences:
        if occ.action not in sig.actions:
            raise ValueError(f"Unknown action {occ.action!r} in scenario.")
        if occ.agent not in sig.agents:
            raise ValueError(f"Unknown agent {occ.agent!r} in scenario.")
        _validate_time(sig, occ.t, allow_action_start=True)
        if occ.t in seen_occ_times:
            old = seen_occ_times[occ.t]
            raise InconsistentScenario(
                "Two action occurrences at the same timepoint are not allowed "
                f"(sequential actions only): ({old.action}, {old.agent}, {old.t}) and "
                f"({occ.action}, {occ.agent}, {occ.t})."
            )
        seen_occ_times[occ.t] = occ

    for obs in Sc.observations:
        _validate_time(sig, obs.t, allow_action_start=False)
        _validate_literal_symbols(sig, obs.literals, f"observation at t={obs.t}")


def _observation_requirements(sig: Signature, Sc: Scenario) -> dict[int, dict[str, int]]:
    """Merge observations into a map t -> fluent -> required value."""

    req: dict[int, dict[str, int]] = {t: {} for t in sig.timepoints()}
    for obs in Sc.observations:
        for lit in obs.literals:
            value = 1 if lit.positive else 0
            old = req[obs.t].get(lit.fluent)
            if old is not None and old != value:
                raise InconsistentScenario(
                    f"Conflicting observations at t={obs.t} for fluent {lit.fluent!r}."
                )
            req[obs.t][lit.fluent] = value
    return req


def _state_satisfies_requirements(state: dict[str, int], req: dict[str, int]) -> bool:
    return all(state.get(f) == v for f, v in req.items())


def _format_requirement_conflict(state: dict[str, int], req: dict[str, int], t: int) -> str:
    """Human-readable explanation for an observation/state mismatch."""

    mismatches: list[str] = []
    for fluent in sorted(req):
        expected = req[fluent]
        actual = state.get(fluent)
        if actual != expected:
            sign = fluent if expected == 1 else f"~{fluent}"
            actual_lit = fluent if actual == 1 else f"~{fluent}"
            mismatches.append(f"expected {sign}, got {actual_lit}")
    joined = "; ".join(mismatches) if mismatches else "state does not satisfy observation"
    return f"At t={t}, projected state conflicts with observation: {joined}."


def _holds_in_state(state: dict[str, int], lits: set[Literal]) -> bool:
    for lit in lits:
        v = state[lit.fluent]
        if lit.positive and v != 1:
            return False
        if not lit.positive and v != 0:
            return False
    return True


def _effect_to_map(effect: set[Literal], *, context: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for lit in effect:
        value = 1 if lit.positive else 0
        old = result.get(lit.fluent)
        if old is not None and old != value:
            raise _TransitionConflict(
                f"Conflicting effects in {context}: both {lit.fluent} and ~{lit.fluent} are required."
            )
        result[lit.fluent] = value
    return result


def _step(
    sig: Signature,
    D: DomainDescription,
    occ: Optional[ActionOccurrence],
    t: int,
    state: dict[str, int],
) -> tuple[dict[str, int], dict[tuple[str, int], set[str]]]:
    """Compute one deterministic transition from t to t+1."""

    local_O = {(a, t + 1): set() for a in sig.actions}

    if occ is None:
        return dict(state), local_O

    fired: list[ActionEffect] = [
        stmt for stmt in D.matching(occ.action, occ.agent) if _holds_in_state(state, stmt.precondition)
    ]

    combined_effect: dict[str, int] = {}
    fired_names: list[str] = []
    for stmt in fired:
        fired_names.append(str(stmt))
        effect_map = _effect_to_map(stmt.effect, context=str(stmt))
        for fluent, value in effect_map.items():
            old = combined_effect.get(fluent)
            if old is not None and old != value:
                rules = " ; ".join(fired_names)
                raise _TransitionConflict(
                    f"At transition t={t}->{t+1}, action {occ.action!r} by {occ.agent!r} "
                    f"has conflicting fired effects for fluent {fluent!r}. Fired rules: {rules}"
                )
            combined_effect[fluent] = value

    next_state = dict(state)

    # Minimal occlusion: exactly the fluents that occur in fired effects.
    occluded = set(combined_effect.keys())
    local_O[(occ.action, t + 1)] = occluded

    # Inertia outside occlusion is already represented by copying the state.
    for fluent, value in combined_effect.items():
        next_state[fluent] = value

    return next_state, local_O


def _initial_states(sig: Signature, req_t0: dict[str, int]) -> Iterable[dict[str, int]]:
    fluents = sorted(sig.fluents)
    free = [f for f in fluents if f not in req_t0]
    for bits in product([0, 1], repeat=len(free)):
        state = dict(req_t0)
        state.update(dict(zip(free, bits)))
        yield state


# ---------------------------------------------------------------------------
# Model construction and queries
# ---------------------------------------------------------------------------


def build_models(sig: Signature, D: DomainDescription, Sc: Scenario) -> ModelSet:
    """Construct all models of (Sc, D), or raise InconsistentScenario.

    The algorithm enumerates admissible initial states and projects each of them forward.
    Later observations filter the admissible initial states, which gives the intended
    backward reasoning behaviour. For example, if f is observed at t=4 and no action can
    change f before t=4, then only initial states with f=true remain.
    """

    _validate_inputs(sig, D, Sc)
    obs_req = _observation_requirements(sig, Sc)
    acs_by_t = {occ.t: occ for occ in Sc.occurrences}

    models: list[Model] = []
    rejected_reasons: list[str] = []

    for initial in _initial_states(sig, obs_req[0]):
        H: dict[tuple[str, int], int] = {}
        O: dict[tuple[str, int], set[str]] = {
            (a, t): set() for a in sig.actions for t in sig.timepoints()
        }

        state = dict(initial)
        for fluent, value in state.items():
            H[(fluent, 0)] = value

        ok = True
        for t in range(0, sig.T):
            occ = acs_by_t.get(t)
            try:
                state, local_O = _step(sig, D, occ, t, state)
            except _TransitionConflict as exc:
                rejected_reasons.append(str(exc))
                ok = False
                break

            O.update(local_O)
            for fluent, value in state.items():
                H[(fluent, t + 1)] = value

            if not _state_satisfies_requirements(state, obs_req[t + 1]):
                rejected_reasons.append(_format_requirement_conflict(state, obs_req[t + 1], t + 1))
                ok = False
                break

        if ok:
            models.append(Model(H=H, O=O, E=sorted(Sc.occurrences, key=lambda x: x.t), sig=sig))

    if not models:
        message = "No model exists: observations, action effects, and inertia cannot be satisfied together."
        if rejected_reasons:
            # Keep the message concise but useful.
            unique = []
            for reason in rejected_reasons:
                if reason not in unique:
                    unique.append(reason)
            message += "\nDetected transition conflict(s):\n- " + "\n- ".join(unique[:5])
        raise InconsistentScenario(message)

    return ModelSet(models=models, sig=sig)


def build_model(sig: Signature, D: DomainDescription, Sc: Scenario) -> ModelSet:
    """Backward-compatible name used by the GUI. Returns all models, not just one."""

    return build_models(sig, D, Sc)


def query_holds(model_set: ModelSet, lits: set[Literal], t: int) -> bool:
    """Q1: Sc, D |= holds alpha at t; true iff alpha holds in every model."""

    _validate_time(model_set.sig, t, allow_action_start=False)
    _validate_literal_symbols(model_set.sig, lits, "query")
    return model_set.holds_count(lits, t) == len(model_set.models)


def _agent_involved_in_model(model: Model, agent: str) -> bool:
    for occ in model.E:
        # The effect of action at t is recorded at t+1.
        if occ.agent == agent and model.O.get((occ.action, occ.t + 1), set()):
            return True
    return False


def query_involved(model_set: ModelSet, agent: str) -> bool:
    """Q2: Sc, D |= involved ag in Sc; true iff ag is involved in every model."""

    if agent not in model_set.sig.agents:
        raise ValueError(f"Unknown agent {agent!r}.")
    return model_set.involved_count(agent) == len(model_set.models)
