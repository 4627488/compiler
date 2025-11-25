import unittest
from src.compiler.lexical_analyzer import LexicalAnalyzer

class TestLexicalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.lexer = LexicalAnalyzer()

    def test_keywords(self):
        code = "if then else while do begin end"
        tokens = self.lexer.analyze(code)
        self.assertEqual(len(tokens), 7)
        for token in tokens:
            self.assertEqual(token["Type"], "KEYWORD")

    def test_identifiers(self):
        code = "x y1 abc_d"
        tokens = self.lexer.analyze(code)
        self.assertEqual(len(tokens), 3)
        for token in tokens:
            self.assertEqual(token["Type"], "ID")
        self.assertEqual(tokens[0]["Value"], "x")
        self.assertEqual(tokens[1]["Value"], "y1")
        self.assertEqual(tokens[2]["Value"], "abc_d")

    def test_integers(self):
        code = "123 0 456789"
        tokens = self.lexer.analyze(code)
        self.assertEqual(len(tokens), 3)
        for token in tokens:
            self.assertEqual(token["Type"], "INT")
        self.assertEqual(tokens[0]["Value"], "123")
        self.assertEqual(tokens[1]["Value"], "0")
        self.assertEqual(tokens[2]["Value"], "456789")

    def test_operators(self):
        code = "+ - * ** = == :="
        tokens = self.lexer.analyze(code)
        self.assertEqual(len(tokens), 7)
        expected_values = ["+", "-", "*", "**", "=", "==", ":="]
        for i, token in enumerate(tokens):
            self.assertEqual(token["Type"], "OPERATOR")
            self.assertEqual(token["Value"], expected_values[i])

    def test_separators(self):
        code = "; , ( ) { }"
        tokens = self.lexer.analyze(code)
        self.assertEqual(len(tokens), 6)
        for token in tokens:
            self.assertEqual(token["Type"], "SEPARATOR")

    def test_complex_expression(self):
        code = "if x > 10 then y := x + 1;"
        # Note: > is not in the original code's operator list, it might be UNKNOWN or handled if I missed it.
        # Looking at the code: > is not handled explicitly, so it will be UNKNOWN.
        # Let's stick to supported operators.
        code = "if x = 10 then y := x + 1;"
        tokens = self.lexer.analyze(code)
        
        # Expected tokens:
        # if (KEYWORD)
        # x (ID)
        # = (OPERATOR)
        # 10 (INT)
        # then (KEYWORD)
        # y (ID)
        # := (OPERATOR)
        # x (ID)
        # + (OPERATOR)
        # 1 (INT)
        # ; (SEPARATOR)
        
        self.assertEqual(len(tokens), 11)
        self.assertEqual(tokens[0]["Type"], "KEYWORD")
        self.assertEqual(tokens[1]["Type"], "ID")
        self.assertEqual(tokens[2]["Type"], "OPERATOR")
        self.assertEqual(tokens[3]["Type"], "INT")
        self.assertEqual(tokens[4]["Type"], "KEYWORD")
        self.assertEqual(tokens[5]["Type"], "ID")
        self.assertEqual(tokens[6]["Type"], "OPERATOR")
        self.assertEqual(tokens[7]["Type"], "ID")
        self.assertEqual(tokens[8]["Type"], "OPERATOR")
        self.assertEqual(tokens[9]["Type"], "INT")
        self.assertEqual(tokens[10]["Type"], "SEPARATOR")

if __name__ == '__main__':
    unittest.main()
