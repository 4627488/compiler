from collections import defaultdict

class SLRParser:
    def __init__(self):
        self.grammar = defaultdict(list)
        self.productions = []  # list of (lhs, rhs)
        self.start_symbol = ''
        self.terminals = set()
        self.non_terminals = set()
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.action_table = {}
        self.goto_table = {}
        self.states = []  # list of frozenset of items

    def parse_grammar(self, text):
        self.grammar = defaultdict(list)
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = None
        self.productions = []

        lines = text.strip().split('\n')
        parsed_rules = []

        for line in lines:
            line = line.strip()
            if not line or "->" not in line:
                continue
            lhs, rhs_part = line.split("->")
            lhs = lhs.strip()
            if not self.start_symbol:
                self.start_symbol = lhs
            self.non_terminals.add(lhs)

            alts = [x.strip() for x in rhs_part.split('|')]
            for alt in alts:
                if ' ' in alt:
                    symbols = alt.split()
                else:
                    symbols = []
                    i = 0
                    while i < len(alt):
                        sym = alt[i]
                        if i + 1 < len(alt) and alt[i+1] == "'":
                            sym += "'"
                            i += 2
                        else:
                            i += 1
                        symbols.append(sym)
                
                # Convert to tuple for hashability in items
                parsed_rules.append((lhs, tuple(symbols)))
                self.grammar[lhs].append(symbols)

        # Identify terminals
        for lhs in self.grammar:
            for rhs in self.grammar[lhs]:
                for sym in rhs:
                    if sym not in self.grammar and sym != '^':
                        self.terminals.add(sym)
        
        self.terminals.add('#')

        # Augment grammar
        original_start = self.start_symbol
        self.augmented_start = original_start + "'"
        while self.augmented_start in self.non_terminals:
             self.augmented_start += "'"
        
        self.non_terminals.add(self.augmented_start)
        self.grammar[self.augmented_start].append([original_start])
        
        # Rebuild productions list: 0 is augmented rule
        self.productions = [(self.augmented_start, (original_start,))]
        for lhs, rhs in parsed_rules:
            self.productions.append((lhs, rhs))

    def compute_first(self):
        self.first = defaultdict(set)
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    if rhs == ['^']:
                        if '^' not in self.first[lhs]:
                            self.first[lhs].add('^')
                            changed = True
                        continue
                    
                    rhs_has_epsilon = True
                    for sym in rhs:
                        sym_first = set()
                        if sym in self.terminals:
                            sym_first.add(sym)
                        elif sym in self.grammar:
                            sym_first = self.first[sym]
                        
                        for f in sym_first:
                            if f != '^':
                                if f not in self.first[lhs]:
                                    self.first[lhs].add(f)
                                    changed = True
                        
                        if '^' not in sym_first:
                            rhs_has_epsilon = False
                            break
                    
                    if rhs_has_epsilon:
                        if '^' not in self.first[lhs]:
                            self.first[lhs].add('^')
                            changed = True

    def compute_follow(self):
        self.follow = defaultdict(set)
        self.follow[self.start_symbol].add('#') # Original start symbol gets #
        # Augmented start symbol follow is empty or irrelevant for parsing table usually, 
        # but we parse starting from augmented rule.
        
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    for i, sym in enumerate(rhs):
                        if sym in self.non_terminals:
                            beta_first = set()
                            beta_has_epsilon = True
                            
                            if i + 1 < len(rhs):
                                for next_sym in rhs[i+1:]:
                                    next_first = set()
                                    if next_sym in self.terminals:
                                        next_first.add(next_sym)
                                    elif next_sym in self.grammar:
                                        next_first = self.first[next_sym]
                                    
                                    for f in next_first:
                                        if f != '^':
                                            beta_first.add(f)
                                    
                                    if '^' not in next_first:
                                        beta_has_epsilon = False
                                        break
                            else:
                                pass
                            
                            for f in beta_first:
                                if f not in self.follow[sym]:
                                    self.follow[sym].add(f)
                                    changed = True
                            
                            if beta_has_epsilon:
                                for f in self.follow[lhs]:
                                    if f not in self.follow[sym]:
                                        self.follow[sym].add(f)
                                        changed = True

    def closure(self, items):
        # items is a set of (lhs, rhs, dot_index)
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for (lhs, rhs, dot) in closure_set:
                if dot < len(rhs):
                    symbol = rhs[dot]
                    if symbol in self.non_terminals:
                        for prod_rhs in self.grammar[symbol]:
                            # Handle epsilon: if prod is ^, dot is at end? 
                            # Usually represented as empty rhs or special char.
                            # Here we use '^'. If rhs is ['^'], it effectively matches empty.
                            # But for LR items, A -> . means A -> epsilon.
                            # If our grammar has A -> ^, we should treat it as A -> . (empty tuple)
                            
                            actual_rhs = tuple(prod_rhs)
                            if actual_rhs == ('^',):
                                actual_rhs = ()
                            
                            item = (symbol, actual_rhs, 0)
                            if item not in closure_set:
                                new_items.add(item)
            
            if new_items:
                closure_set.update(new_items)
                changed = True
        return frozenset(closure_set)

    def goto(self, items, symbol):
        new_items = set()
        for (lhs, rhs, dot) in items:
            if dot < len(rhs) and rhs[dot] == symbol:
                new_items.add((lhs, rhs, dot + 1))
        return self.closure(new_items)

    def canonical_collection(self):
        # Initial item: S' -> . S
        start_prod_rhs = self.productions[0][1] # (S,)
        initial_item = (self.augmented_start, start_prod_rhs, 0)
        
        initial_state = self.closure({initial_item})
        self.states = [initial_state]
        
        # We need to map state (frozenset) to index
        state_map = {initial_state: 0}
        
        queue = [0]
        while queue:
            state_idx = queue.pop(0)
            state_items = self.states[state_idx]
            
            # Collect all symbols that can appear after dot
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
                    queue.append(len(self.states) - 1)
                
                next_state_idx = state_map[next_state]
                
                if sym in self.terminals:
                    self.action_table[(state_idx, sym)] = ('shift', next_state_idx)
                elif sym in self.non_terminals:
                    self.goto_table[(state_idx, sym)] = next_state_idx

    def build_table(self):
        self.compute_first()
        self.compute_follow()
        self.canonical_collection()
        
        # Add reduce actions and accept
        for i, state_items in enumerate(self.states):
            for (lhs, rhs, dot) in state_items:
                if dot == len(rhs): # Dot at end
                    if lhs == self.augmented_start:
                        self.action_table[(i, '#')] = ('accept',)
                    else:
                        # Reduce A -> alpha
                        # Find production index
                        # Note: rhs in items might be () if it was ^
                        # In productions list, we stored it as tuple of symbols, or ('^',) ?
                        # In parse_grammar, we stored ('^',) if it was ^.
                        # In closure, we converted ('^',) to ().
                        # So we need to match carefully.
                        
                        lookup_rhs = rhs
                        if len(rhs) == 0:
                            # It was epsilon production. In productions list it might be ('^',)
                            # Let's check how we stored it.
                            # In parse_grammar: self.grammar[lhs].append(symbols) -> symbols is ['^']
                            # self.productions.append((lhs, tuple(symbols))) -> (lhs, ('^',))
                            pass
                        
                        # Try to find (lhs, rhs) in self.productions
                        prod_idx = -1
                        for idx, (p_lhs, p_rhs) in enumerate(self.productions):
                            if p_lhs == lhs:
                                if p_rhs == ('^',) and rhs == ():
                                    prod_idx = idx
                                    break
                                if p_rhs == rhs:
                                    prod_idx = idx
                                    break
                        
                        if prod_idx != -1:
                            for a in self.follow[lhs]:
                                if (i, a) in self.action_table:
                                    # Conflict
                                    existing = self.action_table[(i, a)]
                                    # print(f"Conflict at state {i}, symbol {a}: {existing} vs reduce {prod_idx}")
                                    pass
                                self.action_table[(i, a)] = ('reduce', prod_idx)

    def parse(self, input_string):
        if not input_string.endswith('#'):
            input_string += '#'
            
        stack = [0]
        steps = []
        
        # Tokenize
        tokens = []
        i = 0
        while i < len(input_string):
            matched = False
            sorted_terms = sorted(list(self.terminals), key=len, reverse=True)
            for t in sorted_terms:
                if input_string[i:].startswith(t):
                    tokens.append(t)
                    i += len(t)
                    matched = True
                    break
            if not matched:
                tokens.append(input_string[i])
                i += 1
        
        idx = 0
        while True:
            state = stack[-1]
            current_token = tokens[idx] if idx < len(tokens) else None
            
            step_info = {
                "stack": str(stack),
                "input": "".join(tokens[idx:]),
                "action": ""
            }
            
            if (state, current_token) in self.action_table:
                action = self.action_table[(state, current_token)]
                if action[0] == 'shift':
                    step_info["action"] = f"Shift {action[1]}"
                    stack.append(current_token) # Push symbol (optional, usually just state is enough for logic, but for debug/output we might want it)
                    # Wait, standard LR stack is s0 X1 s1 X2 s2 ...
                    # My stack currently only has states? 
                    # Let's push symbol then state.
                    stack.append(action[1])
                    idx += 1
                elif action[0] == 'reduce':
                    prod_idx = action[1]
                    lhs, rhs = self.productions[prod_idx]
                    step_info["action"] = f"Reduce {lhs} -> {' '.join(rhs)}"
                    
                    # Pop 2 * |rhs| items
                    num_to_pop = 0
                    if rhs != ('^',):
                        num_to_pop = 2 * len(rhs)
                    
                    for _ in range(num_to_pop):
                        stack.pop()
                    
                    top_state = stack[-1]
                    if (top_state, lhs) in self.goto_table:
                        new_state = self.goto_table[(top_state, lhs)]
                        stack.append(lhs)
                        stack.append(new_state)
                    else:
                        step_info["action"] = "Error (Goto)"
                        steps.append(step_info)
                        break
                elif action[0] == 'accept':
                    step_info["action"] = "Accept"
                    steps.append(step_info)
                    break
            else:
                step_info["action"] = "Error"
                steps.append(step_info)
                break
            
            steps.append(step_info)
            
        return steps
