// ============================================================================
//  活动投票封存 —— 单文件 HTTP 服务（C++17，仅标准库 + 系统 socket）
//
//  编译：g++ -O2 -std=c++17 -pthread main.cpp -o main
//        （Windows 下额外加 -lws2_32）
//  运行：./main          默认监听 0.0.0.0:8000，可用 PORT 环境变量覆盖
//
//  设计要点：
//    1. 单一数据源 —— 只存 {poll_id: {title, status, options, voter_choice}}，
//       票数、total_votes、排序全部在输出时从 voter_choice 推导，天然不会漂移。
//    2. 单线程 accept 循环 —— 每个请求「校验 + 变更 + 序列化」在一个线程内顺序完成，
//       没有锁也没有竞态，天然满足题目要求的原子性。
//    3. id 只在创建成功后递增 —— 非法请求直接返回，不会消耗 id。
// ============================================================================

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <numeric>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

// ---------------------------------------------------------------------------
// 0. 平台适配：POSIX（判题机 Linux）与 Windows（本机自测）都能编译
// ---------------------------------------------------------------------------
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
using socket_t = SOCKET;
static const socket_t kInvalidSocket = INVALID_SOCKET;
static void closeSocket(socket_t fd) { ::closesocket(fd); }
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
using socket_t = int;
static const socket_t kInvalidSocket = -1;
static void closeSocket(socket_t fd) { ::close(fd); }
#endif

// 单个请求的最大字节数，超过直接判为坏请求，避免被超大 body 拖死
static const size_t kMaxRequestBytes = 1u << 20;  // 1 MiB

// ===========================================================================
// 1. UTF-8 工具：长度按「码点」而不是「字节」计算，空白按 Python str.strip()
// ===========================================================================

// 把一个 Unicode 码点编码成 UTF-8 追加到 out
static void appendUtf8(std::string &out, uint32_t cp) {
    if (cp < 0x80) {
        out += static_cast<char>(cp);
    } else if (cp < 0x800) {
        out += static_cast<char>(0xC0 | (cp >> 6));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
        out += static_cast<char>(0xE0 | (cp >> 12));
        out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    } else {
        out += static_cast<char>(0xF0 | (cp >> 18));
        out += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    }
}

// 从 pos 开始解码一个 UTF-8 码点；成功则前移 pos 并返回 true。
// 会拒绝过长编码、代理区码点和超出 0x10FFFF 的码点，因此也兼作合法性校验。
static bool decodeUtf8(const std::string &text, size_t &pos, uint32_t &cp) {
    if (pos >= text.size()) return false;
    unsigned char first = static_cast<unsigned char>(text[pos]);
    if (first < 0x80) {
        cp = first;
        pos += 1;
        return true;
    }
    int extra = 0;       // 后续续字节的个数
    uint32_t value = 0;
    if ((first & 0xE0) == 0xC0) {
        extra = 1;
        value = first & 0x1F;
    } else if ((first & 0xF0) == 0xE0) {
        extra = 2;
        value = first & 0x0F;
    } else if ((first & 0xF8) == 0xF0) {
        extra = 3;
        value = first & 0x07;
    } else {
        return false;  // 0x80..0xBF 作为首字节、或 0xF8 以上的非法首字节
    }
    if (pos + static_cast<size_t>(extra) >= text.size()) return false;
    for (int i = 1; i <= extra; ++i) {
        unsigned char next = static_cast<unsigned char>(text[pos + i]);
        if ((next & 0xC0) != 0x80) return false;
        value = (value << 6) | (next & 0x3F);
    }
    // 拒绝「同一码点却有更短编码」的非最短形式
    if (extra == 1 && value < 0x80) return false;
    if (extra == 2 && value < 0x800) return false;
    if (extra == 3 && value < 0x10000) return false;
    if (value > 0x10FFFF) return false;
    if (value >= 0xD800 && value <= 0xDFFF) return false;  // 代理区不能单独出现
    cp = value;
    pos += static_cast<size_t>(extra) + 1;
    return true;
}

// 统计 UTF-8 字符串的码点个数（等价于 Python 的 len(str)）；非法编码返回 false
static bool countCodepoints(const std::string &text, size_t &count) {
    size_t pos = 0;
    count = 0;
    uint32_t cp = 0;
    while (pos < text.size()) {
        if (!decodeUtf8(text, pos, cp)) return false;
        ++count;
    }
    return true;
}

// Python str.strip() 认定的空白：ASCII 控制空白 + 常见 Unicode 空白
// 覆盖全角空格 U+3000、NBSP U+00A0 等，避免与判题器的 Python len()/strip() 行为不一致
static bool isPythonSpace(uint32_t cp) {
    return cp == 0x20 || (cp >= 0x09 && cp <= 0x0D) || (cp >= 0x1C && cp <= 0x1F) ||
           cp == 0x85 || cp == 0xA0 || cp == 0x1680 ||
           (cp >= 0x2000 && cp <= 0x200A) || cp == 0x2028 || cp == 0x2029 ||
           cp == 0x202F || cp == 0x205F || cp == 0x3000;
}

// 去除首尾 Unicode 空白；遇到非法 UTF-8 字节时按「非空白」保留，不在这里报错
static std::string trimUnicode(const std::string &text) {
    size_t pos = 0;
    size_t start = 0;
    size_t end = 0;
    bool seen = false;
    while (pos < text.size()) {
        size_t begin = pos;
        uint32_t cp = 0;
        if (!decodeUtf8(text, pos, cp)) {
            pos = begin + 1;  // 坏字节：当作一个普通字符跳过
            cp = 0xFFFD;
        }
        if (!isPythonSpace(cp)) {
            if (!seen) {
                start = begin;
                seen = true;
            }
            end = pos;
        }
    }
    if (!seen) return std::string();
    return text.substr(start, end - start);
}

// ===========================================================================
// 2. 极简 JSON 解析器（标准库没有 JSON，这里手写一个只覆盖题目所需子集的）
//    支持：对象、数组、字符串（含 \uXXXX 与代理对）、数字、true/false/null
// ===========================================================================

struct Json {
    enum Kind { NUL, BOOL, NUM, STR, ARR, OBJ };
    Kind kind = NUL;
    bool boolean = false;
    double number = 0;
    std::string text;
    std::vector<Json> items;
    std::vector<std::pair<std::string, Json>> fields;

    // 按 key 取对象成员；不存在或不是对象时返回 nullptr
    const Json *find(const std::string &key) const {
        if (kind != OBJ) return nullptr;
        for (const auto &field : fields) {
            if (field.first == key) return &field.second;
        }
        return nullptr;
    }
};

class JsonParser {
  public:
    explicit JsonParser(const std::string &source) : src(source) {}

    // 解析整个字符串；尾部有多余内容视为非法
    bool parse(Json &out) {
        pos = 0;
        if (!parseValue(out, 0)) return false;
        skipSpace();
        return pos == src.size();
    }

  private:
    const std::string &src;
    size_t pos = 0;

    void skipSpace() {
        while (pos < src.size()) {
            char ch = src[pos];
            if (ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') {
                ++pos;
            } else {
                break;
            }
        }
    }

    bool matchLiteral(const char *literal) {
        size_t length = 0;
        while (literal[length] != '\0') ++length;
        if (pos + length > src.size()) return false;
        for (size_t i = 0; i < length; ++i) {
            if (src[pos + i] != literal[i]) return false;
        }
        pos += length;
        return true;
    }

    bool parseHex4(uint32_t &value) {
        if (pos + 4 > src.size()) return false;
        uint32_t result = 0;
        for (int i = 0; i < 4; ++i) {
            char ch = src[pos + i];
            int digit = -1;
            if (ch >= '0' && ch <= '9') digit = ch - '0';
            else if (ch >= 'a' && ch <= 'f') digit = ch - 'a' + 10;
            else if (ch >= 'A' && ch <= 'F') digit = ch - 'A' + 10;
            if (digit < 0) return false;
            result = result * 16 + static_cast<uint32_t>(digit);
        }
        pos += 4;
        value = result;
        return true;
    }

    bool parseString(std::string &out) {
        out.clear();
        if (pos >= src.size() || src[pos] != '"') return false;
        ++pos;
        while (pos < src.size()) {
            unsigned char ch = static_cast<unsigned char>(src[pos]);
            if (ch == '"') {  // 字符串结束
                ++pos;
                return true;
            }
            if (ch < 0x20) return false;  // 裸控制字符在 JSON 里必须转义
            if (ch != '\\') {             // 普通字节（含多字节 UTF-8 的每个字节）原样保留
                out += static_cast<char>(ch);
                ++pos;
                continue;
            }
            ++pos;
            if (pos >= src.size()) return false;
            char esc = src[pos++];
            switch (esc) {
                case '"': out += '"'; break;
                case '\\': out += '\\'; break;
                case '/': out += '/'; break;
                case 'b': out += '\b'; break;
                case 'f': out += '\f'; break;
                case 'n': out += '\n'; break;
                case 'r': out += '\r'; break;
                case 't': out += '\t'; break;
                case 'u': {
                    uint32_t cp = 0;
                    if (!parseHex4(cp)) return false;
                    if (cp >= 0xD800 && cp <= 0xDBFF) {  // 高代理项：必须紧跟低代理项
                        if (pos + 1 >= src.size() || src[pos] != '\\' || src[pos + 1] != 'u') return false;
                        pos += 2;
                        uint32_t low = 0;
                        if (!parseHex4(low) || low < 0xDC00 || low > 0xDFFF) return false;
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (low - 0xDC00);
                    } else if (cp >= 0xDC00 && cp <= 0xDFFF) {
                        return false;  // 孤立低代理项
                    }
                    appendUtf8(out, cp);
                    break;
                }
                default: return false;
            }
        }
        return false;  // 没有收尾引号
    }

    bool parseNumber(Json &out) {
        size_t start = pos;
        if (pos < src.size() && src[pos] == '-') ++pos;
        if (pos >= src.size()) return false;
        if (src[pos] == '0') {
            ++pos;
        } else if (src[pos] >= '1' && src[pos] <= '9') {
            while (pos < src.size() && src[pos] >= '0' && src[pos] <= '9') ++pos;
        } else {
            return false;
        }
        if (pos < src.size() && src[pos] == '.') {
            ++pos;
            size_t digits = pos;
            while (pos < src.size() && src[pos] >= '0' && src[pos] <= '9') ++pos;
            if (pos == digits) return false;
        }
        if (pos < src.size() && (src[pos] == 'e' || src[pos] == 'E')) {
            ++pos;
            if (pos < src.size() && (src[pos] == '+' || src[pos] == '-')) ++pos;
            size_t digits = pos;
            while (pos < src.size() && src[pos] >= '0' && src[pos] <= '9') ++pos;
            if (pos == digits) return false;
        }
        out.kind = Json::NUM;
        out.number = std::strtod(src.substr(start, pos - start).c_str(), nullptr);
        return true;
    }

    bool parseArray(Json &out, int depth) {
        out.kind = Json::ARR;
        ++pos;  // '['
        skipSpace();
        if (pos < src.size() && src[pos] == ']') {
            ++pos;
            return true;
        }
        while (true) {
            Json item;
            if (!parseValue(item, depth + 1)) return false;
            out.items.push_back(std::move(item));
            skipSpace();
            if (pos >= src.size()) return false;
            if (src[pos] == ',') {
                ++pos;
                continue;
            }
            if (src[pos] == ']') {
                ++pos;
                return true;
            }
            return false;
        }
    }

    bool parseObject(Json &out, int depth) {
        out.kind = Json::OBJ;
        ++pos;  // '{'
        skipSpace();
        if (pos < src.size() && src[pos] == '}') {
            ++pos;
            return true;
        }
        while (true) {
            skipSpace();
            std::string key;
            if (!parseString(key)) return false;
            skipSpace();
            if (pos >= src.size() || src[pos] != ':') return false;
            ++pos;
            Json value;
            if (!parseValue(value, depth + 1)) return false;
            out.fields.emplace_back(std::move(key), std::move(value));
            skipSpace();
            if (pos >= src.size()) return false;
            if (src[pos] == ',') {
                ++pos;
                continue;
            }
            if (src[pos] == '}') {
                ++pos;
                return true;
            }
            return false;
        }
    }

    bool parseValue(Json &out, int depth) {
        if (depth > 64) return false;  // 防御性深度限制，避免恶意嵌套打爆栈
        skipSpace();
        if (pos >= src.size()) return false;
        char ch = src[pos];
        if (ch == '{') return parseObject(out, depth);
        if (ch == '[') return parseArray(out, depth);
        if (ch == '"') {
            out.kind = Json::STR;
            return parseString(out.text);
        }
        if (ch == 't') {
            if (!matchLiteral("true")) return false;
            out.kind = Json::BOOL;
            out.boolean = true;
            return true;
        }
        if (ch == 'f') {
            if (!matchLiteral("false")) return false;
            out.kind = Json::BOOL;
            out.boolean = false;
            return true;
        }
        if (ch == 'n') {
            if (!matchLiteral("null")) return false;
            out.kind = Json::NUL;
            return true;
        }
        if (ch == '-' || (ch >= '0' && ch <= '9')) return parseNumber(out);
        return false;
    }
};

// 把字符串转义成 JSON 字符串内容的合法形式（处理引号、反斜杠、控制字符）
static std::string escapeJson(const std::string &value) {
    static const char *hex = "0123456789abcdef";
    std::string out;
    out.reserve(value.size() + 8);
    for (unsigned char ch : value) {
        switch (ch) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (ch < 0x20) {
                    out += "\\u00";
                    out += hex[(ch >> 4) & 0x0F];
                    out += hex[ch & 0x0F];
                } else {
                    out += static_cast<char>(ch);  // 非 ASCII 直接输出 UTF-8
                }
        }
    }
    return out;
}

// ===========================================================================
// 3. 数据模型：单一数据源
// ===========================================================================

struct Poll {
    std::string title;                                     // 已 trim 的标题
    std::string status;                                    // "open" / "closed"
    std::vector<std::string> options;                      // 候选项，保持创建时的原始顺序
    std::unordered_map<std::string, size_t> indexOf;       // 候选项 -> 下标，用于 O(1) 查票
    std::unordered_map<std::string, std::string> voterChoice;  // voter_id -> 候选项（每人一张有效票）
};

static std::unordered_map<std::string, Poll> g_polls;  // poll_id -> 投票
static long long g_nextPollId = 1;                     // 只在创建成功时递增

// 渲染成完整 Poll JSON：票数与 total_votes 全部从 voterChoice 现算
static std::string renderPoll(const std::string &pollId, const Poll &poll) {
    // (1) 统计每个候选项的票数
    std::vector<size_t> votes(poll.options.size(), 0);
    for (const auto &entry : poll.voterChoice) {
        auto found = poll.indexOf.find(entry.second);
        if (found != poll.indexOf.end()) votes[found->second] += 1;
    }

    // (2) 排序：票数降序；票数相同则按创建时的原始顺序（下标升序）
    std::vector<size_t> order(poll.options.size());
    std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(), [&votes](size_t left, size_t right) {
        if (votes[left] != votes[right]) return votes[left] > votes[right];
        return left < right;
    });

    // (3) 拼 JSON
    std::string results = "[";
    for (size_t i = 0; i < order.size(); ++i) {
        if (i) results += ',';
        size_t index = order[i];
        results += "{\"option\":\"" + escapeJson(poll.options[index]) + "\",\"votes\":" +
                   std::to_string(votes[index]) + "}";
    }
    results += "]";

    return "{\"id\":\"" + escapeJson(pollId) + "\",\"title\":\"" + escapeJson(poll.title) +
           "\",\"status\":\"" + poll.status + "\",\"results\":" + results +
           ",\"total_votes\":" + std::to_string(poll.voterChoice.size()) + "}";
}

// ===========================================================================
// 4. 请求 / 响应结构与通用工具
// ===========================================================================

struct HttpRequest {
    std::string method;
    std::string path;  // 不含 query string
    std::string body;
};

struct Response {
    int status = 200;
    std::string body;
};

// 统一错误响应：非 2xx + JSON body，重点是不改数据
static void setError(Response &resp, int status, const std::string &message) {
    resp.status = status;
    resp.body = "{\"error\":\"" + escapeJson(message) + "\"}";
}

static int hexValue(char ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

// 百分号解码：/polls/poll%5F1/... 也能正确匹配
static std::string percentDecode(const std::string &input) {
    std::string out;
    out.reserve(input.size());
    for (size_t i = 0; i < input.size(); ++i) {
        if (input[i] == '%' && i + 2 < input.size()) {
            int high = hexValue(input[i + 1]);
            int low = hexValue(input[i + 2]);
            if (high >= 0 && low >= 0) {
                out += static_cast<char>(high * 16 + low);
                i += 2;
                continue;
            }
        }
        out += input[i];
    }
    return out;
}

// 把路径拆成段，忽略空段并做百分号解码；query string 直接丢弃
static std::vector<std::string> splitPath(const std::string &rawPath) {
    std::string path = rawPath;
    size_t question = path.find('?');
    if (question != std::string::npos) path = path.substr(0, question);

    std::vector<std::string> parts;
    std::string current;
    for (char ch : path) {
        if (ch == '/') {
            if (!current.empty()) {
                parts.push_back(percentDecode(current));
                current.clear();
            }
        } else {
            current += ch;
        }
    }
    if (!current.empty()) parts.push_back(percentDecode(current));
    return parts;
}

// voter_id 只允许 [A-Za-z0-9_-]，长度 1~32（纯 ASCII，字节数即字符数）
static bool isValidVoterId(const std::string &voterId) {
    if (voterId.empty() || voterId.size() > 32) return false;
    for (unsigned char ch : voterId) {
        bool allowed = (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') ||
                       (ch >= '0' && ch <= '9') || ch == '_' || ch == '-';
        if (!allowed) return false;
    }
    return true;
}

// ===========================================================================
// 5. 业务处理
// ===========================================================================

// POST /polls —— 创建投票
static void handleCreate(const std::string &body, Response &resp) {
    Json root;
    JsonParser parser(body);
    if (!parser.parse(root) || root.kind != Json::OBJ) {
        return setError(resp, 400, "request body must be a json object");
    }

    // ---- title：必填字符串，trim 后码点数 1~80 ----
    const Json *titleField = root.find("title");
    if (titleField == nullptr || titleField->kind != Json::STR) {
        return setError(resp, 400, "title is required");
    }
    std::string title = trimUnicode(titleField->text);
    size_t titleLength = 0;
    if (!countCodepoints(title, titleLength) || titleLength < 1 || titleLength > 80) {
        return setError(resp, 400, "title length must be 1..80 characters");
    }

    // ---- options：数组，2~8 项，每项 trim 后码点数 1~40 且不得重复 ----
    const Json *optionsField = root.find("options");
    if (optionsField == nullptr || optionsField->kind != Json::ARR) {
        return setError(resp, 400, "options is required");
    }
    if (optionsField->items.size() < 2 || optionsField->items.size() > 8) {
        return setError(resp, 400, "options size must be 2..8");
    }
    std::vector<std::string> options;
    std::unordered_set<std::string> seen;
    for (const Json &item : optionsField->items) {
        if (item.kind != Json::STR) {
            return setError(resp, 400, "each option must be a string");
        }
        std::string option = trimUnicode(item.text);
        size_t optionLength = 0;
        if (!countCodepoints(option, optionLength) || optionLength < 1 || optionLength > 40) {
            return setError(resp, 400, "option length must be 1..40 characters");
        }
        if (!seen.insert(option).second) {  // 去空白后重复
            return setError(resp, 400, "options must be unique");
        }
        options.push_back(option);
    }

    // ---- 全部校验通过后才分配 id，保证非法请求不消耗 id ----
    std::string pollId = "poll_" + std::to_string(g_nextPollId);
    Poll poll;
    poll.title = title;
    poll.status = "open";
    poll.options = options;
    for (size_t i = 0; i < options.size(); ++i) poll.indexOf[options[i]] = i;
    g_polls[pollId] = std::move(poll);
    ++g_nextPollId;

    resp.status = 200;
    resp.body = renderPoll(pollId, g_polls[pollId]);
}

// PUT /polls/{poll_id}/votes/{voter_id} —— 投票 / 改票
static void handleVote(const std::string &pollId, const std::string &voterId,
                       const std::string &body, Response &resp) {
    auto pollIt = g_polls.find(pollId);
    if (pollIt == g_polls.end()) {
        return setError(resp, 404, "poll not found");
    }
    if (!isValidVoterId(voterId)) {
        return setError(resp, 400, "invalid voter id");
    }

    Json root;
    JsonParser parser(body);
    if (!parser.parse(root) || root.kind != Json::OBJ) {
        return setError(resp, 400, "request body must be a json object");
    }
    const Json *optionField = root.find("option");
    if (optionField == nullptr || optionField->kind != Json::STR) {
        return setError(resp, 400, "option is required");
    }

    Poll &poll = pollIt->second;
    if (poll.status != "open") {  // 结票后拒绝一切投票 / 改票，且数据不变
        return setError(resp, 409, "poll is closed");
    }

    // 候选项必须存在于该投票；先精确匹配，再退一步按 trim 后匹配（候选词本身已 trim）
    auto indexIt = poll.indexOf.find(optionField->text);
    if (indexIt == poll.indexOf.end()) {
        indexIt = poll.indexOf.find(trimUnicode(optionField->text));
    }
    if (indexIt == poll.indexOf.end()) {
        return setError(resp, 400, "unknown option");
    }

    // 首次投票 / 改票 / 重复投同一项，都只是覆盖同一个 key：
    //   - 首次：新增一个 key，票数 +1、人数 +1
    //   - 改票：只改 value，旧项票数自动 -1、新项 +1，人数不变
    //   - 重复：value 不变，数据完全不变
    poll.voterChoice[voterId] = poll.options[indexIt->second];

    resp.status = 200;
    resp.body = renderPoll(pollId, poll);
}

// POST /polls/{poll_id}/close —— 结票（幂等）
static void handleClose(const std::string &pollId, Response &resp) {
    auto pollIt = g_polls.find(pollId);
    if (pollIt == g_polls.end()) {
        return setError(resp, 404, "poll not found");
    }
    pollIt->second.status = "closed";  // 已是 closed 时重复赋值，天然幂等
    resp.status = 200;
    resp.body = renderPoll(pollId, pollIt->second);
}

// POST /reset —— 全量清空（含 id 计数），保证与启动状态一致
static void handleReset(Response &resp) {
    g_polls.clear();
    g_nextPollId = 1;
    resp.status = 200;
    resp.body = "{\"ok\":true}";
}

// 路由分发：只做「方法 + 路径段数」的精确匹配
static void route(const HttpRequest &req, Response &resp) {
    std::vector<std::string> parts = splitPath(req.path);

    // GET /health —— README 接口表未列出，但样例脚本会调用
    if (req.method == "GET" && parts.size() == 1 && parts[0] == "health") {
        resp.status = 200;
        resp.body = "{\"status\":\"ok\"}";
        return;
    }
    if (req.method == "POST" && parts.size() == 1 && parts[0] == "reset") {
        return handleReset(resp);
    }
    if (req.method == "POST" && parts.size() == 1 && parts[0] == "polls") {
        return handleCreate(req.body, resp);
    }
    if (req.method == "PUT" && parts.size() == 4 && parts[0] == "polls" && parts[2] == "votes") {
        return handleVote(parts[1], parts[3], req.body, resp);
    }
    if (req.method == "POST" && parts.size() == 3 && parts[0] == "polls" && parts[2] == "close") {
        return handleClose(parts[1], resp);
    }

    setError(resp, 404, "not found");
}

// ===========================================================================
// 6. HTTP 传输层
// ===========================================================================

// 循环发送直到把整个响应写完（send 可能只写出一部分）
static void sendAll(socket_t client, const std::string &data) {
    size_t sent = 0;
    while (sent < data.size()) {
        long long written = static_cast<long long>(
            ::send(client, data.data() + sent, static_cast<int>(data.size() - sent), 0));
        if (written <= 0) return;
        sent += static_cast<size_t>(written);
    }
}

// 解析头部块，取出 Content-Length（头名大小写不敏感，缺省 0）
static bool parseHeaders(const std::string &head, size_t &contentLength) {
    contentLength = 0;
    size_t pos = head.find("\r\n");  // 跳过请求行
    if (pos == std::string::npos) return true;
    pos += 2;
    while (pos < head.size()) {
        size_t end = head.find("\r\n", pos);
        if (end == std::string::npos) end = head.size();
        std::string line = head.substr(pos, end - pos);
        pos = end + 2;
        size_t colon = line.find(':');
        if (colon == std::string::npos) continue;
        std::string name = line.substr(0, colon);
        std::string value = line.substr(colon + 1);
        std::string lower;
        for (char ch : name) lower += static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
        if (lower != "content-length") continue;
        size_t length = 0;
        bool any = false;
        for (char ch : value) {
            if (ch == ' ' || ch == '\t') continue;
            if (ch < '0' || ch > '9') return false;
            length = length * 10 + static_cast<size_t>(ch - '0');
            any = true;
            if (length > kMaxRequestBytes) return false;
        }
        if (!any) return false;
        contentLength = length;
    }
    return true;
}

// 读取一个完整请求：先收头部，再按 Content-Length 收满 body
static bool readRequest(socket_t client, HttpRequest &req) {
    std::string buffer;
    char chunk[8192];
    size_t headerEnd = std::string::npos;
    size_t contentLength = 0;
    bool headersReady = false;

    while (true) {
        if (!headersReady) {
            size_t split = buffer.find("\r\n\r\n");
            if (split != std::string::npos) {
                if (!parseHeaders(buffer.substr(0, split), contentLength)) return false;
                headerEnd = split;
                headersReady = true;
            }
        }
        if (headersReady && buffer.size() >= headerEnd + 4 + contentLength) break;

        long long received = static_cast<long long>(::recv(client, chunk, static_cast<int>(sizeof(chunk)), 0));
        if (received <= 0) return false;  // 连接关闭或读超时
        buffer.append(chunk, static_cast<size_t>(received));
        if (buffer.size() > kMaxRequestBytes) return false;
    }

    std::string head = buffer.substr(0, headerEnd);
    size_t lineEnd = head.find("\r\n");
    std::string requestLine = head.substr(0, lineEnd == std::string::npos ? head.size() : lineEnd);
    size_t first = requestLine.find(' ');
    if (first == std::string::npos) return false;
    size_t second = requestLine.find(' ', first + 1);
    req.method = requestLine.substr(0, first);
    req.path = second == std::string::npos ? requestLine.substr(first + 1)
                                           : requestLine.substr(first + 1, second - first - 1);
    req.body = buffer.substr(headerEnd + 4, contentLength);
    return !req.method.empty() && !req.path.empty();
}

// 组装响应报文（Connection: close，一个连接只处理一个请求）
static std::string buildResponse(const Response &resp) {
    const char *reason = "OK";
    switch (resp.status) {
        case 200: reason = "OK"; break;
        case 400: reason = "Bad Request"; break;
        case 404: reason = "Not Found"; break;
        case 409: reason = "Conflict"; break;
        default: reason = "Internal Server Error"; break;
    }
    return "HTTP/1.1 " + std::to_string(resp.status) + " " + reason + "\r\n" +
           "Content-Type: application/json; charset=utf-8\r\n" +
           "Content-Length: " + std::to_string(resp.body.size()) + "\r\n" +
           "Connection: close\r\n\r\n" + resp.body;
}

// 给连接设置读超时，避免客户端连上不发数据把单线程服务卡死
static void setRecvTimeout(socket_t client, int seconds) {
#ifdef _WIN32
    DWORD timeout = static_cast<DWORD>(seconds * 1000);
    ::setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char *>(&timeout), sizeof(timeout));
#else
    timeval tv{};
    tv.tv_sec = seconds;
    tv.tv_usec = 0;
    ::setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
#endif
}

// 单个连接的完整处理：读请求 -> 路由 -> 写响应；任何异常都不能让服务退出
static void handleConnection(socket_t client) {
    setRecvTimeout(client, 10);

    HttpRequest req;
    Response resp;
    try {
        if (!readRequest(client, req)) {
            resp.status = 400;
            resp.body = "{\"error\":\"bad request\"}";
        } else {
            route(req, resp);
        }
    } catch (...) {
        resp.status = 500;
        resp.body = "{\"error\":\"internal error\"}";
    }

    std::string output = buildResponse(resp);
    sendAll(client, output);
}

// ===========================================================================
// 7. 入口
// ===========================================================================

int main() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) return 1;
#else
    // 客户端提前断开时写 socket 会触发 SIGPIPE，默认动作是杀进程，必须忽略
    ::signal(SIGPIPE, SIG_IGN);
#endif

    int port = 8000;
    if (const char *env = std::getenv("PORT")) {
        int parsed = std::atoi(env);
        if (parsed > 0 && parsed < 65536) port = parsed;
    }

    socket_t server = ::socket(AF_INET, SOCK_STREAM, 0);
    if (server == kInvalidSocket) return 1;

    int reuse = 1;
    ::setsockopt(server, SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char *>(&reuse), sizeof(reuse));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_ANY);  // 监听 0.0.0.0
    address.sin_port = htons(static_cast<unsigned short>(port));

    if (::bind(server, reinterpret_cast<sockaddr *>(&address), sizeof(address)) < 0) return 1;
    if (::listen(server, 128) < 0) return 1;

    while (true) {
        socket_t client = ::accept(server, nullptr, nullptr);
        if (client == kInvalidSocket) continue;  // 被信号打断等情况，继续等下一个连接
        handleConnection(client);
        closeSocket(client);
    }
}
