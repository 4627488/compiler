from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional


class SLRParser:
    """
    SLR(1) Parser implementation matching the C++ slr.cpp logic.
    """
    EPSILON = '^'
    END_SYMBOL = '#'

    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self.grammar: Dict[str, List[List[str]]] = defaultdict(list)
        self.productions: List[Tuple[str, Tuple[str, ...]]] = []  # indexed; 0 is augmented
        self.production_index: Dict[Tuple[str, Tuple[str, ...]], int] = {}
        self.start_symbol: str = ''
        self.augmented_start: str = ''
        self.terminals: Set[str] = set()
        self.non_terminals: Set[str] = set()
        self.first: Dict[str, Set[str]] = defaultdict(set)
        self.follow: Dict[str, Set[str]] = defaultdict(set)
        self.action_table: Dict[Tuple[int, str], Tuple] = {}
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self.states: List[frozenset] = []
        self.transitions: List[Dict[str, object]] = []
        self.conflicts: List[Dict[str, object]] = []

    # -------------------------------------------------------
    # Grammar parsing
    # -------------------------------------------------------
    def _split_rhs(self, alt: str) -> List[str]:
        """Split a RHS alternative into symbols. Supports either space-separated
        tokens or a compact form like i+i*i with optional primes."""
        alt = alt.strip()
        if alt == self.EPSILON or alt == 'ε':
            return [self.EPSILON]

        if ' ' in alt:
            return [sym for sym in alt.split() if sym]

        symbols: List[str] = []
        i = 0
        while i < len(alt):
            if alt[i].isspace():
                i += 1
                continue
            sym = alt[i]
            i += 1
            # Handle primes like E'
            while i < len(alt) and alt[i] == "'":
                sym += "'"
                i += 1
            # Handle multi-char identifiers like "id"
            if sym.isalpha() and sym.islower():
                while i < len(alt) and alt[i].isalnum():
                    sym += alt[i]
                    i += 1
            symbols.append(sym)
        return symbols

    def _is_non_terminal(self, sym: str) -> bool:
        """Check if symbol is a non-terminal (starts with uppercase letter)."""
        return len(sym) > 0 and sym[0].isupper()

    def parse_grammar(self, text: str):
        self._reset_state()

        lines = text.strip().split('\n')
        raw_productions: List[Tuple[str, List[str]]] = []

        for line in lines:
            line = line.strip()
            if not line or '->' not in line:
                continue
            lhs, rhs_part = line.split('->', 1)
            lhs = lhs.strip()
            if not self.start_symbol:
                self.start_symbol = lhs
            self.non_terminals.add(lhs)

            alternatives = [alt.strip() for alt in rhs_part.split('|') if alt.strip()]
            for alt in alternatives:
                symbols = self._split_rhs(alt)
                raw_productions.append((lhs, symbols))
                self.grammar[lhs].append(symbols)

        # Collect all non-terminals from RHS as well
        for lhs in list(self.grammar.keys()):
            for rhs in self.grammar[lhs]:
                for sym in rhs:
                    if self._is_non_terminal(sym):
                        self.non_terminals.add(sym)

        # Identify terminals (anything that's not a non-terminal and not epsilon)
        for lhs in self.grammar:
            for rhs in self.grammar[lhs]:
                for sym in rhs:
                    if sym != self.EPSILON and sym not in self.non_terminals:
                        self.terminals.add(sym)
        self.terminals.add(self.END_SYMBOL)

        # Augment grammar: S' -> S
        self.augmented_start = self.start_symbol + "'"
        while self.augmented_start in self.non_terminals:
            self.augmented_start += "'"
        self.non_terminals.add(self.augmented_start)
        self.grammar[self.augmented_start] = [[self.start_symbol]]

        # Build productions list: 0 is augmented rule
        self.productions = []
        self.production_index = {}
        self._add_production(self.augmented_start, tuple([self.start_symbol]))
        for lhs, rhs in raw_productions:
            self._add_production(lhs, tuple(rhs))

    def _add_production(self, lhs: str, rhs: Tuple[str, ...]):
        idx = len(self.productions)
        self.productions.append((lhs, rhs))
        self.production_index[(lhs, rhs)] = idx

    # -------------------------------------------------------
    # FIRST & FOLLOW
    # -------------------------------------------------------
    def compute_first(self):
        self.first = defaultdict(set)
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    # Handle epsilon production
                    if rhs == [self.EPSILON]:
                        if self.EPSILON not in self.first[lhs]:
                            self.first[lhs].add(self.EPSILON)
                            changed = True
                        continue

                    all_can_eps = True
                    for sym in rhs:
                        if sym == self.EPSILON:
                            continue
                        if sym in self.terminals:
                            if sym not in self.first[lhs]:
                                self.first[lhs].add(sym)
                                changed = True
                            all_can_eps = False
                            break
                        if sym in self.non_terminals:
                            before = len(self.first[lhs])
                            self.first[lhs] |= {x for x in self.first[sym] if x != self.EPSILON}
                            if len(self.first[lhs]) != before:
                                changed = True
                            if self.EPSILON not in self.first[sym]:
                                all_can_eps = False
                                break
                        else:
                            # Unknown symbol, treat as terminal
                            if sym not in self.first[lhs]:
                                self.first[lhs].add(sym)
                                changed = True
                            all_can_eps = False
                            break

                    if all_can_eps:
                        if self.EPSILON not in self.first[lhs]:
                            self.first[lhs].add(self.EPSILON)
                            changed = True

    def compute_follow(self):
        self.follow = defaultdict(set)
        # Add # to FOLLOW of augmented start symbol (like C++ does with $)
        self.follow[self.augmented_start].add(self.END_SYMBOL)
        # Also add to original start symbol
        self.follow[self.start_symbol].add(self.END_SYMBOL)

        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    for i, sym in enumerate(rhs):
                        if sym not in self.non_terminals:
                            continue

                        # Case 1: A -> αBβ, add FIRST(β) - {ε} to FOLLOW(B)
                        trailer = rhs[i + 1:]
                        first_beta = self._first_of_sequence(trailer)

                        before = len(self.follow[sym])
                        self.follow[sym] |= {x for x in first_beta if x != self.EPSILON}
                        if len(self.follow[sym]) != before:
                            changed = True

                        # Case 2: A -> αB or A -> αBβ where ε ∈ FIRST(β)
                        # Add FOLLOW(A) to FOLLOW(B)
                        if not trailer or self.EPSILON in first_beta:
                            before = len(self.follow[sym])
                            self.follow[sym] |= self.follow[lhs]
                            if len(self.follow[sym]) != before:
                                changed = True

    def _first_of_sequence(self, seq: List[str]) -> Set[str]:
        result: Set[str] = set()
        if not seq:
            result.add(self.EPSILON)
            return result
        for sym in seq:
            if sym == self.EPSILON:
                continue
            if sym in self.terminals:
                result.add(sym)
                return result
            if sym in self.non_terminals:
                result |= {x for x in self.first[sym] if x != self.EPSILON}
                if self.EPSILON not in self.first[sym]:
                    return result
            else:
                result.add(sym)
                return result
        result.add(self.EPSILON)
        return result

    # -------------------------------------------------------
    # LR(0) items & canonical collection
    # -------------------------------------------------------
    def closure(self, items: Set[Tuple[str, Tuple[str, ...], int]]) -> frozenset:
        """Compute closure of a set of LR(0) items."""
        closure_set = set(items)
        added_left = set()  # Track which non-terminals we've added items for

        changed = True
        while changed:
            changed = False
            new_items = set()
            for (lhs, rhs, dot) in list(closure_set):
                if dot < len(rhs):
                    symbol = rhs[dot]
                    if symbol in self.non_terminals and symbol not in added_left:
                        added_left.add(symbol)
                        # Add all productions for this non-terminal
                        for prod_rhs in self.grammar[symbol]:
                            if prod_rhs == [self.EPSILON]:
                                item = (symbol, tuple(), 0)
                            else:
                                item = (symbol, tuple(prod_rhs), 0)
                            if item not in closure_set:
                                new_items.add(item)
            if new_items:
                closure_set.update(new_items)
                changed = True
        return frozenset(closure_set)

    def goto(self, items: frozenset, symbol: str) -> frozenset:
        """Compute GOTO(items, symbol)."""
        moved = set()
        for (lhs, rhs, dot) in items:
            if dot < len(rhs) and rhs[dot] == symbol:
                moved.add((lhs, rhs, dot + 1))
        return self.closure(moved) if moved else frozenset()

    def canonical_collection(self):
        """Build the canonical collection of LR(0) item sets."""
        # Initial item: S' -> .S
        start_rhs = tuple([self.start_symbol])
        start_item = (self.augmented_start, start_rhs, 0)
        i0 = self.closure({start_item})

        self.states = [i0]
        state_map = {i0: 0}
        self.transitions = []

        queue = [0]
        while queue:
            cur_idx = queue.pop(0)
            state_items = self.states[cur_idx]

            # Collect all symbols that appear after the dot
            symbols = set()
            for (lhs, rhs, dot) in state_items:
                if dot < len(rhs):
                    symbols.add(rhs[dot])

            for sym in symbols:
                next_state = self.goto(state_items, sym)
                if not next_state:
                    continue

                if next_state not in state_map:
                    state_map[next_state] = len(self.states)
                    self.states.append(next_state)
                    queue.append(state_map[next_state])

                to_idx = state_map[next_state]
                is_terminal = sym in self.terminals
                self.transitions.append({
                    "from": cur_idx,
                    "symbol": sym,
                    "to": to_idx,
                    "kind": 'T' if is_terminal else 'N'
                })

    # -------------------------------------------------------
    # Parsing table construction
    # -------------------------------------------------------
    def build_table(self):
        self.action_table = {}
        self.goto_table = {}
        self.conflicts = []

        self.compute_first()
        self.compute_follow()
        self.canonical_collection()

        cell_actions: Dict[Tuple[int, str], List[Tuple]] = defaultdict(list)

        for state_idx, state_items in enumerate(self.states):
            for (lhs, rhs, dot) in state_items:
                if dot < len(rhs):
                    # Shift or goto
                    symbol = rhs[dot]
                    next_state = self._find_transition(state_idx, symbol)
                    if next_state is not None:
                        if symbol in self.terminals:
                            # Shift action
                            cell_actions[(state_idx, symbol)].append(('shift', next_state))
                        else:
                            # Goto (non-terminal)
                            self.goto_table[(state_idx, symbol)] = next_state
                else:
                    # Dot at end - reduce or accept
                    if lhs == self.augmented_start:
                        # Accept
                        cell_actions[(state_idx, self.END_SYMBOL)].append(('accept',))
                    else:
                        # Reduce
                        prod_idx = self._production_lookup(lhs, rhs)
                        if prod_idx != -1:
                            for terminal in self.follow[lhs]:
                                cell_actions[(state_idx, terminal)].append(('reduce', prod_idx))

        # Resolve conflicts and fill action table
        for key, actions in cell_actions.items():
            if len(actions) > 1:
                kinds = {a[0] for a in actions}
                if 'shift' in kinds and 'reduce' in kinds:
                    conflict_kind = 'shift/reduce'
                elif kinds == {'reduce'}:
                    conflict_kind = 'reduce/reduce'
                else:
                    conflict_kind = 'ambiguous'
                self.conflicts.append({
                    "state": key[0],
                    "symbol": key[1],
                    "actions": actions,
                    "kind": conflict_kind
                })

            # Select action (prefer shift over reduce)
            chosen = self._select_action(actions)
            if chosen:
                self.action_table[key] = chosen

    def _find_transition(self, from_state: int, symbol: str) -> Optional[int]:
        for t in self.transitions:
            if t["from"] == from_state and t["symbol"] == symbol:
                return t["to"]
        return None

    def _production_lookup(self, lhs: str, rhs: Tuple[str, ...]) -> int:
        key = (lhs, rhs)
        if key in self.production_index:
            return self.production_index[key]
        # Handle epsilon case
        if rhs == ():
            key = (lhs, (self.EPSILON,))
            return self.production_index.get(key, -1)
        return -1

    def _select_action(self, actions: List[Tuple]) -> Optional[Tuple]:
        if not actions:
            return None
        # Prefer shift over reduce
        for a in actions:
            if a[0] == 'shift':
                return a
        return actions[0]

    def is_slr(self) -> bool:
        return len(self.conflicts) == 0

    # -------------------------------------------------------
    # Display helpers for UI
    # -------------------------------------------------------
    def _format_action(self, action: Tuple) -> str:
        if not action:
            return ''
        kind = action[0]
        if kind == 'shift':
            return f"s{action[1]}"
        if kind == 'reduce':
            return f"r{action[1]}"
        if kind == 'accept':
            return 'acc'
        return 'err'

    def _format_action_verbose(self, action: Tuple) -> str:
        if not action:
            return ''
        kind = action[0]
        if kind == 'shift':
            return f"s{action[1]}"
        if kind == 'reduce':
            lhs, rhs = self.productions[action[1]]
            rhs_str = ' '.join(rhs) if rhs != (self.EPSILON,) and rhs != () else self.EPSILON
            return f"r{action[1]} ({lhs} -> {rhs_str})"
        if kind == 'accept':
            return 'acc'
        return 'err'

    def get_productions_display(self) -> List[Dict[str, object]]:
        """Get all productions for display, including augmented."""
        display = []
        for idx, (lhs, rhs) in enumerate(self.productions):
            rhs_str = ' '.join(rhs) if rhs and rhs != (self.EPSILON,) else self.EPSILON
            display.append({"Index": idx, "Production": f"{lhs} -> {rhs_str}"})
        return display

    def get_states_display(self) -> List[Dict[str, object]]:
        """Get canonical collection items for display."""
        rows = []
        for idx, state in enumerate(self.states):
            items_str = []
            sorted_items = sorted(state, key=lambda x: (x[0], x[1], x[2]))
            for (lhs, rhs, dot) in sorted_items:
                rhs_list = list(rhs)
                rhs_list.insert(dot, '·')
                if not rhs_list:
                    rhs_list = ['·']
                items_str.append(f"{lhs} -> {' '.join(rhs_list)}")
            rows.append({"State": f"I{idx}", "Items": '\n'.join(items_str)})
        return rows

    def get_parsing_table_matrix(self):
        """Get ACTION and GOTO table as matrix for display."""
        action_syms = sorted(self.terminals)
        goto_syms = sorted(nt for nt in self.non_terminals if nt != self.augmented_start)

        rows = []
        for state_idx in range(len(self.states)):
            row = {"State": f"I{state_idx}"}
            for sym in action_syms:
                action = self.action_table.get((state_idx, sym))
                row[sym] = self._format_action(action) if action else ''
            for sym in goto_syms:
                val = self.goto_table.get((state_idx, sym))
                row[sym] = f"{val}" if val is not None else ''
            rows.append(row)
        return action_syms, goto_syms, rows

    def get_transitions_display(self) -> List[Dict[str, str]]:
        """Get transitions for display."""
        rows = []
        for t in self.transitions:
            rows.append({
                "From": f"I{t['from']}",
                "Symbol": t['symbol'],
                "To": f"I{t['to']}",
                "Type": "Terminal" if t['kind'] == 'T' else "Non-Terminal"
            })
        return rows

    # -------------------------------------------------------
    # Parsing
    # -------------------------------------------------------
    def _tokenize(self, input_string: str) -> List[str]:
        s = input_string.strip()
        if not s.endswith(self.END_SYMBOL):
            s += self.END_SYMBOL
        tokens: List[str] = []
        i = 0
        terminal_list = sorted(self.terminals, key=len, reverse=True)
        while i < len(s):
            if s[i].isspace():
                i += 1
                continue
            matched = False
            for term in terminal_list:
                if s[i:].startswith(term):
                    tokens.append(term)
                    i += len(term)
                    matched = True
                    break
            if not matched:
                tokens.append(s[i])
                i += 1
        return tokens

    def parse(self, input_string: str) -> List[Dict[str, str]]:
        """Parse input string and return step-by-step trace."""
        if not self.action_table:
            raise ValueError("Parsing table has not been built. Call build_table() first.")

        tokens = self._tokenize(input_string)

        # Two stacks like C++: state stack and symbol stack
        state_stack: List[int] = [0]
        symbol_stack: List[str] = [self.END_SYMBOL]

        idx = 0
        steps: List[Dict[str, str]] = []
        step_count = 0

        while True:
            step_count += 1
            state = state_stack[-1]
            lookahead = tokens[idx] if idx < len(tokens) else self.END_SYMBOL

            # Format stacks for display
            state_str = ' '.join(f"I{s}" for s in state_stack)
            symbol_str = ' '.join(symbol_stack)
            remaining = ''.join(tokens[idx:])

            action = self.action_table.get((state, lookahead))

            step_info = {
                "Step": str(step_count),
                "State Stack": state_str,
                "Symbol Stack": symbol_str,
                "Input": remaining,
                "Action": "",
                "ACTION": "",
                "GOTO": ""
            }

            if not action:
                step_info["Action"] = "Error"
                steps.append(step_info)
                break

            if action[0] == 'shift':
                next_state = action[1]
                step_info["Action"] = "Shift"
                step_info["ACTION"] = f"s{next_state}"
                steps.append(step_info)

                state_stack.append(next_state)
                symbol_stack.append(lookahead)
                idx += 1

            elif action[0] == 'reduce':
                prod_idx = action[1]
                lhs, rhs = self.productions[prod_idx]
                rhs_len = 0 if rhs == (self.EPSILON,) or rhs == () else len(rhs)

                rhs_str = ' '.join(rhs) if rhs and rhs != (self.EPSILON,) else self.EPSILON
                step_info["Action"] = f"Reduce: {lhs} -> {rhs_str}"
                step_info["ACTION"] = f"r{prod_idx}"

                # Pop from stacks
                for _ in range(rhs_len):
                    if len(state_stack) > 1:
                        state_stack.pop()
                    if len(symbol_stack) > 1:
                        symbol_stack.pop()

                # Look up GOTO
                top_state = state_stack[-1]
                goto_state = self.goto_table.get((top_state, lhs))
                if goto_state is None:
                    step_info["GOTO"] = "Error"
                    steps.append(step_info)
                    break

                step_info["GOTO"] = f"{goto_state}"
                steps.append(step_info)

                state_stack.append(goto_state)
                symbol_stack.append(lhs)

            elif action[0] == 'accept':
                step_info["Action"] = "Accept ✓"
                step_info["ACTION"] = "acc"
                steps.append(step_info)
                break

            else:
                step_info["Action"] = "Error"
                steps.append(step_info)
                break

        return steps
