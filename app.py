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
        parser.build_table()  # builds FIRST, FOLLOW, ACTION/GOTO

        # --- Productions (including augmented) ---
        st.subheader("📑 Productions (Augmented Grammar)")
        st.table(pd.DataFrame(parser.get_productions_display()))

        # --- Grammar Snapshot ---
        st.subheader("📊 Grammar Snapshot")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("States", len(parser.states))
        col_b.metric("Terminals", len(parser.terminals))
        col_c.metric("Non-Terminals", len(parser.non_terminals))
        col_d.metric("Productions", len(parser.productions))

        # --- Terminals & Non-Terminals ---
        st.markdown(f"**Terminals:** {', '.join(sorted(parser.terminals))}")
        st.markdown(f"**Non-Terminals:** {', '.join(sorted(parser.non_terminals))}")

        # --- SLR(1) Status ---
        st.subheader("🔍 SLR(1) Status")
        if parser.is_slr():
            st.success("✅ Grammar is SLR(1) — no shift/reduce or reduce/reduce conflicts detected.")
        else:
            st.error("❌ Grammar is NOT SLR(1). Conflicts detected in the ACTION table.")
            conflict_rows = []
            for c in parser.conflicts:
                formatted_actions = []
                for act in c["actions"]:
                    formatted_actions.append(parser._format_action_verbose(act))
                conflict_rows.append({
                    "State": f"I{c['state']}",
                    "Symbol": c["symbol"],
                    "Actions": ", ".join(formatted_actions),
                    "Kind": c["kind"]
                })
            st.table(pd.DataFrame(conflict_rows))

        # --- First & Follow Sets ---
        st.subheader("🐲 First & Follow Sets")
        ff_data = []
        for nt in sorted(parser.non_terminals):
            ff_data.append({
                "Non-Terminal": nt,
                "FIRST": "{ " + ", ".join(sorted(parser.first[nt])) + " }",
                "FOLLOW": "{ " + ", ".join(sorted(parser.follow[nt])) + " }"
            })
        st.table(pd.DataFrame(ff_data))

        # --- Canonical Collection of LR(0) Items ---
        st.subheader("🍁 Canonical Collection of LR(0) Items")
        for row in parser.get_states_display():
            with st.expander(f"State {row['State']}"):
                st.text(row["Items"])

        # --- State Transitions ---
        if parser.transitions:
            st.subheader("🔀 State Transitions (GOTO Table)")
            trans_rows = parser.get_transitions_display()
            st.dataframe(pd.DataFrame(trans_rows))

        # --- Parsing Table ---
        st.subheader("📋 Parsing Table (ACTION | GOTO)")
        action_syms, goto_syms, table_rows = parser.get_parsing_table_matrix()
        if table_rows:
            df = pd.DataFrame(table_rows).set_index("State")
            st.dataframe(df)

        st.subheader("⚙️ Parsing Process")
        try:
            steps = parser.parse(slr_input_str)
            st.table(pd.DataFrame(steps))
        except Exception as e:
            st.error(f"Parsing Error: {e}")

