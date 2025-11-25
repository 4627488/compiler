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