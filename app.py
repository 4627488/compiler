import streamlit as st
import pandas as pd
import graphviz
from src.compiler.lexical_analyzer import LexicalAnalyzer
from src.compiler.rg_nfa import RG_NFA_Converter
from src.compiler.ll1_parser import LL1Parser

# ==========================================
# Streamlit UI
# ==========================================

st.set_page_config(page_title="Compiler Principles Visualization", layout="wide")
st.title("Compiler Principles Visualization System")

tab1, tab2, tab3 = st.tabs(["Lexical Analysis", "Regular Grammar to NFA", "LL(1) Parsing"])

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

