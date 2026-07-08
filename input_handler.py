"""
输入处理 (InputHandler) 模块

遍历 Pygame 事件队列，产出统一命令字典。实现 per-frame 单方向缓冲策略
（同帧多方向键取最后有效者）、方向键到方向向量映射及反向拦截、
QUIT 事件处理、R/Q 键仅在 GAME_OVER/VICTORY 时生效、焦点丢失/恢复检测控制暂停标志、
加速键轮询检测（通过 pygame.key.get_pressed 持续轮询物理按键状态）。
"""

from typing import Dict, Optional, Tuple

import pygame

from config import BOOST_KEY
from game import GameState


class InputHandler:
    """输入处理：遍历 Pygame 事件队列，产出统一命令字典。

    支持的方向键映射：
    - K_UP    -> (0, -1)
    - K_DOWN  -> (0,  1)
    - K_LEFT  -> (-1, 0)
    - K_RIGHT -> (1,  0)

    反向拦截：新方向与当前方向相反时忽略。
    Per-frame 单方向缓冲：同一帧内多个方向键，取最后有效者（已通过反向拦截的）。
    焦点丢失自动暂停，焦点恢复自动继续。
    加速键通过 pygame.key.get_pressed() 轮询检测物理按键状态，暂停时返回 False。

    Attributes:
        _paused: 窗口是否处于失焦暂停状态
        _boost_active: 加速标志位（WINDOWFOCUSLOST 时被强行清除）
    """

    # 方向键 -> 方向向量映射
    DIRECTION_MAP: Dict[int, Tuple[int, int]] = {
        pygame.K_UP: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_RIGHT: (1, 0),
    }

    def __init__(self) -> None:
        """初始化输入处理器，暂停标志和加速标志初始为 False。"""
        self._paused: bool = False
        self._boost_active: bool = False

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def is_boost_pressed(self) -> bool:
        """检测加速键是否被按住。

        通过 pygame.key.get_pressed()[BOOST_KEY] 持续轮询物理按键状态。
        当游戏处于暂停状态（窗口失焦）时始终返回 False，即使物理按键被按住。

        Returns:
            True 表示加速键当前被按住且游戏未暂停
        """
        if self._paused:
            return False
        return bool(pygame.key.get_pressed()[BOOST_KEY])

    def process_events(
        self,
        current_direction: Tuple[int, int],
        state: GameState,
    ) -> dict:
        """遍历 Pygame 事件队列，产出统一命令字典。

        处理流程：
        1. 遍历全部事件
        2. QUIT 事件（窗口关闭按钮）—— 最高优先级，立即返回
        3. 方向键 —— 反向拦截 + per-frame 缓冲（同帧多方向键取最后有效者）
        4. R 键 —— 仅在 GAME_OVER 或 VICTORY 状态时返回 restart
        5. Q 键 —— 仅在 GAME_OVER 或 VICTORY 状态时返回 quit
        6. 窗口焦点事件 —— 失焦暂停、聚焦继续，此时丢弃方向输入
           失焦时同时强行清除 _boost_active 标志
        7. 加速键轮询 —— 通过 is_boost_pressed() 获取当前加速状态

        Args:
            current_direction: 蛇的当前移动方向向量 (dx, dy)
            state: 当前游戏状态（RUNNING / GAME_OVER / VICTORY）

        Returns:
            命令字典，格式为 {'action': str, 'boost': bool, 'direction'?: (dx, dy)}
            action 可能的值为: 'direction', 'restart', 'quit', 'pause', 'resume', 'none'
        """
        last_action: str = 'none'
        last_direction: Optional[Tuple[int, int]] = None

        for event in pygame.event.get():
            # 窗口关闭事件 — 最高优先级，立即返回
            if event.type == pygame.QUIT:
                return {'action': 'quit', 'boost': self.is_boost_pressed()}

            # 窗口焦点事件 — 控制暂停/恢复
            # 注意：Pygame 中将焦点变化作为独立事件类型，而非 WINDOWEVENT 子类型
            elif event.type == pygame.WINDOWFOCUSLOST:
                self._paused = True
                self._boost_active = False
                last_action = 'pause'
                last_direction = None
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self._paused = False
                last_action = 'resume'
                last_direction = None

            # 键盘事件
            elif event.type == pygame.KEYDOWN:
                # 方向键处理 — per-frame 单方向缓冲（最后有效者胜出）
                if event.key in self.DIRECTION_MAP:
                    new_dir = self.DIRECTION_MAP[event.key]
                    if not self._is_reverse(new_dir, current_direction):
                        last_direction = new_dir
                        last_action = 'direction'

                # R 键：仅在 GAME_OVER / VICTORY 状态时生效
                elif event.key == pygame.K_r:
                    if state in (GameState.GAME_OVER, GameState.VICTORY):
                        last_action = 'restart'
                        last_direction = None

                # Q 键：仅在 GAME_OVER / VICTORY 状态时生效
                elif event.key == pygame.K_q:
                    if state in (GameState.GAME_OVER, GameState.VICTORY):
                        last_action = 'quit'
                        last_direction = None

        # 构造返回命令（统一追加 boost 字段）
        if last_action == 'direction' and last_direction is not None:
            return {
                'action': 'direction',
                'direction': last_direction,
                'boost': self.is_boost_pressed(),
            }

        return {'action': last_action, 'boost': self.is_boost_pressed()}

    def is_paused(self) -> bool:
        """返回当前暂停状态。

        暂停由窗口焦点丢失事件触发，由焦点恢复事件解除。

        Returns:
            True 表示游戏已暂停（窗口失焦），False 表示正常
        """
        return self._paused

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _is_reverse(
        new_dir: Tuple[int, int],
        current_dir: Tuple[int, int],
    ) -> bool:
        """检查新方向是否为当前方向的反方向。

        新方向与当前方向分量互为相反数时即为反向：
        new_dir + current_dir == (0, 0)

        Args:
            new_dir: 候选新方向向量
            current_dir: 当前移动方向向量

        Returns:
            True 表示新方向与当前方向相反（应拦截）
        """
        return (
            new_dir[0] + current_dir[0] == 0
            and new_dir[1] + current_dir[1] == 0
        )
