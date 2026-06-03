# Action Language with Agents

## Running the GUI

```bash
python alag_app.py
```

The program consists of three source files:

- `alag_engine.py` — reasoning engine, model construction, and Q1/Q2 query evaluation,
- `alag_app.py` — Tkinter GUI with forms and built-in examples,
- `example_tests.py` — regression tests and runnable examples for checking the engine.

## Built-in examples

After starting the program, the first tab is **0. Examples**. Select an example and use:

- **Load example** — fills `F`, `Ac`, `Ag`, `T`, `causes` rules, observations, action occurrences, and the default query.
- **Load example + build** — loads the example and immediately builds the model set. For consistent scenarios, it also prints the default answers for Q1 and Q2.

Double-clicking an example name also loads it and immediately builds the model set. The same quick example selector is available on the **1. Signature** tab.

The examples cover:

1. `a by Agent causes f` — a simple effect, Q1, and Q2 `involved`.
2. Multiple `causes` rules for one action and one agent.
3. Later observation restricting earlier states through inertia (`wait`).
4. Contradictory observations after only `wait` actions.
5. Conflicting effects `f` and `~f` when conditions `g` and `h` hold together.
6. No contradiction when only one conditional rule fires.
7. Agent without a matching rule for an action — empty effect and `involved = NO`.
8. Explicit identity rules for `wait`: `wait by bob causes stolen if stolen` and `wait by bob causes ~stolen if ~stolen`.
9. Contradictory observations at the same timepoint.
10. A preparation action creates `g=true` and `h=true`, which later causes conflicting effects.
11. The same conflicting rules without firing the conflict; the output shows minimal `O`.
12. Several preconditions in one rule, for example `unlock by ag causes opened if has_key, near_door, ~blocked`.
13. Several preconditions where one missing condition blocks the effect.

Practical note: the `if P` part accepts a whole set of literals. Write conditions separated by commas or spaces, for example `g, h, ~p` or `{g; h; ~p}`. All literals in `P` must hold at the action time for the rule to fire. Multiple observations at one timepoint are allowed if they are consistent, but two actions cannot start at the same timepoint because DS8 assumes sequential actions.

## Running tests

```bash
python example_tests.py
```

The tests check multiple `causes` statements, several preconditions in one rule, `involved`, backward restriction through inertia, contradictory observations, conflicting fired effects, an agent with empty effect, and all examples bundled in the GUI.

## Main implementation points

- Multiple statements `A by ag causes E if P` are allowed for the same action and agent; one statement may also contain many preconditions in `P`, for example `if g, h, ~p`.
- If two fired rules require different values of the same fluent, the scenario is inconsistent because the history function `H` cannot assign both `f=0` and `f=1` at the same timepoint.
- Observations from later timepoints filter admissible initial states, so backward reasoning is obtained through model filtering and inertia.
- Inertia is preserved: outside the minimal set `O(A,t+1)`, fluent values are copied from the previous timepoint.
- `involved ag in Sc` returns `YES` only when, in every admissible model, the agent has at least one action with a non-empty actual effect/minimal occlusion.
- Actions may start only at `t = 0, ..., T-1`, because each action lasts one time unit and terminates at `t+1`.
