"""
食物 (Food) 实体模块

纯逻辑组件，管理食物在网格中的坐标。
不依赖 Pygame，可独立导入使用。
"""

import random
from typing import Iterable, Tuple


class Food:
    """食物实体：管理食物网格坐标。

    respawn() 计算全量格子与占用格子的集合差，随机选取一个可用格。
    当棋盘被蛇身占满时（无可用格子）返回 False，作为胜利条件。

    Attributes:
        position: 食物在网格中的坐标 (初始值为 (-1, -1) 占位)
    """

    def __init__(self, grid_cols: int, grid_rows: int) -> None:
        """初始化食物。

        position 初始化为 (-1, -1) 占位值，表示尚未生成。

        Args:
            grid_cols: 网格列数
            grid_rows: 网格行数
        """
        self._grid_cols = grid_cols
        self._grid_rows = grid_rows
        self.position: Tuple[int, int] = (-1, -1)

    def respawn(self, occupied_cells: Iterable[Tuple[int, int]]) -> bool:
        """在未被占据的格子中随机生成食物位置。

        计算 all_cells - set(occupied_cells) 的集合差获取可用格子，
        从中随机选取一个作为新的食物位置。

        Args:
            occupied_cells: 已被占据的格子坐标集合（如蛇身全部格子）

        Returns:
            True 表示成功生成食物，False 表示无可用格子（棋盘已满，玩家胜利）
        """
        all_cells = {
            (x, y)
            for x in range(self._grid_cols)
            for y in range(self._grid_rows)
        }
        occupied_set = set(occupied_cells)
        available = all_cells - occupied_set

        if not available:
            return False

        self.position = random.choice(list(available))
        return True

    def reset(self) -> None:
        """重置食物位置到占位值 (-1, -1)。"""
        self.position = (-1, -1)
