"""
图像处理工具函数
"""

from typing import Union, Tuple, Optional
from pathlib import Path
import numpy as np


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    加载图像文件

    Args:
        image_path: 图像文件路径

    Returns:
        图像数组 (H, W, C)
    """
    try:
        from PIL import Image
        img = Image.open(image_path).convert('RGB')
        return np.array(img)
    except ImportError:
        raise ImportError("请安装 Pillow: pip install Pillow")


def preprocess_image(
    image: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
    normalize: bool = True
) -> np.ndarray:
    """
    预处理图像

    Args:
        image: 输入图像数组
        target_size: 目标尺寸 (H, W)
        normalize: 是否归一化到 [0, 1]

    Returns:
        预处理后的图像
    """
    try:
        from PIL import Image

        # 转换为 PIL Image
        if isinstance(image, np.ndarray):
            img = Image.fromarray(image)
        else:
            img = image

        # 调整大小
        img = img.resize(target_size[::-1])  # PIL 使用 (W, H)

        # 转回 numpy
        img_array = np.array(img)

        # 归一化
        if normalize:
            img_array = img_array.astype(np.float32) / 255.0

        return img_array

    except ImportError:
        raise ImportError("请安装 Pillow: pip install Pillow")


def extract_image_features(image: np.ndarray) -> np.ndarray:
    """
    提取图像特征（占位符函数）

    Args:
        image: 输入图像

    Returns:
        图像特征向量
    """
    # TODO: 实现基于预训练模型的特征提取
    # 这里返回一个随机特征向量作为占位符
    return np.random.randn(512).astype(np.float32)
