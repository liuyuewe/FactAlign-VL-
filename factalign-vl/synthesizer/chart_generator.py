"""
合成数据工厂模块
用于生成带"绝对真值"的图表数据集
"""

import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import re

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DESCRIPTIONS_DIR = PROJECT_ROOT / "data" / "descriptions"

for dir_path in [CHARTS_DIR, METADATA_DIR, DESCRIPTIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

CHINESE_FOOD_ITEMS = ["苹果", "香蕉", "橙子", "葡萄", "西瓜", "草莓", "芒果", "菠萝", "桃子", "梨",
                       "白菜", "萝卜", "土豆", "西红柿", "黄瓜", "茄子", "青椒", "洋葱", "菠菜", "生菜"]
CHINESE_ANIMALS = ["狗", "猫", "鸟", "鱼", "兔子", "猴子", "熊猫", "老虎", "狮子", "大象"]
CHINESE_CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "重庆",
                  "天津", "苏州", "郑州", "长沙", "沈阳", "青岛", "济南", "大连", "哈尔滨", "长春"]
MONTHS = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]
DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
YEARS = ["2020年", "2021年", "2022年", "2023年", "2024年"]
PRODUCTS = ["手机", "电脑", "电视", "冰箱", "洗衣机", "空调", "自行车", "汽车", "书籍", "服装"]
SUBJECTS = ["数学", "语文", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "体育"]

CHART_COLORS = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
    '#FF6384', '#C9CBCF', '#4BC0C0', '#FF7F50', '#87CEEB', '#DDA0DD'
]

def generate_random_data(num_bars: int = None, value_range: Tuple[int, int] = (10, 100)) -> Dict[str, int]:
    """生成随机数据字典"""
    if num_bars is None:
        num_bars = random.randint(4, 8)

    items = random.sample(CHINESE_FOOD_ITEMS + CHINESE_ANIMALS + CHINESE_CITIES + PRODUCTS, num_bars)
    data = {}
    for item in items:
        data[item] = random.randint(value_range[0], value_range[1])
    return data

def generate_time_series_data(num_points: int = None, value_range: Tuple[int, int] = (20, 100)) -> Tuple[List[str], List[int]]:
    """生成时间序列数据"""
    if num_points is None:
        num_points = random.randint(6, 12)

    if random.random() < 0.5:
        labels = random.sample(MONTHS, num_points)
    else:
        labels = [f"{i+1}月" for i in range(num_points)]

    values = [random.randint(value_range[0], value_range[1]) for _ in range(num_points)]
    return labels, values

def generate_table_data(num_rows: int = None, num_cols: int = 3) -> Tuple[List[List[str]], List[str]]:
    """生成表格数据"""
    if num_rows is None:
        num_rows = random.randint(4, 8)

    categories = random.sample(CHINESE_FOOD_ITEMS + PRODUCTS, num_cols - 1)
    headers = ["项目"] + categories + ["总计"]

    rows = []
    for i in range(num_rows):
        item = random.choice(CHINESE_CITIES + CHINESE_ANIMALS)
        values = [random.randint(10, 100) for _ in range(num_cols - 1)]
        total = sum(values)
        row = [item] + values + [total]
        rows.append(row)

    return headers, rows

class ChartGenerator:
    """图表生成器"""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.chart_id = 0

    def _get_next_id(self) -> str:
        self.chart_id += 1
        return f"chart_{self.chart_id:05d}"

    def _save_figure(self, fig, chart_type: str, chart_id: str) -> Path:
        img_path = CHARTS_DIR / f"{chart_type}" / f"{chart_id}.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(img_path, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return img_path

    def generate_bar_chart(self) -> Tuple[Path, Dict]:
        """生成柱状图"""
        chart_id = self._get_next_id()
        data = generate_random_data()

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(data)), list(data.values()), color=random.sample(CHART_COLORS, len(data)))

        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(list(data.keys()), rotation=45, ha='right')
        ax.set_ylabel('数值')
        ax.set_title(f'柱状图 - {chart_id}')
        ax.set_ylim(0, max(data.values()) * 1.1)

        for bar, val in zip(bars, data.values()):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   str(val), ha='center', va='bottom', fontsize=10)

        img_path = self._save_figure(fig, "bar", chart_id)

        metadata = {
            "chart_id": chart_id,
            "chart_type": "bar",
            "data": data,
            "labels": list(data.keys()),
            "values": list(data.values()),
            "title": f"柱状图 - {chart_id}",
            "colors": [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(data))]
        }

        meta_path = METADATA_DIR / f"{chart_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return img_path, metadata

    def generate_line_chart(self) -> Tuple[Path, Dict]:
        """生成折线图"""
        chart_id = self._get_next_id()
        labels, values = generate_time_series_data()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(labels, values, marker='o', linewidth=2, markersize=8,
               color=random.choice(CHART_COLORS), markerfacecolor='white', markeredgewidth=2)

        ax.set_xlabel('时间')
        ax.set_ylabel('数值')
        ax.set_title(f'折线图 - {chart_id}')
        ax.set_ylim(0, max(values) * 1.1)
        ax.grid(True, alpha=0.3)

        for i, (x, y) in enumerate(zip(labels, values)):
            ax.annotate(str(y), (x, y), textcoords="offset points",
                       xytext=(0, 10), ha='center', fontsize=9)

        img_path = self._save_figure(fig, "line", chart_id)

        metadata = {
            "chart_id": chart_id,
            "chart_type": "line",
            "labels": labels,
            "values": values,
            "title": f"折线图 - {chart_id}",
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values)
        }

        meta_path = METADATA_DIR / f"{chart_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return img_path, metadata

    def generate_table_image(self) -> Tuple[Path, Dict]:
        """生成表格图"""
        chart_id = self._get_next_id()
        headers, rows = generate_table_data()

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('tight')
        ax.axis('off')

        table = ax.table(cellText=rows, colLabels=headers, loc='center',
                        cellLoc='center', colColours=['#E6E6FA']*len(headers))

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(fontweight='bold', color='black')
                cell.set_facecolor('#E6E6FA')
            else:
                if row % 2 == 0:
                    cell.set_facecolor('#F0F8FF')

        ax.set_title(f'表格数据 - {chart_id}', pad=20, fontsize=14, fontweight='bold')

        img_path = self._save_figure(fig, "table", chart_id)

        data_dict = {row[0]: row[1:-1] for row in rows}
        metadata = {
            "chart_id": chart_id,
            "chart_type": "table",
            "headers": headers,
            "rows": rows,
            "data": data_dict,
            "title": f"表格数据 - {chart_id}"
        }

        meta_path = METADATA_DIR / f"{chart_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return img_path, metadata

    def generate_all(self, num_bar: int = 500, num_line: int = 500, num_table: int = 500) -> Dict[str, List]:
        """生成所有类型的图表"""
        results = {"bar": [], "line": [], "table": []}

        print(f"开始生成柱状图 ({num_bar} 张)...")
        for i in range(num_bar):
            if (i + 1) % 50 == 0:
                print(f"  已生成 {i + 1}/{num_bar} 张")
            img_path, metadata = self.generate_bar_chart()
            results["bar"].append({"image": str(img_path), "metadata": metadata})

        print(f"开始生成折线图 ({num_line} 张)...")
        for i in range(num_line):
            if (i + 1) % 50 == 0:
                print(f"  已生成 {i + 1}/{num_line} 张")
            img_path, metadata = self.generate_line_chart()
            results["line"].append({"image": str(img_path), "metadata": metadata})

        print(f"开始生成表格图 ({num_table} 张)...")
        for i in range(num_table):
            if (i + 1) % 50 == 0:
                print(f"  已生成 {i + 1}/{num_table} 张")
            img_path, metadata = self.generate_table_image()
            results["table"].append({"image": str(img_path), "metadata": metadata})

        return results

def split_dataset(all_charts: List[Dict], train_ratio: float = 0.8,
                 val_ratio: float = 0.1, test_ratio: float = 0.1) -> Dict[str, List]:
    """划分训练集、验证集、测试集"""
    random.shuffle(all_charts)

    total = len(all_charts)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)

    train_set = all_charts[:train_size]
    val_set = all_charts[train_size:train_size + val_size]
    test_set = all_charts[train_size + val_size:]

    return {
        "train": train_set,
        "val": val_set,
        "test": test_set
    }

if __name__ == "__main__":
    print("=" * 60)
    print("开始生成合成数据集")
    print("=" * 60)

    generator = ChartGenerator(seed=42)
    results = generator.generate_all(num_bar=10, num_line=10, num_table=10)

    all_charts = results["bar"] + results["line"] + results["table"]
    datasets = split_dataset(all_charts)

    print(f"\n数据集划分完成:")
    print(f"  训练集: {len(datasets['train'])} 条")
    print(f"  验证集: {len(datasets['val'])} 条")
    print(f"  测试集: {len(datasets['test'])} 条")
    print(f"\n总计: {len(all_charts)} 张图表")
