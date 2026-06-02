"""
Action Language with Agents GUI application (Tkinter).

Run:
    python alag_app.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from alag_engine import (
    Signature,
    DomainDescription,
    Scenario,
    Observation,
    ActionOccurrence,
    ActionEffect,
    ModelSet,
    parse_literal_set,
    build_model,
    query_holds,
    query_involved,
    InconsistentScenario,
    literal_set_to_str,
)


EXAMPLES = [
    {
        "name": "1. Prosty efekt: a by Agent causes f",
        "description": (
            "Najprostszy przypadek z konsultacji: akcja a wykonana przez właściwego agenta "
            "ma niepusty efekt, więc po wykonaniu zachodzi f, a agent jest involved. "
            "To sprawdza poprawność Q1 oraz Q2."
        ),
        "fluents": ["f"],
        "actions": ["a"],
        "agents": ["Agent"],
        "T": 1,
        "statements": [
            {"action": "a", "agent": "Agent", "effect": "f", "precondition": ""},
        ],
        "observations": [],
        "occurrences": [
            {"action": "a", "agent": "Agent", "t": 0},
        ],
        "query_lits": "f",
        "query_t": 1,
        "query_agent": "Agent",
        "expected": "Build: spójny model. Query holds {f} at 1 = YES. Query involved Agent = YES.",
    },
    {
        "name": "2. Wiele causes dla jednej akcji + involved",
        "description": (
            "Jedna akcja ma dwie reguły causes. Jeśli g zachodzi w chwili 0, obie reguły "
            "odpalają i po akcji zachodzą f oraz h. Minimalne O(a,1) powinno zawierać tylko "
            "fluenty zmieniane przez efekty: {f, h}."
        ),
        "fluents": ["f", "g", "h"],
        "actions": ["a"],
        "agents": ["ag"],
        "T": 2,
        "statements": [
            {"action": "a", "agent": "ag", "effect": "f", "precondition": "g"},
            {"action": "a", "agent": "ag", "effect": "h", "precondition": "g"},
        ],
        "observations": [
            {"literals": "g", "t": 0},
        ],
        "occurrences": [
            {"action": "a", "agent": "ag", "t": 0},
        ],
        "query_lits": "f, h",
        "query_t": 1,
        "query_agent": "ag",
        "expected": "Build: spójny model. holds {f,h} at 1 = YES. involved ag = YES.",
    },
    {
        "name": "3. Obserwacja w przyszłości działa wstecz przez wait",
        "description": (
            "Nie obserwujemy stolen w chwili 0. Po czterech akcjach wait obserwujemy stolen "
            "w chwili 4. Ponieważ wait ma pusty efekt i działa inercja, program odrzuca wszystkie "
            "modele początkowe z ~stolen. Wspólny wniosek: stolen zachodzi także wcześniej."
        ),
        "fluents": ["stolen"],
        "actions": ["wait"],
        "agents": ["bob"],
        "T": 4,
        "statements": [
            {"action": "wait", "agent": "bob", "effect": "", "precondition": ""},
        ],
        "observations": [
            {"literals": "stolen", "t": 4},
        ],
        "occurrences": [
            {"action": "wait", "agent": "bob", "t": 0},
            {"action": "wait", "agent": "bob", "t": 1},
            {"action": "wait", "agent": "bob", "t": 2},
            {"action": "wait", "agent": "bob", "t": 3},
        ],
        "query_lits": "stolen",
        "query_t": 0,
        "query_agent": "bob",
        "expected": "Build: spójny model. holds {stolen} at 0 = YES. involved bob = NO, bo wait ma pusty efekt.",
    },
    {
        "name": "4. Sprzeczne obserwacje po samych wait",
        "description": (
            "To jest przykład na niespójny scenariusz: w chwili 0 obserwujemy ~stolen, "
            "w chwili 4 obserwujemy stolen, a po drodze są tylko akcje wait z pustym efektem. "
            "Inercja wymusza zachowanie wartości, więc nie istnieje model."
        ),
        "fluents": ["stolen"],
        "actions": ["wait"],
        "agents": ["bob"],
        "T": 4,
        "statements": [
            {"action": "wait", "agent": "bob", "effect": "", "precondition": ""},
        ],
        "observations": [
            {"literals": "~stolen", "t": 0},
            {"literals": "stolen", "t": 4},
        ],
        "occurrences": [
            {"action": "wait", "agent": "bob", "t": 0},
            {"action": "wait", "agent": "bob", "t": 1},
            {"action": "wait", "agent": "bob", "t": 2},
            {"action": "wait", "agent": "bob", "t": 3},
        ],
        "query_lits": "stolen",
        "query_t": 4,
        "query_agent": "bob",
        "expected": "Build: INCONSISTENT SCENARIO.",
    },
    {
        "name": "5. Sprzeczne efekty, gdy g i h są true",
        "description": (
            "Przykład na sprzeczną dziedzinę/scenariusz: ta sama akcja powoduje f jeśli g "
            "oraz ~f jeśli h. Sam opis akcji może być użyteczny, dopóki g i h nie zachodzą razem. "
            "W tym scenariuszu obserwujemy g oraz h w chwili 0 i wykonujemy a, więc obie reguły "
            "odpalają jednocześnie i żądają różnych wartości f w chwili 1. Nie ma funkcji H, czyli nie ma modelu."
        ),
        "fluents": ["f", "g", "h"],
        "actions": ["a"],
        "agents": ["ag"],
        "T": 1,
        "statements": [
            {"action": "a", "agent": "ag", "effect": "f", "precondition": "g"},
            {"action": "a", "agent": "ag", "effect": "~f", "precondition": "h"},
        ],
        "observations": [
            {"literals": "g, h", "t": 0},
        ],
        "occurrences": [
            {"action": "a", "agent": "ag", "t": 0},
        ],
        "query_lits": "f",
        "query_t": 1,
        "query_agent": "ag",
        "expected": "Build: INCONSISTENT SCENARIO, bo efekty f i ~f odpalają razem.",
    },
    {
        "name": "6. Brak sprzeczności, gdy odpala tylko jedna reguła",
        "description": (
            "Ten przykład używa tych samych dwóch reguł co poprzedni, ale w chwili 0 zachodzi g "
            "oraz ~h. Odpala więc tylko reguła powodująca f. To pokazuje, że sam zestaw reguł "
            "nie musi być globalnie zabroniony — problem pojawia się w scenariuszu, który doprowadza "
            "do jednoczesnego spełnienia warunków sprzecznych efektów."
        ),
        "fluents": ["f", "g", "h"],
        "actions": ["a"],
        "agents": ["ag"],
        "T": 1,
        "statements": [
            {"action": "a", "agent": "ag", "effect": "f", "precondition": "g"},
            {"action": "a", "agent": "ag", "effect": "~f", "precondition": "h"},
        ],
        "observations": [
            {"literals": "g, ~h", "t": 0},
        ],
        "occurrences": [
            {"action": "a", "agent": "ag", "t": 0},
        ],
        "query_lits": "f",
        "query_t": 1,
        "query_agent": "ag",
        "expected": "Build: spójny model. holds {f} at 1 = YES. involved ag = YES.",
    },
    {
        "name": "7. Agent bez reguły dla akcji ma pusty efekt",
        "description": (
            "Reguła jest podana dla akcji a wykonywanej przez Alice, ale w scenariuszu akcję wykonuje Bob. "
            "Zgodnie z treścią zadania taki agent może wykonać akcję, ale efekt jest pusty. "
            "Dlatego f nie musi zachodzić po akcji, a Bob nie jest involved."
        ),
        "fluents": ["f"],
        "actions": ["a"],
        "agents": ["Alice", "Bob"],
        "T": 1,
        "statements": [
            {"action": "a", "agent": "Alice", "effect": "f", "precondition": ""},
        ],
        "observations": [],
        "occurrences": [
            {"action": "a", "agent": "Bob", "t": 0},
        ],
        "query_lits": "f",
        "query_t": 1,
        "query_agent": "Bob",
        "expected": "Build: spójny model. holds {f} at 1 = NO. involved Bob = NO.",
    },
    {
        "name": "8. Wait jako reguły tożsamości + sprzeczne obserwacje",
        "description": (
            "Ten wariant pokazuje dokładnie sytuację z konsultacji: wait ma dwie reguły, "
            "wait powoduje stolen jeśli stolen oraz ~stolen jeśli ~stolen. To nie tworzy zmiany, "
            "tylko jawnie zachowuje wartość. Jeśli obserwujemy ~stolen w chwili 0 oraz stolen "
            "w chwili 4, po czterech waitach nie ma modelu, bo żadna akcja nie może zmienić wartości."
        ),
        "fluents": ["stolen"],
        "actions": ["wait"],
        "agents": ["bob"],
        "T": 4,
        "statements": [
            {"action": "wait", "agent": "bob", "effect": "stolen", "precondition": "stolen"},
            {"action": "wait", "agent": "bob", "effect": "~stolen", "precondition": "~stolen"},
        ],
        "observations": [
            {"literals": "~stolen", "t": 0},
            {"literals": "stolen", "t": 4},
        ],
        "occurrences": [
            {"action": "wait", "agent": "bob", "t": 0},
            {"action": "wait", "agent": "bob", "t": 1},
            {"action": "wait", "agent": "bob", "t": 2},
            {"action": "wait", "agent": "bob", "t": 3},
        ],
        "query_lits": "stolen",
        "query_t": 4,
        "query_agent": "bob",
        "expected": "Build: INCONSISTENT SCENARIO, bo wait nie zmienia stolen na przeciwną wartość.",
    },
    {
        "name": "9. Sprzeczne obserwacje w tej samej chwili",
        "description": (
            "Najprostsza niespójność obserwacyjna: w tym samym timepoincie podajemy f oraz ~f. "
            "Program powinien od razu zgłosić brak modelu, bo funkcja H nie może przyjmować dwóch wartości."
        ),
        "fluents": ["f"],
        "actions": ["wait"],
        "agents": ["ag"],
        "T": 1,
        "statements": [
            {"action": "wait", "agent": "ag", "effect": "", "precondition": ""},
        ],
        "observations": [
            {"literals": "f", "t": 0},
            {"literals": "~f", "t": 0},
        ],
        "occurrences": [],
        "query_lits": "f",
        "query_t": 0,
        "query_agent": "ag",
        "expected": "Build: INCONSISTENT SCENARIO, bo obserwacje wymagają f=1 i f=0 jednocześnie.",
    },
    {
        "name": "10. Sprzeczne reguły dopiero po akcji przygotowującej",
        "description": (
            "Sama para reguł a -> f jeśli g oraz a -> ~f jeśli h nie musi psuć dziedziny. "
            "Problem pojawia się dopiero w scenariuszu, który doprowadza do stanu g=true i h=true, "
            "a potem wykonuje a. Tutaj akcja prepare ustawia g i h, więc późniejsze a żąda jednocześnie f i ~f."
        ),
        "fluents": ["f", "g", "h"],
        "actions": ["prepare", "a"],
        "agents": ["ag"],
        "T": 2,
        "statements": [
            {"action": "prepare", "agent": "ag", "effect": "g, h", "precondition": ""},
            {"action": "a", "agent": "ag", "effect": "f", "precondition": "g"},
            {"action": "a", "agent": "ag", "effect": "~f", "precondition": "h"},
        ],
        "observations": [],
        "occurrences": [
            {"action": "prepare", "agent": "ag", "t": 0},
            {"action": "a", "agent": "ag", "t": 1},
        ],
        "query_lits": "f",
        "query_t": 2,
        "query_agent": "ag",
        "expected": "Build: INCONSISTENT SCENARIO, bo prepare tworzy g i h, a potem a ma sprzeczne efekty.",
    },
    {
        "name": "11. Te same sprzeczne reguły, ale bez odpalenia konfliktu",
        "description": (
            "Kontrast do poprzedniego przykładu. Reguły dla a są takie same, lecz nie ma akcji, która ustawia h, "
            "a obserwacja mówi g oraz ~h. Odpala tylko efekt f, więc model istnieje. Wydruk O pokazuje minimalną "
            "inkluzję: tylko fluent f może zmienić wartość po a, reszta zachowuje się przez inercję."
        ),
        "fluents": ["f", "g", "h"],
        "actions": ["a", "wait"],
        "agents": ["ag"],
        "T": 2,
        "statements": [
            {"action": "a", "agent": "ag", "effect": "f", "precondition": "g"},
            {"action": "a", "agent": "ag", "effect": "~f", "precondition": "h"},
            {"action": "wait", "agent": "ag", "effect": "", "precondition": ""},
        ],
        "observations": [
            {"literals": "g, ~h", "t": 0},
        ],
        "occurrences": [
            {"action": "wait", "agent": "ag", "t": 0},
            {"action": "a", "agent": "ag", "t": 1},
        ],
        "query_lits": "f",
        "query_t": 2,
        "query_agent": "ag",
        "expected": "Build: spójny model. holds {f} at 2 = YES. involved ag = YES.",
    },
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Action Language with Agents")
        self.geometry("1050x720")

        self.sig = Signature(T=9)
        self.D = DomainDescription()
        self.Sc = Scenario()
        self.model: Optional[ModelSet] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.nb = nb
        # Examples are first, so after opening the app the user can immediately click
        # a ready scenario and fill the whole program automatically.
        self._build_examples_tab(nb)
        self._build_signature_tab(nb)
        self._build_domain_tab(nb)
        self._build_scenario_tab(nb)
        self._build_query_tab(nb)

        self.status = tk.StringVar(value="Apply a signature to begin.")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(
            fill="x", side="bottom"
        )

    # ----- Tab 1: Signature -----
    def _build_signature_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="1. Signature")

        info = (
            "Define the fluents, actions, agents, and time T.\n"
            "Separate entries with commas or spaces. Actions may start only at t=0,...,T-1."
        )
        ttk.Label(f, text=info, foreground="#444").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 12), padx=8
        )

        ttk.Label(f, text="Fluents (F):").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.fluents_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.fluents_var, width=80).grid(row=1, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Actions (Ac):").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self.actions_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.actions_var, width=80).grid(row=2, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Agents (Ag):").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        self.agents_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.agents_var, width=80).grid(row=3, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Time T:").grid(row=4, column=0, sticky="e", padx=6, pady=4)
        self.T_var = tk.IntVar(value=9)
        ttk.Spinbox(f, from_=1, to=50, textvariable=self.T_var, width=8).grid(row=4, column=1, sticky="w", padx=6)

        ttk.Button(f, text="Apply", command=self._apply_signature).grid(
            row=5, column=1, sticky="w", padx=6, pady=12
        )

        quick = ttk.LabelFrame(f, text="Szybkie wczytanie przykładu")
        quick.grid(row=6, column=0, columnspan=2, sticky="we", padx=8, pady=(8, 4))
        ttk.Label(quick, text="Przykład:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.quick_example_combo = ttk.Combobox(
            quick,
            values=[ex["name"] for ex in EXAMPLES],
            state="readonly",
            width=52,
        )
        self.quick_example_combo.grid(row=0, column=1, sticky="we", padx=6, pady=6)
        self.quick_example_combo.current(0)
        ttk.Button(
            quick,
            text="Wczytaj przykład",
            command=lambda: self._load_quick_example(build=False),
        ).grid(row=0, column=2, sticky="w", padx=4, pady=6)
        ttk.Button(
            quick,
            text="Wczytaj przykład + zbuduj",
            command=lambda: self._load_quick_example(build=True),
        ).grid(row=0, column=3, sticky="w", padx=4, pady=6)
        quick.columnconfigure(1, weight=1)

        ttk.Label(
            f,
            text=(
                "Po wczytaniu przykładu program sam uzupełnia F, Ac, Ag, T, reguły causes, "
                "obserwacje, akcje i domyślne query."
            ),
            foreground="#444",
            wraplength=900,
        ).grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 0))

        ttk.Label(
            f,
            text=(
                "Tip: if the initial value of a fluent is not observed at t=0, the engine keeps all "
                "initial values that can still satisfy later observations. This is why backward reasoning works."
            ),
            foreground="#666",
            wraplength=900,
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=8, pady=(10, 0))

        f.columnconfigure(1, weight=1)

    def _parse_name_set(self, text: str) -> set[str]:
        return {x.strip() for x in text.replace(",", " ").split() if x.strip()}

    def _apply_signature(self):
        try:
            fluents = self._parse_name_set(self.fluents_var.get())
            actions = self._parse_name_set(self.actions_var.get())
            agents = self._parse_name_set(self.agents_var.get())
            if not fluents or not actions or not agents:
                raise ValueError("Fluents, actions, and agents must each be non-empty.")
            self.sig = Signature(fluents=fluents, actions=actions, agents=agents, T=int(self.T_var.get()))
            self.D = DomainDescription()
            self.Sc = Scenario()
            self.model = None
            self._refresh_action_dd()
            self._refresh_agent_dd()
            self._refresh_dd_list()
            self._refresh_obs_list()
            self._refresh_occ_list()
            self._set_status(
                f"Signature applied: |F|={len(fluents)}, |Ac|={len(actions)}, |Ag|={len(agents)}, T={self.sig.T}."
            )
        except Exception as e:
            messagebox.showerror("Signature error", str(e))

    # ----- Tab 2: Domain description -----
    def _build_domain_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="2. Domain description")

        top = ttk.LabelFrame(f, text="Add action effect statement: A by ag causes E if P")
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Action A:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.dd_action = ttk.Combobox(top, width=18, state="readonly")
        self.dd_action.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(top, text="Agent ag:").grid(row=0, column=2, sticky="e", padx=4)
        self.dd_agent = ttk.Combobox(top, width=18, state="readonly")
        self.dd_agent.grid(row=0, column=3, sticky="w", padx=4)

        ttk.Label(top, text="Effect E:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.dd_effect = tk.StringVar()
        ttk.Entry(top, textvariable=self.dd_effect, width=42).grid(row=1, column=1, sticky="we", padx=4)

        ttk.Label(top, text="Precondition P:").grid(row=1, column=2, sticky="e", padx=4)
        self.dd_pre = tk.StringVar()
        ttk.Entry(top, textvariable=self.dd_pre, width=42).grid(row=1, column=3, sticky="we", padx=4)

        ttk.Button(top, text="Add causes statement", command=self._add_statement).grid(row=2, column=1, pady=8, sticky="w")
        ttk.Button(top, text="Remove selected", command=self._remove_statement).grid(row=2, column=2, pady=8, sticky="w")
        ttk.Label(
            top,
            text="Negation: ~f, -f, !f, not f, or ¬f. Empty field means empty set. Multiple statements for one action are allowed.",
            foreground="#666",
            wraplength=900,
        ).grid(row=3, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 6))

        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        self.dd_list = tk.Listbox(f, height=14, font=("Courier", 10))
        self.dd_list.pack(fill="both", expand=True, padx=8, pady=8)

    def _add_statement(self):
        try:
            a = self.dd_action.get().strip()
            ag = self.dd_agent.get().strip()
            if a not in self.sig.actions:
                raise ValueError(f"Unknown action {a!r}. Apply signature first.")
            if ag not in self.sig.agents:
                raise ValueError(f"Unknown agent {ag!r}. Apply signature first.")
            effect = parse_literal_set(self.dd_effect.get())
            pre = parse_literal_set(self.dd_pre.get())
            for lit in effect | pre:
                if lit.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {lit.fluent!r}.")
            self.D.add(ActionEffect(a, effect, pre, ag))
            self.model = None
            self._refresh_dd_list()
            self._set_status(f"Added statement: {a} by {ag} causes {literal_set_to_str(effect)}.")
        except Exception as e:
            messagebox.showerror("Domain description error", str(e))

    def _remove_statement(self):
        sel = self.dd_list.curselection()
        if not sel:
            return
        self.D.remove_at(sel[0])
        self.model = None
        self._refresh_dd_list()
        self._set_status("Selected statement removed.")

    def _refresh_dd_list(self):
        self.dd_list.delete(0, "end")
        for i, stmt in enumerate(self.D.statements, start=1):
            self.dd_list.insert("end", f"{i:02d}. {stmt}")

    def _refresh_action_dd(self):
        actions = sorted(self.sig.actions)
        for combo_name in ["dd_action", "sc_action"]:
            combo = getattr(self, combo_name, None)
            if combo is not None:
                combo["values"] = actions
                if actions:
                    combo.set(actions[0])

    def _refresh_agent_dd(self):
        agents = sorted(self.sig.agents)
        for combo_name in ["dd_agent", "sc_agent", "q_agent"]:
            combo = getattr(self, combo_name, None)
            if combo is not None:
                combo["values"] = agents
                if agents:
                    combo.set(agents[0])

    # ----- Tab 3: Scenario -----
    def _build_scenario_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="3. Scenario")

        obs_box = ttk.LabelFrame(f, text="Observations (L, t) — what is known to hold at time t")
        obs_box.pack(fill="x", padx=8, pady=6)
        ttk.Label(obs_box, text="Literals:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.sc_obs_lits = tk.StringVar()
        ttk.Entry(obs_box, textvariable=self.sc_obs_lits, width=55).grid(row=0, column=1, sticky="we", padx=4)
        ttk.Label(obs_box, text="t:").grid(row=0, column=2, sticky="e", padx=4)
        self.sc_obs_t = tk.IntVar(value=0)
        ttk.Spinbox(obs_box, from_=0, to=50, textvariable=self.sc_obs_t, width=6).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Button(obs_box, text="Add", command=self._add_obs).grid(row=0, column=4, padx=8)
        ttk.Button(obs_box, text="Remove selected", command=self._remove_obs).grid(row=0, column=5, padx=4)
        obs_box.columnconfigure(1, weight=1)

        self.obs_list = tk.Listbox(f, height=6, font=("Courier", 10))
        self.obs_list.pack(fill="x", padx=8, pady=4)

        ao_box = ttk.LabelFrame(f, text="Action occurrences (A, ag, t); actions start at t and end at t+1")
        ao_box.pack(fill="x", padx=8, pady=6)
        ttk.Label(ao_box, text="Action:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.sc_action = ttk.Combobox(ao_box, width=16, state="readonly")
        self.sc_action.grid(row=0, column=1, padx=4)
        ttk.Label(ao_box, text="Agent:").grid(row=0, column=2, sticky="e", padx=4)
        self.sc_agent = ttk.Combobox(ao_box, width=16, state="readonly")
        self.sc_agent.grid(row=0, column=3, padx=4)
        ttk.Label(ao_box, text="t:").grid(row=0, column=4, sticky="e", padx=4)
        self.sc_t = tk.IntVar(value=0)
        ttk.Spinbox(ao_box, from_=0, to=50, textvariable=self.sc_t, width=6).grid(row=0, column=5, padx=4)
        ttk.Button(ao_box, text="Add", command=self._add_occ).grid(row=0, column=6, padx=8)
        ttk.Button(ao_box, text="Remove selected", command=self._remove_occ).grid(row=0, column=7, padx=4)

        self.occ_list = tk.Listbox(f, height=8, font=("Courier", 10))
        self.occ_list.pack(fill="both", expand=True, padx=8, pady=4)

    def _add_obs(self):
        try:
            lits = parse_literal_set(self.sc_obs_lits.get())
            for lit in lits:
                if lit.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {lit.fluent!r}.")
            t = int(self.sc_obs_t.get())
            if not (0 <= t <= self.sig.T):
                raise ValueError(f"t must be in [0, {self.sig.T}].")
            self.Sc.observations.append(Observation(lits, t))
            self.model = None
            self._refresh_obs_list()
            self._set_status(f"Observation added at t={t}.")
        except Exception as e:
            messagebox.showerror("Observation error", str(e))

    def _remove_obs(self):
        sel = self.obs_list.curselection()
        if sel:
            self.Sc.observations.pop(sel[0])
            self.model = None
            self._refresh_obs_list()

    def _refresh_obs_list(self):
        self.obs_list.delete(0, "end")
        for i, obs in enumerate(self.Sc.observations, start=1):
            self.obs_list.insert("end", f"{i:02d}. ({literal_set_to_str(obs.literals)}, t={obs.t})")

    def _add_occ(self):
        try:
            a = self.sc_action.get().strip()
            ag = self.sc_agent.get().strip()
            t = int(self.sc_t.get())
            if a not in self.sig.actions:
                raise ValueError("Unknown action.")
            if ag not in self.sig.agents:
                raise ValueError("Unknown agent.")
            if not (0 <= t < self.sig.T):
                raise ValueError(f"Action time t must be in [0, {self.sig.T - 1}], because it ends at t+1.")
            if any(o.t == t for o in self.Sc.occurrences):
                raise ValueError(f"Another action already occurs at t={t} (sequential actions only).")
            self.Sc.occurrences.append(ActionOccurrence(a, ag, t))
            self.Sc.occurrences.sort(key=lambda o: o.t)
            self.model = None
            self._refresh_occ_list()
            self._set_status(f"Action occurrence added: ({a}, {ag}, {t}).")
        except Exception as e:
            messagebox.showerror("Action occurrence error", str(e))

    def _remove_occ(self):
        sel = self.occ_list.curselection()
        if sel:
            self.Sc.occurrences.pop(sel[0])
            self.model = None
            self._refresh_occ_list()

    def _refresh_occ_list(self):
        self.occ_list.delete(0, "end")
        for i, occ in enumerate(self.Sc.occurrences, start=1):
            self.occ_list.insert("end", f"{i:02d}. ({occ.action}, {occ.agent}, t={occ.t})")

    # ----- Tab 4: Query & run -----
    def _build_query_tab(self, nb):
        f = ttk.Frame(nb)
        self.query_frame = f
        nb.add(f, text="4. Query & run")

        top = ttk.LabelFrame(f, text="Build the model set")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Build models & show trajectory", command=self._build_and_show).pack(side="left", padx=8, pady=6)
        ttk.Button(top, text="Clear output", command=lambda: self.out.delete("1.0", "end")).pack(side="left", padx=4)

        q1 = ttk.LabelFrame(f, text="Query 1: holds α at t when Sc")
        q1.pack(fill="x", padx=8, pady=6)
        ttk.Label(q1, text="Literals α:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.q_lits = tk.StringVar()
        ttk.Entry(q1, textvariable=self.q_lits, width=40).grid(row=0, column=1, padx=4)
        ttk.Label(q1, text="t:").grid(row=0, column=2, sticky="e", padx=4)
        self.q_t = tk.IntVar(value=0)
        ttk.Spinbox(q1, from_=0, to=50, textvariable=self.q_t, width=6).grid(row=0, column=3, padx=4)
        ttk.Button(q1, text="Ask", command=self._ask_holds).grid(row=0, column=4, padx=8)

        q2 = ttk.LabelFrame(f, text="Query 2: involved ag in Sc")
        q2.pack(fill="x", padx=8, pady=6)
        ttk.Label(q2, text="Agent:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.q_agent = ttk.Combobox(q2, width=16, state="readonly")
        self.q_agent.grid(row=0, column=1, padx=4)
        ttk.Button(q2, text="Ask", command=self._ask_involved).grid(row=0, column=2, padx=8)

        out_box = ttk.LabelFrame(f, text="Output")
        out_box.pack(fill="both", expand=True, padx=8, pady=8)
        self.out = scrolledtext.ScrolledText(out_box, font=("Courier New", 10), wrap="none", height=20)
        self.out.pack(fill="both", expand=True)

    def _build_and_show(self):
        self.out.delete("1.0", "end")
        try:
            self.model = build_model(self.sig, self.D, self.Sc)
        except InconsistentScenario as e:
            self.model = None
            self.out.insert("end", "INCONSISTENT SCENARIO\n\n")
            self.out.insert("end", f"{e}\n")
            self._set_status("Scenario is inconsistent w.r.t. the domain description.")
            return
        except Exception as e:
            self.model = None
            messagebox.showerror("Build error", str(e))
            return

        self.out.insert("end", f"Model set built: {len(self.model)} admissible model(s).\n")
        self.out.insert("end", "Values shown below are consequences common to all models. '?' means 0 in some models and 1 in others.\n\n")
        self._print_trajectory()
        self._set_status(f"Model set built successfully: {len(self.model)} model(s).")

    def _print_trajectory(self):
        if self.model is None:
            return
        ms = self.model
        T = self.sig.T
        fluents = sorted(self.sig.fluents)
        col_w = 7

        head = f"{'t':<14}" + "".join(f"{t:>{col_w}}" for t in range(0, T + 1))
        self.out.insert("end", head + "\n")

        acs_by_t = {o.t: o for o in self.Sc.occurrences}
        action_row = f"{'action':<14}"
        for t in range(0, T + 1):
            occ = acs_by_t.get(t)
            cell = occ.action[: col_w - 1] if occ else "-"
            action_row += f"{cell:>{col_w}}"
        self.out.insert("end", action_row + "\n")

        agent_row = f"{'agent':<14}"
        for t in range(0, T + 1):
            occ = acs_by_t.get(t)
            cell = occ.agent[: col_w - 1] if occ else "-"
            agent_row += f"{cell:>{col_w}}"
        self.out.insert("end", agent_row + "\n")
        self.out.insert("end", "-" * (14 + col_w * (T + 1)) + "\n")

        for fluent in fluents:
            row = f"{fluent:<14}"
            for t in range(0, T + 1):
                common = ms.common_value(fluent, t)
                cell = "?" if common is None else str(common)
                row += f"{cell:>{col_w}}"
            self.out.insert("end", row + "\n")

        self.out.insert("end", "\nMinimal occlusion O(A, t+1) for actual action occurrences:\n")
        if not self.Sc.occurrences:
            self.out.insert("end", "  (no action occurrences)\n")
            return

        for occ in sorted(self.Sc.occurrences, key=lambda x: x.t):
            variants = []
            for model in ms.models:
                fs = frozenset(model.O.get((occ.action, occ.t + 1), set()))
                if fs not in variants:
                    variants.append(fs)
            if len(variants) == 1:
                items = sorted(variants[0])
                text = "{" + ", ".join(items) + "}" if items else "{}"
            else:
                rendered = []
                for fs in variants:
                    items = sorted(fs)
                    rendered.append("{" + ", ".join(items) + "}" if items else "{}")
                text = " or ".join(rendered)
            self.out.insert("end", f"  action at t={occ.t}: O({occ.action}, {occ.t + 1}) = {text}\n")

    def _ask_holds(self):
        if self.model is None:
            messagebox.showinfo("No model", "Build the model set first.")
            return
        try:
            lits = parse_literal_set(self.q_lits.get())
            for lit in lits:
                if lit.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {lit.fluent!r}.")
            t = int(self.q_t.get())
            if not (0 <= t <= self.sig.T):
                raise ValueError(f"t must be in [0, {self.sig.T}].")
            res = query_holds(self.model, lits, t)
            count = self.model.holds_count(lits, t)
            lit_str = literal_set_to_str(lits)
            verdict = "YES" if res else "NO"
            self.out.insert(
                "end",
                f"\n[holds {lit_str} at {t} when Sc]  {verdict}  ({count}/{len(self.model)} model(s) satisfy it)\n",
            )
            self.out.see("end")
        except Exception as e:
            messagebox.showerror("Query error", str(e))

    def _ask_involved(self):
        if self.model is None:
            messagebox.showinfo("No model", "Build the model set first.")
            return
        try:
            ag = self.q_agent.get().strip()
            if ag not in self.sig.agents:
                raise ValueError(f"Unknown agent {ag!r}.")
            res = query_involved(self.model, ag)
            count = self.model.involved_count(ag)
            verdict = "YES" if res else "NO"
            self.out.insert(
                "end",
                f"\n[involved {ag} in Sc]  {verdict}  ({count}/{len(self.model)} model(s) have a non-empty effect for this agent)\n",
            )
            self.out.see("end")
        except Exception as e:
            messagebox.showerror("Query error", str(e))

    # ----- Tab 5: Examples -----
    def _build_examples_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="0. PRZYKŁADY")

        top = ttk.LabelFrame(f, text="Gotowe przykłady z konsultacji")
        top.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(top)
        left.pack(side="left", fill="y", padx=(8, 6), pady=8)
        ttk.Label(left, text="Wybierz przykład:").pack(anchor="w")
        self.examples_list = tk.Listbox(left, height=18, width=46, exportselection=False)
        self.examples_list.pack(fill="y", expand=False, pady=(4, 8))
        for ex in EXAMPLES:
            self.examples_list.insert("end", ex["name"])
        self.examples_list.bind("<<ListboxSelect>>", lambda _event: self._show_selected_example_info())
        self.examples_list.bind("<Double-Button-1>", lambda _event: self._load_selected_example(build=True))

        ttk.Button(left, text="Wczytaj przykład", command=lambda: self._load_selected_example(build=False)).pack(fill="x", pady=2)
        ttk.Button(left, text="Wczytaj przykład + zbuduj", command=lambda: self._load_selected_example(build=True)).pack(fill="x", pady=2)

        right = ttk.Frame(top)
        right.pack(side="left", fill="both", expand=True, padx=(6, 8), pady=8)
        ttk.Label(
            right,
            text="Opis przykładu i oczekiwany wynik:",
        ).pack(anchor="w")
        self.examples_info = scrolledtext.ScrolledText(right, font=("Courier New", 10), wrap="word", height=20)
        self.examples_info.pack(fill="both", expand=True, pady=(4, 0))

        self.examples_list.selection_set(0)
        self._show_selected_example_info()

    def _load_quick_example(self, build: bool = False):
        """Load an example from the selector visible on the Signature tab."""
        name = self.quick_example_combo.get() if hasattr(self, "quick_example_combo") else EXAMPLES[0]["name"]
        idx = next((i for i, ex in enumerate(EXAMPLES) if ex["name"] == name), 0)
        if hasattr(self, "examples_list"):
            self.examples_list.selection_clear(0, "end")
            self.examples_list.selection_set(idx)
            self.examples_list.see(idx)
            self._show_selected_example_info()
        self._load_example(EXAMPLES[idx], build=build)

    def _selected_example(self) -> dict:
        sel = self.examples_list.curselection()
        if not sel:
            self.examples_list.selection_set(0)
            sel = self.examples_list.curselection()
        return EXAMPLES[sel[0]]

    def _format_example_info(self, ex: dict) -> str:
        lines = [
            ex["name"],
            "=" * len(ex["name"]),
            "",
            ex["description"],
            "",
            "Signature:",
            f"  F  = {{{', '.join(ex['fluents'])}}}",
            f"  Ac = {{{', '.join(ex['actions'])}}}",
            f"  Ag = {{{', '.join(ex['agents'])}}}",
            f"  T  = {ex['T']}",
            "",
            "Domain description:",
        ]
        for st in ex["statements"]:
            eff = st["effect"] or "{}"
            pre = st["precondition"] or "{}"
            lines.append(f"  {st['action']} by {st['agent']} causes {eff} if {pre}")
        if not ex["statements"]:
            lines.append("  (empty)")

        lines.extend(["", "Observations:"])
        for obs in ex["observations"]:
            lines.append(f"  ({obs['literals'] or '{}'}, t={obs['t']})")
        if not ex["observations"]:
            lines.append("  (empty)")

        lines.extend(["", "Action occurrences:"])
        for occ in ex["occurrences"]:
            lines.append(f"  ({occ['action']}, {occ['agent']}, t={occ['t']})")
        if not ex["occurrences"]:
            lines.append("  (empty)")

        lines.extend([
            "",
            "Default queries after loading:",
            f"  Q1: holds {{{ex['query_lits']}}} at {ex['query_t']} when Sc",
            f"  Q2: involved {ex['query_agent']} in Sc",
            "",
            "Expected:",
            f"  {ex['expected']}",
            "",
            "Tip: double-click na nazwie przykładu wczytuje go i od razu buduje model.",
        ])
        return "\n".join(lines)

    def _show_selected_example_info(self):
        ex = self._selected_example()
        self.examples_info.configure(state="normal")
        self.examples_info.delete("1.0", "end")
        self.examples_info.insert("end", self._format_example_info(ex))
        self.examples_info.configure(state="disabled")

    def _load_selected_example(self, build: bool = False):
        self._load_example(self._selected_example(), build=build)

    def _load_example(self, ex: dict, build: bool = False):
        try:
            self._apply_example(ex)
        except Exception as e:
            messagebox.showerror("Example error", str(e))
            return

        if build:
            self.nb.select(self.query_frame)
            self._build_and_show()
            if self.model is not None:
                self._append_default_query_answers(ex)
                self._set_status(f"Loaded and built example: {ex['name']}.")
        else:
            self._set_status(f"Loaded example: {ex['name']}. You can now build the model or ask queries.")
            if hasattr(self, "out"):
                self.out.delete("1.0", "end")
                self.out.insert("end", self._format_example_info(ex))
                self.out.insert("end", "\n\nKliknij 'Build models & show trajectory', aby uruchomić ten przykład.\n")

    def _append_default_query_answers(self, ex: dict):
        """Run and print the example's default Q1/Q2 without showing popups."""
        if self.model is None:
            return

        try:
            lits = parse_literal_set(ex["query_lits"])
            t = int(ex["query_t"])
            lit_str = literal_set_to_str(lits)
            holds_res = query_holds(self.model, lits, t)
            holds_count = self.model.holds_count(lits, t)
            self.out.insert(
                "end",
                f"\n[default Q1: holds {lit_str} at {t} when Sc]  "
                f"{'YES' if holds_res else 'NO'}  ({holds_count}/{len(self.model)} model(s) satisfy it)\n",
            )

            ag = ex["query_agent"]
            involved_res = query_involved(self.model, ag)
            involved_count = self.model.involved_count(ag)
            self.out.insert(
                "end",
                f"[default Q2: involved {ag} in Sc]  "
                f"{'YES' if involved_res else 'NO'}  ({involved_count}/{len(self.model)} model(s) have a non-empty effect)\n",
            )
            self.out.see("end")
        except Exception as exc:
            self.out.insert("end", f"\nCould not run default queries: {exc}\n")

    def _apply_example(self, ex: dict):
        self.sig = Signature(
            fluents=set(ex["fluents"]),
            actions=set(ex["actions"]),
            agents=set(ex["agents"]),
            T=int(ex["T"]),
        )
        self.D = DomainDescription()
        for st in ex["statements"]:
            self.D.add(
                ActionEffect(
                    st["action"],
                    parse_literal_set(st["effect"]),
                    parse_literal_set(st["precondition"]),
                    st["agent"],
                )
            )

        self.Sc = Scenario()
        for obs in ex["observations"]:
            self.Sc.observations.append(Observation(parse_literal_set(obs["literals"]), int(obs["t"])))
        for occ in ex["occurrences"]:
            self.Sc.occurrences.append(ActionOccurrence(occ["action"], occ["agent"], int(occ["t"])))
        self.Sc.occurrences.sort(key=lambda item: item.t)
        self.model = None

        # Update form fields so the user can inspect and edit the loaded example.
        self.fluents_var.set(" ".join(ex["fluents"]))
        self.actions_var.set(" ".join(ex["actions"]))
        self.agents_var.set(" ".join(ex["agents"]))
        self.T_var.set(int(ex["T"]))
        if hasattr(self, "quick_example_combo"):
            self.quick_example_combo.set(ex["name"])
        self._refresh_action_dd()
        self._refresh_agent_dd()
        self._refresh_dd_list()
        self._refresh_obs_list()
        self._refresh_occ_list()

        if hasattr(self, "q_lits"):
            self.q_lits.set(ex["query_lits"])
        if hasattr(self, "q_t"):
            self.q_t.set(int(ex["query_t"]))
        if hasattr(self, "q_agent") and ex["query_agent"] in self.sig.agents:
            self.q_agent.set(ex["query_agent"])

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _set_status(self, msg: str):
        self.status.set(msg)


if __name__ == "__main__":
    App().mainloop()
