# Action Language with Agents

A GUI tool for reasoning about actions, agents, and their effects over time using a simple action language formalism.

## Requirements

Python 3.10+ with `tkinter`

## Run

```bash
python alag_app.py
```

## Usage

The interface has four tabs:

1. **Signature** - define fluents, actions, agents, and time T
2. **Domain description** - add effect statements: `A causes E if P by ag`
3. **Scenario** - add observations `(literals, t)` and action occurrences `(action, agent, t)`
4. **Query & run** - build the model and run queries:
   - `holds a at t` - are literals `a` true at time `t`?
   - `involved ag` - did agent `ag` cause at least one non empty effect?

## Notation

- Positive literal: `f`
- Negative literal: `~f`
- Multiple literals: comma separated, e.g. `f1, ~f2`
