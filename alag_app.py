"""
Action Language with Agents GUI application (Tkinter).

Run: python alag_app.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from alag_engine import (
    Signature, DomainDescription, Scenario, Observation, ActionOccurrence,
    ActionEffect, Model,
    parse_literal_set, build_model, query_holds, query_involved,
    InconsistentScenario,
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Action Language with Agents")
        self.geometry("950x680")

        self.sig = Signature(T=9)
        self.D = DomainDescription()
        self.Sc = Scenario()
        self.model: Optional[Model] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

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

        info = ("Define the fluents, actions, agents, and time T.\n"
                "Separate entries with commas or spaces.")
        ttk.Label(f, text=info, foreground="#444").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 12), padx=8
        )

        ttk.Label(f, text="Fluents (F):").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.fluents_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.fluents_var, width=70).grid(row=1, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Actions (Ac):").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self.actions_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.actions_var, width=70).grid(row=2, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Agents (Ag):").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        self.agents_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.agents_var, width=70).grid(row=3, column=1, sticky="we", padx=6)

        ttk.Label(f, text="Time T:").grid(row=4, column=0, sticky="e", padx=6, pady=4)
        self.T_var = tk.IntVar(value=9)
        ttk.Spinbox(f, from_=1, to=50, textvariable=self.T_var, width=8).grid(row=4, column=1, sticky="w", padx=6)

        ttk.Button(f, text="Apply", command=self._apply_signature).grid(
            row=5, column=1, sticky="w", padx=6, pady=12
        )

        f.columnconfigure(1, weight=1)

    def _apply_signature(self):
        try:
            fluents = {x.strip() for x in self.fluents_var.get().replace(",", " ").split() if x.strip()}
            actions = {x.strip() for x in self.actions_var.get().replace(",", " ").split() if x.strip()}
            agents = {x.strip() for x in self.agents_var.get().replace(",", " ").split() if x.strip()}
            if not fluents or not actions or not agents:
                raise ValueError("Fluents, actions, and agents must each be non-empty.")
            self.sig = Signature(fluents=fluents, actions=actions, agents=agents, T=int(self.T_var.get()))
            self._refresh_action_dd()
            self._refresh_agent_dd()
            self._set_status(
                f"Signature applied: |F|={len(fluents)}, |Ac|={len(actions)}, |Ag|={len(agents)}, T={self.sig.T}."
            )
        except Exception as e:
            messagebox.showerror("Signature error", str(e))

    # ----- Tab 2: Domain description -----
    def _build_domain_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="2. Domain description")

        top = ttk.LabelFrame(f, text="Add action effect statement: A causes E if P by ag")
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Action A:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.dd_action = ttk.Combobox(top, width=18, state="readonly")
        self.dd_action.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(top, text="Effect E (literals):").grid(row=0, column=2, sticky="e", padx=4)
        self.dd_effect = tk.StringVar()
        ttk.Entry(top, textvariable=self.dd_effect, width=30).grid(row=0, column=3, sticky="w", padx=4)

        ttk.Label(top, text="Precondition P:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.dd_pre = tk.StringVar()
        ttk.Entry(top, textvariable=self.dd_pre, width=30).grid(row=1, column=1, columnspan=2, sticky="we", padx=4)

        ttk.Label(top, text="Agent ag:").grid(row=1, column=3, sticky="e", padx=4)
        self.dd_agent = ttk.Combobox(top, width=18, state="readonly")
        self.dd_agent.grid(row=1, column=4, sticky="w", padx=4)

        ttk.Button(top, text="Add / replace", command=self._add_statement).grid(row=2, column=1, pady=8, sticky="w")
        ttk.Button(top, text="Remove selected", command=self._remove_statement).grid(row=2, column=2, pady=8, sticky="w")
        ttk.Label(top, text="Negation: use ~f. Leave blank for empty set.",
                  foreground="#666").grid(row=2, column=3, columnspan=2, sticky="w")

        self.dd_list = tk.Listbox(f, height=12, font=("Courier", 10))
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
            for l in effect | pre:
                if l.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {l.fluent!r}.")
            self.D.statements.pop(a, None)  # replace if exists
            self.D.add(ActionEffect(a, effect, pre, ag))
            self._refresh_dd_list()
            self._set_status(f"Added statement for {a}.")
        except Exception as e:
            messagebox.showerror("Domain description error", str(e))

    def _remove_statement(self):
        sel = self.dd_list.curselection()
        if not sel:
            return
        action = list(self.D.statements.keys())[sel[0]]
        self.D.remove(action)
        self._refresh_dd_list()

    def _refresh_dd_list(self):
        self.dd_list.delete(0, "end")
        for stmt in self.D.statements.values():
            self.dd_list.insert("end", str(stmt))

    def _refresh_action_dd(self):
        actions = sorted(self.sig.actions)
        self.dd_action["values"] = actions
        self.sc_action["values"] = actions
        if actions:
            if not self.dd_action.get():
                self.dd_action.set(actions[0])
            if not self.sc_action.get():
                self.sc_action.set(actions[0])

    def _refresh_agent_dd(self):
        agents = sorted(self.sig.agents)
        self.dd_agent["values"] = agents
        self.sc_agent["values"] = agents
        self.q_agent["values"] = agents
        if agents:
            if not self.dd_agent.get():
                self.dd_agent.set(agents[0])
            if not self.sc_agent.get():
                self.sc_agent.set(agents[0])
            if not self.q_agent.get():
                self.q_agent.set(agents[0])

    # ----- Tab 3: Scenario -----
    def _build_scenario_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="3. Scenario")

        # Observations
        obs_box = ttk.LabelFrame(f, text="Observations  (L, t) — what is known to hold at time t")
        obs_box.pack(fill="x", padx=8, pady=6)
        ttk.Label(obs_box, text="Literals:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.sc_obs_lits = tk.StringVar()
        ttk.Entry(obs_box, textvariable=self.sc_obs_lits, width=40).grid(row=0, column=1, sticky="we", padx=4)
        ttk.Label(obs_box, text="t:").grid(row=0, column=2, sticky="e", padx=4)
        self.sc_obs_t = tk.IntVar(value=0)
        ttk.Spinbox(obs_box, from_=0, to=50, textvariable=self.sc_obs_t, width=6).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Button(obs_box, text="Add", command=self._add_obs).grid(row=0, column=4, padx=8)
        ttk.Button(obs_box, text="Remove selected", command=self._remove_obs).grid(row=0, column=5, padx=4)

        self.obs_list = tk.Listbox(f, height=5, font=("Courier", 10))
        self.obs_list.pack(fill="x", padx=8, pady=4)

        # Action occurrences
        ao_box = ttk.LabelFrame(f, text="Action occurrences  (A, ag, t)")
        ao_box.pack(fill="x", padx=8, pady=6)
        ttk.Label(ao_box, text="Action:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.sc_action = ttk.Combobox(ao_box, width=14, state="readonly")
        self.sc_action.grid(row=0, column=1, padx=4)
        ttk.Label(ao_box, text="Agent:").grid(row=0, column=2, sticky="e", padx=4)
        self.sc_agent = ttk.Combobox(ao_box, width=14, state="readonly")
        self.sc_agent.grid(row=0, column=3, padx=4)
        ttk.Label(ao_box, text="t:").grid(row=0, column=4, sticky="e", padx=4)
        self.sc_t = tk.IntVar(value=1)
        ttk.Spinbox(ao_box, from_=0, to=50, textvariable=self.sc_t, width=6).grid(row=0, column=5, padx=4)
        ttk.Button(ao_box, text="Add", command=self._add_occ).grid(row=0, column=6, padx=8)
        ttk.Button(ao_box, text="Remove selected", command=self._remove_occ).grid(row=0, column=7, padx=4)

        self.occ_list = tk.Listbox(f, height=8, font=("Courier", 10))
        self.occ_list.pack(fill="both", expand=True, padx=8, pady=4)

    def _add_obs(self):
        try:
            lits = parse_literal_set(self.sc_obs_lits.get())
            for l in lits:
                if l.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {l.fluent!r}.")
            t = int(self.sc_obs_t.get())
            if not (0 <= t <= self.sig.T):
                raise ValueError(f"t must be in [0, {self.sig.T}].")
            self.Sc.observations.append(Observation(lits, t))
            self._refresh_obs_list()
            self._set_status(f"Observation added at t={t}.")
        except Exception as e:
            messagebox.showerror("Observation error", str(e))

    def _remove_obs(self):
        sel = self.obs_list.curselection()
        if sel:
            self.Sc.observations.pop(sel[0])
            self._refresh_obs_list()

    def _refresh_obs_list(self):
        self.obs_list.delete(0, "end")
        for o in self.Sc.observations:
            lits = "{" + ", ".join(str(l) for l in o.literals) + "}" if o.literals else "{}"
            self.obs_list.insert("end", f"({lits}, t={o.t})")

    def _add_occ(self):
        try:
            a = self.sc_action.get().strip()
            ag = self.sc_agent.get().strip()
            t = int(self.sc_t.get())
            if a not in self.sig.actions:
                raise ValueError("Unknown action.")
            if ag not in self.sig.agents:
                raise ValueError("Unknown agent.")
            if not (0 <= t <= self.sig.T):
                raise ValueError(f"t must be in [0, {self.sig.T}].")
            if any(o.t == t for o in self.Sc.occurrences):
                raise ValueError(f"Another action already occurs at t={t} (sequential actions only).")
            self.Sc.occurrences.append(ActionOccurrence(a, ag, t))
            self.Sc.occurrences.sort(key=lambda o: o.t)
            self._refresh_occ_list()
            self._set_status(f"Action occurrence added: ({a}, {ag}, {t}).")
        except Exception as e:
            messagebox.showerror("Action occurrence error", str(e))

    def _remove_occ(self):
        sel = self.occ_list.curselection()
        if sel:
            self.Sc.occurrences.pop(sel[0])
            self._refresh_occ_list()

    def _refresh_occ_list(self):
        self.occ_list.delete(0, "end")
        for o in self.Sc.occurrences:
            self.occ_list.insert("end", f"({o.action}, {o.agent}, t={o.t})")

    # ----- Tab 4: Query & run -----
    def _build_query_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="4. Query & run")

        top = ttk.LabelFrame(f, text="Build the model")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Build model & show trajectory",
                   command=self._build_and_show).pack(side="left", padx=8, pady=6)
        ttk.Button(top, text="Clear output",
                   command=lambda: self.out.delete("1.0", "end")).pack(side="left", padx=4)

        q1 = ttk.LabelFrame(f, text="Query 1:  holds a at t when Sc")
        q1.pack(fill="x", padx=8, pady=6)
        ttk.Label(q1, text="Literals a:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.q_lits = tk.StringVar()
        ttk.Entry(q1, textvariable=self.q_lits, width=30).grid(row=0, column=1, padx=4)
        ttk.Label(q1, text="t:").grid(row=0, column=2, sticky="e", padx=4)
        self.q_t = tk.IntVar(value=0)
        ttk.Spinbox(q1, from_=0, to=50, textvariable=self.q_t, width=6).grid(row=0, column=3, padx=4)
        ttk.Button(q1, text="Ask", command=self._ask_holds).grid(row=0, column=4, padx=8)

        q2 = ttk.LabelFrame(f, text="Query 2:  involved ag in Sc")
        q2.pack(fill="x", padx=8, pady=6)
        ttk.Label(q2, text="Agent:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.q_agent = ttk.Combobox(q2, width=14, state="readonly")
        self.q_agent.grid(row=0, column=1, padx=4)
        ttk.Button(q2, text="Ask", command=self._ask_involved).grid(row=0, column=2, padx=8)

        out_box = ttk.LabelFrame(f, text="Output")
        out_box.pack(fill="both", expand=True, padx=8, pady=8)
        self.out = scrolledtext.ScrolledText(out_box, font=("Courier New", 10), wrap="none", height=18)
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

        self.out.insert("end", "Model built. Trajectory:\n\n")
        self._print_trajectory()
        self._set_status("Model built successfully.")

    def _print_trajectory(self):
        m = self.model
        T = self.sig.T
        fluents = sorted(self.sig.fluents)
        col_w = 6
        head = f"{'t':<12}" + "".join(f"{t:>{col_w}}" for t in range(0, T + 1))
        self.out.insert("end", head + "\n")
        acs_by_t = {o.t: o for o in self.Sc.occurrences}
        action_row = f"{'action':<12}"
        for t in range(0, T + 1):
            occ = acs_by_t.get(t)
            cell = (occ.action[:col_w-1] if occ else "-")
            action_row += f"{cell:>{col_w}}"
        self.out.insert("end", action_row + "\n")
        agent_row = f"{'agent':<12}"
        for t in range(0, T + 1):
            occ = acs_by_t.get(t)
            cell = (occ.agent[:col_w-1] if occ else "-")
            agent_row += f"{cell:>{col_w}}"
        self.out.insert("end", agent_row + "\n")
        self.out.insert("end", "-" * (12 + col_w * (T + 1)) + "\n")
        for f in fluents:
            row = f"{f:<12}"
            for t in range(0, T + 1):
                row += f"{m.H[(f, t)]:>{col_w}}"
            self.out.insert("end", row + "\n")
        self.out.insert("end", "\nOcclusion O(A, t+1) (non-empty entries only):\n")
        any_o = False
        for (a, t), fs in sorted(m.O.items()):
            if fs:
                self.out.insert("end", f"  O({a}, {t}) = {{{', '.join(sorted(fs))}}}\n")
                any_o = True
        if not any_o:
            self.out.insert("end", "  (all empty)\n")

    def _ask_holds(self):
        if self.model is None:
            messagebox.showinfo("No model", "Build the model first.")
            return
        try:
            lits = parse_literal_set(self.q_lits.get())
            for l in lits:
                if l.fluent not in self.sig.fluents:
                    raise ValueError(f"Unknown fluent {l.fluent!r}.")
            t = int(self.q_t.get())
            res = query_holds(self.model, lits, t)
            lit_str = "{" + ", ".join(str(l) for l in lits) + "}" if lits else "{}"
            verdict = "YES" if res else "NO"
            self.out.insert("end", f"\n[holds {lit_str} at {t} when Sc]  {verdict}\n")
            self.out.see("end")
        except Exception as e:
            messagebox.showerror("Query error", str(e))

    def _ask_involved(self):
        if self.model is None:
            messagebox.showinfo("No model", "Build the model first.")
            return
        ag = self.q_agent.get().strip()
        res = query_involved(self.model, ag)
        verdict = "YES (has at least one action with non-empty effect)" if res else "NO"
        self.out.insert("end", f"\n[involved {ag} in Sc]  {verdict}\n")
        self.out.see("end")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _set_status(self, msg: str):
        self.status.set(msg)


if __name__ == "__main__":
    App().mainloop()
