from collections import defaultdict
import graphviz

class RG_NFA_Converter:
    def __init__(self):
        pass

    def parse_grammar(self, text, is_right_linear=True):
        # Returns a dict: {'S': ['aA', 'b'], ...} and start symbol
        grammar = defaultdict(list)
        start_symbol = None
        non_terminals = set()
        terminals = set()
        
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or "->" not in line:
                continue
            lhs, rhs_part = line.split("->")
            lhs = lhs.strip()
            if not start_symbol:
                start_symbol = lhs
            non_terminals.add(lhs)
            
            prods = [p.strip() for p in rhs_part.split('|')]
            for p in prods:
                grammar[lhs].append(p)
                for char in p:
                    if not char.isupper() and char != '@':
                        terminals.add(char)
        
        return {
            "prods": grammar,
            "start": start_symbol,
            "non_terminals": sorted(list(non_terminals)),
            "terminals": sorted(list(terminals)),
            "is_right_linear": is_right_linear
        }

    def right_grammar_to_nfa(self, grammar_info):
        # States: Non-terminals + Final State (let's call it 'Z')
        # Transitions: 
        # A -> aB  =>  (A, a) -> B
        # A -> a   =>  (A, a) -> Z
        # A -> @   =>  A is final
        
        prods = grammar_info['prods']
        start = grammar_info['start']
        
        # Map NT to integers
        nt_list = grammar_info['non_terminals']
        state_map = {nt: i for i, nt in enumerate(nt_list)}
        final_state_idx = len(nt_list)
        state_map['Z'] = final_state_idx # Virtual final state
        
        n_states = len(nt_list) + 1
        transitions = defaultdict(list) # (from, input) -> [to_list]
        final_states = set()
        final_states.add(final_state_idx)
        
        # If start symbol not in NT list (should not happen if parsed correctly)
        if start not in state_map:
            return None

        start_idx = state_map[start]
        
        for lhs, rhs_list in prods.items():
            u = state_map[lhs]
            for rhs in rhs_list:
                if rhs == '@':
                    final_states.add(u)
                elif len(rhs) == 1 and rhs.islower(): # A -> a
                    a = rhs
                    v = final_state_idx
                    transitions[(u, a)].append(v)
                elif len(rhs) == 2 and rhs[0].islower() and rhs[1].isupper(): # A -> aB
                    a = rhs[0]
                    b = rhs[1]
                    if b in state_map:
                        v = state_map[b]
                        transitions[(u, a)].append(v)
                else:
                    # Handle cases like A -> B (unit production) or A -> abc
                    # For simplicity, assuming strict regular grammar form A->aB or A->a or A->@
                    pass
                    
        return {
            "n_states": n_states,
            "start": start_idx,
            "finals": final_states,
            "transitions": transitions,
            "state_map_rev": {v: k for k, v in state_map.items()}
        }

    def nfa_to_dot(self, nfa):
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR')
        
        # Nodes
        for i in range(nfa['n_states']):
            label = nfa['state_map_rev'].get(i, str(i))
            shape = 'doublecircle' if i in nfa['finals'] else 'circle'
            dot.node(str(i), label=label, shape=shape)
            
        # Start arrow
        dot.node('start', shape='point')
        dot.edge('start', str(nfa['start']))
        
        # Edges
        for (u, a), v_list in nfa['transitions'].items():
            for v in v_list:
                dot.edge(str(u), str(v), label=a)
                
        return dot
