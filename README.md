# pii-safe-read

**处理含个人隐私的表格时，先生成「安全读取清单」，再按清单只取非敏感列 —— 让手机号、身份证号从源头不进 AI 服务端。**

支持 WPS 金山文档多维表格（dbt）、xlsx 等任何带字段结构的表格。

---

## 为什么需要它

一个容易被忽略的事实：**AI 代理只要读取了某一行/某一列，那些值就已经作为对话内容发到了模型服务端。**
事后在输出里打码、脱敏，都是自欺欺人——字节早就上去了。

所以唯一有效的防护，不是在输出端打码，而是**从请求源头就不取 PII 列**。
本技能做的就是这件事：先把表的所有字段分类，然后带着「只读哪些列」的清单去读数据。

---

## 安装

### 方式 A：把命令发给你的 AI 智能体（推荐）

复制下面这段，直接发给同事的 WorkBuddy / CodeBuddy 智能体，它会自己下载安装并校验：

> 请帮我安装一个 skill，执行这条命令，装完后确认 `pii-safe-read/SKILL.md` 存在：
> ```
> curl -fsSL https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main/install.sh | bash
> ```

> Windows 上把上面那条换成 PowerShell 版：
> ```
> irm https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main/install.ps1 | iex
> ```

### 方式 B：自己跑一行命令

```bash
# macOS / Linux / Git Bash
curl -fsSL https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main/install.sh | bash
```

```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main/install.ps1 | iex
```

### 方式 C：手动复制

下载本仓库，把整个 `pii-safe-read` 文件夹放进技能目录：

| 客户端 | 技能目录 |
|---|---|
| WorkBuddy | `~/.workbuddy/skills/` |
| CodeBuddy | `~/.codebuddy/skills/` |

最终路径应为 `<技能目录>/pii-safe-read/SKILL.md`。

脚本会自动识别客户端类型；如需指定，可设环境变量 `WORKBUDDY_CONFIG_DIR` 或 `CODEBUDDY_CONFIG_DIR`。

---

## 使用流程

### 1. 只取字段结构（零 PII 上传）

对多维表格调用 `dbsheet.get_schema` —— 只返回字段名和类型，不含任何行数据。
**不要**为了「看一眼结构」而用 `get_range_data` 读行数据。

本地 xlsx 用 `openpyxl` / `pandas` 读表头即可，同样不读行。

### 2. 生成安全读取清单

```bash
python scripts/gen_safe_list.py --schema 你的schema.json --title 表名 --out 安全读取清单.md
```

输出两类清单：

| 分类 | 含义 | 处理方式 |
|---|---|---|
| **PII 列** | 命中黑名单关键词的字段 | 永不读取，绝不显示明文 |
| **安全列** | 其余所有字段 | 可正常读取 |

> 本技能采用**最小化黑名单**：默认只拦 10 个关键词，其余字段一律放行。
> 好处是不会误杀业务字段，代价是你需要按自己的表确认黑名单够不够用。

脚本只处理**字段名**（元数据），不碰行数据，所以生成清单这一步本身零 PII 上传。

### 3. 按清单读数据

- ✅ 用 `records_list` / `list_records`，传 `fields` = 清单里安全列的字段 ID（`prefer_id=true`）
- ❌ **禁用 `get_range_data`** —— 它返回选区内所有列，会把 PII 列一起带上来

---

## 默认黑名单（10 个关键词）

`手机`、`电话`、`微信号`、`联系方式`、`邮箱`、`地址`、`身份证`、`住址`、`学位证编号`、`毕业证编号`

匹配方式为**子串包含、大小写不敏感** —— 所以「联系电话」「手机号」「客户地址」这类带前后缀的列名同样会被拦下。

**除以上关键词命中的字段外，所有列一律放行。**

## 按你的表定制规则

默认黑名单刻意做得最小，因为漏拦的代价是隐私泄露，误拦的代价是业务字段读不出来 —— 后者更容易被发现，也更好修。换表后请抽查清单，按需调整 `references/pii_rules.json`：

- `pii_kw` — 命中即判为 PII 列（禁读）。要加严就往这里加词
- `allow_kw` — 优先于 `pii_kw`，用于放行「名字像 PII 但实为状态字段」的列（比如「是否添加微信」）

**建议优先考虑追加的准标识符**（默认名单未收录）：

```json
"pii_kw": ["学号", "准考证号", "工号", "民族", "证书编号"]
```

**需要放行时：**

```json
"allow_kw": ["是否联系", "电话审核"]
```

> ⚠️ 默认规则没有收录任何特定行业的字段。请把你的定制版规则留在本地，**不要**提交回公共仓库。

---

## 必须知道的边界

1. **保护范围是「PII 列不出域」。** 安全列里的业务数据仍会经云端连接器中转，这是使用云端工具的固有代价。
2. **这是强流程，不是硬防火墙。** 它依赖每次都正确传 `fields`，任何一次漏传即上传 PII。
3. **换本地模型（Ollama 等）不够。** 那只挡住模型端，挡不住云端连接器拉数据这一环。真零上传 = 不读 PII 列，或全程本地脚本处理文件。
4. **历史已上传的无法撤回。** 若此前会话已读过 PII，需向平台方发 Erasure 请求，并删除本地会话。详见 `references/workflow.md` 第四节。

---

## 目录结构

```
pii-safe-read/
├── SKILL.md                      # 技能入口（触发词、工作流、边界）
├── install.sh / install.ps1      # 一键安装脚本
├── references/
│   ├── pii_rules.json            # PII 识别规则（可编辑，团队共享 Judge 标准）
│   └── workflow.md               # 完整工作流与补救步骤
└── scripts/
    └── gen_safe_list.py          # 清单生成器
```

---

## 验证安装

```bash
ls ~/.workbuddy/skills/pii-safe-read/SKILL.md
```

装好后，下次对话里提到「安全读取」「PII」「脱敏」「敏感字段」等，智能体会自动加载它。

---

MIT License
