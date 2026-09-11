---
name: pii-safe-read
description: "Generate a field-level PII safe-reading checklist for WPS/Kingsoft Docs multi-dimensional tables (dbt), xlsx, and other structured datasets, then read data without uploading personal identifiers to any AI server. Use this skill when the user wants to inspect or process a table/spreadsheet that may contain personal sensitive information (PII), such as phone numbers, ID numbers, names, addresses, WeChat IDs, emails, etc. It classifies every column as PII / needs-review / safe and enforces column-scoped reading so PII columns are never fetched. Trigger phrases include 安全读取, PII, 隐私, 手机号, 身份证, 脱敏, 不出域, 敏感字段, 金山文档, 多维表格, safe read, PII checklist."
license: MIT
agent_created: true
---

# PII Safe Read（敏感字段安全读取）

把「处理含个人隐私的表格」变成一套可复用、可交接的流程：先生成字段级「安全读取清单」，
再只用列作用域读取，从源头避免手机号、身份证号等个人敏感信息（PII）被上传到 AI 服务端。

## When to use

- 用户要读取/分析一张可能含个人敏感信息的表：WPS 金山文档多维表格(dbt)、xlsx 等。
- 关键词触发：安全读取、PII、隐私、手机号、身份证、脱敏、不出域、敏感字段、金山文档、多维表格。
- 用户要求「别让某类字段上传/显示」时，直接复用此流程。

## Core principle

**不读取 = 不上传。** 只要代理读取了某行/某列，值即作为对话内容传到服务端；事后脱敏已晚。
唯一硬防护：从请求源头就不取 PII 列。详见 `references/workflow.md`。

## Workflow

### 1. 只取字段结构（零 PII 上传）

对目标表调用 `dbsheet.get_schema`（WPS 金山文档多维表格）。该工具仅返回字段名/类型，不含行数据，
结果写入客户端的 `tool-results` 目录下一个 `.txt` JSON 文件。记下该文件路径。
切勿为「看结构」而用 `get_range_data` 读取行数据。

对于本地 xlsx：可用 `openpyxl`/`pandas` 读取表头（`.columns`），同样只读表头、不读行。

### 2. 生成安全读取清单

运行本技能脚本，把 schema 文件转为分类清单：

```bash
python scripts/gen_safe_list.py --schema 路径/到/schema.json --title 表名 --out 安全读取清单.md
```

将 `--schema` 后的路径替换为真实的 schema.json 文件绝对路径，`--title` 替换为表名。脚本读取
`references/pii_rules.json`（技能目录下）的规则，输出两类清单：

- **PII 列黑名单**（永不读取、绝不显示明文）
- **安全列**（可正常读取 —— 未被黑名单命中的字段一律放行）

> 本技能采用**最小化黑名单**：默认只拦 10 个关键词（见 `pii_rules.json`），其余字段全部放行。
> 这样能最大限度避免误杀业务字段，代价是需要你按自己的表确认黑名单是否够用。

### 3. 抽查并校准规则（换表必做）

打开清单，确认分类贴合本表字段名。若你的表里有黑名单未覆盖的敏感列名——编辑 `references/pii_rules.json`
（往 `pii_kw` 增删关键词，子串匹配、大小写不敏感），重跑脚本即可。
常见需追加的准标识符：学号、准考证号、工号、民族、证书编号等。
若某列名含敏感词但值实为状态（是/否），把它加进 `allow_kw` 放行——该名单优先于 `pii_kw`。

### 4. 按清单安全读取数据

- ✅ 用 `records_list` / `list_records`，传 `fields` = 清单「安全列」的字段ID（`prefer_id=true`）。
  数据源只返回这些列，PII 列从请求到响应全程不参与。
- ❌ **禁用 `get_range_data`**：它返回矩形选区所有列，会连带取出 PII 列并上传。
- 🔒 输出时仍默认对残留 PII 脱敏（双保险），但根本防护在「不取」这一环。

### 5. 历史已上传 PII 的补救

若过去会话已读取并上传了 PII（规则生效前），清单无法撤回。按 `references/workflow.md` 第四节
走平台方擦除（向官方隐私/数据删除邮箱发 Erasure 请求 + 删除本地会话）。

## Bundled resources

- `scripts/gen_safe_list.py` — 配置驱动的清单生成器（读 schema + `pii_rules.json` → 输出 .md）。
- `references/pii_rules.json` — 可编辑的 PII 识别规则（**最小化黑名单**：默认拦 10 个关键词，其余全放行）。
- `references/workflow.md` — 完整工作流、读取操作规范、历史 PII 擦除步骤与边界说明。

## Boundaries（必须如实告知用户）

- 本方案保护 **PII 列不出域**；安全列里的业务数据仍经云端连接器中转（使用云端工具的固有代价）。
- 这是**强流程、非硬防火墙**：依赖每次正确传 `fields`。任何一次漏传即上传 PII。
- 换本地模型（如 Ollama）挡不住云端连接器拉取数据这一环；真零上传 = 不读 PII 列或全本地化处理。
