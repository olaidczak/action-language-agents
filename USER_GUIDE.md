# User Guide — Action Language with Agents

## 1. Requirements

The application requires Python 3.10+ with the standard `tkinter` library. No external Python packages are required to run the GUI or tests.

Project files:

- `alag_engine.py` — reasoning engine and query evaluation.
- `alag_app.py` — graphical user interface.
- `example_tests.py` — regression tests and executable examples.
- `README.md` — short project overview.

## 2. Running the application

Open a terminal in the project folder and run:

```bash
python alag_app.py
```

A window titled **Action Language with Agents** should open.

## 3. Using built-in examples

The first tab is **0. Examples**. It contains ready scenarios prepared for demonstration.

1. Select an example from the list.
2. Click **Load example** to fill the fields automatically.
3. Click **Load example + build** to fill the fields and immediately build the model set.
4. Check the generated trajectory, occlusion sets, and query answers in the output panel.

Recommended examples for presentation:

- **2. Wiele causes dla jednej akcji + involved** — shows that several `causes` rules may fire for one action.
- **3. Obserwacja w przyszłości działa wstecz przez wait** — shows inertia and backward restriction from later observations.
- **5. Sprzeczne efekty, gdy g i h są true** — shows inconsistency caused by conflicting fired effects.
- **12. Kilka preconditions w jednej regule** — shows that precondition `P` is a set of literals.

## 4. Creating a custom scenario

### Step 1 — Signature

Open **1. Signature** and enter:

- fluents `F`, for example `loaded alive aimed`,
- actions `Ac`, for example `Load Shoot Wait`,
- agents `Ag`, for example `Hunter Assistant`,
- time bound `T`, for example `9`.

Click **Apply signature**.

### Step 2 — Domain description

Open **2. Domain description** and add rules of the form:

```text
A by ag causes E if P
```

Examples:

```text
Load by Hunter causes loaded if
Shoot by Hunter causes ~alive, ~loaded if loaded
Wait by Bob causes {} if
```

The effect `E` and precondition `P` are sets of literals. Empty `P` means that the action has no precondition. Empty `E` means that the action has no effect.

### Step 3 — Scenario

Open **3. Scenario** and add:

- observations `(L, t)`, for example `{alive, ~loaded}` at `0`,
- action occurrences `(A, ag, t)`, for example `Load` by `Hunter` at `1`.

Only one action may occur at one timepoint, because DS8 assumes deterministic and sequential actions.

### Step 4 — Queries

Open **4. Query & run** and click **Build models & show trajectory**.

For Q1, enter a set of literals and a timepoint, for example:

```text
~alive at 4
```

This corresponds to:

```text
holds {~alive} at 4 when Sc
```

For Q2, select an agent and ask whether the agent is involved:

```text
involved Hunter in Sc
```

## 5. Reading the output

The output shows:

- actions performed at each timepoint,
- agents performing the actions,
- values of all fluents at all timepoints,
- minimal occlusion sets `O(A, t+1)`,
- answers to Q1 and Q2.

Meaning of values:

- `1` — the fluent is true,
- `0` — the fluent is false,
- `?` — different admissible models give different values.

For Q1 the program answers `YES` only if the condition holds in all admissible models.

For Q2 the program answers `YES` only if the agent has at least one action occurrence with a non-empty actual effect/minimal occlusion.

## 6. Running tests

Run:

```bash
python -m py_compile alag_engine.py alag_app.py example_tests.py
python example_tests.py
```

Expected result: a sequence of `OK:` messages, ending with:

```text
OK: all 13 GUI examples match consistency expectations
```

## 7. Building a Windows `.exe`

A true Windows `.exe` should be built on Windows. From the project folder, run:

```bat
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name ALAg alag_app.py
```

The executable will be created in:

```text
dist\ALAg.exe
```

A ready helper script is included as `build_windows_exe.bat`.