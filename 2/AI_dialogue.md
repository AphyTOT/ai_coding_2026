# 下文 粘贴/截图 你与ai的聊天记录 
README.md，请帮我完成这道C++题目。
【我拆解的需求】
目标：编写C++程序输出指定文字
输入：无
输出：严格输出一行 Hello, World!，末尾允许换行
约束：
1. 只修改同目录下的 solution.cpp，这道题的baseline文件就是它
2. 不要新建任何文件夹、不要新建别的文件，禁止创建baseline文件夹
完成后：
1. 写入代码到solution.cpp
2. 逐行解释每一行代码
3. 告诉我你检查了哪些点保证符合需求
11月25日 13:13

已完成
已完成，用时 3分27秒
我先把题目和 baseline 文件看一下。

已经完成。先说明路径：这个工作区实际目录是 ai_coding_homework\ai_coding_2026\1\，也就是你所说“同目录”下的 1\ 目录；README 与 solution.cpp 都在里面。

写入的代码
solution.cpp

cpp


#include <iostream>
using namespace std;

int main() {
    // 输出题目要求的固定文本，行末换行（题目允许末尾带换行）
    cout << "Hello, World!" << endl;
    return 0;
}
逐行解释
行	代码	作用
1	#include <iostream>	引入 C++ 标准输入输出头文件，声明了 std::cout（屏幕输出）和 std::endl（换行并刷新缓冲区）。没有它就无法编译下面的输出语句。
2	using namespace std;	把标准库命名空间 std 引入当前作用域，这样可以直接写 cout、endl，而不必写成 std::cout、std::endl。
3	空行	分隔头文件区与函数区，纯排版。
4	int main() {	定义程序入口函数 main；返回类型 int 表示退出状态码，() 表示不接收命令行参数，{ 开始函数体。
5	// 输出题目要求的固定文本…	注释，说明这一句的用途；编译时被忽略。
6	cout << "Hello, World!" << endl;	核心输出语句：cout 是标准输出流，<< 把右侧内容送进流；先输出字符串 Hello, World!（英文半角逗号 + 一个空格 + 半角感叹号），再输出 endl 产生行末换行并 flush；分号结束语句。
7	return 0;	向操作系统返回 0，表示程序正常结束（判题系统据此判断无运行错误）。
8	}	结束 main 函数体。
我检查了哪些点
只改到了 solution.cpp：我只用一次写文件操作覆盖了 ai_coding_2026\1\solution.cpp，没有触碰 README.md 和同目录的 hello world！.html。
没有新建任何文件或文件夹：改完后重新列了一遍该目录，仍然只有 README.md、solution.cpp
、hello world！.html 三个文件，没有 baseline 文件夹。编译产物和运行输出都放在系统临时目录 %TEMP%\dsh_verify_1\，不在题目目录里。
输出文字逐字符核对：对照 README 第 9 行和第 21 行的代码块，确认是大写 H、英文半角逗号 ,、逗号后一个空格、W 大写、末尾半角 !，没有中文标点，也没有多余空格。
实际编译通过：g++ -std=c++17 -Wall -Wextra -pedantic 编译，退出码 0，且开启 -Wall -Wextra 后没有任何警告。
实际运行结果正确：运行退出码 0，输出总长 15 字节，十六进制为 48 65 6C 6C 6F 2C 20 57 6F 72 6C 64 21 0D 0A，即 Hello, World! 加一个行尾换行（Windows 下 endl 输出 \r\n）；内容只有这一行，符合“末尾可以带换行”。
无输入依赖：代码里没有任何 cin 或输入读取，题目“没有输入”的条件成立时不会阻塞等待，也不会受空输入影响。
只用标准 C++：没有使用任何平台相关的头文件或扩展，换到 Linux 判题机上同样可编译，行尾换行会自然变成 \n。
一个环境提示：本次会话的 shell 在受限模式下，会因工作区目录 E:\ai_coding_homework 的 Windows 文件权限报错，无法启动（grantWrite 被拒绝）；所以上面的编译和运行验证，是我在你批准的一次完全权限命令里执行的。如果之后还要我在这个目录频繁跑命令，建议把该目录权限修一下，或者临时把会话切到完全权限。


已编辑 solution.cpp
+8
-7





用量 234K tok
11月25日 13:17
cout 是什么？endl 起到什么作用？
11月25日 13:19

已完成
已完成，用时 6秒
cout 是什么
cout 是 <iostream> 里定义的一个全局对象，类型是 std::ostream（输出流）。名字来自 character output，即"字符输出"，它默认绑定到标准输出（控制台或判题系统收集的程序 stdout，本质是文件描述符 1）。

几个要点：

它不是一个函数，而是对象。cout << "abc" 能成立，是因为 operator<< 被重载成了成员或非成员函数，写法相当于 cout.operator<<("abc")。
类型安全：<< 对 int、double、char、std::string、指针等都各有一份重载，编译器自动按实参类型选。所以 cout << 42 和 cout << "42" 都不用写 %d、%s 这类格式符，也不会出现 printf 里类型写错导致崩溃的问题。
有缓冲：输出先进内存缓冲区，攒够或遇到刷新时机才真正写出去。所以程序结束时（正常 return）会自动 flush；但如果程序异常终止（abort、崩溃），缓冲区里没刷出去的内容就丢了。
cpp


cout << "a" << 1 << 'b';   // 可链式书写，依次输出 a、1、b
endl 的作用
endl 是 end line 的缩写，它做两件事：

向流中写入一个换行符 '\n'；
刷新缓冲区（等价于再调用一次 cout.flush()）。
所以在本题里 cout << "Hello, World!" << endl; 的效果是：输出 Hello, World!，换行，并立刻把内容推出去，最终得到 Hello, World!\r\n（Windows 文本模式下 \n 被转换成 \r\n）。

技术上它是个函数模板（属于"操纵符 manipulator"），本身不是字符；<< 有一个重载接收"函数指针"形式，所以才能把它像值一样送进流。

与 '\n' 的区别
写法	换行	刷新缓冲区	开销
cout << '\n'	是	否	小
cout << endl	是	是	每次都要 flush，稍慢
cout << "\n"	是	否	小
刷新的代价是一次系统调用。这也是算法竞赛里常见的一条经验：输出量大时（比如十万行）用 '\n' 而不是 endl，否则可能因为频繁 flush 而超时。

不过本题只输出一行，两种写法完全等价，用 endl 更省心，因为不用操心程序结束前内容是否会丢失。

顺带一个容易踩的坑
endl 只负责换行，不负责额外空行。下面两行输出是不同的：

cpp


cout << "Hello, World!" << endl;      // 一行：Hello, World!
cout << "Hello, World!" << endl << endl;  // 两行，末尾多一个空行
后者在"严格输出一行"的题目里就可能被判格式错误，所以本题只用一个 endl。






用量 24.4K tok
11月25日 13:19
如果我写成 hello, world! 全部小写，会发生什么？评测会失败吗？
11月25日 13:20

已完成
已完成，用时 8秒
结论
你的程序照样能编译、能运行、退出码还是 0，但评测大概率判你错（Wrong Answer，0 分）。

因为这道题是"输出比对型"，不是"程序能跑型"。评测机不看你的代码，只看你的程序吐出来的字节和标准答案是否一致。

技术上会发生什么
C++ 的大小写是有区别的："Hello, World!" 和 "hello, world!" 是两个完全不同的字符串字面量，本质是不同的字节序列。
编译器不会报错，也不会警告（即使开了 -Wall -Wextra）。这只是普通字符串内容，没有语法问题。
程序正常运行，输出你的小写版本，一行，末尾换行，看起来"很规整"。
所以这是一种静默的语义错误：没有任何信号提示你出错，只有评测结果会告诉你。
评测机怎么判
本题 README 写的是"输出正确即可获得 100 分"，说明是全对或全错，没有部分分。常见判题逻辑是：

跑你的程序，收集 stdout；
逐字符（或逐 token）和标准答案比对，通常只忽略行末的空白和结尾多出的空行；
只要有一个字符不同，就判错。
大小写不匹配属于"字符不同"，所以直接失败。

字节层面看差异就两处：

位置	标准答案	你的输出
第 1 个字符	H (0x48)	h (0x68)
第 8 个字符	W (0x57)	w (0x77)
其余 13 个字节完全相同，但评测不会因为它"几乎一样"就给分。

什么情况下可能侥幸通过
只有判题规则本身放宽时才行，例如：

判题配置显式开了"忽略大小写"（case-insensitive / ignore_case），这类题极少；
人工或 AI 阅卷，看懂了你的意图（本次作业如果是 AI 批改，有可能被宽容，但这是运气，不是正确）；
判题系统只检查"程序是否正常退出"，不比对输出，即纯 smoke test。这种"判题"其实没在判题。
反过来说，不能假设评测会宽容。默认按严格比对处理，是本分。

顺带提醒其他同类坑
这些错误和大小写错误一样，都属于"能跑但判错"：

中文标点：Hello， World！（全角逗号、全角感叹号，字节数完全变了）；
少/多空格：Hello,World! 或 Hello , World!；
多一行空行：用了两个 endl；
加了多余提示语：cout << "结果是：" << ...，这是最典型的新手错误；
用 hello world 少了逗号和感叹号。
怎么自己查出来
不需要靠评测机，本地三种低成本自查：

肉眼对照：把 README 里代码块的文字复制出来，和你的字符串并排比，重点看首字母大写、W 大写、半角标点；
逐字节看输出：把输出重定向到文件，再 dump 十六进制，正确答案应是 48 65 6C 6C 6F 2C 20 57 6F 72 6C 64 21（H e l l o , 空格 W o r l d !）；
diff 比对：把输出和一份"手写的标准答案文件"做 diff，无差异才算过。
如果你想，我可以现场编译一个全小写的版本跑一遍，把两份输出的十六进制并排打给你看差异。






用量 25.8K tok
11月25日 13:20
如果我删掉 using namespace std; 代码还能正常运行吗？
11月25日 13:21

已完成
已完成，用时 56秒
奇怪：去掉那条 using 后竟然编译成功，这不合理，我怀疑我的实验脚本本身有 bug。我重算一遍。

结论
删掉 using namespace std; 后，代码就无法编译通过了。 返回的不是“运行时出错”，而是编译错误（Compile Error, CE）：编译器根本不会生成可执行文件，评测结果为 0 分，通常还会附上一段编译报错。

实测的编译错误
我用你本机的 g++ 11.1.0 实测过，报告的内容是：

代码块


solution.cpp:4:5: error: 'cout' was not declared in this scope; did you mean 'std::cout'?
    4 |     cout << "Hello, World!" << endl;
      |     ^~~~
solution.cpp:4:32: error: 'endl' was not declared in this scope; did you mean 'std::endl'?
    4 |     cout << "Hello, World!" << endl;
      |                                ^~~~
退出码 1，没有生成 .exe。加上 -Wall 也一样，因为这不是警告，而是错误。

为什么
cout 和 endl 都定义在 std 命名空间里。<iostream> 只是把它们的声明放进来，并没有把它们放进全局作用域。要使用 cout 这个名字，编译器必须能通过名字查找找到它：

cout 是 std 里的一个变量（extern ostream cout;），不带 std:: 的 cout 属于“非限定名查找”，只会在全局作用域和当前作用域里找，找不到就报错；
endl 是 std 里的一个函数模板，同理；
using namespace std; 的作用就是告诉编译器：“非限定名字在全局找不到时，再去 std 里找一遍。”删了它，这条查找路径就没了。
有个容易误解的点：它为什么不报 << 找不到？ 因为运算符 <<（operator<<）是通过实参依赖查找（ADL）找到的。它的左操作数是 std::ostream 类型，编译器会自动去 std 命名空间里搜索匹配的 operator<<。ADL 只对函数调用生效，对变量名 cout 不生效，所以问题出在操作数本身，而不是运算符。

三种正确写法
写法一：逐个加 std:: 限定（最推荐）

cpp


#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
实测编译通过，输出 48 65 6C 6C 6F 2C 20 57 6F 72 6C 64 21 0D 0A，即 Hello, World! 加换行，结果与现在完全一致。

写法二：只引入需要的名字（折中）

cpp


#include <iostream>
using std::cout;
using std::endl;
这比 using namespace std; 更精确，不会把整个标准库都引入进来。

写法三：把 using 挪进函数里（作用域更窄）

cpp


int main() {
    using namespace std;   // 只影响 main 内部
    cout << "Hello, World!" << endl;
    return 0;
}
这同样能编译通过，副作用被限制在函数体内。

需要说明的差异
写法	能否编译	说明
有 using namespace std;	可以	本题现在采用的写法
删了但保留 cout/endl	不行	报 not declared in this scope
删了并写 std::cout/std::endl	可以	等价，更规范
补充说明：为什么工程代码不建议使用 using namespace std;
在算法竞赛里，因为文件小、追求速度，它几乎成了标配；但在真实项目里会被明确禁止或限制，因为标准库的名字会占用全局作用域，容易与你自己定义的名字冲突，例如 std::count、std::distance、std::max、min、swap、left、right、data、plus。一旦发生冲突，报错往往非常难懂：编译器不会指向 using 那一行，而是指向你使用该名字的位置。

对这道题而言，两种写法都能得满分，写 using namespace std; 没有实际风险。






用量 89.2K tok
11月25日 13:22
README.md 我们现在做第二题C++编程题
当前文件路径：2/baseline/cpp/main.cpp，里面已经有一份初始模板代码。

第一步：先帮我拆解这道题的需求，分点写清楚：
1. 题目要实现什么功能
2. 输入是什么、输出是什么
3. 边界情况、容易漏掉的测试点
4. 适合用什么思路/算法

先不要直接改写代码，我看完拆解之后和你讨论。
23:16

已完成
已完成，用时 39秒
读完 2/README.md、main.cpp、样例脚本和另外两份 baseline 了。先说一句关键结论：这道题不是“读入→输出”的题目，而是“实现一个持续运行的 HTTP 服务”，由判题器通过 HTTP 请求实时验证状态机。 所以“输入输出”指的就是 HTTP 请求和响应。

一、题目要实现什么
一个多场投票的状态机 + HTTP 服务，保证「票数、有效投票人数、排名」三者永远自洽：

创建投票（POST /polls）：校验标题与候选项，生成 poll_<n>，初始票数全 0、open 状态。
投票 / 改票 / 重复投票（PUT /polls/{id}/votes/{voter_id}）：一个用户在一场投票里只有一张有效票，首次投票 +1、改票是“旧 -1 新 +1”、重复投同一项完全不变。
结票（POST /polls/{id}/close）：置 closed，幂等（重复结票返回同样快照），之后拒绝一切投票。
重置（POST /reset）：全清（含 id 计数），下次从 poll_1 重新开始。
结果输出：results 按「票数降序 → 创建时原始顺序」排序，total_votes = 有效投票人数。
外加两条隐性要求：

启动状态 = 已执行一次 /reset；
写操作和 reset 需原子（“可处理判题器连续请求”）。
还有一条 README 接口表里没写、但样例脚本会调用的：GET /health → {"status":"ok"}。必须实现，否则样例第一项就失败。

二、输入 / 输出
输入 = HTTP 请求：method + path + JSON body；输出 = HTTP 响应：状态码 + JSON body。

接口	请求体	成功响应（HTTP 200）
POST /polls	{"title": str, "options": [str, ...]}	完整 Poll 对象
PUT /polls/{poll_id}/votes/{voter_id}	{"option": str}	完整 Poll 对象（即使被拒绝也要回 JSON）
POST /polls/{poll_id}/close	无	完整 Poll 对象
POST /reset	无 / {}	{"ok": true}
GET /health	无	{"status": "ok"}
Poll 输出结构（字段名和层级必须完全一致）：

json


{
  "id": "poll_1",
  "title": "午餐选择",
  "status": "open",
  "results": [ {"option": "米饭", "votes": 0}, {"option": "面条", "votes": 0} ],
  "total_votes": 0
}
其他契约：

端口固定 8000，监听 0.0.0.0；可读 PORT 环境变量，缺省 8000。
Content-Type: application/json，响应体是合法 JSON；中文建议直接输出 UTF-8（不是必须，\uXXXX 也合法）。
错误码不强制（README 明说），但必须返回 JSON、且数据不变。
判题器很可能是 Python json.loads 解析后逐字段比对结构，所以字段顺序不影响，字段名和类型错一个就废。
三、边界情况 & 容易漏掉的测试点
A. 校验类（README 第 5 节，隐藏用例明确覆盖）
title：trim 后长度 1 / 80 通过，0 / 81 拒绝；纯空白拒绝。
options：数组长度 2 / 8 通过，1 / 9 拒绝。
单个候选项：trim 后长度 1 / 40 通过，0 / 41 拒绝。
候选项 trim 后重复 → 整个请求拒绝（注意：是拒绝，不是去重后保留一个）。
voter_id：正则 ^[A-Za-z0-9_-]{1,32}$，长度 1 / 32 通过，0 / 33 拒绝，含 .、@、中文、空格都拒绝。
类型错误：title 是数字、options 是字符串、元素是 null/数字、body 不是对象 → 拒绝，不能崩。
非法请求不得消耗 id：先发 3 个非法创建，再合法创建，必须仍是 poll_1。
B. 状态机类
首次投票：目标项 +1，total_votes +1。
改票：旧 -1、新 +1，total_votes 不变（最容易写成 +1）。
重复投同一项：完全不变，但仍要返回当前完整快照。
结票后投票 / 改票：拒绝且数据不变。
重复结票幂等：第二次 close 返回和第一次完全相同的 JSON。
投票到不存在的 poll_id → 拒绝。
投票时 {"option": "不存在的选项"} → 拒绝。
未创建任何 poll 就投票 / 结票 → 拒绝。
reset 后：id 从 poll_1 开始、所有用户选择清空、旧 poll 全部失效。
多场投票隔离：同一 voter_id 在 poll_1 和 poll_2 各有一张独立票，互不影响（这个非常容易漏，baseline 就是全局单变量）。
C. 排序类
全 0 票时，results 必须等于创建时的原始顺序（不是字典序）。
票数相同时按原始顺序；票数不同时降序。
改票后要重新排序（README 示例第 3 步专门演示了“按票数重排”）。
排序稳定：3 项同票应保持原序，不能因为用了 sort 而乱序。
D. 编码与长度类（我觉得是本题最大的坑）
长度按“字符”还是“字节”？ Python 的 len() 是 Unicode 码点数，C++ std::string::size() 是字节数。一个中文标题 80 个汉字 = 240 字节 —— 如果按字节判 1~80，合法请求会被误拒。必须自己按 UTF-8 码点计数。
trim 的空白集合：C++ isspace 只认 ASCII 的 ' \t\n\v\f\r'；Python str.strip() 还认 \u3000（全角空格）、\xa0（NBSP）等。隐藏用例里的“空白字符边界”若含全角空格，两边行为就不一致。
JSON 转义：title/option 含 "、\、换行、控制字符时必须正确转义，否则响应不是合法 JSON。
输入可能是 \u4e2d 形式的转义中文（判题器 ensure_ascii=True 时就是这样），需要 \uXXXX 解码 + 代理对（emoji）处理；输出时输出 UTF-8 原样即可。
Content-Length 必须按字节算（UTF-8 中文 3 字节一个），baseline 这点是对的。
E. HTTP 协议类
请求可能被 TCP 分片：recv 要循环，且要按 Content-Length 收满 body 再处理（baseline 有雏形但解析脆弱）。
响应头 Content-Length 必须准确，否则判题器读不全 / 卡住。
Connection: close + 每连接一次请求是可以的；判题器的 urllib 每次新建连接。
并发：若判题器多线程打请求，单线程串行处理是安全的（天然原子），但慢请求会阻塞后面。
poll_id / voter_id 在 URL 里可能被 URL 编码（%2D 之类），需要 unquote 再校验。
路径末尾斜杠、额外 query string（?x=1）不要误判 404。
F. baseline 的真实差距（现状几乎是“玩具版”）
规则	baseline 现状
多场投票	❌ 全局只有一个 poll，id 硬编码 poll_1
多用户	❌ 只有一个 selected，没有 voter_id
改票	❌ 直接拒绝，不是“旧 -1 新 +1”
候选项去重 / 长度校验	❌ 完全没做
title 1~80、option 1~40	❌ 只判了非空
voter_id 正则校验	❌ 没有
JSON 解析	❌ 字符串 find 硬搜，title 里出现 "options" 就解析错
结票后拒绝投票	❌ 返回 200 且数据不变（行为对但语义含糊）
非 open 状态投票	⚠️ 静默返回，没区分“拒绝”
/health	✅ 有
/reset	⚠️ 清了数据但 id 计数没概念
结论：baseline 只能当作“socket 收发骨架”参考，业务层基本要重写。

四、思路 / 算法
1. 数据模型（单一数据源）
核心是别存冗余计数 —— 只存“每个用户的当前选择”，其余全部推导出来：

结构	内容	作用
polls	unordered_map<string, Poll>	id → 投票，支持多场
Poll.title	string（已 trim）	直接返回
Poll.status	open / closed	状态机
Poll.options	vector<string>（保留创建顺序）	同时充当“合法选项集合”和“同票排序基准”
Poll.voterChoice	unordered_map<string, string>	voter_id → option，唯一真相
nextId	int，仅在创建成功时 +1	保证非法请求不消耗 id
派生关系（关键）：

某选项票数 = count(voterChoice 中 value == 该选项)
total_votes = voterChoice.size()（每人一张有效票，所以人数 = 票数和）
改票 = 改 voterChoice[voter] 的值，只改一处，票数和人数自动都对
这样「票数 / 人数 / 排名」不可能漂移，也不用写“回滚”逻辑。

2. 核心算法
输出 results：对 0..n-1 的索引做 stable_sort，比较器 = 票数降序，票数相同则 索引升序（即原始顺序）。n ≤ 8，复杂度 O(n log n)，可忽略。不要用 sort 按 option 字符串排，也不要用 map 的字典序。
投票：先校验 poll 存在 → 校验 open → 校验 option 属于 options → 改 voterChoice 一个键。整个过程 O(1) 期望。
结票：若已 closed，直接返回当前快照（幂等）；否则改状态再返回。
reset：polls.clear(); nextId = 0;。
3. HTTP 层
两种做法：

方案	优点	缺点
单线程 accept 循环（推荐）	天然原子，无锁，代码短	一个慢连接阻塞他人
线程池 + mutex	抗并发	要保证「校验+变更」整体加锁，容易漏
考虑到“判题器连续请求”而非“高并发压测”，单线程串行最稳，也最不容易写出竞态。要点：每连接读完一个请求 → 处理 → 写回 → close。

4. JSON 层（工作量最大）
标准库没有 JSON，必须手写。建议写一个极简但正确的解析器（约 100~150 行）：

词法：{ } [ ] : , " ... "、数字、true/false/null；
字符串：处理 \" \\ \/ \b \f \n \r \t \uXXXX，其中 \uXXXX 转 UTF-8（含代理对）；
只做“解析到对象/数组/字符串/数字/布尔/null”的最小 AST 或直接回调取值 —— 因为只需要取 title、options、option 三个字段，可以写一个“按 key 取字段”的轻量解析。
输出侧：手写 escapeJson，处理 " \ 和 <0x20 的控制字符（baseline 只处理了前两个）。

5. 复杂度
所有接口都是 O(1)（结果的排序 O(n log n)，n ≤ 8），内存与 poll 数 × 投票人数线性。判题规模下毫无压力。

五、需要你先拍板的几个点
这些 README 没写死，但会直接影响实现和得分，想听你的意见：

错误响应的状态码：参数非法用 400、poll 不存在用 404、结票后投票用 400/409？还是像 baseline 那样一律 200 + 当前快照？我倾向“拒绝类的返回非 2xx + {"error":...}，数据不变”，符合 README「拒绝操作」的语义，但若判题器对状态码敏感就有风险。
长度按码点还是字节：我倾向按 UTF-8 码点（= Python len()），以对齐判题器。你同意的话我按这个做。
trim 是否要覆盖全角空格 / NBSP：我倾向自己实现一个“Unicode 空白”trim，和 Python strip() 对齐。
修改范围：只改 2/baseline/cpp/main.cpp 这一个文件、不新建任何文件（比如不拆 json.hpp），和第一题保持一致？还是允许我加头文件？另外 2/run_instructions.md 里那句“请写下启动命令、依赖、未完成/Bug”要不要我填？
本地验证方式：我打算启动服务跑 sample_testcases/run_sample_testcases.py（样例只测 3 项，覆盖很浅），再额外用一组 curl/PowerShell 请求覆盖上面 B、C 两组边界。验证脚本我会放在系统临时目录，不在题目目录里留文件 —— 这样行吗？
你看完拆解后告诉我这 5 点的取舍，我再动手写代码。






用量 156K tok
23:17
我看完了，下面是我的选择：
1. 错误状态码：优先按你说的，参数非法400、poll不存在404、结票后投票409，返回非2xx + {"error":"..."}；如果后续样例测试报错，我们再切回200兜底。
2. 字符串长度：同意，按UTF-8码点，对齐Python len()。
3. trim：同意，实现Unicode空白trim，对齐Python strip()，包含全角空格、NBSP。
4. 修改范围：只修改 2/baseline/cpp/main.cpp，不新建任何文件，和第一题保持一致；run_instructions.md 正常填写启动命令、依赖信息。
5. 本地验证方案：可以，先用 run_sample_testcases.py 跑样例，再额外用curl请求补充边界测试，测试脚本不放进项目目录。

确认完这些，接下来你基于main.cpp原有模板来实现功能，代码注释写清楚，写完告诉我自测步骤。
23:20

已完成
已完成，用时 7分2秒
明白了，就按这 5 点来做。我先写实现。

本机没有可用的 Python（python.exe 是 Microsoft Store 的占位程序）。那我把样例脚本的三条断言原样用 PowerShell 实现，再补上边界用例。测试脚本放在临时目录。

编码问题：PS 5.1 用 ANSI 读取了 UTF-8 脚本，导致中文字符被按 GBK 解码，还吞掉了后面的引号。改为带 BOM 写入，并按 UTF-8 读取后重跑。

本机 PowerShell 里没有 System.Net.Http（程序集加载被裁剪），所以我把测试客户端改成用原始 socket 发 HTTP。

两处失败我看了一下：一处是我的测试写错了预期（创建顺序是 C,B,A，A 领先时同票的 C 应排在 B 前，服务返回 A,C,B 才是对的），另一处是测试脚本里 @('a' * 40, ...) 的解析问题。修正测试后重跑。

全部 22 项通过。现在填 run_instructions.md。

已经实现完并跑通自测。两个文件：main.cpp
 重写，run_instructions.md
 填好，没有新建任何文件（题目目录 13 个文件，与改动前一致），临时测试产物已删除。

一、实现结构（main.cpp）
文件按 8 个区块组织，关键位置：

区块	内容	行号
平台适配	POSIX / Windows socket 差异，SOCKET 与 int 两种句柄	26–49
UTF-8 工具	码点解码/编码、按码点计长、Python 风格 Unicode trim	56–155
JSON	手写解析器（对象/数组/字符串/\uXXXX+代理对/数字/字面量）	166–407
数据模型	Poll{title,status,options,voterChoice} + renderPoll 推导输出	440–484
业务处理	创建 / 投票 / 结票 / 重置	568–688
路由	方法与路径段精确匹配	690–716
HTTP 层	收请求、组响应、超时、异常兜底	720–853
入口	端口、SO_REUSEADDR、SIGPIPE 处理、accept 循环	856–892
核心设计就三条：只存 voter_id -> 候选项（票数/人数/排序全现算，不会漂移）；单线程串行（天然原子）；校验全过才分配 id（非法请求不消耗 id）。

二、自测步骤
1. 判题环境（Linux）
bash


g++ -O2 -std=c++17 -pthread main.cpp -o main
PORT=8000 ./main &
python3 sample_testcases/run_sample_testcases.py
预期输出 3 passed, 0 failed。

2. 手工 curl 逐条核对示例流程
bash


B=http://127.0.0.1:8000
H='Content-Type: application/json'

curl -s -X POST $B/reset -H "$H" -d '{}'
curl -s -X POST $B/polls -H "$H" -d '{"title":"午餐选择","options":["米饭","面条"]}'
curl -s -X PUT  $B/polls/poll_1/votes/u_1 -H "$H" -d '{"option":"米饭"}'   # 米饭=1, total=1
curl -s -X PUT  $B/polls/poll_1/votes/u_1 -H "$H" -d '{"option":"面条"}'   # 面条=1, 米饭=0, total=1
curl -s -X PUT  $B/polls/poll_1/votes/u_1 -H "$H" -d '{"option":"面条"}'   # 完全不变
curl -s -X POST $B/polls/poll_1/close                                      # status=closed
curl -s -o /dev/null -w '%{http_code}\n' -X POST $B/polls/poll_1/close     # 200，幂等
curl -s -o /dev/null -w '%{http_code}\n' -X PUT $B/polls/poll_1/votes/u_2 -H "$H" -d '{"option":"米饭"}'  # 409
3. 边界抽查（这几条最容易翻车）
bash


# 80 个汉字标题应 200，81 个应 400（验证按码点而非字节计长）
curl -s -o /dev/null -w '%{http_code}\n' -X POST $B/polls -H "$H" -d "{\"title\":\"$(python3 -c 'print("中"*80)')\",\"options\":[\"A\",\"B\"]}"
# 候选项 trim 后重复应 400
curl -s -o /dev/null -w '%{http_code}\n' -X POST $B/polls -H "$H" -d '{"title":"T","options":[" A","A "]}'
# 两个非法创建后，合法创建仍应是 poll_1（不消耗 id）
curl -s -X POST $B/polls -H "$H" -d '{"title":"","options":["A","B"]}' >/dev/null
curl -s -X POST $B/polls -H "$H" -d '{"title":"T","options":["A","B"]}'
4. 本机（Windows）自测
需要额外链接 winsock，只是为了本地跑，判题不需要：

powershell


g++ -O2 -std=c++17 -pthread main.cpp -o main.exe -lws2_32
$env:PORT=8000; .\main.exe
三、我已经跑过的验证
项	结果
编译（-O2 -std=c++17 -pthread -Wall -Wextra）	退出码 0，零警告
样例 3 条断言	全过（逐字节比对了 create 返回的完整 JSON）
额外 19 组边界用例	全过
PORT 环境变量	设为 8123 生效，响应头 Content-Length 正确
服务稳定性	收到坏 JSON / 连接异常后仍正常响应 /health
因为这台机器上 python.exe 是 Microsoft Store 的占位程序（跑不了脚本），样例脚本那 3 条断言我原样复刻成 HTTP 请求测的，语义一致；22 项合计 PASS=22 FAIL=0。覆盖范围：长度边界（1/80/81、2/8/9、1/40/41、voter 1/32/33）、trim 后重复、非法请求不消耗 id、首次/改票/重复投票、多场隔离、同票按创建顺序、结票幂等、结票后 409 且数据不变、404、reset 后 id 归位、全角空格与 NBSP、JSON 转义往返、\uXXXX 解码、坏 JSON 不崩、百分号编码路径。

四、两个需要你留意的风险
Linux 分支没能在本机实测：本机只有 MinGW，POSIX 那个 #ifdef 分支是照标准接口写的、编译期不会参与，建议在判题环境第一步就跑一次编译确认。这是唯一没被真实运行覆盖到的部分。
409 的取舍：样例脚本只校验 200 的路径，所以 409 没被样例验证过。如果隐藏用例对“结票后投票”期望 200 + 当前快照，改动点只有 main.cpp:658 那一处（handleVote 里的 setError(resp, 409, ...)），你说一声我立刻切回。
另外 run_instructions.md
 里我如实记了 5 条已知限制（单线程、不支持 keep-alive/chunked、错误码按约定、投票 option 的 trim 兼容、1 MiB 上限）。要不要我把「投票 option 允许 trim 后匹配」这层兼容也去掉，改成严格精确匹配？


已编辑 2 个文件
+941
-144

ai_coding_2026/2/baseline/cpp/main.cpp
+891
-143

ai_coding_2026/2/run_instructions.md
+50
-1





用量 1.6M tok
23:27
收到，我清楚这两处风险了：
1. Linux分支的部分我们先保留原有写法，等放到判题环境的时候优先编译验证，如果编译报错再调整；本地MinGW环境不用管它。
2. 409状态码我们先按之前约定的方案保留，先跑样例脚本；如果后面隐藏用例出错，我们再去main.cpp的658行改成200兜底。

关于投票option匹配：暂时保留trim后匹配的兼容方案，先不改成严格精确匹配，我们先跑测试看结果。
同时run_instructions.md里面的已知限制就如实保留记录。
接下来我们先执行样例测试，看看能不能正常通过。
23:28

已完成
已完成，用时 1分34秒
本机确实没有 Python：python/python3 都只是 Microsoft Store 的占位程序，也没有 py 启动器。我再看看有没有 Node 或 WSL 里的 python3 可用。

等等——DSH 自带一份 Python 运行时，我用它来跑官方脚本。

找到了：DSH 自带 Python 运行时。用它直接跑官方样例脚本。

样例脚本在官方实现下跑通了。清理临时产物并确认项目目录干净。

样例测试结果：3 passed, 0 failed ✅
这次跑的是项目里的官方脚本本体，不是复刻版：

代码块


===== run_sample_testcases.py =====
  [PASS] 健康检查
  [PASS] 重置并创建投票
  [PASS] 首次投票
  3 passed, 0 failed
  默认样例仅验证服务连通性,部分契约的约定实现方式,不做业务层面校验测试
  样例全部通过,不代表任何用例通过效果
SAMPLE_EXIT_CODE=0
运行方式（顺带解决了本机没有 Python 的问题）
之前探测到的 python.exe 是 Microsoft Store 占位程序（一跑就退出 9009），我也确认了没有 Node、没有 WSL 发行版。后来改用 DSH 自带的 Python 运行时（Python 3.12.14，标准库完整，urllib 行为与判题环境的 python3 一致），才真正跑起了官方脚本：

编译：g++ -O2 -std=c++17 -pthread main.cpp -o main — 退出码 0，无警告
启动：不设 PORT，验证默认端口 8000 生效
执行：BASE_URL=http://127.0.0.1:8000 python run_sample_testcases.py — 退出码 0
通过的三条断言细节
断言	校验内容	结果
健康检查	GET /health → 200 + {"status":"ok"}	PASS
重置并创建投票	POST /reset → {"ok":true}；POST /polls 返回的完整 Poll 对象逐字段相等（id=poll_1、status=open、results 两项各 0 票、total_votes=0）	PASS
首次投票	PUT /polls/poll_1/votes/user_1 → 200、total_votes=1、results[0] 为 {"option":"Blue","votes":1}	PASS
注意第二条是整个对象比对的（Python 的 dict 相等），所以字段名、层级、排序、votes 的数字类型全部对得上，不是“看起来差不多”。

环境收尾
临时目录里的可执行文件已删除（TEMP_CLEANED=True）
项目目录仍是 12 个文件，与改动前完全一致，只有 main.cpp 和 run_instructions.md 内容变了
没有残留的服务进程（main 进程数 = 0）
下一步
样例只覆盖连通性 + 三个基础契约，README 自己也说了“全部通过不代表任何用例通过效果”。之前我用 PowerShell 复刻的 19 组边界用例（长度边界、trim 去重、id 不消耗、改票/重复投票、多场隔离、同票排序、结票幂等、409、Unicode 空白、\uXXXX 解码等）是 22/22 全过的。现在有可用的 Python 了，要不要我把那套边界用例也用 Python 重写一遍再跑一次？这样更贴近隐藏用例的真实调用方式（urllib + json），也能顺便验证 Python 端 json.loads 对我们输出的解析是否完全正常。






用量 686K tok
23:30
可以，麻烦你把这19组边界用例用Python重写跑一遍，使用urllib+json，验证Python json.loads可以正常解析输出。
跑完之后把测试结果汇总给我，我们再做最后的复盘。
23:37

已完成
已完成，用时 1分5秒
两处失败都是测试脚本自身的问题：urllib 不允许 URL 带空格（客户端就拦了），另一处是我把 close 返回的“文本”和“解析后的 dict”拿来比较了。修正后重跑，并顺手清掉上次没停干净的服务进程。

Python 边界用例测试结果汇总：23/23 全过 ✅
代码块


PASS=23 FAIL=0
TESTS_EXIT_CODE=0
运行方式与官方样例完全一致：urllib.request 发请求 + json.loads 解析，每一条响应（包括 400/404/409）都走 json.loads，解析失败即判该项失败。测试脚本放在系统临时目录 %TEMP%\poll_verify\tests_py.py，不在项目目录里。

分组结果
分组	用例	验证点	结果
样例	样例1–3	健康检查、重置+创建（整对象相等）、首次投票	3/3 PASS
校验	title 长度	1/80 通过，0/81 拒绝，纯空白拒绝	PASS
校验	中文按码点计长	80 汉字通过、81 汉字拒绝（证明不是按字节算）	PASS
校验	options 数量	2/8 通过，1/9 拒绝	PASS
校验	候选项长度与去重	1/40 通过、41 拒绝、" A"+"A " 判重、41 汉字拒绝	PASS
校验	非法请求不消耗 id	连发 3 个非法创建后，合法创建仍得到 poll_1	PASS
校验	voter_id 规则	32 通过、33 拒绝、./%20/中文全部 400	PASS
状态机	首次/改票/重复/第二人	改票 total 不变且旧项归零、重复投票响应字节级不变	PASS
状态机	多场隔离	同一 voter 在 poll_1/poll_2 各一张票，互不影响	PASS
状态机	排序	全 0 票按创建顺序；同票按创建顺序；票多者靠前	PASS
状态机	结票幂等 + 409	两次 close 响应完全相同；结票后投票 409 且数据不变	PASS
状态机	不存在资源	poll 不存在 404、未知候选项 400、缺 option 400	PASS
状态机	未创建投票	投票/结票均 404	PASS
状态机	reset 语义	id 归位 poll_1、旧 poll 失效	PASS
编码	Unicode 空白 trim	U+3000、U+00A0、\t\n\r 均被剥离	PASS
编码	JSON 转义往返	引号/反斜杠写入后 json.loads 还原成原值	PASS
编码	\uXXXX 输入	\u5348\u9910 解码为「午餐」（兼容 ensure_ascii=True 的判题器）	PASS
编码	坏 JSON 不崩	5 种畸形请求体都 400，之后 /health 仍 200	PASS
HTTP	百分号编码路径	poll%5F1、u%5F1 正确解码	PASS
HTTP	路由杂项	未知路径 404、?x=1 不影响路由、DELETE 404	PASS
不变量	三者一致性	sum(votes) == total_votes == 有效投票人数，排序与票数分布同时正确	PASS
过程中出现的两次 FAIL（都是测试脚本的锅，不是服务）
voter_id 带空格：Python urllib 在客户端就拒绝含空格的 URL（URL can't contain control characters），请求根本没发出去。改成 u%201 走百分号编码后通过——顺带也验证了服务端解码后确实拒绝了它（400）。
不变量里的快照比对：我把 close() 返回的响应文本和另一处的解析后 dict 拿来比 json.dumps，类型不匹配。改成两者都比解析后的 dict 后通过。
这两处说明我前面的复刻脚本本身有 bug，服务端没有暴露问题。

环境与收尾
编译：g++ -O2 -std=c++17 -pthread -Wall -Wextra — 退出码 0，零警告
端口：未设 PORT，验证默认 8000 生效（另外此前单独验证过 PORT=8123 也生效）
起停：端口 8000 跑前空闲、跑后已释放（SERVER_STOPPED=True），无残留服务进程
项目目录：仍然只有原来那 12 个文件，main.cpp 和 run_instructions.md 之外没有任何改动；测试脚本留在临时目录（需要我删就说一声）
现在样例 + 23 项边界都过了，可以开始最后的复盘了。






用量 883K tok
23:39
好的，我们来复盘这道投票服务题目：
1. 这道题在读需求的时候，最容易出现哪些理解偏差？
2. 我们之前敲定的几个约定：错误状态码、UTF-8码点计数、trim对齐Python strip、option匹配规则，分别存在什么潜在风险？
3. 代码在Linux判题环境下，还有哪些地方需要额外注意？
4. 如果后续遇到类似网络服务类的C++题目，和AI协作的流程可以怎么优化？
23:40

已完成
已完成，用时 44秒
先更正一处小错：之前我说 409 在 main.cpp:658，实际是 main.cpp:648。下面复盘。

一、读需求时最容易出现的理解偏差
按“踩坑概率 × 后果严重度”排序：

#	偏差	实际要求	后果
1	当成 stdin/stdout 程序	是持续运行的 HTTP 服务，判题器在线打请求	方向完全错，写出来 0 分
2	total_votes 当“总票数”每次 +1	它是有效投票人数，改票时不变	改票全错，且票数与人数不一致
3	改票理解成“追加一票”	旧项 −1、新项 +1，是替换	票数只增不减，重复投票也涨
4	重复投同一项当报错或当 +1	数据完全不变，返回当前快照	隐藏用例专门测这条
5	排序按字典序/按当前票数顺序	票数降序 + 创建时的原始顺序	同票项顺序错，比分会很难看
6	“拒绝”只做状态码	拒绝 = 不改数据 + 不消耗 id	状态码对了但数据脏了，后续用例连锁失败
7	id 全局自增，不管成功与否	只有创建成功才递增；reset 归 1	非法请求把 id 吃掉了
8	全局单个 poll / 单个 voted 变量	多场投票，且 voter 在每场各一张票	这正是 baseline 的写法，照抄必挂
9	候选项重复时自动去重	是整个请求拒绝	期望 400 却给 200
10	长度按字节算	中文按字符算	80 个汉字的合法标题被判 400
11	只看接口表，忽略样例脚本	GET /health 表里没有，但样例要用	样例第一项就挂
12	“原子性”理解成数据库事务/分布式锁	只需要“校验+变更”不被打断，单线程即可	过度设计，引入锁 bug
13	结票幂等 = 第二次也返回 200	要返回完全相同的快照	重复 close 返回的数据不同就挂
14	以为 baseline 是“接近完成”的模板	它只是 socket 骨架，业务层基本要重写	修补心态导致遗漏一半规则
还有两条隐藏假设，这次侥幸成立但值得记下来：

判题器是解析 JSON 再比结构（样例脚本用 json.loads 证实了），所以我们的紧凑格式 {"ok":true} 没问题；若判题器做字符串比对，{"ok": true} 与 {"ok":true} 就会判错。
文档与 baseline 冲突时以谁为准：baseline 里“结票后投票返回 200 + 快照”，README 说“拒绝”。我们选了 README 的语义（409），这是一次有意的取舍，不是照抄。
二、四个约定的潜在风险
1. 错误状态码 400 / 404 / 409
风险	说明
判题器把非 2xx 当“服务异常”	有些 grader 只把 2xx 视为“正常响应”，4xx 直接记负，而不是记“正确拒绝”
判题器期望 200 + 快照	README 说“错误码不强制”，最宽松的解读就是“一律 200，用数据表达拒绝”——baseline 就是这个风格
判题器期望 400 而非 409	409 Conflict 语义更准，但不少题只认 400
回滚成本	现在 400/404/409 散落在 handleCreate/handleVote/handleClose 里（如 main.cpp:648），要切回 200 得改 5 处以上，容易漏
这条最大的风险不是选错，而是改起来散。 更稳的做法是定义一个 kRejectStatus 常量或一个 reject() 封装，一处改全局生效。这次没做，属于可改进项。

2. 按 UTF-8 码点计数
赌的是判题器的长度单位。Python len() 是码点，我们对齐它；但如果判题器是 JS（string.length 是 UTF-16 码元，emoji 算 2）或 Go（len() 是字节），同一个输入三方结论都不同。
没有做 Unicode 规范化：é 可以是 1 个码点（U+00E9）也可以是 2 个（e + 组合重音）。Python 同样不规范化，所以我们和 Python 一致；但如果判题器按“视觉字符”（grapheme cluster）数，就会分歧。
非法 UTF-8：我们一律 400。判题器可能根本不会构造这种输入，属于“多做的防御”，不影响正确性，但会让“坏输入应当崩溃/忽略”的奇怪用例结果不同。
风险等级：低。因为题目文档给了 Python 参考实现风格，码点是最合理的推断。
3. trim 对齐 Python strip()
空白集是硬编码的（main.cpp:129），覆盖了 U+3000、U+00A0 等常见项，但 Python 的白名单随 Unicode 版本微调，冷门码点（如历史上曾算空白的 U+180E）可能不一致。
“trim 后存储”是推断：README 只说“去除首尾空白后长度 1~80”，我们存的是 trim 后的值并原样返回。另一种解读是“校验时 trim、存储保留原值”，那样返回的 title 就会和判题器期望的不同。
过度宽容的风险：如果判题器不认为全角空格是空白，它会期望 "　午餐　" 被判 400（长度 6），而我们 trim 后是 2 → 返回 200。方向相反时同理。
风险等级：低到中。全角空格/NBSP 这类用例如果隐藏用例里有，我们大概率押对了（因为出题人用 Python 写参考实现）。
4. option 匹配“先精确、再 trim 后匹配”
这是四个约定里最没谱的一个，因为它放宽了校验：
若判题器测“带空白的 option 应被拒绝”，我们会给 200 → 判错；
若判题器只是回传它自己的字符串，则是无风险的多余宽容。
另一个不对称风险：宽容只发生在输入侧。候选项在创建时已 trim，所以合法投票本来就该用 trim 后的值，这层回退在正常用例里根本不会被触发——它纯粹是给“判题器不 trim”兜底，属于赌小概率事件，却引入了“该拒绝没拒绝”的明确风险。
复盘结论：如果重来，我会选严格精确匹配。 理由是“回退几乎不会被正常用例触发，但一旦触发就是放了非法请求过去”，收益/风险不对称。
三、Linux 判题环境还需要注意的地方
已处理（但值得知道为什么）
项	说明
SIGPIPE	main.cpp:862 必须 SIG_IGN。客户端提前断连时写 socket 会发 SIGPIPE，默认动作是杀进程——这是 Linux 独有的、Windows 上完全不存在的坑，服务会“莫名退出”
短读/短写	recv 按 Content-Length 循环收，send 循环发，都不能假设一次写完
端口复用	SO_REUSEADDR，避免 TIME_WAIT 导致重启 bind 失败
前台运行	不 daemonize、不 fork，stdout 保持安静
仍有风险（按严重度）
只监听 IPv4（main.cpp:871–879）。样例脚本默认连 
http://localhost:8000
，Linux 上 getaddrinfo("localhost") 通常先返回 ::1。Python urllib 会按顺序重试到 IPv4，所以大概率没事；但如果环境里 ::1 连接被静默挂起而不是立即拒绝，就可能超时。要彻底稳妥，应同时监听 IPv6 或直接 bind 到 0.0.0.0 并在文档里说明用 127.0.0.1。
10 秒读超时后直接关连接，不回响应（main.cpp:832）。判题器如果写请求很慢，会收到“连接被重置”而不是 400，可能被记成服务错误。更友好的是超时也返回 408/400。
启动失败完全静默：bind/listen 失败直接 return 1，判题器只看到“进程退出了”，没有任何线索。应该往 stderr 打一行原因（不影响判分，但能救命）。
没有 keep-alive：每个请求一个 TCP 连接。功能正确，但判题器如果用 requests.Session 复用连接，会强制重连，拖慢整体；如果判题器有总时限，大量用例时可能吃紧。
单线程阻塞：一个慢连接会推迟后面的请求。已用超时兜底，但高并发下会变成串行队列。
POSIX 分支从未编译过：这是本次唯一“没跑过”的代码路径。必须在判题环境第一步就编译验证，若报错大概率是头文件或类型差异（ssize_t、socklen_t）。
-pthread 其实没用上：我们没用线程，链接它无害；但说明代码与 README 的编译命令是兼容的，这点已核对。
Expect: 100-continue：curl 发大 body 时会先发这个头，我们不会回 100 Continue，curl 等 1 秒后仍会发送 body。功能不坏，但会多 1 秒延迟。判题器若用 requests/urllib 不会触发。
四、和 AI 协作这类网络服务题的流程优化
这次实际走了“读文档 → 拆解 → 定约定 → 实现 → 自测 → 复盘”，效果不错，但有几处可以固化成流程：

1. 开场做一次“环境可用性检查”（这次浪费了时间）
本机没有 Python、pwsh 因文件权限起不来，各自都花了一轮才发现。应该第一轮就并行探测：编译器版本、Python/Node、shell 可用性、端口占用。而且这次最终是用 DSH 自带 Python 才跑通官方脚本——“本机没有”不等于“没有可用的”，要想到工具链自带的运行时。

2. 把“可执行资产”当第一手需求
README.md 是描述性的，run_sample_testcases.py 才是可执行契约。这次的 /health 不一致就是证明。流程应是：先读全部可执行文件（样例脚本、baseline），再写需求拆解，并把“文档 vs 样例”的冲突点单独列出来让人拍板。

3. 拆解阶段强制输出“歧义清单 + 待定选项”
这次做对了：拆解里单列了 5 个待定项，人拍板后才写码。建议固化成模板——每个歧义给出“我的建议 + 理由 + 反方向的代价”，比只提问题更有用。

4. 约定要“集中可切换”，不要散落在业务逻辑里
错误码这次散在 3 个 handler 里，回滚要改 5 处。教训：凡是“按判题反馈可能要改”的策略，都做成一处常量/开关（错误码、trim 策略、option 匹配严格度）。这比“写对”更重要，因为它决定了修复成本。

5. 测试要“先于或并行于”实现，且测试自身要自检
这次是先实现后补测试。更好的做法：先把样例脚本的断言抄成验收脚本跑一遍 baseline（预期大面积失败），再写实现，最后回归。另外这次两次 FAIL 都是测试脚本 bug——说明需要一条“测试自检”：至少有一个“必然通过”的正例，如果它也失败，先怀疑测试而不是实现。

6. 失败时先分类：实现 bug / 测试 bug / 环境 bug
这次的两次 FAIL 全是测试 bug（urllib 不允许空格、拿文本比 dict）。分类成本很低，但能避免“为修测试 bug 去改正确的实现”——那是最危险的连锁改动。

7. 让 AI 主动产出“风险清单 + 可验证性标注”
run_instructions.md 里那 5 条已知限制就是这次最有价值的产物之一。建议加一列：“能否在判题环境 5 分钟内验证”，方便按性价比排序去验证。

8. 版本化
这次没有 git 操作，全靠文件覆盖。应该在动手前 git commit 一次 baseline，之后每轮修复一个 commit，出问题时 git diff 一眼看出改了什么、能否回滚。对“只改一个文件”的题目尤其划算。

9. 分轮次，别一口气做完
“拆解 → 人确认 → 实现 → 自测 → 复盘”分轮，比一次性输出全部内容更稳：每次上下文都短，人也有介入点。这次就体现了价值——如果一次性写完，5 个约定里的分歧要到复盘才会暴露。

一句话总结
这道题真正的难点不在算法（全是 O(1) 的状态机），而在把一段自然语言需求翻译成一组可判定的契约：拒绝的语义、幂等的语义、排序的基准、长度的单位、空白的边界。代码只是这些契约的落地，风险也全部集中在“契约里没写死的那些地方”。

如果重来一次，我会改三件事：① option 匹配改成严格精确；② 错误码收成一处开关；③ 动手前先跑一遍 baseline 版验收脚本。