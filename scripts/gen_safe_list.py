#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PII 安全读取清单生成器 (pii-safe-read skill)

读取 kdocs 多维表格 dbsheet.get_schema 工具返回的 schema JSON(仅字段结构, 不含任何行数据),
按 references/pii_rules.json 的关键词规则, 将每个字段分为 PII / REVIEW / SAFE 三类,
输出一份可对照执行的「安全读取清单.md」。

关键隐私原则: 本脚本只处理字段名(元数据), 绝不读取行数据, 因此零 PII 值上传。

用法:
  python gen_safe_list.py --schema <schema.json> [--out <checklist.md>] [--title <表名>]

参数:
  --schema   必填。dbsheet.get_schema 返回的 schema JSON 文件路径(在 WorkBuddy 的 tool-results 目录下)。
  --out      选填。输出清单 .md 路径, 默认 ./安全读取清单.md。
  --title    选填。清单标题所用的表名, 默认「数据表」。
"""
import json
import os
import argparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(SKILL_DIR, "references", "pii_rules.json")


def load_rules():
    if not os.path.exists(RULES_PATH):
        raise SystemExit(f"[错误] 未找到规则文件: {RULES_PATH}")
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


def classify(name, rules):
    low = (name or "").lower()
    # allow_kw 优先于 pii_kw: 命中则放行(用于实为状态/布尔字段, 如「是否添加微信」)
    for k in rules.get("allow_kw", []):
        if k and k in low:
            return "SAFE"
    for k in rules.get("pii_kw", []):
        if k and k in low:
            return "PII"
    for k in rules.get("review_kw", []):
        if k and k in low:
            return "REVIEW"
    return "SAFE"


def load_sheets(schema_path):
    data = json.loads(open(schema_path, encoding="utf-8").read())
    # 兼容两种返回结构: 顶层 {"data":{"detail":{"sheets":[...]}}} 或 {"sheets":[...]}
    detail = data
    if isinstance(data.get("data"), dict) and "detail" in data["data"]:
        detail = data["data"]["detail"]
    sheets = detail.get("sheets", [])
    if not sheets:
        raise SystemExit("[错误] schema 中未找到 sheets 字段, 请确认传入的是 dbsheet.get_schema 的返回文件。")
    return sheets


def build_checklist(sheets, rules, title):
    total = pii = review = safe = 0
    L = []
    L.append(f"# 安全读取清单 ——《{title}》\n")
    L.append("> 数据来源：dbsheet.get_schema（仅字段结构，不含任何行数据，零 PII 值上传）\n")
    L.append("> **用途**：处理此表时，仅读取「安全列」；「PII 列」永不读取/不显示明文；「需人工确认列」读取前先确认不含敏感值。\n")
    L.append("")
    L.append("> **🔒 读取操作规范（确保 PII 不碰 WorkBuddy 服务器）**：\n")
    L.append("> - 必须用 `records_list` / `list_records` 并传 `fields` = 本清单「安全列」的字段ID（`prefer_id=true`），从源头只取安全列。\n")
    L.append("> - **禁止使用 `get_range_data`**（它返回矩形选区内所有列，会连带取出 PII 列并上传）。\n")
    L.append("> - 「需人工确认列」（备注类等）默认不读取，除非确认其值不含手机号/身份证。\n")
    L.append("> - PII 列从请求到响应全程不参与，故其值不会经过 WorkBuddy 服务端（仅安全列的业务数据仍经云端连接器中转，此乃使用云端工具的固有代价）。\n")
    L.append("> - 本规范仅防「未来」上传；历史会话已上传的 PII 不在此列，需平台方擦除（见 references/workflow.md）。\n")
    L.append("")

    L.append("## 一、PII 列黑名单（永不读取，绝不显示明文）\n")
    L.append("| 子表 | 字段ID | 字段名 | 类型 |")
    L.append("|---|---|---|---|")
    for s in sheets:
        sname = s.get("name", "?")
        for f in s.get("fields", []):
            nm = f.get("name", "")
            total += 1
            if classify(nm, rules) == "PII":
                pii += 1
                L.append(f"| {sname} | {f.get('id','')} | {nm} | {f.get('type','')} |")
    L.append("")
    L.append(f"> 共 **{pii}** 个 PII 列（跨 {len(sheets)} 张子表）。\n")

    L.append("## 二、需人工确认列（自由文本，值里可能夹带手机号/身份证，读取前先确认）\n")
    L.append("| 子表 | 字段ID | 字段名 | 类型 |")
    L.append("|---|---|---|---|")
    for s in sheets:
        sname = s.get("name", "?")
        for f in s.get("fields", []):
            nm = f.get("name", "")
            if classify(nm, rules) == "REVIEW":
                review += 1
                L.append(f"| {sname} | {f.get('id','')} | {nm} | {f.get('type','')} |")
    L.append("")
    L.append(f"> 共 **{review}** 个需人工确认列。\n")

    L.append("## 三、各子表安全列（可正常读取）\n")
    for s in sheets:
        sname = s.get("name", "?")
        fields = s.get("fields", [])
        safe_fields = [(f.get("id",""), f.get("name",""), f.get("type","")) for f in fields if classify(f.get("name",""), rules) == "SAFE"]
        safe += len(safe_fields)
        L.append(f"### {sname}（共 {len(fields)} 列，安全 {len(safe_fields)} 列）\n")
        L.append("| 字段ID | 字段名 | 类型 |")
        L.append("|---|---|---|")
        for fid, nm, typ in safe_fields:
            L.append(f"| {fid} | {nm} | {typ} |")
        L.append("")

    L.append("## 四、统计\n")
    L.append(f"- 子表总数：{len(sheets)}")
    L.append(f"- 字段总数：{total}")
    L.append(f"- 安全列：{safe}")
    L.append(f"- PII 列（禁读）：{pii}")
    L.append(f"- 需人工确认列：{review}")
    return "\n".join(L), dict(total=total, pii=pii, review=review, safe=safe, sheets=len(sheets))


def main():
    ap = argparse.ArgumentParser(description="PII 安全读取清单生成器")
    ap.add_argument("--schema", required=True, help="dbsheet.get_schema 返回的 schema JSON 文件路径")
    ap.add_argument("--out", default=None, help="输出清单 .md 路径, 默认 ./安全读取清单.md")
    ap.add_argument("--title", default="数据表", help="清单标题用的表名")
    args = ap.parse_args()

    rules = load_rules()
    sheets = load_sheets(args.schema)
    md, stats = build_checklist(sheets, rules, args.title)
    out_path = args.out or os.path.join(os.getcwd(), "安全读取清单.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("已生成:", out_path)
    print(f"子表={stats['sheets']} 字段={stats['total']} 安全={stats['safe']} PII={stats['pii']} 需确认={stats['review']}")


if __name__ == "__main__":
    main()
