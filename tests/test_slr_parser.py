import unittest
from src.compiler.slr_parser import SLRParser

class TestSLRParser(unittest.TestCase):
    def setUp(self):
        self.parser = SLRParser()
        # Standard expression grammar (left recursive)
        self.grammar_text = """
        E -> E + T | T
        T -> T * F | F
        F -> ( E ) | i
        """

    def test_parse_grammar(self):
        self.parser.parse_grammar(self.grammar_text)
        self.assertIn('E', self.parser.grammar)
        self.assertIn('T', self.parser.grammar)
        self.assertIn('F', self.parser.grammar)
        # Check augmented start symbol
        self.assertTrue(any(s.startswith("E'") for s in self.parser.non_terminals))

    def test_build_table(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.build_table()
        # Just check if table is populated
        self.assertTrue(len(self.parser.action_table) > 0)
        self.assertTrue(len(self.parser.goto_table) > 0)

    def test_parse(self):
        self.parser.parse_grammar(self.grammar_text)
        self.parser.build_table()
        
        # Test valid string
        steps = self.parser.parse("i+i*i")
        last_step = steps[-1]
        self.assertEqual(last_step['action'], 'Accept')
        
        # Test another valid string
        steps = self.parser.parse("(i+i)*i")
        last_step = steps[-1]
        self.assertEqual(last_step['action'], 'Accept')
        
        # Test invalid string
        steps = self.parser.parse("i+")
        last_step = steps[-1]
        self.assertNotEqual(last_step['action'], 'Accept')
