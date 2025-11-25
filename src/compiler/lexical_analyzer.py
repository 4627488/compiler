
class LexicalAnalyzer:
    def __init__(self):
        self.keywords = {"if", "then", "else", "while", "do", "begin", "end"} # Expanded a bit for general use
        self.symbol_table = {}
        self.const_table = {}
        self.tokens = []

    def is_keyword(self, token):
        return token in self.keywords

    def get_id_index(self, identifier):
        if identifier not in self.symbol_table:
            self.symbol_table[identifier] = len(self.symbol_table)
        return self.symbol_table[identifier]

    def get_const_index(self, value):
        if value not in self.const_table:
            self.const_table[value] = len(self.const_table)
        return self.const_table[value]

    def analyze(self, source_code):
        self.tokens = []
        self.symbol_table = {}
        self.const_table = {}
        
        i = 0
        n = len(source_code)
        line_num = 1
        
        while i < n:
            char = source_code[i]
            
            if char.isspace():
                if char == '\n':
                    line_num += 1
                i += 1
                continue
            
            if char.isalpha() or char == '_':
                lexeme = char
                i += 1
                while i < n and (source_code[i].isalnum() or source_code[i] == '_'):
                    lexeme += source_code[i]
                    i += 1
                
                if self.is_keyword(lexeme):
                    self.tokens.append({"Line": line_num, "Type": "KEYWORD", "Value": lexeme, "Index": "-"})
                else:
                    idx = self.get_id_index(lexeme)
                    self.tokens.append({"Line": line_num, "Type": "ID", "Value": lexeme, "Index": idx})
                continue
            
            if char.isdigit():
                lexeme = char
                i += 1
                while i < n and source_code[i].isdigit():
                    lexeme += source_code[i]
                    i += 1
                
                idx = self.get_const_index(lexeme)
                self.tokens.append({"Line": line_num, "Type": "INT", "Value": lexeme, "Index": idx})
                continue
                
            # Operators and Separators
            if char == '+':
                self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "+", "Index": "-"})
                i += 1
            elif char == '-':
                self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "-", "Index": "-"})
                i += 1
            elif char == '*':
                if i + 1 < n and source_code[i+1] == '*':
                    self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "**", "Index": "-"})
                    i += 2
                else:
                    self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "*", "Index": "-"})
                    i += 1
            elif char == '=':
                if i + 1 < n and source_code[i+1] == '=':
                    self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "==", "Index": "-"})
                    i += 2
                else:
                    self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": "=", "Index": "-"})
                    i += 1
            elif char == ':':
                if i + 1 < n and source_code[i+1] == '=':
                    self.tokens.append({"Line": line_num, "Type": "OPERATOR", "Value": ":=", "Index": "-"})
                    i += 2
                else:
                    self.tokens.append({"Line": line_num, "Type": "SEPARATOR", "Value": ":", "Index": "-"})
                    i += 1
            elif char in ';,(){}':
                self.tokens.append({"Line": line_num, "Type": "SEPARATOR", "Value": char, "Index": "-"})
                i += 1
            else:
                self.tokens.append({"Line": line_num, "Type": "UNKNOWN", "Value": char, "Index": "-"})
                i += 1
        
        return self.tokens
