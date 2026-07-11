"""
游戏 (Game) 协调模块

定义 Game 协调器类。GameState 枚举定义于 config 模块并在此重新导出以保持向后兼容。
Game 协调器：持有所有组件实例、管理分数和 GameState 状态机、
协调主循环（tick -> 处理输入 -> 更新逻辑 -> 渲染 -> flip）。
"""

import pygame

from config import (
    BASE_TICK_INTERVAL, BOOST_SPEED_MULTIPLIER, BOOST_TRANSITION_SECONDS,
    DIFFICULTY_INCREMENT, MAX_BOOST_MULTIPLIER, MAX_CATCHUP_STEPS,
    MAX_DIFFICULTY_MULTIPLIER, MIN_TICK_INTERVAL,
    SCORE_THRESHOLD_INTERVAL,
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
        self.difficulty_level: int = 0
        self.difficulty_multiplier: float = 0.0

        # 生成首个食物（排除蛇身占据的格子）
        self.food.respawn(self.snake.body)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------

    def run(self) -> None:
        """主游戏循环：渲染与逻辑解耦架构。

        渲染以固定 RENDER_FPS (60) 帧率驱动，逻辑通过时间累加器
        （accumulator += dt ms）按可变 tick_interval 推进。

        每帧执行顺序：
        1. renderer.tick()                — 帧率控制 @ RENDER_FPS，返回 ms 级 dt
        2. input_handler.process_events() — 事件处理 -> 命令字典
        3. _handle_command(command)       — 分发命令（quit/restart/direction）
        4. _update_boost_state(dt, boost) — 平滑加速过渡
        5. 累加器 logic: accumulator += dt，累加器 >= tick_interval 时
           触发 _update()，最多连续触发 MAX_CATCHUP_STEPS 次
        6. renderer.draw_frame()          — 图层化渲染（含 is_boosting 传递）
        7. pygame.display.flip()          — 双缓冲交换

        spiral-of-death 保护：MAX_CATCHUP_STEPS=5 限制单帧最多5次逻辑更新，
        超限时丢弃多余 accumulator 时间。非 RUNNING 或暂停时 accumulator 清零，
        不推进逻辑。

        当 _handle_command 返回 False（quit 命令）时循环终止。
        """
        import logging
        _logger = logging.getLogger(__name__)

        running = True
        accumulator: float = 0.0
        while running:
            # 1. 渲染帧率控制（返回距上次 tick 的毫秒数）
            dt = self.renderer.tick()

            # 2. 输入事件处理（使用 committed_direction 确保跨帧反向检测稳定）
            command = self.input_handler.process_events(
                self.snake.committed_direction, self.state
            )
            running = self._handle_command(command)

            # 3. 平滑加速状态过渡（每帧执行，含 dt）
            self._update_boost_state(dt, command.get('boost', False))

            # 4. 时间累加器逻辑更新
            if self.state == GameState.RUNNING and not self.input_handler.is_paused():
                accumulator += dt
                catchup_steps = 0

                while accumulator >= self._get_current_tick_interval():
                    current_interval = self._get_current_tick_interval()
                    if accumulator < current_interval:
                        break
                    self._update()
                    accumulator -= current_interval
                    catchup_steps += 1

                    # spiral-of-death 保护
                    if catchup_steps >= MAX_CATCHUP_STEPS:
                        if accumulator > 0:
                            _logger.debug(
                                "RT-002: Max catchup steps (%d) reached, "
                                "discarding %.1fms excess accumulator",
                                MAX_CATCHUP_STEPS, accumulator,
                            )
                        accumulator = 0.0
                        break
            else:
                # 非 RUNNING 或暂停：清空累加器，不推进逻辑
                accumulator = 0.0

            # 5. 图层化渲染
            # 计算综合倍率（用于 HUD 显示）
            effective_multiplier = (
                1.0
                + self.difficulty_multiplier
                + (self.snake.boost_multiplier - 1.0)
            )
            self.renderer.draw_frame(
                self.snake, self.food, self.score, self.state,
                is_boosting=self.snake.is_boosting,
                difficulty_level=self.difficulty_level,
                effective_multiplier=effective_multiplier,
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

    def _update_difficulty(self) -> None:
        """根据当前分数重新计算难度等级和难度倍率。

        level = score // SCORE_THRESHOLD_INTERVAL
        multiplier = min(level * DIFFICULTY_INCREMENT, MAX_DIFFICULTY_MULTIPLIER)

        幂等：相同 score 反复调用结果不变。基于 score 计算 level 再乘 increment，
        无浮点累加误差风险。
        """
        self.difficulty_level = self.score // SCORE_THRESHOLD_INTERVAL
        self.difficulty_multiplier = min(
            self.difficulty_level * DIFFICULTY_INCREMENT,
            MAX_DIFFICULTY_MULTIPLIER,
        )

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

        # 吃到食物：加分 + 难度更新 + 重新生成
        if grow_flag:
            self.score += SCORE_PER_FOOD
            self._update_difficulty()
            if not self.food.respawn(self.snake.body):
                self.state = GameState.VICTORY
                self._reset_boost()
                return

        # 边界碰撞检测
        if self.snake.check_boundary_collision(GRID_COLS, GRID_ROWS):
            self.state = GameState.GAME_OVER
            self._reset_boost()
            return

        # 自撞检测
        if self.snake.check_self_collision():
            self.state = GameState.GAME_OVER
            self._reset_boost()
            return

    # ------------------------------------------------------------------
    # 加速状态管理
    # ------------------------------------------------------------------

    def _update_boost_state(self, dt: float, boost_pressed: bool) -> None:
        """每帧更新加速状态的平滑过渡。

        根据 boost_pressed 决定目标倍率（BOOST_SPEED_MULTIPLIER 或 1.0），
        在 BOOST_TRANSITION_SECONDS 时长内线性插值平滑过渡。

        BOOST_TRANSITION_SECONDS <= 0 时直接瞬时切换（不插值）。
        非 RUNNING 状态（GAME_OVER/VICTORY）下强制目标倍率为 1.0，
        确保加速在非游玩状态下不生效。

        Args:
            dt: 距上一帧的时间（毫秒）
            boost_pressed: 加速键是否当前被按住
        """
        # 非 RUNNING 状态强制倍率为 1.0（不允许加速）
        if self.state != GameState.RUNNING:
            target = 1.0
        else:
            target = BOOST_SPEED_MULTIPLIER if boost_pressed else 1.0
        current = self.snake.boost_state['current_multiplier']

        if abs(target - current) < 0.001:
            # 已足够接近目标，直接设为目标值
            current = target
        elif BOOST_TRANSITION_SECONDS <= 0:
            # 无过渡时长配置，瞬时切换
            current = target
        else:
            # 线性插值平滑过渡
            rate = (BOOST_SPEED_MULTIPLIER - 1.0) / (BOOST_TRANSITION_SECONDS * 1000.0)
            if target > current:
                current += rate * dt
                if current > target:
                    current = target
            else:
                current -= rate * dt
                if current < target:
                    current = target

        # 防御性 clamp：保证倍率在安全范围内
        current = max(1.0, min(MAX_BOOST_MULTIPLIER, current))
        self.snake.boost_state['current_multiplier'] = current
        self.snake.boost_state['is_active'] = current > 1.01

    def _get_current_tick_interval(self) -> float:
        """根据难度倍率和加速倍率计算实际逻辑 tick 间隔(ms)。

        公式: interval = BASE_TICK_INTERVAL / (1 + difficulty + boost_extra)
        其中 boost_extra = boost_multiplier - 1.0。

        施加 max(result, MIN_TICK_INTERVAL) 硬下限，确保 tick 不低于 20ms。
        防御性校验：interval 为 NaN / 零 / 负值时回退到 BASE_TICK_INTERVAL。

        Returns:
            当前逻辑 tick 间隔（毫秒），保证 >= MIN_TICK_INTERVAL
        """
        import logging
        _logger = logging.getLogger(__name__)

        boost_extra = self.snake.boost_multiplier - 1.0
        effective = 1.0 + self.difficulty_multiplier + boost_extra
        try:
            interval = BASE_TICK_INTERVAL / effective
            if interval <= 0 or interval != interval:  # NaN 检查
                raise ValueError("invalid interval: {}".format(interval))
        except (ValueError, ZeroDivisionError):
            _logger.error(
                "RT-001: tick_interval computed as invalid "
                "(effective=%.1f, difficulty=%.1f, boost=%.1f), "
                "fallback to BASE_TICK_INTERVAL (%d)",
                effective, self.difficulty_multiplier,
                self.snake.boost_multiplier, BASE_TICK_INTERVAL,
            )
            interval = float(BASE_TICK_INTERVAL)
        return max(float(MIN_TICK_INTERVAL), float(interval))

    def _reset_boost(self) -> None:
        """强制复位加速状态到初始值。

        在状态转换（GAME_OVER / VICTORY / restart）时调用，
        确保加速状态 100% 复位（NFR-R001）。
        同时复位 snake.boost_state 和 input_handler._boost_active。
        """
        self.snake.boost_state['is_active'] = False
        self.snake.boost_state['current_multiplier'] = 1.0
        self.input_handler._boost_active = False

    # ------------------------------------------------------------------
    # 状态重置
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """重置全部组件到初始状态。

        执行顺序：
        1. snake.reset()           — 恢复初始身体坐标和方向（含 boost_state）
        2. food.reset() + respawn  — 重置占位值并重新生成食物
        3. score = 0, state = RUNNING — 重置分数和游戏状态
        4. _reset_boost()          — 双重保险确保 boost 完全复位
        """
        self.snake.reset()
        self.food.reset()
        self.food.respawn(self.snake.body)
        self.score = 0
        self.state = GameState.RUNNING
        self.difficulty_level = 0
        self.difficulty_multiplier = 0.0
        self._reset_boost()
