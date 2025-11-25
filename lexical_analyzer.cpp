#include <bits/stdc++.h>
using namespace std;

struct Production {
    string lhs;  // 左部非终结符(单个大写字母)
    string rhs;  // 右部:如 "aB" / "a" / "@"
};

struct Grammar {
    bool isRightLinear;               // true: 右线性；false: 左线性(只是标记,算法中不强依赖)
    vector<string> nonterminals;      // 非终结符集合(每个是长度1的大写字母)
    vector<char> terminals;           // 终结符集合(单个小写字母)
    string startSymbol;               // 开始符号
    vector<Production> prods;         // 产生式集合
};

struct NFA {
    int nStates = 0;                            // 状态数
    vector<char> alphabet;                     // 字母表
    unordered_map<char,int> symIndex;          // 终结符 -> 下标
    int start = 0;                             // 初始状态
    vector<bool> isFinal;                      // 是否是终结状态
    vector<vector<vector<int>>> trans;         // trans[state][symIdx] = {next states}
    vector<vector<int>> eps;                   // eps[state] = {epsilon next states}
};

// ===================== 小工具 =====================

void printGrammar(const Grammar& g) {
    cout << (g.isRightLinear ? "Right-linear regular grammar:" : "Left-linear regular grammar:") << "\n";
    cout << "(Here @ denotes the empty string ε)\n";
    map<string, vector<string>> grouped;
    for (auto &p : g.prods) {
        grouped[p.lhs].push_back(p.rhs);
    }
    for (auto &nt : g.nonterminals) {
        if (!grouped.count(nt)) continue;
        auto &vec = grouped[nt];
        sort(vec.begin(), vec.end());
        vec.erase(unique(vec.begin(), vec.end()), vec.end());
        cout << nt << "->";
        for (size_t i = 0; i < vec.size(); ++i) {
            if (i) cout << "|";
            cout << vec[i];
        }
        cout << "\n";
    }
}

void printNFA(const NFA& nfa) {
    cout << "NFA information:\n";
    cout << "Number of states: " << nfa.nStates << "\n";
    cout << "Alphabet: ";
    for (char c : nfa.alphabet) cout << c << " ";
    cout << "\n";
    cout << "Start state: " << nfa.start << "\n";
    cout << "Final states: ";
    for (int i = 0; i < nfa.nStates; ++i)
        if (nfa.isFinal[i]) cout << i << " ";
    cout << "\n";
    cout << "Transition function (@ denotes ε-transitions):\n";
    for (int s = 0; s < nfa.nStates; ++s) {
        for (size_t si = 0; si < nfa.alphabet.size(); ++si) {
            for (int to : nfa.trans[s][si]) {
                cout << s << " --" << nfa.alphabet[si] << "--> " << to << "\n";
            }
        }
        for (int to : nfa.eps[s]) {
            cout << s << " --@--> " << to << "  (ε)\n";
        }
    }
}

// 输入函数

Grammar readGrammar() {
    Grammar g;
    cout << "Please choose grammar type:\n";
    cout << "1. Right-linear regular grammar\n";
    cout << "2. Left-linear regular grammar\n";
    int t;
    cin >> t;
    g.isRightLinear = (t == 1);

    int nNT;
    cout << "Please enter the number of nonterminals:";
    cin >> nNT;
    g.nonterminals.resize(nNT);
    cout << "Please enter the nonterminals (separated by spaces, e.g. S A B):\n";
    for (int i = 0; i < nNT; ++i) cin >> g.nonterminals[i];

    int nT;
    cout << "Please enter the number of terminals:";
    cin >> nT;
    g.terminals.resize(nT);
    cout << "Please enter the terminals (separated by spaces, e.g. a b):\n";
    for (int i = 0; i < nT; ++i) cin >> g.terminals[i];

    cout << "Please enter the start symbol (e.g. S):";
    cin >> g.startSymbol;

    int nLines;
    cout << "Please enter the number of production lines (each line may have multiple right-hand sides separated by |):";
    cin >> nLines;
    cout << "Example of line format:  S->aA|b|@\n";
    cout << "Convention: @ denotes the empty string ε; the grammar must be in standard regular form.\n";
    string line;
    getline(cin, line); // 吃掉换行
    for (int i = 0; i < nLines; ++i) {
        getline(cin, line);
        if (line.empty()) { --i; continue; }
        string tmp;
        for (char c : line) {
            if (!isspace((unsigned char)c)) tmp.push_back(c);
        }
        auto pos = tmp.find("->");
        if (pos == string::npos) {
            cerr << "Production format error, skipping this line: " << line << "\n";
            continue;
        }
        string lhs = tmp.substr(0, pos);
        string rhsAll = tmp.substr(pos + 2);
        string cur;
        for (size_t j = 0; j <= rhsAll.size(); ++j) {
            if (j == rhsAll.size() || rhsAll[j] == '|') {
                if (!cur.empty()) {
                    g.prods.push_back({lhs, cur});
                }
                cur.clear();
            } else cur.push_back(rhsAll[j]);
        }
    }
    return g;
}

NFA readNFA() {
    NFA nfa;
    cout << "Please enter the number of states of the NFA:";
    cin >> nfa.nStates;

    int m;
    cout << "Please enter the number of input symbols:";
    cin >> m;
    nfa.alphabet.resize(m);
    cout << "Please enter the input symbols (e.g. a b):\n";
    for (int i = 0; i < m; ++i) {
        cin >> nfa.alphabet[i];
        nfa.symIndex[nfa.alphabet[i]] = i;
    }

    cout << "Please enter the index of the start state (0 ~ " << nfa.nStates - 1 << "):";
    cin >> nfa.start;

    nfa.isFinal.assign(nfa.nStates, false);
    cout << "Please enter the number of final states:";
    int f;
    cin >> f;
    cout << "Please enter the indices of the final states:";
    for (int i = 0; i < f; ++i) {
        int x;
        cin >> x;
        if (0 <= x && x < nfa.nStates) nfa.isFinal[x] = true;
    }

    nfa.trans.assign(nfa.nStates, vector<vector<int>>(m));
    nfa.eps.assign(nfa.nStates, {});

    cout << "Please enter the number of transitions:";
    int t;
    cin >> t;
    cout << "Each transition format: source_state input_symbol target_state\n";
    cout << "For an ε-transition, use @ as the input symbol\n";
    for (int i = 0; i < t; ++i) {
        int from, to;
        string sym;
        cin >> from >> sym >> to;
        if (sym == "@") {
            if (0 <= from && from < nfa.nStates && 0 <= to && to < nfa.nStates)
                nfa.eps[from].push_back(to);
        } else {
            char c = sym[0];
            auto it = nfa.symIndex.find(c);
            if (it == nfa.symIndex.end()) {
                cerr << "Unknown input symbol " << c << ", ignoring this transition\n";
                continue;
            }
            int idx = it->second;
            nfa.trans[from][idx].push_back(to);
        }
    }
    return nfa;
}

//  核心算法:文法 -> NFA 

// 右线性正规文法 -> NFA
NFA RightGrammarToNFA(const Grammar& g) {
    NFA nfa;
    int nNT = (int)g.nonterminals.size();
    nfa.nStates = nNT + 1; // 多一个收尾终结状态
    int finalState = nfa.nStates - 1;

    // 字母表
    nfa.alphabet = g.terminals;
    for (size_t i = 0; i < g.terminals.size(); ++i)
        nfa.symIndex[g.terminals[i]] = (int)i;

    // 非终结符 -> 状态编号映射
    unordered_map<string,int> ntIndex;
    for (int i = 0; i < nNT; ++i)
        ntIndex[g.nonterminals[i]] = i;

    auto itStart = ntIndex.find(g.startSymbol);
    if (itStart == ntIndex.end()) {
        cerr << "Start symbol not in the set of nonterminals, failed to construct NFA!\n";
        nfa.nStates = 0;
        return nfa;
    }
    nfa.start = itStart->second;

    nfa.isFinal.assign(nfa.nStates, false);
    nfa.isFinal[finalState] = true;
    nfa.trans.assign(nfa.nStates,
                     vector<vector<int>>(nfa.alphabet.size()));
    nfa.eps.assign(nfa.nStates, {});

    for (auto &p : g.prods) {
        auto it = ntIndex.find(p.lhs);
        if (it == ntIndex.end()) continue;
        int from = it->second;
        const string &rhs = p.rhs;

        if (rhs == "@") {
            // A -> ε:对应状态 A 也是终结状态
            nfa.isFinal[from] = true;
        } else if (rhs.size() == 1) {
            // A -> a
            char a = rhs[0];
            auto itSym = nfa.symIndex.find(a);
            if (itSym == nfa.symIndex.end()) {
                cerr << "Unknown terminal " << a << " appears in production, ignored\n";
                continue;
            }
            int idx = itSym->second;
            nfa.trans[from][idx].push_back(finalState);
        } else if (rhs.size() == 2) {
            // A -> aB
            char a = rhs[0];
            string B(1, rhs[1]);
            auto itSym = nfa.symIndex.find(a);
            auto itNT = ntIndex.find(B);
            if (itSym == nfa.symIndex.end() || itNT == ntIndex.end()) {
                cerr << "Production " << p.lhs << "->" << rhs
                     << " does not match the A->aB form, ignored\n";
                continue;
            }
            int idx = itSym->second;
            int to = itNT->second;
            nfa.trans[from][idx].push_back(to);
        } else {
            cerr << "Right-hand side of production too long (>2), not supported by this program:" 
                 << p.lhs << "->" << rhs << "\n";
        }
    }

    return nfa;
}

// NFA 反转:得到识别逆语言的 NFA
NFA ReverseNFA(const NFA& a) {
    NFA b;
    b.alphabet = a.alphabet;
    for (size_t i = 0; i < b.alphabet.size(); ++i)
        b.symIndex[b.alphabet[i]] = (int)i;

    b.nStates = a.nStates + 1; // 新增一个统一初始状态
    int newStart = a.nStates;
    b.start = newStart;

    b.isFinal.assign(b.nStates, false);
    b.trans.assign(b.nStates,
                   vector<vector<int>>(b.alphabet.size()));
    b.eps.assign(b.nStates, {});

    // 新 NFA 的唯一终结状态是旧的初始状态
    b.isFinal[a.start] = true;

    int m = (int)b.alphabet.size();

    // 反转所有非 ε 转换
    for (int p = 0; p < a.nStates; ++p) {
        for (int si = 0; si < m; ++si) {
            for (int q : a.trans[p][si]) {
                b.trans[q][si].push_back(p);
            }
        }
        // 反转 ε 转换
        for (int q : a.eps[p]) {
            b.eps[q].push_back(p);
        }
    }

    // 新初始状态 通过 ε-边 指向原来的所有终结状态
    for (int q = 0; q < a.nStates; ++q) {
        if (a.isFinal[q]) {
            b.eps[newStart].push_back(q);
        }
    }

    return b;
}

// 左线性文法 -> NFA
NFA LeftGrammarToNFA(const Grammar& g) {
    Grammar gr;
    gr.isRightLinear = true;
    gr.nonterminals = g.nonterminals;
    gr.terminals = g.terminals;
    gr.startSymbol = g.startSymbol;
    gr.prods.clear();

    for (auto &p : g.prods) {
        string newRhs;
        if (p.rhs == "@") newRhs = "@";
        else newRhs = string(p.rhs.rbegin(), p.rhs.rend());
        gr.prods.push_back({p.lhs, newRhs});
    }

    NFA nfaForReverse = RightGrammarToNFA(gr); // 识别 L^R
    NFA result = ReverseNFA(nfaForReverse);    // 识别 L
    return result;
}

// 核心算法:NFA -> 文法
vector<vector<int>> epsilonClosures(const NFA& a) {
    int n = a.nStates;
    vector<vector<int>> clos(n);
    for (int s = 0; s < n; ++s) {
        vector<int> stack{ s };
        vector<int> vis(n, 0);
        vis[s] = 1;
        while (!stack.empty()) {
            int x = stack.back(); stack.pop_back();
            clos[s].push_back(x);
            for (int y : a.eps[x]) {
                if (!vis[y]) {
                    vis[y] = 1;
                    stack.push_back(y);
                }
            }
        }
    }
    return clos;
}

// 消除 NFA 的 ε-转换,得到等价的 ε-自由 NFA
NFA RemoveEpsilon(const NFA& a) {
    NFA b;
    b.nStates = a.nStates;
    b.alphabet = a.alphabet;
    for (size_t i = 0; i < b.alphabet.size(); ++i)
        b.symIndex[b.alphabet[i]] = (int)i;
    b.start = a.start;

    int n = b.nStates;
    int m = (int)b.alphabet.size();
    b.trans.assign(n, vector<vector<int>>(m));
    b.eps.assign(n, {}); // 不再有 ε-边
    b.isFinal.assign(n, false);

    auto clos = epsilonClosures(a);

    // 新的终结状态:ε-闭包中包含任一旧终结状态
    for (int s = 0; s < n; ++s) {
        bool f = false;
        for (int t : clos[s]) {
            if (a.isFinal[t]) { f = true; break; }
        }
        b.isFinal[s] = f;
    }

    // 新的转换函数:δ'(p, a) = ?_{r ∈ ε-closure(p)} ε-closure(δ(r,a))
    for (int s = 0; s < n; ++s) {
        for (int si = 0; si < m; ++si) {
            set<int> dest;
            for (int r : clos[s]) {
                for (int q : a.trans[r][si]) {
                    for (int t : clos[q]) {
                        dest.insert(t);
                    }
                }
            }
            b.trans[s][si] = vector<int>(dest.begin(), dest.end());
        }
    }

    return b;
}

// NFA -> 右线性正规文法
Grammar NFAtoRightGrammar(const NFA& a) {
    NFA b = RemoveEpsilon(a);

    Grammar g;
    g.isRightLinear = true;
    g.terminals = b.alphabet;

    int n = b.nStates;
    if (n > 26) {
        cerr << "Warning: number of states " << n << " > 26, cannot represent all nonterminals with single uppercase letters.\n";
        cerr << "The following construction will still proceed, but you may need to rename them manually to meet assignment requirements.\n";
    }

    g.nonterminals.clear();
    vector<string> ids(n);
    for (int i = 0; i < n; ++i) {
        char c = 'A' + (i % 26);
        ids[i] = string(1, c);
        g.nonterminals.push_back(ids[i]);
    }

    g.startSymbol = ids[b.start];

    // 转移 => 产生式 A_p -> a A_q
    for (int s = 0; s < n; ++s) {
        string lhs = ids[s];
        for (size_t si = 0; si < b.alphabet.size(); ++si) {
            char c = b.alphabet[si];
            for (int q : b.trans[s][si]) {
                string rhs;
                rhs.push_back(c);
                rhs += ids[q];
                g.prods.push_back({lhs, rhs});
            }
        }
    }

    // 终结状态 => 加 A_p -> @
    for (int s = 0; s < n; ++s) {
        if (b.isFinal[s]) {
            g.prods.push_back({ids[s], "@"});
        }
    }

    return g;
}

// NFA -> 左线性正规文法
Grammar NFAtoLeftGrammar(const NFA& a) {
    NFA rev = ReverseNFA(a);          // 识别 L^R
    Grammar gRight = NFAtoRightGrammar(rev); // 右线性文法,识别 L^R

    Grammar gLeft;
    gLeft.isRightLinear = false;
    gLeft.nonterminals = gRight.nonterminals;
    gLeft.terminals = gRight.terminals;
    gLeft.startSymbol = gRight.startSymbol;

    for (auto &p : gRight.prods) {
        string newRhs;
        if (p.rhs == "@") newRhs = "@";
        else newRhs = string(p.rhs.rbegin(), p.rhs.rend());
        gLeft.prods.push_back({p.lhs, newRhs});
    }
    return gLeft;
}

int main() {
    // cout<<"OK";
    while (1) {
        cout << "=====================================\n";
        cout << "Conversion between regular grammars (left/right-linear) and FA\n";
        cout << "=====================================\n";
        cout << "1. Regular grammar -> FA\n";
        cout << "2. FA -> right-linear regular grammar\n";
        cout << "3. FA -> left-linear regular grammar\n";
        cout << "0. Exit\n";
        cout << "Please enter an option:";

        int op;
        if (!(cin >> op)) break;
        if (op == 0) break;

        if (op == 1) {
            Grammar g = readGrammar();
            NFA nfa;
            if (g.isRightLinear) {
                nfa = RightGrammarToNFA(g);
            } else {
                nfa = LeftGrammarToNFA(g);
            }
            if (nfa.nStates == 0) {
                cerr << "Failed to construct NFA, please check whether the grammar input is in regular form.\n";
            } else {
                printNFA(nfa);
            }
        } else if (op == 2) {
            NFA nfa = readNFA();
            Grammar g = NFAtoRightGrammar(nfa);
            printGrammar(g);
        } else if (op == 3) {
            NFA nfa = readNFA();
            Grammar g = NFAtoLeftGrammar(nfa);
            printGrammar(g);
        } else {
            cout << "Invalid option, please try again.\n";
        }

        cout << "\n";
    }

    return 0;
}
