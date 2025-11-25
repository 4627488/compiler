# LL（1）文法扫描器:
# 根据现有的文法
# 创建first集
# 创建follow集
# 创建预测分析表
# 对输入的字符进行分析
flag = 0 # first或者follow是否变化的标志
step = 0 # 分析过程每一步

def add_value(dict, key, value): # 列表中添加元素
    global flag
    if key not in dict:
        dict[key] = [value]
        flag = 1
    elif value not in dict[key]:
        dict[key].append(value)
        flag = 1


def add_list(dict1, key1, dict2, key2): # 列表2的内容给列表1，去重去空符
    global flag
    if key1 not in dict1: # 初始化列表1
        dict1[key1] = []
        flag = 1

    if key2 in LL.V_T:
        if key2 not in dict1[key1]:  # First(V_T)=V_T
            dict1[key1].append(key2)
            flag = 1
        return

    if key2 not in dict2: # 初始化列表2
        dict2[key2] = []
        flag = 1

    for a in dict2[key2]: # 添加
        if a not in dict1[key1] and a != '^':
            dict1[key1].append(a)
            flag = 1



class LL1():
    def __init__(self):
        self.grammer = {}   # 文法
        self.start_V = ''   # 文法的开始符
        self.V_N = []       # 文法的非终结符
        self.V_T = []       # 文法的终结符
        self.V_N_T = []     # 并集
        self.test_input = ''  # 样例输入
        self.First = {}     # first集
        self.Follow = {}    # follow集
        self.Table = {}     # 分析表


    def get_grammer(self):
        # 用于得到文法
        '''
        E->TE'
        E'->+TE'|^
        T->FT'
        T'->*FT'|^
        F->(E)|i
        '''

        self.grammer = { # 这里的E'用_E表示，其他也是如此
            'E': [['T', '_E']],
            '_E': [['+', 'T', '_E'], ['^']],
            'T': [['F', '_T']],
            '_T': [['*', 'F', '_T'], ['^']],
            'F': [['(', 'E', ')'], ['i']],
        }

        self.V_N = ['E', '_E', 'T', '_T', 'F']      # 非终结符
        self.V_T = ['+', '*', '(', ')', 'i', '^']   # 终结符
        self.V_a = ['+', '*', '(', ')', 'i', '#']   # 分析表的纵轴部分
        self.start_V = 'E'                           # 开始符号

    def input_data(self): # 输入内容
        # self.test_input = 'i+i*i#'
        print('输入一以#结束的符号串(包括+—*/（）i#)：',end='')
        self.test_input = input()
        if self.test_input[-1] != '#':
            print('ERROR! 结尾一定要是#')
            exit()


    def create_first(self):
        # 默认要处理的都是单个非终结符
        global flag
        while True:
            flag = 0  # 判断First集
            # 对于每一个非终结符
            for key in self.grammer:
                if key in self.V_T: # 终结符
                    add_value(self.First, key, key)
                else:   # 非终结符
                    for part in self.grammer[key]:
                        # 非终结符->终结符开头
                        if part[0] in self.V_T:
                            add_value(self.First, key, part[0])
                        else: # 非终结符->非终结符开头
                            # 把非终结符First集加入原来的First中
                            add_list(self.First, key, self.First, part[0])
                            pass

                        # 判断目前是否能够推出空符
                        for i in range(0, len(part)-1):
                            if part[i] not in self.First or '^' not in self.First[part[i]]:
                                break
                            add_list(self.First, key, self.First, part[i+1])
                            if i == len(part)-2 and '^' in self.First[part[i+1]]:
                                add_value(self.First, key, '^')

            if flag == 0: # First没有变化，结束
                break


    def create_follow(self):
        # 默认处理单个非终结符
        # 第 1 步
        add_value(self.Follow, self.start_V, '#')
        global flag
        while True:
            flag = 0 # 判断是否结束
            for key in self.grammer: # 对于每一个产生式
                for value in self.grammer[key]: # 对每一个结果
                    pre=''  # 指向前一个数的指针
                    this='' # 当前指针
                    for i in range(len(value)+1): # 遍历每一个
                        pre = this
                        # this = value[i]
                        if i < len(value): this = value[i]
                        # print(pre, this)
                        if i == 0:
                            continue
                        if i < len(value) and pre in self.V_N:
                            add_list(self.Follow, pre, self.First, this)
                            if this in self.V_N and '^' in self.First[this]:
                                add_list(self.Follow, pre, self.Follow, key)
                        if i == len(value) and pre in self.V_N:
                            add_list(self.Follow, pre, self.Follow, key)
            if flag == 0:
                break


    def create_analyse(self):
        # 初始化预测表
        for A in self.V_N:
            self.Table[A] = {}
            for a in self.V_a:
                if a == '^':continue
                self.Table[A][a] = ''

        # 进行预测表的构造
        for A in self.grammer: # 对于每一个产生式
            for part in self.grammer[A]: # 对产生式右部的每一部分
                for a in self.V_a: # 对于每一个终结符
                    if a == '^': # 横轴忽略空符
                        continue
                    if part[0] in self.V_T: # 右部开头为终结符，First集为本身
                        if a == part[0]:
                            self.Table[A][a] = part
                    elif a in self.First[part[0]]: # 右部开头为非终结符
                        self.Table[A][a] = part

                if part[0] in self.V_T: # 如果右部开头为终结符，first集为本身
                    if part[0] == '^': # 空符
                        for b in self.Follow[A]: #
                            if b not in self.V_N:
                                self.Table[A][b] = part
                elif '^' in self.First[part[0]]: # 右部开头不是终结符，判断空符是否属于first
                    for b in self.Follow[A]:
                        if b not in self.V_N:
                            self.Table[A][b] = part


    def check(self):
        # print('First =  ', self.First)
        # print('Follow = ', self.Follow)
        #
        # for i in self.Table:
        #     print(i, self.Table[i])
        # pass
        # 开始进行分析：
        index = 0
        stack = []
        temp = ''
        # 初始化
        stack.append('#')
        stack.append(self.start_V)
        print('步骤   ','分析栈  ', '剩余输入串   ', '所用产生式')

        # 分析开始
        while True:
            self.print_step(stack, index, temp) # 打印最后的分析步骤
            if stack[-1] == self.test_input[index] == '#': # 分析成功
                break
            if stack[-1] == self.test_input[index]: # 栈顶元素匹配成功
                stack.pop()
                index+=1
            if stack[-1] in self.V_N: # 如果栈顶符号为非终结符，查表
                if self.Table[stack[-1]][self.test_input[index]] == '':
                    print(self.test_input+'为非法符号串')
                    #print('ERROR!输入串不合法！')
                    #print('输入的符号"', self.test_input[index], '"无法匹配文法！')
                    exit()
                    break
                else:
                    temp = stack.pop()
                    for a in reversed(self.Table[temp][self.test_input[index]]):
                        if a != '^':
                            stack.append(a)

    def print_step(self, stack, index, last): # 打印最后的分析步骤
        global step
        # 步骤
        print("{:<7d}".format(step), end='')
        # 分析栈
        str = ''
        for ch in stack:
            str+=ch
        print('{:8}'.format(str),end='')
        print(' ', end='')


        # 剩余输入串
        print('{:12}'.format(self.test_input[index:]),end=' ')
        # 所用产生式
        if last != '':
            print(last,end='')
            print('->', end='')
            for ch in self.Table[last][self.test_input[index]]:
                print(ch, end='')
        print()
        step+=1


# 程序开始
LL = LL1()
LL.get_grammer()
LL.create_first()
LL.create_follow()
LL.create_analyse()
LL.input_data()
LL.check()
print(LL.test_input+'为合法符号串')
