# Action Language with Agents — poprawiony program

## Uruchomienie GUI

```bash
python alag_app.py
```

Program składa się z trzech plików kodu:

- `alag_engine.py` — silnik semantyki, budowanie modeli i obsługa zapytań Q1/Q2,
- `alag_app.py` — aplikacja Tkinter z formularzami i przykładami,
- `example_tests.py` — testy regresyjne/przykłady do szybkiego sprawdzenia silnika.

## Gotowe przykłady w programie

Po uruchomieniu programu pierwsza zakładka to **0. PRZYKŁADY**. Wybierasz przykład z listy i klikasz:

- **Wczytaj przykład** — program uzupełnia `F`, `Ac`, `Ag`, `T`, reguły `causes`, obserwacje, akcje oraz domyślne query.
- **Wczytaj przykład + zbuduj** — robi to samo, od razu buduje modele i dla spójnych scenariuszy automatycznie wypisuje domyślne odpowiedzi na Q1/Q2.

Dwuklik na nazwie przykładu także wczytuje go i od razu buduje model. Ten sam wybór przykładu jest dostępny w zakładce **1. Signature** pod polami sygnatury.

Przykłady obejmują:

1. `a by Agent causes f` — prosty efekt, Q1 i Q2 `involved`.
2. Wiele reguł `causes` dla jednej akcji i jednego agenta.
3. Wsteczne zawężanie modeli przez późniejszą obserwację i inercję (`wait`).
4. Sprzeczne obserwacje po samych akcjach `wait`.
5. Sprzeczne efekty `f` i `~f`, gdy warunki `g` i `h` zachodzą razem.
6. Brak sprzeczności, gdy odpala tylko jedna z warunkowych reguł.
7. Agent bez pasującej reguły dla akcji — pusty efekt i `involved = NO`.
8. Jawne reguły tożsamości dla `wait`: `wait by bob causes stolen if stolen` oraz `wait by bob causes ~stolen if ~stolen`.
9. Wzajemnie sprzeczne obserwacje w tym samym timepoincie.
10. Akcja przygotowująca tworzy stan `g=true, h=true`, przez co późniejsza akcja ma sprzeczne efekty.
11. Te same sprzeczne reguły, ale bez odpalenia konfliktu; wydruk pokazuje minimalne `O`.
12. Kilka preconditions w jednej regule, np. `unlock by ag causes opened if has_key, near_door, ~blocked`.
13. Kilka preconditions, ale jedna niespełniona — akcja wykonuje się z pustym efektem.

Uwaga praktyczna: część `if P` przyjmuje cały zbiór literałów. Wpisz warunki po przecinku albo spacjach, np. `g, h, ~p` lub `{g; h; ~p}`. Wszystkie muszą zachodzić w chwili wykonania akcji, żeby reguła odpaliła. W jednym timepoincie może być wiele obserwacji, o ile nie są sprzeczne, ale nie mogą startować dwie akcje, bo DS8 zakłada akcje sekwencyjne.

## Uruchomienie testów

```bash
python example_tests.py
```

Testy sprawdzają m.in. wiele `causes`, wiele preconditions w jednej regule, involved, wsteczne wnioskowanie przez inercję, sprzeczne obserwacje, sprzeczne skutki akcji, przypadek agenta bez efektu oraz wszystkie przykłady z GUI.

## Najważniejsze poprawki

- Dopuszczone jest wiele instrukcji `A by ag causes E if P` dla tej samej akcji/agenta; dodatkowo jedna instrukcja może mieć wiele preconditions w `P`, np. `if g, h, ~p`.
- Jeśli dwie odpalone reguły wymagają różnych wartości tego samego fluentu, scenariusz jest niespójny, bo funkcja `H` nie może mieć jednocześnie `f=0` i `f=1`.
- Obserwacje z przyszłych timepointów filtrują dopuszczalne stany początkowe, więc działa wnioskowanie „wstecz” przez inercję.
- Zasada inercji jest zachowana: poza minimalnym zbiorem `O(A,t+1)` wartości fluentów są kopiowane z poprzedniego timepointu.
- `involved ag in Sc` zwraca `YES` tylko wtedy, gdy w każdym modelu agent ma przynajmniej jedną akcję z niepustym minimalnym efektem/occlusion.
- Akcje mogą zaczynać się tylko w `t = 0, ..., T-1`, bo trwają jedną jednostkę czasu i kończą się w `t+1`.
- Przycisk **Wczytaj przykład + zbuduj** został sprawdzony i teraz po zbudowaniu dopisuje również domyślne Q1/Q2, żeby było od razu widać wynik.
