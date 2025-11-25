#include <iostream>
#include <fstream>
#include <string>
#include <cctype>
#include <unordered_map>
#include <vector>
#include <set>
using namespace std;

/**
 * LexicalAnalyzer：一个简单的词法分析器，按照状态转换图算法实现。
 * 它从输入文件中逐字符读取源代码，识别单词符号（标识符、关键字、整数、运算符、分隔符），
 * 并以 (TokenType, value) 格式输出词法分析结果。
 *
 * 词法分析器使用 Reserve、InsertId 和 InsertConst 函数来识别保留字、
 * 将标识符插入符号表，以及将整型常量插入常量表。
 *
 * 本实现仅使用 C++ 标准库，不依赖第三方库。
 * 程序结构清晰，模块分明，并包含注释，便于后续扩展。
 */

// Token结构定义（包含类型和值），可选
struct Token {
    string type;
    string value;
};

class LexicalAnalyzer {
private:
    // 保留字集合，用于快速查找关键字。
    set<string> keywords;
    // 标识符符号表（存储唯一的标识符字符串）。
    unordered_map<string, int> symbolTableMap;
    vector<string> symbolTableList; // 符号表索引到标识符字符串的映射
    // 常量表（用于存储整数常量）。
    unordered_map<int, int> constTableMap;
    vector<int> constTableList;     // 常量表索引到整数值的映射

    // 初始化保留字集合（模拟 Reserve 函数预置保留字）。
    void initKeywords() {
        // 将所有关键字插入 keywords 集合。
        // 下列仅为题目要求的示例关键字（可扩展）。
        keywords.insert("if");
        keywords.insert("then");
        keywords.insert("else");
        // 可根据语言需要在此处增加其他保留字，如：
        // keywords.insert("begin");
        // keywords.insert("end");
        // 等等。
    }

public:
    LexicalAnalyzer() {
        initKeywords();
    }

    // 模拟 Reserve 函数：判断字符串是否为保留字
    // 若是保留字则返回 true，否则返回 false。
    bool Reserve(const string &strToken) {
        return (keywords.find(strToken) != keywords.end());
    }

    // 模拟 InsertId 函数：将标识符插入符号表（若已存在则直接返回索引）
    // 返回符号表中该标识符的索引
    int InsertId(const string &identifier) {
        auto it = symbolTableMap.find(identifier);
        if (it != symbolTableMap.end()) {
            // 标识符已在表中，返回已有索引
            return it->second;
        } else {
            // 新标识符，插入符号表
            int index = symbolTableList.size();
            symbolTableList.push_back(identifier);
            symbolTableMap[identifier] = index;
            return index;
        }
    }

    // 模拟 InsertConst 函数：将常量插入常量表（若不存在则插入）
    // 将数字字符串转换为整数值进行存储
    // 返回常量表中该常量的索引
    int InsertConst(const string &constLexeme) {
        // 将字符串转换为整数（假设输入格式合法）
        int value = 0;
        try {
            value = stoi(constLexeme);
        } catch (...) {
            value = 0; // 若转换失败，赋值0（一般不会发生）
        }
        auto it = constTableMap.find(value);
        if (it != constTableMap.end()) {
            // 常量已存在，返回原索引
            return it->second;
        } else {
            // 新常量，插入常量表
            int index = constTableList.size();
            constTableList.push_back(value);
            constTableMap[value] = index;
            return index;
        }
    }

    // 词法分析主函数：从输入流读取字符，识别单词符号并写入输出流。
    void analyze(ifstream &fin, ofstream &fout) {
        char c;
        // 从输入流逐字符读取直到文件结束
        while (true) {
            c = fin.get();
            if (!fin) { // 文件结束或读取错误
                break;
            }

            // 跳过空白字符（空格、制表符、换行等）
            if (isspace(static_cast<unsigned char>(c))) {
                // 不产生记号，继续读取下一个字符
                continue;
            }

            // 初始状态：判断该字符开始的是哪类单词符号
            if (isalpha(static_cast<unsigned char>(c))) {
                // 识别标识符或关键字
                // 状态转换：以字母开头进入标识符/关键字识别状态
                string lexeme;
                lexeme.push_back(c);
                // 持续读取字母或数字字符，组成完整标识符
                while (true) {
                    char nextChar = fin.peek();  // 预读下一个字符
                    if (isalnum(static_cast<unsigned char>(nextChar))) {
                        // 若下一个字符是字母或数字，属于标识符的一部分
                        lexeme.push_back(fin.get());  // 读取并追加字符
                    } else {
                        // 遇到非字母数字字符，标识符结束
                        break;
                    }
                }
                // 已完整读取一个标识符字符串（可能是关键字）
                if (Reserve(lexeme)) {
                    // 该字符串是保留字
                    fout << "(KEYWORD, " << lexeme << ")" << endl;
                } else {
                    // 非保留字，则是用户定义的标识符
                    int idIndex = InsertId(lexeme);
                    fout << "(ID, " << idIndex << ")" << endl;
                }
            }
            else if (isdigit(static_cast<unsigned char>(c))) {
                // 识别整数常量
                // 状态转换：以数字开头进入整数常量识别状态
                string number;
                number.push_back(c);
                // 持续读取后续数字字符
                while (true) {
                    char nextChar = fin.peek();
                    if (isdigit(static_cast<unsigned char>(nextChar))) {
                        number.push_back(fin.get());
                    } else {
                        break;
                    }
                }
                // 已完整读取一个数字常量
                // 注：如出现 "123abc" 这样的情况应当视为词法错误
                // （简化处理：假定数字和字母之间总有分隔符）
                int constIndex = InsertConst(number);
                fout << "(INT, " << constIndex << ")" << endl;
            }
            else {
                // 运算符或分隔符等单字符处理，以及多字符运算符判别
                if (c == '+') {
                    // '+' 运算符（加法）
                    fout << "(OPERATOR, +)" << endl;
                }
                else if (c == '-') {
                    // '-' 运算符（减法）
                    fout << "(OPERATOR, -)" << endl;
                }
                else if (c == '*') {
                    // '*' 运算符，或作为 "**" 运算符（乘方）的开始
                    char nextChar = fin.peek();
                    if (nextChar == '*') {
                        // 识别到 "**" 运算符
                        fin.get(); // 消耗第二个 '*'
                        fout << "(OPERATOR, **)" << endl;
                    } else {
                        // 单个 '*' 运算符（乘法）
                        fout << "(OPERATOR, *)" << endl;
                    }
                }
                else if (c == '=') {
                    // '=' 运算符，或作为 "==" 运算符的开始
                    char nextChar = fin.peek();
                    if (nextChar == '=') {
                        // 识别到 "==" 运算符（等于比较）
                        fin.get(); // 消耗第二个 '='
                        fout << "(OPERATOR, ==)" << endl;
                    } else {
                        // 单个 '=' 运算符（赋值或比较）
                        fout << "(OPERATOR, =)" << endl;
                    }
                }
                else if (c == ':') {
                    // ':' 符号，或作为 ":=" 运算符的开始
                    char nextChar = fin.peek();
                    if (nextChar == '=') {
                        // 识别到 ":=" 运算符（赋值）
                        fin.get(); // 消耗 '='
                        fout << "(OPERATOR, :=)" << endl;
                    } else {
                        // 单独的 ':' 在该语言中无独立含义（此处作为分隔符处理）
                        fout << "(SEPARATOR, :)" << endl;
                    }
                }
                else if (c == ';') {
                    // ';' 分隔符（语句结束符）
                    fout << "(SEPARATOR, ;)" << endl;
                }
                else if (c == ',') {
                    // ',' 分隔符（列表分隔符）
                    fout << "(SEPARATOR, ,)" << endl;
                }
                else if (c == '(') {
                    // '(' 分隔符（左括号）
                    fout << "(SEPARATOR, " << c << ")" << endl;
                }
                else if (c == ')') {
                    // ')' 分隔符（右括号）
                    fout << "(SEPARATOR, " << c << ")" << endl;
                }
                else if (c == '{') {
                    // '{' 分隔符（左花括号）
                    fout << "(SEPARATOR, {)" << endl;
                }
                else if (c == '}') {
                    // '}' 分隔符（右花括号）
                    fout << "(SEPARATOR, })" << endl;
                }
                else {
                    // 未识别的字符或运算符
                    // 将其作为 UNKNOWN 记号输出（或忽略）
                    fout << "(UNKNOWN, " << c << ")" << endl;
                }
            }
        }
    }
};

int main(int argc, char* argv[]) {
    // 检查参数：需要提供输入文件路径
    string inputFile;
    string outputFile;
    if (argc < 2) {
        // cerr << "Usage: " << argv[0] << " <source code file> [output file]" << endl;
        // return 1;
        inputFile = "input.txt"; // 默认输入文件名
    } else {
        inputFile = argv[1];
    }
    if (argc >= 3) {
        outputFile = argv[2];
    } else {
        outputFile = "output.txt"; // 默认输出文件名
    }

    ifstream fin(inputFile);
    if (!fin) {
        cerr << "Error: Unable to open input file " << inputFile << endl;
        return 1;
    }
    ofstream fout(outputFile);
    if (!fout) {
        cerr << "Error: Unable to create output file " << outputFile << endl;
        return 1;
    }

    // 创建词法分析器实例并执行分析
    LexicalAnalyzer lexer;
    lexer.analyze(fin, fout);

    fin.close();
    fout.close();

    cout << "Lexical analysis completed, results have been written to " << outputFile << endl;
    return 0;
}
/*
g++ lexical_analyzer.cpp -o lexical_analyzer
./lexical_analyzer input.txt output.txt
*/