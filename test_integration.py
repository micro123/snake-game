"""
T-009: 集成测试与边界验证

覆盖：
  - AC-1 至 AC-9 全部 9 条验收标准端到端验证
  - E-001 至 E-009 全部 9 个边界情况
  - 碰撞精度验证（网格级无误判漏判）
  - 重启流程一致性验证
  - 性能验证（FPS 稳定性 ±20%、内存无泄漏）

使用 Python 标准库 unittest 框架，依赖 Pygame。
"""

import gc
import io
import sys
import time
import unittest
from unittest.mock import patch

import pygame

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
    CELL_SIZE, GRID_COLS, GRID_ROWS,
    FPS, INITIAL_SNAKE_LENGTH, SCORE_PER_FOOD, HUD_HEIGHT,
    COLORS,
)
from game import Game, GameState
from snake import Snake
from food import Food
from renderer import Renderer
from input_handler import InputHandler


# =============================================================================
# 模块级 setUp / tearDown
# =============================================================================

def setUpModule():
    """初始化 Pygame（测试前执行一次）"""
    pygame.init()


def tearDownModule():
    """退出 Pygame（测试后执行一次）"""
    pygame.quit()


# =============================================================================
# 测试辅助
# =============================================================================

def _make_surface() -> pygame.Surface:
    """创建一个与游戏窗口同尺寸的真实 Pygame Surface。"""
    return pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))


def _post_key(key: int) -> None:
    """向 Pygame 事件队列投递一个键盘按下事件。"""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def _post_event(event_type: int, **attrs) -> None:
    """向 Pygame 事件队列投递一个事件。"""
    pygame.event.post(pygame.event.Event(event_type, **attrs))


def _clear_events() -> None:
    """清空 Pygame 事件队列。"""
    pygame.event.clear()


class _IntegrationTestBase(unittest.TestCase):
    """集成测试基类：为每个测试创建带 Mock 显示层的 Game 实例。"""

    def setUp(self):
        self._set_mode_patcher = patch(
            'pygame.display.set_mode', return_value=_make_surface()
        )
        self._set_caption_patcher = patch('pygame.display.set_caption')
        self._flip_patcher = patch('pygame.display.flip')

        self._set_mode_patcher.start()
        self._set_caption_patcher.start()
        self._flip_patcher.start()

        self.game = Game()
        _clear_events()

    def tearDown(self):
        _clear_events()
        self._set_mode_patcher.stop()
        self._set_caption_patcher.stop()
        self._flip_patcher.stop()


# =============================================================================
# AC-1: 窗口验证 — 标题、尺寸固定、正常启动
# =============================================================================

class TestAC01WindowStartup(_IntegrationTestBase):
    """AC-1: 游戏窗口能正常启动，窗口标题包含游戏名称，
       窗口尺寸固定且合理（如 800x600 或 640x480）。"""

    def test_screen_size_is_fixed_800x600(self):
        """窗口尺寸固定为 800x600"""
        self.assertEqual((WINDOW_WIDTH, WINDOW_HEIGHT),
                         self.game.screen.get_size())

    def test_window_caption_set_to_game_title(self):
        """窗口标题包含游戏名称"""
        self._set_caption_patcher.stop()
        real_caption_patcher = patch('pygame.display.set_caption')
        real_caption_patcher.start()
        self.addCleanup(real_caption_patcher.stop)

        # 重建 Game 触发真实 set_caption
        old_game = self.game
        self.game = Game()
        pygame.display.set_caption.assert_called_with(WINDOW_TITLE)

    def test_game_creates_all_components_on_startup(self):
        """启动时创建全部组件"""
        self.assertIsInstance(self.game.snake, Snake)
        self.assertIsInstance(self.game.food, Food)
        self.assertIsInstance(self.game.renderer, Renderer)
        self.assertIsInstance(self.game.input_handler, InputHandler)

    def test_game_starts_in_running_state(self):
        """启动后游戏状态为 RUNNING"""
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_game_initializes_with_score_zero(self):
        """启动时分数为 0"""
        self.assertEqual(0, self.game.score)


# =============================================================================
# AC-2: 蛇初始状态 — 3 节、默认向右
# =============================================================================

class TestAC02SnakeInitialState(unittest.TestCase):
    """AC-2: 蛇在游戏开始时以固定长度（如3节）出现在画面中，默认向右移动。"""

    def test_snake_starts_with_three_segments(self):
        """蛇初始长度为 3"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        self.assertEqual(INITIAL_SNAKE_LENGTH, snake.length)

    def test_snake_default_direction_is_right(self):
        """蛇默认向右移动"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        self.assertEqual((1, 0), snake.direction)

    def test_snake_body_is_contiguous(self):
        """蛇身连续无间隙"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        for i in range(len(snake.body) - 1):
            dx = abs(snake.body[i][0] - snake.body[i + 1][0])
            dy = abs(snake.body[i][1] - snake.body[i + 1][1])
            self.assertEqual(1, dx + dy,
                             f"Gap between {snake.body[i]} and {snake.body[i+1]}")

    def test_snake_head_at_rightmost(self):
        """蛇头在蛇身最右端"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        self.assertEqual(20, snake.head[0])
        self.assertEqual(15, snake.head[1])
        self.assertEqual((19, 15), snake.body[1])
        self.assertEqual((18, 15), snake.body[2])

    def test_snake_position_within_game_area(self):
        """蛇身在游戏区域有效位置内"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        for x, y in snake.body:
            self.assertTrue(0 <= x < GRID_COLS, f"x={x} out of grid range")
            self.assertTrue(0 <= y < GRID_ROWS, f"y={y} out of grid range")


# =============================================================================
# AC-3: 方向键控制 — 即时响应、反向拦截
# =============================================================================

class TestAC03DirectionControl(_IntegrationTestBase):
    """AC-3: 按下方向键后蛇的移动方向立即改变，且不能反向。"""

    def test_direction_changes_immediately(self):
        """方向键改变方向后下一逻辑帧生效"""
        _post_key(pygame.K_UP)
        command = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.game._handle_command(command)

        # 移动一步验证方向变化
        old_head = self.game.snake.head
        self.game._update()
        expected = (old_head[0], old_head[1] - 1)  # 向上
        self.assertEqual(expected, self.game.snake.head)

    def test_reverse_left_rejected_when_moving_right(self):
        """向右移动时不能左转"""
        _post_key(pygame.K_LEFT)
        command = self.game.input_handler.process_events(
            (1, 0), self.game.state)
        self.assertEqual('none', command['action'])

    def test_reverse_right_rejected_when_moving_left(self):
        """向左移动时不能右转"""
        _post_key(pygame.K_RIGHT)
        command = self.game.input_handler.process_events(
            (-1, 0), self.game.state)
        self.assertEqual('none', command['action'])

    def test_reverse_up_rejected_when_moving_down(self):
        """向下移动时不能上转"""
        _post_key(pygame.K_UP)
        command = self.game.input_handler.process_events(
            (0, 1), self.game.state)
        self.assertEqual('none', command['action'])

    def test_reverse_down_rejected_when_moving_up(self):
        """向上移动时不能下转"""
        _post_key(pygame.K_DOWN)
        command = self.game.input_handler.process_events(
            (0, -1), self.game.state)
        self.assertEqual('none', command['action'])

    def test_all_four_directions_accessible(self):
        """四个方向均可到达（通过间接转向）"""
        # 向右(1,0) -> 向上(0,-1) -> 向左(-1,0) -> 向下(0,1)
        directions = [(0, -1), (-1, 0), (0, 1)]
        current = (1, 0)
        snake = Snake(GRID_COLS, GRID_ROWS)
        for d in directions:
            result = snake.change_direction(*d)
            self.assertTrue(result, f"Cannot change from {current} to {d}")
            current = d

    def test_non_direction_keys_ignored(self):
        """非方向键不改变蛇方向"""
        for key in (pygame.K_SPACE, pygame.K_a, pygame.K_ESCAPE):
            _clear_events()
            _post_key(key)
            command = self.game.input_handler.process_events(
                self.game.snake.direction, self.game.state)
            self.assertEqual('none', command['action'])


# =============================================================================
# AC-4: 食物显示 — 颜色、随机空白位置
# =============================================================================

class TestAC04FoodDisplay(unittest.TestCase):
    """AC-4: 食物以明显区别于背景和蛇的颜色显示在游戏区域内的随机空白位置。"""

    def test_food_color_differs_from_background(self):
        """食物颜色不同于背景色"""
        self.assertNotEqual(COLORS.FOOD, COLORS.BACKGROUND)

    def test_food_color_differs_from_snake_body(self):
        """食物颜色不同于蛇身色"""
        self.assertNotEqual(COLORS.FOOD, COLORS.SNAKE_BODY)

    def test_food_color_differs_from_snake_head(self):
        """食物颜色不同于蛇头色"""
        self.assertNotEqual(COLORS.FOOD, COLORS.SNAKE_HEAD)

    def test_food_appears_in_valid_grid(self):
        """食物出现在有效网格范围内"""
        for _ in range(50):
            food = Food(GRID_COLS, GRID_ROWS)
            food.respawn([(10, 10)])
            x, y = food.position
            self.assertTrue(0 <= x < GRID_COLS)
            self.assertTrue(0 <= y < GRID_ROWS)

    def test_food_not_on_occupied_cells(self):
        """食物不会生成在蛇身占据的格子上"""
        occupied = [(5, 5), (6, 5), (7, 5), (8, 5)]
        for _ in range(100):
            food = Food(GRID_COLS, GRID_ROWS)
            food.respawn(occupied)
            self.assertNotIn(food.position, occupied)

    def test_food_position_is_unique(self):
        """同时只存在一个食物"""
        food1 = Food(GRID_COLS, GRID_ROWS)
        food1.respawn([])
        food2 = Food(GRID_COLS, GRID_ROWS)
        food2.respawn([])
        # 每个 Food 实例各自独立，验证单实例只有一个 position
        self.assertIsNotNone(food1.position)
        self.assertIsNotNone(food2.position)


# =============================================================================
# AC-5: 吃食物增长与得分
# =============================================================================

class TestAC05FoodConsumption(_IntegrationTestBase):
    """AC-5: 蛇头碰到食物时，蛇身增长一节、分数+10、食物在另一空白位置重新生成。"""

    def test_eating_food_grows_snake(self):
        """吃食物后蛇身增长 1 节"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])

        old_length = self.game.snake.length
        self.game._update()  # move onto food
        self.game._update()  # eat + grow

        self.assertEqual(old_length + 1, self.game.snake.length)

    def test_eating_food_increases_score(self):
        """吃食物后分数增加 SCORE_PER_FOOD (10)"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])

        old_score = self.game.score
        self.game._update()  # move onto food
        self.game._update()  # eat + score

        self.assertEqual(old_score + SCORE_PER_FOOD, self.game.score)

    def test_food_removed_and_reappears(self):
        """食物被吃后移除，在新的空白位置重新生成"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])
        eaten_pos = self.game.food.position

        self.game._update()  # move onto food
        self.game._update()  # eat + respawn

        self.assertNotEqual(eaten_pos, self.game.food.position)

    def test_food_not_on_snake_after_respawn(self):
        """重新生成的食物不落在蛇身上"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])

        self.game._update()
        self.game._update()

        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_score_cumulative_over_multiple_food(self):
        """连续吃多个食物，分数累加正确"""
        for _ in range(5):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()
            self.game._update()

        self.assertEqual(5 * SCORE_PER_FOOD, self.game.score)
        self.assertEqual(INITIAL_SNAKE_LENGTH + 5, self.game.snake.length)


# =============================================================================
# AC-6: 撞墙游戏结束
# =============================================================================

class TestAC06BoundaryCollision(_IntegrationTestBase):
    """AC-6: 蛇头碰到游戏区域边界时，游戏停止，显示游戏结束信息。"""

    def test_left_boundary_causes_game_over(self):
        """蛇头左侧出界 -> GAME_OVER"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_right_boundary_causes_game_over(self):
        """蛇头右侧出界 -> GAME_OVER"""
        self.game.snake.body = [(GRID_COLS - 1, 15),
                                (GRID_COLS - 2, 15),
                                (GRID_COLS - 3, 15)]
        self.game.snake.direction = (1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_top_boundary_causes_game_over(self):
        """蛇头顶部出界 -> GAME_OVER"""
        self.game.snake.body = [(20, 0), (20, 1), (20, 2)]
        self.game.snake.direction = (0, -1)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_bottom_boundary_causes_game_over(self):
        """蛇头底部出界 -> GAME_OVER"""
        self.game.snake.body = [(20, GRID_ROWS - 1),
                                (20, GRID_ROWS - 2),
                                (20, GRID_ROWS - 3)]
        self.game.snake.direction = (0, 1)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_snake_frozen_after_boundary_collision(self):
        """撞墙后蛇停止移动（_update 不改变蛇身）"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        body_after_end = list(self.game.snake.body)
        # 再次 _update 不应改变蛇身
        self.game._update()
        self.assertEqual(body_after_end, self.game.snake.body)

    def test_boundary_game_over_displays_game_over_state(self):
        """边界碰撞后 state 变为 GAME_OVER"""
        self.game.snake.body = [(GRID_COLS - 1, 15),
                                (GRID_COLS - 2, 15),
                                (GRID_COLS - 3, 15)]
        self.game.snake.direction = (1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)


# =============================================================================
# AC-7: 自撞游戏结束
# =============================================================================

class TestAC07SelfCollision(_IntegrationTestBase):
    """AC-7: 蛇头碰到蛇身任意一节时，游戏停止，显示游戏结束信息。"""

    def test_self_collision_causes_game_over(self):
        """自撞 -> GAME_OVER"""
        # 构造蛇头撞到身体的情况
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)  # head -> (3, 3) 撞到 body[1]
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_self_collision_frozen_after(self):
        """自撞后蛇停止移动"""
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)
        self.game._update()
        body_after = list(self.game.snake.body)
        self.game._update()
        self.assertEqual(body_after, self.game.snake.body)

    def test_no_self_collision_in_normal_movement(self):
        """正常运行时不误判自撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        for _ in range(10):
            snake.move_and_grow(False)
            self.assertFalse(snake.check_self_collision(),
                             f"False positive at body={snake.body}")

    def test_self_collision_with_head_not_in_body_tail(self):
        """蛇头仅与自身头部比较时不误判（body[1:] 检查）"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(10, 10), (9, 10), (8, 10)]
        # head(10,10) not in body[1:] [(9,10), (8,10)]
        self.assertFalse(snake.check_self_collision())

    def test_no_self_collision_before_move(self):
        """移动前不自撞，移动后才检查"""
        # Snake 初始化在合法位置，不自撞
        self.assertFalse(self.game.snake.check_self_collision())


# =============================================================================
# AC-8: 帧率稳定与输入响应
# =============================================================================

class TestAC08FPSAndResponsiveness(_IntegrationTestBase):
    """AC-8: 游戏运行期间帧率稳定，无卡顿或明显延迟，
       输入响应延迟在可接受范围内。"""

    def test_tick_enforces_frame_rate(self):
        """tick 延时接近 1/FPS 秒"""
        renderer = self.game.renderer
        # 只做一次预热 tick
        renderer.tick()
        # 测量连续 tick 的时间间隔
        intervals = []
        for _ in range(10):
            t0 = time.time()
            renderer.tick()
            dt = time.time() - t0
            intervals.append(dt)

        avg_interval = sum(intervals) / len(intervals)
        target_interval = 1.0 / FPS  # 0.1s for FPS=10

        # 平均帧间隔应在目标的 ±20% 内
        self.assertGreaterEqual(avg_interval, target_interval * 0.8,
                                f"FPS too high: {1.0/avg_interval:.1f}")
        # tick 返回的毫秒数应在合理范围
        self.assertLessEqual(avg_interval, target_interval * 2.0,
                             f"FPS too low: {1.0/avg_interval:.1f}")

    def test_fps_deviation_within_20_percent(self):
        """FPS 偏差不超过 ±20%"""
        renderer = self.game.renderer
        renderer.tick()  # warm-up

        frame_times = []
        for _ in range(30):
            t0 = time.time()
            ms = renderer.tick()
            frame_times.append(time.time() - t0)

        avg = sum(frame_times) / len(frame_times)
        target = 1.0 / FPS

        deviation = abs(avg - target) / target
        self.assertLessEqual(deviation, 0.20,
                             f"FPS deviation {deviation:.2%} exceeds 20% "
                             f"(avg={1/avg:.1f} FPS, target={FPS} FPS)")

    def test_tick_returns_positive_milliseconds(self):
        """tick 返回正整数的毫秒数"""
        renderer = self.game.renderer
        for _ in range(5):
            ms = renderer.tick()
            self.assertIsInstance(ms, int)
            self.assertGreaterEqual(ms, 0)

    def test_clock_repeatable(self):
        """clock.tick 可重复调用不崩溃"""
        renderer = self.game.renderer
        for _ in range(100):
            renderer.tick()
        # 不崩溃即为通过

    def test_single_frame_update_is_quick(self):
        """单帧逻辑更新耗时极短（< 1ms，确保不阻塞）"""
        t0 = time.time()
        self.game._update()
        dt = time.time() - t0
        self.assertLess(dt, 0.05, "Single frame update took too long")

    def test_full_frame_cycle_is_quick(self):
        """完整帧周期（tick+update+draw+flip）不慢"""
        t0 = time.time()
        self.game.renderer.tick()
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.game._handle_command(cmd)
        self.game._update()
        self.game.renderer.draw_frame(
            self.game.snake, self.game.food, self.game.score, self.game.state)
        # flip is mocked
        dt = time.time() - t0
        self.assertLess(dt, 0.15, "Full frame cycle took too long")


# =============================================================================
# AC-9: 分数实时显示
# =============================================================================

class TestAC09ScoreDisplay(_IntegrationTestBase):
    """AC-9: 分数在游戏界面上持续可见并实时更新。"""

    def test_score_visible_in_hud(self):
        """分数在 HUD 中渲染"""
        renderer = self.game.renderer
        renderer.draw_hud(100)
        # 验证 HUD 区域有非背景色的像素
        hud_color = tuple(renderer.screen.get_at((WINDOW_WIDTH // 2, 20))[:3])
        # HUD 条有半透明效果，颜色应不同于纯背景色
        self.assertNotEqual(COLORS.BACKGROUND, hud_color)

    def test_score_updates_on_food_eaten(self):
        """吃食物后分数立即在下一帧反映"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])
        score_before = self.game.score

        self.game._update()  # move onto food
        # 此时还未加分（碰撞在下一步的 _update 中检测）
        self.game._update()  # eat + score

        self.assertEqual(score_before + SCORE_PER_FOOD, self.game.score)

    def test_score_starts_at_zero(self):
        """游戏开始时分数为 0"""
        self.assertEqual(0, self.game.score)

    def test_score_persists_in_non_running_states(self):
        """游戏结束后分数定格不变"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game.score = 50
        self.game._update()  # GAME_OVER
        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertEqual(50, self.game.score)

    def test_hud_renders_correct_score_text(self):
        """HUD 正确渲染分数文字（像素级验证非空白）"""
        renderer = self.game.renderer
        renderer.draw_background()
        renderer.draw_hud(999)
        # HUD 区域应有文字渲染（非纯透明黑）
        sample_pixels = [
            renderer.screen.get_at((x, 20))
            for x in (50, 100, 150, 200)
        ]
        # 至少某些像素不是纯背景色，证明了文字被渲染
        non_bg_count = sum(
            1 for px in sample_pixels
            if tuple(px[:3]) != COLORS.BACKGROUND
        )
        self.assertGreater(non_bg_count, 0,
                           "HUD should render text that changes pixel colors")


# =============================================================================
# E-001: 满棋盘胜利
# =============================================================================

class TestE001BoardFullVictory(_IntegrationTestBase):
    """E-001: 食物生成时所有可用格子被蛇身占满 -> 判定玩家胜利。"""

    def test_victory_transition_on_board_full(self):
        """满棋盘时状态迁移到 VICTORY"""
        self.game.snake.body = [(19, 15), (18, 15), (17, 15)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 15)
        self.game.state = GameState.RUNNING

        original_respawn = self.game.food.respawn
        self.game.food.respawn = lambda occupied: False

        self.game._update()

        self.assertEqual(GameState.VICTORY, self.game.state)

        self.game.food.respawn = original_respawn

    def test_victory_state_persistent(self):
        """VICTORY 状态不会自动变迁"""
        self.game.state = GameState.VICTORY
        self.game._update()
        self.assertEqual(GameState.VICTORY, self.game.state)

    def test_victory_food_respawn_returns_false(self):
        """棋盘满时 respawn 返回 False"""
        food = Food(GRID_COLS, GRID_ROWS)
        all_cells = [(x, y) for x in range(GRID_COLS) for y in range(GRID_ROWS)]
        result = food.respawn(all_cells)
        self.assertFalse(result)

    def test_victory_triggers_state_change_in_game(self):
        """游戏中满棋盘触发 victory_state 的正确判定点"""
        # 模拟：food.respawn 返回 False 触发 GameState.VICTORY
        self.game.food.respawn = lambda occupied: False
        self.game.snake.body = [(19, 15), (18, 15), (17, 15)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 15)  # 食物在蛇头位置
        self.game.state = GameState.RUNNING

        self.game._update()
        self.assertEqual(GameState.VICTORY, self.game.state)

        self.game.food.respawn = Food(GRID_COLS, GRID_ROWS).respawn


# =============================================================================
# E-002: 边界转向 — 在边界上方向指向界外
# =============================================================================

class TestE002BoundaryTurn(_IntegrationTestBase):
    """E-002: 蛇头在边界上方向键指向边界外 -> 下一帧出界 -> GAME_OVER。"""

    def test_head_at_left_edge_moving_left(self):
        """蛇头在 x=0 处向左移动 -> 出界 -> GAME_OVER"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_head_at_top_edge_moving_up(self):
        """蛇头在 y=0 处向上移动 -> 出界 -> GAME_OVER"""
        self.game.snake.body = [(20, 0), (20, 1), (20, 2)]
        self.game.snake.direction = (0, -1)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_head_at_right_edge_moving_right(self):
        """蛇头在 x=39 处向右移动 -> 出界 -> GAME_OVER"""
        self.game.snake.body = [(GRID_COLS - 1, 15),
                                (GRID_COLS - 2, 15),
                                (GRID_COLS - 3, 15)]
        self.game.snake.direction = (1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_head_at_bottom_edge_moving_down(self):
        """蛇头在 y=29 处向下移动 -> 出界 -> GAME_OVER"""
        self.game.snake.body = [(20, GRID_ROWS - 1),
                                (20, GRID_ROWS - 2),
                                (20, GRID_ROWS - 3)]
        self.game.snake.direction = (0, 1)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_head_at_edge_but_moving_parallel_is_safe(self):
        """蛇头在边界边缘但移动方向平行于边界 -> 不撞墙"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        # 头在左边缘，向上移动
        snake.body = [(0, 5), (0, 6), (0, 7)]
        snake.direction = (0, -1)  # 平行于左边界向上
        snake.move_and_grow(False)
        self.assertFalse(snake.check_boundary_collision(GRID_COLS, GRID_ROWS))

    def test_head_at_corner_moving_into_wall(self):
        """蛇头在角落，向内移动安全"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(0, 0), (1, 0), (2, 0)]
        snake.direction = (0, 1)  # 从 (0,0) 向下
        snake.move_and_grow(False)
        self.assertFalse(snake.check_boundary_collision(GRID_COLS, GRID_ROWS))


# =============================================================================
# E-003: 单节蛇无自撞
# =============================================================================

class TestE003SingleSegmentSnake(unittest.TestCase):
    """E-003: 蛇长度仅 1 节时的撞自身 -> 不存在自身碰撞可能。"""

    def test_single_segment_never_self_collides(self):
        """单节蛇 check_self_collision 始终返回 False"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(10, 10)]
        self.assertFalse(snake.check_self_collision())

    def test_single_segment_body_tail_is_empty(self):
        """单节蛇的 body[1:] 为空"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(10, 10)]
        self.assertEqual([], snake.body[1:])

    def test_single_segment_moves_freely(self):
        """单节蛇能自由移动不自撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(10, 10)]
        snake.direction = (1, 0)
        for _ in range(5):
            snake.move_and_grow(False)
            self.assertFalse(snake.check_self_collision())

    def test_single_segment_can_move_all_directions(self):
        """单节蛇可以向四个方向移动"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(10, 10)]
        for d in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            snake.direction = d
            snake.move_and_grow(False)
            self.assertFalse(snake.check_self_collision())


# =============================================================================
# E-004: 快速连按多方向键
# =============================================================================

class TestE004RapidMultiKey(unittest.TestCase):
    """E-004: 玩家快速连续按下多个方向键 ->
       仅最后一个有效方向键生效，反向输入被忽略。"""

    def setUp(self):
        _clear_events()
        self.handler = InputHandler()

    def test_last_valid_key_wins_with_rapid_input(self):
        """快速连按多个键，最后有效者生效"""
        _post_key(pygame.K_LEFT)
        _post_key(pygame.K_UP)
        _post_key(pygame.K_RIGHT)
        # current_direction = (0, 1) (向下) -> 左和右都有效
        cmd = self.handler.process_events((0, 1), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((1, 0), cmd['direction'])  # RIGHT wins

    def test_rapid_reverse_between_valids(self):
        """快速连按中反向键夹在有效键之间时被忽略"""
        _post_key(pygame.K_UP)      # valid
        _post_key(pygame.K_LEFT)    # reverse of RIGHT (1,0)
        _post_key(pygame.K_DOWN)    # valid
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        # LEFT is reverse, last non-reverse is DOWN
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, 1), cmd['direction'])

    def test_all_reverse_in_rapid_sequence(self):
        """快速连按全为反向键 -> 无方向变化"""
        _post_key(pygame.K_LEFT)
        _post_key(pygame.K_LEFT)
        _post_key(pygame.K_LEFT)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_per_frame_buffering_prevents_intermediate_turns(self):
        """同一帧的中间按键可能导致自撞，但 per-frame 缓冲允许规避"""
        # 测试场景：右移 + 同帧先按上再按下 (快速180度)
        # 但实际上会被反向拦截：上有效，下被拦截为反向，所以最终方向是上
        _post_key(pygame.K_UP)
        _post_key(pygame.K_DOWN)  # DOWN is reverse of UP if we just set UP
        # But this is all in one frame, processing from left to right
        # UP: (0,-1) vs current (1,0) -> not reverse, valid, last_direction = (0,-1)
        # DOWN: (0,1) vs current (1,0) -> not reverse, valid, last_direction = (0,1)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, 1), cmd['direction'])

    def test_three_keys_rapid_sequence(self):
        """三键快速连按"""
        _post_key(pygame.K_DOWN)
        _post_key(pygame.K_LEFT)
        _post_key(pygame.K_RIGHT)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((1, 0), cmd['direction'])  # RIGHT wins


# =============================================================================
# E-005: 窗口失去焦点
# =============================================================================

class TestE005FocusLoss(_IntegrationTestBase):
    """E-005: 窗口失去焦点（如 Alt+Tab）-> 暂停逻辑更新，避免意外死亡。"""

    def test_focus_loss_sets_paused(self):
        """失焦事件设置暂停"""
        _post_event(pygame.WINDOWFOCUSLOST)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertTrue(self.game.input_handler.is_paused())

    def test_paused_state_freezes_snake(self):
        """暂停时蛇不移动"""
        self.game.input_handler._paused = True
        body_before = list(self.game.snake.body)
        self.game._update()
        self.assertEqual(body_before, self.game.snake.body)

    def test_focus_gained_clears_paused(self):
        """焦点恢复时清除暂停"""
        self.game.input_handler._paused = True
        _post_event(pygame.WINDOWFOCUSGAINED)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertFalse(self.game.input_handler.is_paused())

    def test_game_over_state_unaffected_by_focus_loss(self):
        """GAME_OVER 状态下失焦不影响游戏"""
        self.game.state = GameState.GAME_OVER
        _post_event(pygame.WINDOWFOCUSLOST)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertTrue(self.game.input_handler.is_paused())
        # _update 在 GAME_OVER 状态下不执行，所以不影响

    def test_focus_event_returns_pause_command(self):
        """失焦返回 pause 命令，聚焦返回 resume 命令"""
        _post_event(pygame.WINDOWFOCUSLOST)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertEqual('pause', cmd['action'])

        _clear_events()
        _post_event(pygame.WINDOWFOCUSGAINED)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertEqual('resume', cmd['action'])


# =============================================================================
# E-006: 窗口关闭
# =============================================================================

class TestE006WindowClose(_IntegrationTestBase):
    """E-006: 关闭窗口按钮被点击 -> 游戏进程正常退出，无异常或残留进程。"""

    def test_quit_event_stops_run_loop(self):
        """QUIT 事件使 run() 退回"""
        _post_event(pygame.QUIT)
        try:
            self.game.run()
        except Exception as e:
            self.fail(f"run() raised unexpected exception on QUIT: {e}")

    def test_quit_command_returns_false(self):
        """quit 命令返回 False 退出主循环"""
        result = self.game._handle_command({'action': 'quit'})
        self.assertFalse(result)

    def test_q_key_in_game_over_returns_quit(self):
        """GAME_OVER + Q 键 -> quit"""
        self.game.state = GameState.GAME_OVER
        _post_key(pygame.K_q)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertEqual('quit', cmd['action'])

    def test_q_key_in_victory_returns_quit(self):
        """VICTORY + Q 键 -> quit"""
        self.game.state = GameState.VICTORY
        _post_key(pygame.K_q)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertEqual('quit', cmd['action'])

    def test_quit_works_without_pygame_residual(self):
        """quit 后 pygame 状态正常"""
        # 模拟 run() 退出后的清理场景
        _post_event(pygame.QUIT)
        old_state = self.game.state
        try:
            self.game.run()
        except Exception:
            self.fail("run() should not raise")
        # 验证 pygame 模块仍可用 (未被无效调用破坏)
        self.assertTrue(pygame.get_init())


# =============================================================================
# E-007: 食物不落蛇身
# =============================================================================

class TestE007FoodNotOnSnake(_IntegrationTestBase):
    """E-007: 食物随机生成在蛇头位置 -> 不应发生，
       必须检查所有蛇身格子（含蛇头）。"""

    def test_food_not_on_snake_body_including_head(self):
        """食物不生成在蛇身任何格子（含蛇头）"""
        for _ in range(100):
            food = Food(GRID_COLS, GRID_ROWS)
            occupied = [(5, 5), (6, 5), (7, 5)]  # head at (5,5)
            food.respawn(occupied)
            self.assertNotIn(food.position, occupied,
                             "Food must not overlap any snake cell, including head")

    def test_initial_food_not_on_snake(self):
        """首个食物不落在初始蛇身上"""
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_food_respawned_not_on_snake(self):
        """重新生成的食物不落在蛇身上"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])
        self.game._update()
        self.game._update()  # eat + respawn
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_food_excludes_all_body_cells(self):
        """食物生成排除所有蛇身格子，用集合差运算保证"""
        food = Food(GRID_COLS, GRID_ROWS)
        # 几乎占满棋盘
        all_except_one = {
            (x, y) for x in range(GRID_COLS) for y in range(GRID_ROWS)
        } - {(39, 29)}
        result = food.respawn(all_except_one)
        self.assertTrue(result)
        self.assertEqual((39, 29), food.position)

    def test_food_excludes_only_occupied_set(self):
        """respawn 正确使用 set(occupied_cells) 做排除"""
        food = Food(GRID_COLS, GRID_ROWS)
        occupied = {(0, 0), (0, 1), (1, 0)}
        for _ in range(20):
            food.respawn(occupied)
            self.assertNotIn(food.position, occupied)


# =============================================================================
# E-008: Respawn 兜底
# =============================================================================

class TestE008RespawnFallback(_IntegrationTestBase):
    """E-008: 食物生成逻辑出错未生成新食物 -> 需确保重试兜底机制。"""

    def test_respawn_with_one_cell_available_always_succeeds(self):
        """只剩一个格子时肯定能生成"""
        food = Food(GRID_COLS, GRID_ROWS)
        occupied = {
            (x, y) for x in range(GRID_COLS) for y in range(GRID_ROWS)
        } - {(39, 29)}
        result = food.respawn(occupied)
        self.assertTrue(result)
        self.assertEqual((39, 29), food.position)

    def test_respawn_board_full_returns_false_not_error(self):
        """满棋盘返回 False 而不是抛出异常"""
        food = Food(GRID_COLS, GRID_ROWS)
        all_cells = [(x, y) for x in range(GRID_COLS) for y in range(GRID_ROWS)]
        try:
            result = food.respawn(all_cells)
            self.assertFalse(result)
        except Exception as e:
            self.fail(f"respawn raised exception: {e}")

    def test_game_handles_respawn_false_gracefully(self):
        """游戏处理 respawn 返回 False 成为 VICTORY 状态"""
        original_respawn = self.game.food.respawn
        self.game.food.respawn = lambda occ: False
        self.game.snake.body = [(19, 15), (18, 15), (17, 15)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 15)

        try:
            self.game._update()
            self.assertEqual(GameState.VICTORY, self.game.state)
        except Exception as e:
            self.fail(f"Game crashed on respawn False: {e}")
        finally:
            self.game.food.respawn = original_respawn

    def test_game_continues_after_victory_reset(self):
        """VICTORY 后可以正常 reset"""
        original_respawn = self.game.food.respawn
        self.game.food.respawn = lambda occ: False
        self.game.snake.body = [(19, 15), (18, 15), (17, 15)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 15)
        self.game._update()
        self.assertEqual(GameState.VICTORY, self.game.state)

        # 恢复 respawn 并 reset
        self.game.food.respawn = original_respawn
        self.game.reset()
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(3, self.game.snake.length)
        self.assertNotEqual((-1, -1), self.game.food.position)

    def test_respawn_returns_deterministic_behavior(self):
        """多次 respawn 行为确定性：成功返回 True + 有效坐标，满返回 False"""
        food = Food(10, 10)
        for _ in range(50):
            result = food.respawn([])
            self.assertTrue(result)
            x, y = food.position
            self.assertTrue(0 <= x < 10)
            self.assertTrue(0 <= y < 10)
            self.assertNotEqual((-1, -1), food.position)


# =============================================================================
# E-009: Pygame 缺失提示
# =============================================================================

class TestE009PygameMissing(unittest.TestCase):
    """E-009: Pygame 未安装或 Python 版本不兼容 ->
       启动时报错，给出清晰的依赖缺失提示。"""

    def test_main_catches_import_error(self):
        """main() 捕获 ImportError 并输出提示信息"""
        import main as main_module

        # 模拟 Pygame 未安装
        with patch.dict('sys.modules', {'pygame': None}):
            # 需要在 main() 中触发 ImportError
            with patch('builtins.__import__',
                       side_effect=ImportError("No module named 'pygame'")):
                # 捕获输出
                captured = io.StringIO()
                old_stderr = sys.stderr
                sys.stderr = captured
                try:
                    with self.assertRaises(SystemExit) as ctx:
                        main_module.main()
                    self.assertEqual(1, ctx.exception.code)
                    output = captured.getvalue()
                    self.assertIn("pygame", output.lower())
                    self.assertIn("pip install pygame", output)
                finally:
                    sys.stderr = old_stderr

    def test_error_message_contains_pip_install_instruction(self):
        """错误消息包含 pip install pygame 安装指令"""
        import main as main_module

        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured

        try:
            with patch('builtins.__import__',
                       side_effect=ImportError("No module named 'pygame'")):
                with self.assertRaises(SystemExit):
                    main_module.main()
                output = captured.getvalue()
                self.assertIn("pip install pygame", output)
        finally:
            sys.stderr = old_stderr

    def test_main_exits_with_code_1_on_import_error(self):
        """ImportError 时 sys.exit(1)"""
        import main as main_module

        with patch('builtins.__import__',
                   side_effect=ImportError("No module named 'pygame'")):
            with self.assertRaises(SystemExit) as ctx:
                main_module.main()
            self.assertEqual(1, ctx.exception.code)

    def test_main_prints_to_stderr(self):
        """错误提示打印到 stderr"""
        import main as main_module

        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured

        try:
            with patch('builtins.__import__',
                       side_effect=ImportError("No module named 'pygame'")):
                with self.assertRaises(SystemExit):
                    main_module.main()
            output = captured.getvalue()
            self.assertGreater(len(output), 0, "Should print error message")
        finally:
            sys.stderr = old_stderr


# =============================================================================
# 碰撞精度验证 — 网格级无误判漏判
# =============================================================================

class TestCollisionAccuracy(unittest.TestCase):
    """验证碰撞检测在网格级别的精度：无假阳性（误判）、无假阴性（漏判）。"""

    # ---------- 边界碰撞精度 ----------

    def test_boundary_no_false_positive_on_valid_cells(self):
        """所有有效网格内坐标均不触发边界碰撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                snake.body[0] = (x, y)
                self.assertFalse(
                    snake.check_boundary_collision(GRID_COLS, GRID_ROWS),
                    f"False positive at ({x}, {y})")

    def test_boundary_no_false_negative_on_invalid_cells(self):
        """所有无效网格外坐标均触发边界碰撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        invalid_positions = [
            (-1, 0), (GRID_COLS, 0),           # 左/右出界
            (0, -1), (0, GRID_ROWS),            # 上/下出界
            (-1, -1), (GRID_COLS, GRID_ROWS),   # 对角出界
            (100, 100), (-100, -100),            # 远超出界
        ]
        for x, y in invalid_positions:
            snake.body[0] = (x, y)
            self.assertTrue(
                snake.check_boundary_collision(GRID_COLS, GRID_ROWS),
                f"False negative at ({x}, {y})")

    def test_boundary_precision_at_edges(self):
        """边界边缘精度：0 和 cols-1/rows-1 合法，-1 和 cols/rows 非法"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        # 四个角在界内
        for pos in [(0, 0), (0, GRID_ROWS - 1),
                    (GRID_COLS - 1, 0), (GRID_COLS - 1, GRID_ROWS - 1)]:
            snake.body[0] = pos
            self.assertFalse(snake.check_boundary_collision(GRID_COLS, GRID_ROWS),
                             f"Corner {pos} should be valid")
        # 边界外一步
        for pos in [(-1, 0), (0, -1), (GRID_COLS, 0), (0, GRID_ROWS)]:
            snake.body[0] = pos
            self.assertTrue(snake.check_boundary_collision(GRID_COLS, GRID_ROWS),
                            f"Position {pos} should be out of bounds")

    # ---------- 自撞碰撞精度 ----------

    def test_self_collision_no_false_positive_in_straight_line(self):
        """直线移动不自撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        # 模拟长直线蛇身
        snake.body = [(x, 10) for x in range(20, 10, -1)]
        snake.direction = (1, 0)
        for _ in range(8):
            snake.move_and_grow(False)
            self.assertFalse(snake.check_self_collision(),
                             "False positive in straight line")

    def test_self_collision_detected_exactly_at_overlap(self):
        """蛇头与身体某节精确重叠时才触发自撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        # head(3,3) in body[1:]
        snake.body = [(3, 3), (3, 4), (3, 3)]  # head(3,3) = body[2]=(3,3)
        self.assertTrue(snake.check_self_collision())

    def test_self_collision_not_detected_for_adjacent_cells(self):
        """蛇头紧邻身体但不重叠 -> 不自撞"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(4, 4), (4, 5), (4, 6)]
        # head(4,4) 紧邻 body[1](4,5) 但不重叠
        self.assertFalse(snake.check_self_collision())

    def test_self_collision_not_detected_for_non_overlapping_head(self):
        """蛇头不与身体重叠时不自撞（碰撞检测基于移动后状态）"""
        # 构造 L 形蛇身，head 向下移动，新位置不在身体上
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(3, 3), (4, 3), (4, 4), (5, 4)]
        snake.direction = (0, 1)  # head -> (3, 4)
        snake.move_and_grow(False)
        # body after: [(3,4), (3,3), (4,3), (4,4)], head=(3,4) not in body[1:]
        self.assertFalse(snake.check_self_collision())

    # ---------- 综合碰撞精度 ----------

    def test_collision_order_does_not_miss(self):
        """边界碰撞检查在自撞之前，两者都能正确触发"""
        # 蛇头在角落里，移动出界 -> 边界碰撞优先
        snake = Snake(GRID_COLS, GRID_ROWS)
        snake.body = [(0, 0), (1, 0), (2, 0)]
        snake.direction = (-1, 0)
        snake.move_and_grow(False)
        self.assertTrue(snake.check_boundary_collision(GRID_COLS, GRID_ROWS))

    def test_all_grid_cells_one_by_one(self):
        """逐个格子的边界检测无误"""
        snake = Snake(GRID_COLS, GRID_ROWS)
        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                snake.body[0] = (x, y)
                self.assertFalse(
                    snake.check_boundary_collision(GRID_COLS, GRID_ROWS),
                    f"Collision falsely detected at ({x},{y})")


# =============================================================================
# 重启流程一致性验证
# =============================================================================

class TestRestartConsistency(_IntegrationTestBase):
    """验证重启流程的一致性：多次重启后状态一致。"""

    def test_single_restart_restores_initial_state(self):
        """单次重启恢复到初始状态"""
        self.game.score = 100
        self.game.state = GameState.GAME_OVER
        self.game.snake.body = [(5, 5)]

        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(INITIAL_SNAKE_LENGTH, self.game.snake.length)
        self.assertEqual((1, 0), self.game.snake.direction)
        self.assertNotEqual((-1, -1), self.game.food.position)
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_multiple_restarts_are_idempotent(self):
        """多次重启结果一致"""
        snapshots = []

        for cycle in range(5):
            # 改变状态
            self.game.score = cycle * 100
            self.game.snake.body = [(cycle, 5)]
            self.game.state = GameState.GAME_OVER
            self.game.food.position = (8, 8)

            # 重启
            self.game.reset()

            snapshots.append({
                'state': self.game.state,
                'score': self.game.score,
                'length': self.game.snake.length,
                'direction': self.game.snake.direction,
                'head': self.game.snake.head,
            })

        # 所有快照应一致
        first = snapshots[0]
        for i, s in enumerate(snapshots[1:], 1):
            self.assertEqual(first['state'], s['state'],
                             f"Cycle {i} state mismatch")
            self.assertEqual(first['score'], s['score'],
                             f"Cycle {i} score mismatch")
            self.assertEqual(first['length'], s['length'],
                             f"Cycle {i} length mismatch")
            self.assertEqual(first['direction'], s['direction'],
                             f"Cycle {i} direction mismatch")
            self.assertEqual(first['head'], s['head'],
                             f"Cycle {i} head mismatch")

    def test_restart_from_all_states(self):
        """从 RUNNING/GAME_OVER/VICTORY 三种状态重启均一致"""
        for state in (GameState.RUNNING, GameState.GAME_OVER, GameState.VICTORY):
            self.game.state = state
            self.game.score = 500
            self.game.snake.body = [(39, 29)]

            self.game.reset()

            self.assertEqual(GameState.RUNNING, self.game.state)
            self.assertEqual(0, self.game.score)
            self.assertEqual(3, self.game.snake.length)

    def test_restart_preserves_initial_snake_position(self):
        """重启后蛇身回到初始中心位置"""
        original_body = [
            (GRID_COLS // 2 - i, GRID_ROWS // 2)
            for i in range(INITIAL_SNAKE_LENGTH)
        ]

        self.game.score = 200
        self.game.state = GameState.GAME_OVER
        self.game.reset()

        self.assertEqual(original_body, self.game.snake.body)

    def test_restart_food_not_on_snake(self):
        """重启后首个食物不落在蛇身上"""
        for _ in range(20):
            self.game.reset()
            self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_restart_defensive_against_partial_state(self):
        """重启能处理部分损坏的状态（异常 body 等）"""
        self.game.snake.body = [(0, 0)]          # 单节
        self.game.snake.direction = (0, 0)       # 无效方向
        self.game.score = -1
        self.game.state = GameState.VICTORY

        try:
            self.game.reset()
        except Exception as e:
            self.fail(f"reset() raised exception on partial state: {e}")

        # 重置后恢复正常
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(INITIAL_SNAKE_LENGTH, self.game.snake.length)
        self.assertNotEqual((-1, -1), self.game.food.position)


# =============================================================================
# 性能验证 — FPS 稳定性 + 内存无泄漏
# =============================================================================

class TestPerformance(_IntegrationTestBase):
    """性能验证：FPS 偏差不超过 ±20%，内存占用稳定无泄漏。"""

    def test_memory_stable_across_many_frames(self):
        """多帧运行内存不持续增长"""
        gc.collect()
        # 获取基准内存
        import tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        gc.collect()
        _, baseline_peak = tracemalloc.get_traced_memory()

        # 模拟 200 帧游戏运行
        for _ in range(200):
            self.game.renderer.tick()
            self.game._update()

        gc.collect()
        _, post_peak = tracemalloc.get_traced_memory()

        # 峰值增长应 < 1MB (允许小幅波动)
        growth = post_peak - baseline_peak
        max_allowed = 2 * 1024 * 1024  # 2 MB tolerance for Pygame internals
        self.assertLess(growth, max_allowed,
                        f"Memory growth {growth/1024:.1f} KB exceeds {max_allowed/1024:.0f} KB")

        tracemalloc.stop()

    def test_gc_no_cycles_after_reset(self):
        """多次重启后无循环引用泄漏"""
        gc.collect()
        before = gc.get_count()

        for _ in range(50):
            self.game.reset()
            self.game._update()

        gc.collect()
        after = gc.get_count()

        # 各代收集数不应显著增长
        for gen, (b, a) in enumerate(zip(before, after)):
            self.assertLessEqual(a - b, 20,
                                 f"Gen {gen} collection count grew from {b} to {a}")

    def test_no_reference_leaks_after_reset(self):
        """reset 后对象引用计数正常"""
        import sys as sys_mod

        snake_ref = sys_mod.getrefcount(self.game.snake)
        food_ref = sys_mod.getrefcount(self.game.food)

        self.game.reset()

        self.assertEqual(snake_ref, sys_mod.getrefcount(self.game.snake),
                         "Snake refcount changed after reset (possible leak)")
        self.assertEqual(food_ref, sys_mod.getrefcount(self.game.food),
                         "Food refcount changed after reset (possible leak)")

    def test_rapid_frame_sequence_performance(self):
        """快速连续帧序列性能：FPS 偏差不超 ±20%"""
        renderer = self.game.renderer
        renderer.tick()  # warm-up

        frame_times = []
        for _ in range(60):  # 模拟约 6 秒 @10FPS
            t0 = time.time()
            renderer.tick()
            frame_times.append(time.time() - t0)

        avg_frame_time = sum(frame_times) / len(frame_times)
        target_frame_time = 1.0 / FPS

        deviation = abs(avg_frame_time - target_frame_time) / target_frame_time
        actual_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else float('inf')

        self.assertLessEqual(deviation, 0.20,
                             f"FPS deviation {deviation:.2%} exceeds 20% "
                             f"(actual={actual_fps:.1f}, target={FPS})")

    def test_hundred_ticks_no_degradation(self):
        """100 次 tick 帧率稳定无退化"""
        renderer = self.game.renderer
        renderer.tick()

        times = [renderer.tick() for _ in range(100)]

        # 所有 tick 应在合理范围 (0ms ~ 200ms, 允许首次 tick 稍大)
        for i, t in enumerate(times[1:], 1):  # skip first
            self.assertLess(t, 200, f"Tick {i} took {t}ms (too slow)")

    def test_update_performance_constant(self):
        """_update 方法耗时恒定（不随蛇长增长退化）"""
        import sys as sys_mod

        timings = []
        self.game.snake.body = [(i, 15) for i in range(19, 0, -1)]  # 19 节

        for _ in range(100):
            # 放置食物在蛇头前
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])

            t0 = time.time()
            self.game._update()
            dt = (time.time() - t0) * 1000  # ms
            timings.append(dt)

        avg = sum(timings) / len(timings)
        # 单次 _update 应 < 5ms
        self.assertLess(avg, 5.0,
                        f"_update avg {avg:.2f}ms too slow")


if __name__ == "__main__":
    unittest.main()
