import unittest
from src.compiler.rg_nfa import RG_NFA_Converter

class TestRGNFAConverter(unittest.TestCase):
    def setUp(self):
        self.converter = RG_NFA_Converter()
        self.grammar_text = """
        S -> a A | b
        A -> a S | b
        """

    def test_parse_grammar(self):
        info = self.converter.parse_grammar(self.grammar_text)
        self.assertEqual(info['start'], 'S')
        self.assertIn('S', info['prods'])
        self.assertIn('A', info['prods'])
        self.assertIn('a', info['terminals'])
        self.assertIn('b', info['terminals'])

    def test_nfa_conversion(self):
        info = self.converter.parse_grammar(self.grammar_text)
        nfa = self.converter.right_grammar_to_nfa(info)
        
        # States: S, A, Z (final)
        # S -> aA => (S, a) -> A
        # S -> b => (S, b) -> Z
        # A -> aS => (A, a) -> S
        # A -> b => (A, b) -> Z
        
        self.assertIsNotNone(nfa)
        self.assertEqual(nfa['n_states'], 3) # S, A, Z
        
        # Check transitions
        # We need to know the indices.
        # Let's find index of S and A
        s_idx = -1
        a_idx = -1
        z_idx = -1
        
        for idx, name in nfa['state_map_rev'].items():
            if name == 'S': s_idx = idx
            elif name == 'A': a_idx = idx
            elif name == 'Z': z_idx = idx # Assuming Z is mapped to 'Z' or it's the extra state
            
        # Actually the code does: state_map['Z'] = final_state_idx
        # So we can find Z by checking finals
        self.assertEqual(len(nfa['finals']), 1)
        z_idx = list(nfa['finals'])[0]
        
        # Check transitions
        # (S, a) -> A
        self.assertIn(a_idx, nfa['transitions'][(s_idx, 'a')])
        # (S, b) -> Z
        self.assertIn(z_idx, nfa['transitions'][(s_idx, 'b')])
        # (A, a) -> S
        self.assertIn(s_idx, nfa['transitions'][(a_idx, 'a')])
        # (A, b) -> Z
        self.assertIn(z_idx, nfa['transitions'][(a_idx, 'b')])

if __name__ == '__main__':
    unittest.main()
