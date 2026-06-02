"""
Regression tests / runnable examples for the corrected Action Language with Agents engine.

Run:
    python example_tests.py

These tests intentionally cover the points from consultations:
- many `causes` statements for one action/agent,
- backward reasoning from later observations through inertia,
- `involved` based on non-empty minimal occlusion, not just occurrence in Acs,
- contradictory observations,
- contradictory fired effects,
- no contradiction when conflicting rules do not fire together,
- examples bundled in the GUI.
"""

from alag_engine import (
    Signature,
    DomainDescription,
    Scenario,
    Observation,
    ActionOccurrence,
    ActionEffect,
    Literal,
    build_model,
    query_holds,
    query_involved,
    InconsistentScenario,
    parse_literal_set,
)
from alag_app import EXAMPLES


def L(name: str) -> Literal:
    return Literal(name, True)


def N(name: str) -> Literal:
    return Literal(name, False)


def _expect_inconsistent(sig: Signature, D: DomainDescription, Sc: Scenario) -> str:
    try:
        build_model(sig, D, Sc)
    except InconsistentScenario as exc:
        return str(exc)
    raise AssertionError("Expected inconsistency")


def test_many_causes_and_involved():
    sig = Signature(fluents={"f", "g", "h"}, actions={"a"}, agents={"ag"}, T=2)
    D = DomainDescription([
        ActionEffect("a", {L("f")}, {L("g")}, "ag"),
        ActionEffect("a", {L("h")}, {L("g")}, "ag"),
    ])
    Sc = Scenario(
        observations=[Observation({L("g")}, 0)],
        occurrences=[ActionOccurrence("a", "ag", 0)],
    )
    ms = build_model(sig, D, Sc)
    assert query_holds(ms, {L("f"), L("h")}, 1)
    assert ms.representative.O[("a", 1)] == {"f", "h"}
    assert query_involved(ms, "ag")
    print("OK: many causes + minimal occlusion + involved")


def test_backward_observation():
    # No observation at t=0, no action changes stolen. Observation at t=4 constrains
    # all admissible initial states to stolen=true.
    sig = Signature(fluents={"stolen"}, actions={"wait"}, agents={"bob"}, T=4)
    D = DomainDescription([ActionEffect("wait", set(), set(), "bob")])
    Sc = Scenario(
        observations=[Observation({L("stolen")}, 4)],
        occurrences=[
            ActionOccurrence("wait", "bob", 0),
            ActionOccurrence("wait", "bob", 1),
            ActionOccurrence("wait", "bob", 2),
            ActionOccurrence("wait", "bob", 3),
        ],
    )
    ms = build_model(sig, D, Sc)
    assert query_holds(ms, {L("stolen")}, 0)
    assert query_holds(ms, {L("stolen")}, 4)
    assert not query_involved(ms, "bob")  # wait has empty effect, so the agent is not involved
    print("OK: backward observation through inertia + empty-effect wait")


def test_conflicting_observations_after_waits():
    sig = Signature(fluents={"stolen"}, actions={"wait"}, agents={"bob"}, T=4)
    D = DomainDescription([ActionEffect("wait", set(), set(), "bob")])
    Sc = Scenario(
        observations=[Observation({N("stolen")}, 0), Observation({L("stolen")}, 4)],
        occurrences=[
            ActionOccurrence("wait", "bob", 0),
            ActionOccurrence("wait", "bob", 1),
            ActionOccurrence("wait", "bob", 2),
            ActionOccurrence("wait", "bob", 3),
        ],
    )
    msg = _expect_inconsistent(sig, D, Sc)
    assert "observation" in msg.lower()
    print("OK: inconsistent observations with only wait actions")


def test_identity_wait_still_preserves_value():
    # Variant mentioned in consultations: wait has explicit identity effects.
    sig = Signature(fluents={"stolen"}, actions={"wait"}, agents={"bob"}, T=4)
    D = DomainDescription([
        ActionEffect("wait", {L("stolen")}, {L("stolen")}, "bob"),
        ActionEffect("wait", {N("stolen")}, {N("stolen")}, "bob"),
    ])
    Sc = Scenario(
        observations=[Observation({N("stolen")}, 0), Observation({L("stolen")}, 4)],
        occurrences=[ActionOccurrence("wait", "bob", t) for t in range(4)],
    )
    _expect_inconsistent(sig, D, Sc)
    print("OK: explicit identity wait cannot turn ~stolen into stolen")


def test_mutually_contradictory_observations_same_time():
    sig = Signature(fluents={"f"}, actions={"wait"}, agents={"ag"}, T=1)
    D = DomainDescription([ActionEffect("wait", set(), set(), "ag")])
    Sc = Scenario(observations=[Observation({L("f")}, 0), Observation({N("f")}, 0)])
    msg = _expect_inconsistent(sig, D, Sc)
    assert "Conflicting observations" in msg
    print("OK: mutually contradictory observations at one timepoint")


def test_conflicting_effects_when_two_conditions_true():
    sig = Signature(fluents={"f", "g", "h"}, actions={"a"}, agents={"ag"}, T=1)
    D = DomainDescription([
        ActionEffect("a", {L("f")}, {L("g")}, "ag"),
        ActionEffect("a", {N("f")}, {L("h")}, "ag"),
    ])
    Sc = Scenario(
        observations=[Observation({L("g"), L("h")}, 0)],
        occurrences=[ActionOccurrence("a", "ag", 0)],
    )
    msg = _expect_inconsistent(sig, D, Sc)
    assert "conflicting fired effects" in msg
    print("OK: conflicting effects make scenario inconsistent")


def test_no_conflict_when_conditions_do_not_cooccur():
    sig = Signature(fluents={"f", "g", "h"}, actions={"a"}, agents={"ag"}, T=1)
    D = DomainDescription([
        ActionEffect("a", {L("f")}, {L("g")}, "ag"),
        ActionEffect("a", {N("f")}, {L("h")}, "ag"),
    ])
    Sc = Scenario(
        observations=[Observation({L("g"), N("h")}, 0)],
        occurrences=[ActionOccurrence("a", "ag", 0)],
    )
    ms = build_model(sig, D, Sc)
    assert query_holds(ms, {L("f")}, 1)
    print("OK: no conflict if only one conditional effect fires")


def test_prior_action_can_create_conflict_later():
    sig = Signature(fluents={"f", "g", "h"}, actions={"prepare", "a"}, agents={"ag"}, T=2)
    D = DomainDescription([
        ActionEffect("prepare", {L("g"), L("h")}, set(), "ag"),
        ActionEffect("a", {L("f")}, {L("g")}, "ag"),
        ActionEffect("a", {N("f")}, {L("h")}, "ag"),
    ])
    Sc = Scenario(occurrences=[ActionOccurrence("prepare", "ag", 0), ActionOccurrence("a", "ag", 1)])
    _expect_inconsistent(sig, D, Sc)
    print("OK: previous action can create a later conflicting-effect state")


def test_agent_without_matching_rule_has_empty_effect():
    sig = Signature(fluents={"f"}, actions={"a"}, agents={"Alice", "Bob"}, T=1)
    D = DomainDescription([ActionEffect("a", {L("f")}, set(), "Alice")])
    Sc = Scenario(occurrences=[ActionOccurrence("a", "Bob", 0)])
    ms = build_model(sig, D, Sc)
    assert not query_holds(ms, {L("f")}, 1)  # some models have f=0
    assert not query_involved(ms, "Bob")
    print("OK: non-designated agent executes action with empty effect")


def test_all_gui_examples_are_executable_at_engine_level():
    for ex in EXAMPLES:
        sig = Signature(
            fluents=set(ex["fluents"]),
            actions=set(ex["actions"]),
            agents=set(ex["agents"]),
            T=int(ex["T"]),
        )
        D = DomainDescription([
            ActionEffect(
                st["action"],
                parse_literal_set(st["effect"]),
                parse_literal_set(st["precondition"]),
                st["agent"],
            )
            for st in ex["statements"]
        ])
        Sc = Scenario(
            observations=[Observation(parse_literal_set(obs["literals"]), int(obs["t"])) for obs in ex["observations"]],
            occurrences=[ActionOccurrence(occ["action"], occ["agent"], int(occ["t"])) for occ in ex["occurrences"]],
        )
        should_be_inconsistent = "INCONSISTENT" in ex["expected"]
        if should_be_inconsistent:
            _expect_inconsistent(sig, D, Sc)
        else:
            ms = build_model(sig, D, Sc)
            assert len(ms) >= 1, ex["name"]
            # Default query fields are syntactically valid.
            query_holds(ms, parse_literal_set(ex["query_lits"]), int(ex["query_t"]))
            query_involved(ms, ex["query_agent"])
    print(f"OK: all {len(EXAMPLES)} GUI examples match consistency expectations")


if __name__ == "__main__":
    test_many_causes_and_involved()
    test_backward_observation()
    test_conflicting_observations_after_waits()
    test_identity_wait_still_preserves_value()
    test_mutually_contradictory_observations_same_time()
    test_conflicting_effects_when_two_conditions_true()
    test_no_conflict_when_conditions_do_not_cooccur()
    test_prior_action_can_create_conflict_later()
    test_agent_without_matching_rule_has_empty_effect()
    test_all_gui_examples_are_executable_at_engine_level()
