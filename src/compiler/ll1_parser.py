from collections import defaultdict

class LL1Parser:
    def __init__(self):
        self.grammar = {}
        self.start_symbol = ''
        self.terminals = set()
        self.non_terminals = set()
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.table = {}
        
    def parse_grammar(self, text):
        self.grammar = defaultdict(list)
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = None
        
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or "->" not in line:
                continue
            lhs, rhs_part = line.split("->")
            lhs = lhs.strip()
            if not self.start_symbol:
                self.start_symbol = lhs
            self.non_terminals.add(lhs)
            
            # Split by |
            alts = [x.strip() for x in rhs_part.split('|')]
            for alt in alts:
                # Split symbols in RHS. 
                # Simple assumption: Non-terminals are Uppercase (or start with _), Terminals are others.
                # But user might input E', _E. 
                # Let's use a simple tokenizer for the RHS or assume space separated if complex?
                # The original python code used lists: ['T', '_E'].
                # Let's try to parse "T _E" or "T_E" or "i".
                # For simplicity, let's assume standard single char terminals/non-terminals OR space separated.
                # If no spaces, we treat each char as symbol unless it's a known multi-char convention like E'.
                # To be robust, let's ask user to space separate if ambiguous, but here we try to be smart.
                
                # Heuristic: if string contains spaces, split by space.
                if ' ' in alt:
                    symbols = alt.split()
                else:
                    # If no spaces, treat each char as symbol, EXCEPT if we detect ' after a char
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
                
                self.grammar[lhs].append(symbols)
                for s in symbols:
                    if s != '^': # ^ is epsilon
                        # If it's not a non-terminal (we don't know all NTs yet, but we can infer)
                        pass 

        # Identify terminals: anything in RHS that is not in LHS keys and not ^
        for lhs in self.grammar:
            for rhs in self.grammar[lhs]:
                for sym in rhs:
                    if sym not in self.grammar and sym != '^':
                        self.terminals.add(sym)
        
        # Also add #
        self.terminals.add('#')

    def compute_first(self):
        self.first = defaultdict(set)
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    # rhs is a list of symbols
                    # First(lhs) includes First(rhs)
                    
                    # If rhs is empty or ^
                    if rhs == ['^']:
                        if '^' not in self.first[lhs]:
                            self.first[lhs].add('^')
                            changed = True
                        continue
                    
                    # Calculate First(rhs)
                    rhs_has_epsilon = True
                    for sym in rhs:
                        # First(sym)
                        sym_first = set()
                        if sym in self.terminals:
                            sym_first.add(sym)
                        elif sym in self.grammar:
                            sym_first = self.first[sym]
                        
                        # Add First(sym) - {^} to First(lhs)
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
        self.follow[self.start_symbol].add('#')
        
        changed = True
        while changed:
            changed = False
            for lhs in self.grammar:
                for rhs in self.grammar[lhs]:
                    # A -> alpha B beta
                    for i, sym in enumerate(rhs):
                        if sym in self.non_terminals:
                            # Calculate First(beta)
                            beta_first = set()
                            beta_has_epsilon = True
                            
                            # beta is rhs[i+1:]
                            if i + 1 < len(rhs):
                                # Compute First of the rest
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
                                # beta is empty, so it has epsilon
                                pass
                            
                            # Add First(beta) - {^} to Follow(sym)
                            for f in beta_first:
                                if f not in self.follow[sym]:
                                    self.follow[sym].add(f)
                                    changed = True
                            
                            # If beta => ^, add Follow(lhs) to Follow(sym)
                            if beta_has_epsilon:
                                for f in self.follow[lhs]:
                                    if f not in self.follow[sym]:
                                        self.follow[sym].add(f)
                                        changed = True

    def build_table(self):
        self.table = defaultdict(dict)
        for lhs in self.grammar:
            for rhs in self.grammar[lhs]:
                # Calculate First(rhs)
                rhs_first = set()
                rhs_has_epsilon = True
                
                if rhs == ['^']:
                    pass # handled by epsilon check
                else:
                    for sym in rhs:
                        sym_first = set()
                        if sym in self.terminals:
                            sym_first.add(sym)
                        elif sym in self.grammar:
                            sym_first = self.first[sym]
                        
                        for f in sym_first:
                            if f != '^':
                                rhs_first.add(f)
                        
                        if '^' not in sym_first:
                            rhs_has_epsilon = False
                            break
                
                # Rule 1: For each a in First(rhs), add A->rhs to M[A, a]
                for a in rhs_first:
                    if a in self.table[lhs]:
                        # Conflict
                        pass 
                    self.table[lhs][a] = rhs
                
                # Rule 2: If ^ in First(rhs), for each b in Follow(A), add A->rhs to M[A, b]
                if rhs_has_epsilon:
                    for b in self.follow[lhs]:
                        self.table[lhs][b] = rhs

    def parse(self, input_string):
        # input_string should end with #
        if not input_string.endswith('#'):
            input_string += '#'
            
        stack = ['#', self.start_symbol]
        index = 0
        steps = []
        
        # Tokenize input simply (char by char for now, or match terminals)
        # To match the LL1.py logic, let's assume single char terminals unless specified otherwise.
        # But wait, input might be "i+i*i#".
        # We need to match tokens from terminals set.
        
        # Simple tokenizer for the parser
        tokens = []
        i = 0
        while i < len(input_string):
            # Try to match the longest terminal
            matched = False
            # Sort terminals by length desc to match longest first
            sorted_terms = sorted(list(self.terminals), key=len, reverse=True)
            
            for t in sorted_terms:
                if input_string[i:].startswith(t):
                    tokens.append(t)
                    i += len(t)
                    matched = True
                    break
            if not matched:
                # Skip unknown or error?
                # For now just take char
                tokens.append(input_string[i])
                i += 1
        
        idx = 0
        while len(stack) > 0:
            top = stack[-1]
            current_token = tokens[idx] if idx < len(tokens) else None
            
            step_info = {
                "stack": "".join(stack),
                "input": "".join(tokens[idx:]),
                "action": ""
            }
            
            if top == current_token:
                if top == '#':
                    step_info["action"] = "Accept"
                    steps.append(step_info)
                    break
                else:
                    step_info["action"] = f"Match {top}"
                    stack.pop()
                    idx += 1
            elif top in self.terminals:
                step_info["action"] = "Error"
                steps.append(step_info)
                break
            elif top in self.table and current_token in self.table[top]:
                prod = self.table[top][current_token]
                step_info["action"] = f"{top} -> {''.join(prod)}"
                stack.pop()
                if prod != ['^']:
                    for sym in reversed(prod):
                        stack.append(sym)
            else:
                step_info["action"] = "Error"
                steps.append(step_info)
                break
            
            steps.append(step_info)
            
        return steps
