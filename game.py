"""
游戏 (Game) 协调模块

定义 Game 协调器类。GameState 枚举定义于 config 模块并在此重新导出以保持向后兼容。
Game 协调器：持有所有组件实例、管理分数和 GameState 状态机、
协调主循环（tick -> 处理输入 -> 更新逻辑 -> 渲染 -> flip）。
"""

import pygame

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
    GRID_COLS, GRID_ROWS,
    INITIAL_SNAKE_LENGTH, SCORE_PER_FOOD,
    GameState,  # noqa: F401 (重新导出供外部使用)
)
from snake import Snake
from food import Food
from renderer import Renderer
from input_handler import InputHandler


# 重新导出 GameState 以保持向后兼容（renderer/input_handler/tests 均从此导入）
__all__ = ["Game", "GameState"]


class Game:
    """游戏协调器：管理全部组件和游戏状态机。

    持有 Snake, Food, Renderer, InputHandler 组件实例；
    管理分数、GameState 状态机；协调主游戏循环。

    Attributes:
        snake: Snake 实例
        food: Food 实例
        renderer: Renderer 实例
        input_handler: InputHandler 实例
        score: 当前分数
        state: 当前游戏状态（GameState 枚举）
        screen: Pygame 窗口 Surface
    """

    def __init__(self) -> None:
        """初始化游戏：创建窗口、实例化全部组件、生成首个食物。

        - 创建 800x600 固定尺寸窗口，设置标题为"贪吃蛇"
        - 实例化 Snake（中心位置，3节，向右）
        - 实例化 Food（占位值 (-1, -1)）
        - 实例化 Renderer（绑定窗口 Surface，初始化字体和时钟）
        - 实例化 InputHandler
        - 调用 food.respawn() 生成首个食物
        - 分数初始化为 0，状态设置为 RUNNING
        """
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)

        self.snake = Snake(GRID_COLS, GRID_ROWS, INITIAL_SNAKE_LENGTH)
        self.food = Food(GRID_COLS, GRID_ROWS)
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()

        self.score: int = 0
        self.state: GameState = GameState.RUNNING

        # 生成首个食物（排除蛇身占据的格子）
        self.food.respawn(self.snake.body)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------

    def run(self) -> None:
        """主游戏循环：按固定帧率循环执行。

        每帧执行顺序：
        1. renderer.tick()               — 帧率控制
        2. input_handler.process_events() — 事件处理 -> 命令字典
        3. _handle_command(command)       — 分发命令（quit/restart/direction）
        4. _update()                      — 更新游戏逻辑
        5. renderer.draw_frame()          — 图层化渲染
        6. pygame.display.flip()          — 双缓冲交换

        当 _handle_command 返回 False（quit 命令）时循环终止。
        """
        running = True
        while running:
            self.renderer.tick()
            command = self.input_handler.process_events(
                self.snake.direction, self.state
            )
            running = self._handle_command(command)
            self._update()
            self.renderer.draw_frame(
                self.snake, self.food, self.score, self.state
            )
            pygame.display.flip()

    # ------------------------------------------------------------------
    # 命令分发
    # ------------------------------------------------------------------

    def _handle_command(self, command: dict) -> bool:
        """分发 InputHandler 产出的命令字典。

        支持的命令 action：
        - 'quit':     返回 False 退出主循环
        - 'restart':  调用 reset() 重置游戏
        - 'direction': 仅在 RUNNING 状态下变更蛇的方向
        - 其他 ('none', 'pause', 'resume'): 无操作，返回 True

        Args:
            command: 命令字典 {'action': str, 'direction'?: (dx, dy)}

        Returns:
            True 表示继续运行主循环，False 表示退出
        """
        action = command.get('action', 'none')

        if action == 'quit':
            return False

        if action == 'restart':
            self.reset()

        if action == 'direction' and self.state == GameState.RUNNING:
            direction = command.get('direction')
            if direction:
                self.snake.change_direction(*direction)

        return True

    # ------------------------------------------------------------------
    # 逻辑更新
    # ------------------------------------------------------------------

    def _update(self) -> None:
        """更新游戏逻辑：碰撞检测 -> 移动 -> 状态迁移。

        仅在 RUNNING 状态且未暂停时执行。

        流程：
        1. 检测食物碰撞（蛇头 == 食物位置，在移动前判断）
        2. move_and_grow(grow_flag)：蛇前进一步，根据碰撞决定是否增长
        3. 若吃到食物：加分 + 重新生成食物（若棋盘满则 VICTORY）
        4. 边界碰撞检测 -> GAME_OVER
        5. 自撞检测 -> GAME_OVER
        """
        if self.state != GameState.RUNNING:
            return

        if self.input_handler.is_paused():
            return

        # 计算移动后的新蛇头位置（在移动前预判，确保蛇头到达食物格子的同一帧就触发吃食）
        new_head = (
            self.snake.head[0] + self.snake.direction[0],
            self.snake.head[1] + self.snake.direction[1],
        )
        grow_flag = (new_head == self.food.position)

        # 移动蛇（grow_flag=True 时保留尾部，身体净增1节）
        self.snake.move_and_grow(grow_flag)

        # 吃到食物：加分 + 重新生成
        if grow_flag:
            self.score += SCORE_PER_FOOD
            if not self.food.respawn(self.snake.body):
                self.state = GameState.VICTORY
                return

        # 边界碰撞检测
        if self.snake.check_boundary_collision(GRID_COLS, GRID_ROWS):
            self.state = GameState.GAME_OVER
            return

        # 自撞检测
        if self.snake.check_self_collision():
            self.state = GameState.GAME_OVER
            return

    # ------------------------------------------------------------------
    # 状态重置
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """重置全部组件到初始状态。

        执行顺序：
        1. snake.reset()           — 恢复初始身体坐标和方向
        2. food.reset() + respawn  — 重置占位值并重新生成食物
        3. score = 0, state = RUNNING — 重置分数和游戏状态
        """
        self.snake.reset()
        self.food.reset()
        self.food.respawn(self.snake.body)
        self.score = 0
        self.state = GameState.RUNNING
