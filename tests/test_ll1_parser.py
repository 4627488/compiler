import unittest
from src.compiler.ll1_parser import LL1Parser

class TestLL1Parser(unittest.TestCase):
    def setUp(self):
        self.parser = LL1Parser()
        self.grammar_text = """
        E -> T E'
        E' -> + T E' | ^
        T -> F T'
        T' -> * F T' | ^
        F -> ( E ) | i
        """

    def test_parse_grammar(self):
        self.parser.parse_grammar(self.grammar_text)
        self.assertIn('E', self.parser.grammar)
        self.assertIn('E\'', self.parser.grammar)
        self.assertIn('T', self.parser.grammar)
        self.assertIn('T\'', self.parser.grammar)
        self.assertIn('F', self.parser.grammar)
        self.assertEqual(self.parser.start_symbol, 'E')
        self.assertIn('+', self.parser.terminals)
        self.assertIn('*', self.parser.terminals)
        self.assertIn('(', self.parser.terminals)
        self.assertIn(')', self.parser.terminals)
        self.assertIn('i', self.parser.terminals)

    def test_first_set(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.compute_first()
        
        # First(F) = {(, i}
        self.assertIn('(', self.parser.first['F'])
        self.assertIn('i', self.parser.first['F'])
        
        # First(T') = {*, ^}
        self.assertIn('*', self.parser.first['T\''])
        self.assertIn('^', self.parser.first['T\''])
        
        # First(E) = First(T) = First(F) = {(, i}
        self.assertIn('(', self.parser.first['E'])
        self.assertIn('i', self.parser.first['E'])

    def test_follow_set(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.compute_first()
        self.parser.compute_follow()
        
        # Follow(E) = {), #}
        self.assertIn(')', self.parser.follow['E'])
        self.assertIn('#', self.parser.follow['E'])
        
        # Follow(E') = Follow(E) = {), #}
        self.assertIn(')', self.parser.follow['E\''])
        self.assertIn('#', self.parser.follow['E\''])

    def test_parse_string(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.compute_first()
        self.parser.compute_follow()
        self.parser.build_table()
        
        input_str = "i+i*i"
        steps = self.parser.parse(input_str)
        
        # Check if the last step is Accept
        self.assertEqual(steps[-1]["action"], "Accept")

    def test_parse_error(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.compute_first()
        self.parser.compute_follow()
        self.parser.build_table()
        
        input_str = "i+" # Incomplete
        steps = self.parser.parse(input_str)
        
        self.assertEqual(steps[-1]["action"], "Error")

if __name__ == '__main__':
    unittest.main()