# Compiler Principles Visualization System

这是一个基于 Python 和 Streamlit 开发的编译器原理可视化工具。主要用于演示编译原理中的核心算法过程。

## 功能模块

1. **词法分析 (Lexical Analysis)**
   - 支持自定义源代码输入。
   - 识别关键字、标识符、常量等 Token。
   - 输出 Token 表。

2. **正规文法转 NFA (Regular Grammar to NFA)**
   - 输入右线性文法。
   - 自动转换为 NFA（非确定性有限自动机）。
   - 提供状态转换图可视化和转换表。

3. **LL(1) 语法分析 (LL(1) Parsing)**
   - 计算 First 和 Follow 集合。
   - 生成 LL(1) 预测分析表。
   - 展示输入串的详细分析栈过程。

## 贡献者与分工 (Contributors)

本项目由三人团队协作完成。各成员**分别独立主导一个核心模块**的设计与实现，并共同参与系统集成与测试，**整体工作量分配均衡**。具体分工如下：

| 成员 | 负责模块 | 具体工作内容 |
| :--- | :--- | :--- |
| **黄耘青** | **架构与词法分析** | • 搭建 Streamlit 界面框架与多页面布局 (`app.py`)<br>• 管理项目依赖 (`pyproject.toml`)与环境配置<br>• 实现词法分析器 (`lexical_analyzer.py`) |
| **赵乐坤** | **正规文法转 NFA** | • 实现正规文法解析与 NFA 转换算法 (`rg_nfa.py`)<br>• 集成 Graphviz，实现状态转换图的自动渲染<br>• 编写 NFA 转换相关的单元测试与集成测试 |
| **何东泽** | **LL(1) 分析** | • 实现 LL(1) 核心算法，包括 First/Follow 集计算 (`ll1_parser.py`)<br>• 构建预测分析表与分析栈模拟逻辑<br>• 封装分析过程数据供前端展示 |

## 环境要求

- Python 3.12

## 安装与运行

1. 克隆项目或下载源码。

2. 安装依赖：
   ```bash
   uv sync
   ```

3. 运行应用：
   ```bash
   uv run streamlit run app.py
   ```

4. 浏览器会自动打开 `http://localhost:8501`。
