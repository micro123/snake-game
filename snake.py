"""
贪吃蛇 (Snake) 实体模块

纯逻辑组件，管理蛇身坐标列表和移动方向。
实现 move-and-grow 合二为一操作、方向切换（含反向拦截）、
边界碰撞检测、自撞检测及状态重置。
本模块不依赖 Pygame，可独立导入使用。
"""

from typing import List, Tuple


class Snake:
    """蛇实体：管理蛇身坐标和移动方向。

    body 为坐标元组列表，索引 0 为蛇头。body[1:] 为蛇身。

    Attributes:
        body: 蛇身坐标列表 (蛇头在索引 0)
        direction: 当前移动方向向量 (dx, dy)
    """

    # 有效方向向量集合
    VALID_DIRECTIONS = {(1, 0), (-1, 0), (0, -1), (0, 1)}

    def __init__(self, grid_cols: int, grid_rows: int, initial_length: int = 3) -> None:
        """初始化蛇。

        蛇身初始位于网格中心、水平排列、默认向右移动。

        Args:
            grid_cols: 网格列数
            grid_rows: 网格行数
            initial_length: 初始蛇身长度（默认 3 节）
        """
        if grid_cols < initial_length:
            raise ValueError(
                f"grid_cols ({grid_cols}) must be >= initial_length ({initial_length})"
            )
        self._grid_cols = grid_cols
        self._grid_rows = grid_rows
        self._initial_length = initial_length

        self.body: List[Tuple[int, int]] = []
        self.direction: Tuple[int, int] = (1, 0)  # 默认向右
        self.boost_state = {
            'is_active': False,
            'current_multiplier': 1.0,
        }
        self._init_body()

    def _init_body(self) -> None:
        """初始化蛇身坐标：网格中心、水平排列、蛇头位于最右端。"""
        center_col = self._grid_cols // 2
        center_row = self._grid_rows // 2
        # 蛇头在 center_col（最右端），尾部向左延伸
        # body[0]=蛇头=(center_col, center_row)
        # body[1]=(center_col-1, center_row)
        # body[2]=(center_col-2, center_row) ...
        self.body = [
            (center_col - i, center_row)
            for i in range(self._initial_length)
        ]
        self.direction = (1, 0)

    @property
    def head(self) -> Tuple[int, int]:
        """获取蛇头坐标。"""
        return self.body[0]

    @property
    def length(self) -> int:
        """获取蛇身长度（节数）。"""
        return len(self.body)

    @property
    def is_boosting(self) -> bool:
        """获取加速状态：是否当前处于加速中。"""
        return self.boost_state['is_active']

    @property
    def boost_multiplier(self) -> float:
        """获取当前加速倍率，保证返回值 >= 1.0。"""
        return max(1.0, self.boost_state['current_multiplier'])

    # ------------------------------------------------------------------
    # 核心逻辑
    # ------------------------------------------------------------------

    def move_and_grow(self, grow_flag: bool) -> None:
        """移动蛇：在蛇头前方插入新头部，根据 grow_flag 决定是否移除尾部。

        合二为一操作：insert head + 条件 pop tail。
        无论是否增长，蛇头都会前移。grow_flag=True 时尾部保留，身体净增 1 节；
        grow_flag=False 时尾部弹出，身体长度保持不变。

        Args:
            grow_flag: 是否增长（True=保留尾部，False=弹出尾部）
        """
        new_head = (self.head[0] + self.direction[0], self.head[1] + self.direction[1])
        self.body.insert(0, new_head)
        if not grow_flag:
            self.body.pop()

    def change_direction(self, dx: int, dy: int) -> bool:
        """尝试更改蛇的移动方向。

        拦截反向输入：如果新方向与当前方向恰好相反（(dx, dy) == (-self.direction[0], -self.direction[1])），
        则拒绝更改并返回 False。非有效方向（非上下左右）也返回 False。

        Args:
            dx: X 方向增量（-1, 0 或 1）
            dy: Y 方向增量（-1, 0 或 1）

        Returns:
            True 表示方向已更改，False 表示被拦截（反向输入或无效方向）
        """
        new_direction = (dx, dy)
        if new_direction not in self.VALID_DIRECTIONS:
            return False
        # 反向拦截：新方向 + 当前方向 == (0, 0) 即为反向
        if (dx + self.direction[0] == 0) and (dy + self.direction[1] == 0):
            return False
        self.direction = new_direction
        return True

    # ------------------------------------------------------------------
    # 碰撞检测
    # ------------------------------------------------------------------

    def check_boundary_collision(self, cols: int, rows: int) -> bool:
        """检查蛇头是否越界（撞墙）。

        Args:
            cols: 网格列数
            rows: 网格行数

        Returns:
            True 表示蛇头坐标超出 [0, cols-1] 或 [0, rows-1] 范围（撞墙）
        """
        x, y = self.head
        return x < 0 or x >= cols or y < 0 or y >= rows

    def check_self_collision(self) -> bool:
        """检查蛇头是否碰撞自身身体。

        在 body[1:] 中查找蛇头坐标。若蛇身仅 1 节（只有蛇头），
        body[1:] 为空，不可能自撞，返回 False。

        Returns:
            True 表示蛇头与蛇身任意一节重合（自撞）
        """
        return self.head in self.body[1:]

    # ------------------------------------------------------------------
    # 状态重置
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """重置蛇到初始状态：恢复初始身体坐标、移动方向和加速状态。"""
        self._init_body()
        self.boost_state['is_active'] = False
        self.boost_state['current_multiplier'] = 1.0
