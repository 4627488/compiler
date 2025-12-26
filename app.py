import streamlit as st
import pandas as pd
import graphviz
from src.compiler.lexical_analyzer import LexicalAnalyzer
from src.compiler.rg_nfa import RG_NFA_Converter
from src.compiler.ll1_parser import LL1Parser
from src.compiler.slr_parser import SLRParser

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Compiler Principles Visualization", layout="wide")
st.title("Compiler Principles Visualization System")

tab1, tab2, tab3, tab4 = st.tabs(["Lexical Analysis", "Regular Grammar to NFA", "LL(1) Parsing", "SLR(1) Parsing"])

# --- Tab 1: Lexical Analysis ---
with tab1:
    st.header("Lexical Analyzer")
    st.markdown("Input source code below to perform lexical analysis.")
    
    default_code = """if x = 10 then
    y := 20
else
    y := 30;"""
    
    code_input = st.text_area("Source Code", value=default_code, height=200)
    
    if st.button("Analyze", key="lex_btn"):
        lexer = LexicalAnalyzer()
        tokens = lexer.analyze(code_input)
        
        df = pd.DataFrame(tokens)
        st.table(df)

# --- Tab 2: Regular Grammar to NFA ---
with tab2:
    st.header("Regular Grammar to NFA")
    st.markdown("Input a Right-Linear Regular Grammar.")
    
    default_grammar = """S -> aA | b
A -> aS | b"""
    
    rg_input = st.text_area("Grammar Rules", value=default_grammar, height=150)
    
    if st.button("Convert to NFA", key="nfa_btn"):
        converter = RG_NFA_Converter()
        grammar_info = converter.parse_grammar(rg_input)
        
        st.subheader("Parsed Grammar")
        st.write(grammar_info['prods'])
        
        nfa = converter.right_grammar_to_nfa(grammar_info)
        
        if nfa:
            st.subheader("NFA Visualization")
            dot = converter.nfa_to_dot(nfa)
            st.graphviz_chart(dot)
            
            st.subheader("Transition Table")
            # Format transition table for display
            rows = []
            for (u, a), v_list in nfa['transitions'].items():
                u_name = nfa['state_map_rev'][u]
                v_names = [nfa['state_map_rev'][v] for v in v_list]
                rows.append({"From State": u_name, "Input": a, "To States": ", ".join(v_names)})
            st.table(pd.DataFrame(rows))
        else:
            st.error("Failed to generate NFA. Check grammar format.")

# --- Tab 3: LL(1) Parsing ---
with tab3:
    st.header("LL(1) Parser")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Grammar")
        default_ll1 = """E -> T E'
E' -> + T E' | ^
T -> F T'
T' -> * F T' | ^
F -> ( E ) | i"""
        ll1_grammar_input = st.text_area("LL(1) Grammar (Use ^ for epsilon)", value=default_ll1, height=200)
        
    with col2:
        st.subheader("Input String")
        ll1_input_str = st.text_input("Input String (end with #)", value="i+i*i#")
    
    if st.button("Parse", key="ll1_btn"):
        parser = LL1Parser()
        parser.parse_grammar(ll1_grammar_input)
        parser.compute_first()
        parser.compute_follow()
        parser.build_table()
        
        st.subheader("First & Follow Sets")
        
        # Display First/Follow
        ff_data = []
        for nt in parser.non_terminals:
            ff_data.append({
                "Non-Terminal": nt,
                "First": ", ".join(parser.first[nt]),
                "Follow": ", ".join(parser.follow[nt])
            })
        st.table(pd.DataFrame(ff_data))
        
        st.subheader("Parsing Table")
        # Display Table
        table_rows = []
        for nt, row in parser.table.items():
            row_dict = {"Non-Terminal": nt}
            for term in parser.terminals:
                if term in row:
                    row_dict[term] = "".join(row[term])
                else:
                    row_dict[term] = ""
            table_rows.append(row_dict)
        st.dataframe(pd.DataFrame(table_rows).set_index("Non-Terminal"))
        
        st.subheader("Parsing Process")
        steps = parser.parse(ll1_input_str)
        st.table(pd.DataFrame(steps))

# --- Tab 4: SLR(1) Parsing ---
with tab4:
    st.header("SLR(1) Parser")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Grammar")
        default_slr = """E -> E + T | T
T -> T * F | F
F -> ( E ) | i"""
        slr_grammar_input = st.text_area("SLR(1) Grammar", value=default_slr, height=200, key="slr_grammar")
        
    with col2:
        st.subheader("Input String")
        slr_input_str = st.text_input("Input String (end with #)", value="i+i*i#", key="slr_input")
    
    if st.button("Parse", key="slr_btn"):
        parser = SLRParser()
        parser.parse_grammar(slr_grammar_input)
        parser.build_table() # This computes first, follow, and builds tables
        
        st.subheader("First & Follow Sets")
        ff_data = []
        for nt in parser.non_terminals:
            if nt == parser.augmented_start: continue
            ff_data.append({
                "Non-Terminal": nt,
                "First": ", ".join(parser.first[nt]),
                "Follow": ", ".join(parser.follow[nt])
            })
        st.table(pd.DataFrame(ff_data))
        
        st.subheader("Canonical Collection of LR(0) Items")
        states_data = []
        for i, state in enumerate(parser.states):
            items_str = []
            for (lhs, rhs, dot) in state:
                rhs_list = list(rhs)
                rhs_list.insert(dot, ".")
                items_str.append(f"{lhs} -> {' '.join(rhs_list)}")
            states_data.append({
                "State ID": i,
                "Items": "\n".join(items_str)
            })
        st.table(pd.DataFrame(states_data))

        st.subheader("Parsing Table")
        # Combine Action and Goto tables
        # Columns: Terminals (Action) + Non-Terminals (Goto)
        all_symbols = sorted(list(parser.terminals)) + sorted(list(parser.non_terminals))
        if parser.augmented_start in all_symbols:
            all_symbols.remove(parser.augmented_start)
            
        table_rows = []
        for i in range(len(parser.states)):
            row_dict = {"State": i}
            for sym in all_symbols:
                val = ""
                if sym in parser.terminals:
                    if (i, sym) in parser.action_table:
                        action = parser.action_table[(i, sym)]
                        if action[0] == 'shift':
                            val = f"s{action[1]}"
                        elif action[0] == 'reduce':
                            val = f"r{action[1]}"
                        elif action[0] == 'accept':
                            val = "acc"
                elif sym in parser.non_terminals:
                    if (i, sym) in parser.goto_table:
                        val = str(parser.goto_table[(i, sym)])
                
                row_dict[sym] = val
            table_rows.append(row_dict)
            
        st.dataframe(pd.DataFrame(table_rows).set_index("State"))
        
        st.subheader("Parsing Process")
        try:
            steps = parser.parse(slr_input_str)
            st.table(pd.DataFrame(steps))
        except Exception as e:
            st.error(f"Parsing Error: {e}")

