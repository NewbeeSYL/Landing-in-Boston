import json
import re
from pathlib import Path

# ===== 配置 =====
INPUT_FILES = [
    "allston.json",
    "back+bay.json",
    "brighton.json",
    "fenway-kenmore.json",
    "jamaica+plain.json",
    "somerville.json",
    "south+end.json"
]

OUTPUT_SUFFIX = "_sample.json"
SAMPLES_PER_FILE = 15  # 每个区想要几条，可以自己改成 10、20 等


def parse_price(item):
    """
    从 Zillow 的 units 里取最低价格。
    例如: "$2,250+" -> 2250
    """
    units = item.get("units")
    if not isinstance(units, list) or not units:
        return None

    prices = []
    for u in units:
        price_str = u.get("price", "")
        m = re.search(r"\$([\d,]+)", price_str)
        if m:
            prices.append(int(m.group(1).replace(",", "")))

    if not prices:
        return None
    return min(prices)


def stratified_sample_by_price(data, n):
    """
    按价格排序，均匀抽样 n 条。
    如果总数比 n 少，就只返回总数那么多（不会多出来）。
    """
    priced = []

    for item in data:
        price = parse_price(item)
        if price is not None:
            priced.append((price, item))

    if not priced:
        print("⚠️ 这个文件里找不到任何带价格的房源，跳过。")
        return []

    # 按价格升序
    priced.sort(key=lambda x: x[0])

    total = len(priced)
    # 防止 “想要 15 条，但只有 8 条” 的情况，多出来就没有意义
    n = min(n, total)

    result = []
    for i in range(n):
        idx = int(i * total / n)
        result.append(priced[idx][1])

    return result


# ===== 主过程 =====
for file in INPUT_FILES:
    path = Path(file)

    if not path.exists():
        print(f"❌ 文件不存在：{file}")
        continue

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"❌ 读取 {file} 出错：{e}")
            continue

    if not isinstance(data, list):
        print(f"⚠️ {file} 里的内容不是列表（不是 [ {{...}}, {{...}} ] 的结构），跳过。")
        continue

    print(f"处理 {file}，共 {len(data)} 条原始房源")

    sampled = stratified_sample_by_price(data, SAMPLES_PER_FILE)

    out_file = path.stem + OUTPUT_SUFFIX
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(sampled, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {out_file}（{len(sampled)} 条）\n")

print("🎉 全部抽样完成！")
