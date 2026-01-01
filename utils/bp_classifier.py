"""血壓分級分類器（根據 WHO 標準）"""
from typing import Tuple


def classify_blood_pressure(systolic: int, diastolic: int) -> Tuple[str, str]:
    """
    根據 WHO 標準分類血壓
    
    Returns:
        Tuple[str, str]: (分類名稱, 顏色標籤)
    """
    if systolic < 120 and diastolic < 80:
        return ("正常", "green")
    elif systolic < 130 and diastolic < 85:
        return ("正常偏高", "lightgreen")
    elif systolic < 140 and diastolic < 90:
        return ("一級高血壓（輕度）", "orange")
    elif systolic < 160 and diastolic < 100:
        return ("二級高血壓（中度）", "darkorange")
    elif systolic < 180 and diastolic < 110:
        return ("三級高血壓（重度）", "red")
    else:
        return ("高血壓危象", "darkred")


def get_category_color(category: str) -> str:
    """根據分類名稱取得顏色"""
    color_map = {
        "正常": "green",
        "正常偏高": "lightgreen",
        "一級高血壓（輕度）": "orange",
        "二級高血壓（中度）": "darkorange",
        "三級高血壓（重度）": "red",
        "高血壓危象": "darkred"
    }
    return color_map.get(category, "gray")


