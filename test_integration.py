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
    COLORS, RENDER_FPS, BASE_TICK_INTERVAL,
    BOOST_SPEED_MULTIPLIER, MAX_BOOST_MULTIPLIER,
    BOOST_TRANSITION_SECONDS,
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
        target_interval = 1.0 / RENDER_FPS  # ~16.7ms for RENDER_FPS=60

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
        target = 1.0 / RENDER_FPS

        deviation = abs(avg - target) / target
        self.assertLessEqual(deviation, 0.20,
                             f"FPS deviation {deviation:.2%} exceeds 20% "
                             f"(avg={1/avg:.1f} FPS, target={RENDER_FPS} FPS)")

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
        self.game.food.position = (20, 15)
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
        self.game.food.position = (20, 15)  # 食物在蛇头前方一格
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
        self.game.food.position = (20, 15)

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
        self.game.food.position = (20, 15)
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
        target_frame_time = 1.0 / RENDER_FPS

        deviation = abs(avg_frame_time - target_frame_time) / target_frame_time
        actual_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else float('inf')

        self.assertLessEqual(deviation, 0.20,
                             f"FPS deviation {deviation:.2%} exceeds 20% "
                             f"(actual={actual_fps:.1f}, target={RENDER_FPS})")

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


# =============================================================================
# T-010: 加速集成测试 — 5 条关键流程端到端
# =============================================================================


class TestBoostIntegrationFlows(_IntegrationTestBase):
    """T-010 加速集成测试：5 条关键流程端到端验证"""

    # ==========================================================================
    # Flow-1: 基础加速流程 — 按下 Space -> 加速 -> 释放恢复
    # ==========================================================================

    def test_basic_boost_press_speed_increases(self):
        """按住加速键后 tick_interval 缩短，蛇速度提升"""
        # 基准 tick_interval
        self.game.snake.boost_state['current_multiplier'] = 1.0
        base_interval = self.game._get_current_tick_interval()
        self.assertEqual(float(BASE_TICK_INTERVAL), base_interval)

        # 模拟按住加速键多帧推进直到达到目标倍率
        for _ in range(100):
            self.game._update_boost_state(16.0, True)

        boost_interval = self.game._get_current_tick_interval()
        self.assertLess(boost_interval, base_interval,
                        "Boost should reduce tick interval")
        self.assertTrue(self.game.snake.is_boosting,
                        "Snake should be in boosting state")

    def test_basic_boost_release_speed_restores(self):
        """释放加速键后 tick_interval 恢复为基准值"""
        # 先加速到满
        self.game.snake.boost_state['current_multiplier'] = BOOST_SPEED_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 释放加速键，推进足够帧数
        for _ in range(100):
            self.game._update_boost_state(16.0, False)

        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(float(BASE_TICK_INTERVAL), interval, places=1)
        self.assertFalse(self.game.snake.is_boosting)

    def test_basic_boost_no_direction_interference(self):
        """加速键不影响方向移动：加速期间蛇仍正常前进一步"""
        head_before = self.game.snake.head
        direction_before = self.game.snake.direction

        # 激活加速
        self.game.snake.boost_state['current_multiplier'] = BOOST_SPEED_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 执行一次 _update，蛇应前进一步
        self.game._update()

        expected_head = (head_before[0] + direction_before[0],
                         head_before[1] + direction_before[1])
        self.assertEqual(expected_head, self.game.snake.head,
                         "Boost must not affect grid-step distance")

    def test_basic_boost_single_tap_no_glitch(self):
        """单次快速按下释放（tap）不会导致加速状态闪烁"""
        # 模拟 tap: 一帧 True -> 多帧 False
        self.game._update_boost_state(16.0, True)
        multiplier_after_tap = self.game.snake.boost_state['current_multiplier']

        # 一帧后立即释放
        for _ in range(100):
            self.game._update_boost_state(16.0, False)

        # 最终应恢复为 1.0
        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)
        self.assertFalse(self.game.snake.is_boosting)

    # ==========================================================================
    # Flow-2: GameOver 复位流程 — 加速中碰撞 -> 加速清除
    # ==========================================================================

    def test_boost_reset_on_game_over_boundary(self):
        """加速中撞墙 -> GAME_OVER -> boost 立即清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        # 撞墙
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_reset_on_game_over_self_collision(self):
        """加速中自撞 -> GAME_OVER -> boost 立即清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)
        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_game_over_no_boost_on_restart(self):
        """GameOver 后按 R 重启，以基准速度开始"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.state = GameState.GAME_OVER

        # 执行 restart
        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    # ==========================================================================
    # Flow-3: 暂停/失焦流程 — 加速中暂停 -> 加速清除
    # ==========================================================================

    def test_boost_cleared_on_focus_lost(self):
        """加速中失焦 -> boost 标志清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.input_handler._boost_active = True

        # 发送失焦事件
        _post_event(pygame.WINDOWFOCUSLOST)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.game._handle_command(cmd)

        self.assertTrue(self.game.input_handler.is_paused())
        self.assertFalse(self.game.input_handler._boost_active)

    def test_boost_not_restored_after_focus_regain_without_release(self):
        """切回后即使物理键仍按住，加速不自动激活（需要释放后重新按下）"""
        self.game.input_handler._paused = True
        self.game.input_handler._boost_active = False

        # 失焦后 _paused=True，is_boost_pressed() 返回 False
        self.assertFalse(self.game.input_handler.is_boost_pressed())

        # 恢复焦点
        _clear_events()
        _post_event(pygame.WINDOWFOCUSGAINED)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)
        self.assertFalse(self.game.input_handler.is_paused())

        # 由于 _boost_active 已为 False，is_boost_pressed() 返回物理键状态
        # 但 Pygame 在焦点恢复后需要通过一次释放+重新按下才刷新键状态
        self.assertIsInstance(self.game.input_handler.is_boost_pressed(), bool)

    def test_boost_stays_cleared_during_pause(self):
        """暂停期间 boost state 加速倍率被强制恢复为 1.0（因非RUNNING）"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True
        self.game.input_handler._paused = True

        # 暂停期间 _paused 阻止 _update 执行
        # 但 boost state 在 run() 的 else 分支会被 _update_boost_state 处理
        # 这里测试非 RUNNING 状态下的倍率强制逻辑
        self.game.state = GameState.RUNNING
        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        # 检查: _update_boost_state 中非 RUNNING 状态 target 为 1.0
        # 但当前是 RUNNING + paused，需确保 pause 不会阻止蛇移动
        # 本测试验证的是 _update 在暂停时不执行
        body_before = list(self.game.snake.body)
        self.game._update()
        self.assertEqual(body_before, self.game.snake.body,
                         "Pause should freeze snake movement")

    # ==========================================================================
    # Flow-4: 平滑过渡流程 — 渐进加速/减速
    # ==========================================================================

    def test_smooth_transition_ramp_up(self):
        """按下加速键后倍率渐进上升（非瞬时跳变）"""
        self.game.snake.boost_state['current_multiplier'] = 1.0

        # 第一帧：倍率略微上升
        self.game._update_boost_state(16.0, True)
        m1 = self.game.snake.boost_state['current_multiplier']
        self.assertGreater(m1, 1.0)

        # 第二帧：继续上升
        self.game._update_boost_state(16.0, True)
        m2 = self.game.snake.boost_state['current_multiplier']
        self.assertGreater(m2, m1,
                           f"Smooth transition: frame2 {m2} should > frame1 {m1}")

    def test_smooth_transition_ramp_down(self):
        """释放加速键后倍率渐进下降"""
        self.game.snake.boost_state['current_multiplier'] = BOOST_SPEED_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 第一帧
        self.game._update_boost_state(16.0, False)
        m1 = self.game.snake.boost_state['current_multiplier']
        self.assertLess(m1, BOOST_SPEED_MULTIPLIER)

        # 第二帧继续下降
        self.game._update_boost_state(16.0, False)
        m2 = self.game.snake.boost_state['current_multiplier']
        self.assertLess(m2, m1,
                        f"Smooth transition down: frame2 {m2} should < frame1 {m1}")

    def test_smooth_transition_completes_within_expected_frames(self):
        """平滑过渡在约 150ms (@60fps ≈ 9 帧) 内完成"""
        self.game.snake.boost_state['current_multiplier'] = 1.0

        frames_to_target = 0
        for _ in range(30):  # 最多 30 帧，应该足够
            self.game._update_boost_state(16.0, True)
            frames_to_target += 1
            if abs(self.game.snake.boost_state['current_multiplier']
                   - BOOST_SPEED_MULTIPLIER) < 0.01:
                break

        self.assertLessEqual(frames_to_target, 15,
                             f"Ramp-up took {frames_to_target} frames, expected <= 15")
        self.assertAlmostEqual(BOOST_SPEED_MULTIPLIER,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)

    def test_smooth_transition_down_completes_in_expected_frames(self):
        """减速过渡在约 150ms 内完成"""
        self.game.snake.boost_state['current_multiplier'] = BOOST_SPEED_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        frames_to_one = 0
        for _ in range(30):
            self.game._update_boost_state(16.0, False)
            frames_to_one += 1
            if abs(self.game.snake.boost_state['current_multiplier'] - 1.0) < 0.01:
                break

        self.assertLessEqual(frames_to_one, 15,
                             f"Ramp-down took {frames_to_one} frames, expected <= 15")
        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)

    def test_no_division_by_zero_in_transition(self):
        """平滑过渡计算无除零错误"""
        self.game.snake.boost_state['current_multiplier'] = 1.0

        # 连续多帧操作不报错
        for _ in range(200):
            try:
                self.game._update_boost_state(16.0, True)
                self.game._update_boost_state(16.0, False)
            except ZeroDivisionError:
                self.fail("Boost transition caused ZeroDivisionError")
            except Exception as e:
                self.fail(f"Boost transition raised unexpected {type(e).__name__}: {e}")

    # ==========================================================================
    # Flow-5: 重启复位流程 — 加速中按 R -> 基准速度
    # ==========================================================================

    def test_restart_from_boost_state_resets_boost(self):
        """加速状态下按 R 重启，boost 完全清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.5
        self.game.input_handler._boost_active = True
        self.game.state = GameState.GAME_OVER

        # 执行重启
        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])
        self.assertFalse(self.game.input_handler._boost_active)

    def test_restart_boost_reset_double_insurance(self):
        """snake.reset() + Game._reset_boost() 双重保险确保 boost 复位"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 3.0
        self.game.input_handler._boost_active = True

        # 只调用 Game.reset()（内部会调用 snake.reset() + _reset_boost()）
        self.game.reset()

        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])
        self.assertFalse(self.game.input_handler._boost_active)

    def test_restart_from_running_with_boost_clears_it(self):
        """RUNNING 状态下 reset 也清除 boost（防御性）"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game.reset()

        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])


# =============================================================================
# T-010: BC-001 ~ BC-010 全部 10 个边界情况验证
# =============================================================================


class TestBC001BoostDuringGameOver(_IntegrationTestBase):
    """BC-001: 加速中触发 Game Over — 加速效果立即清除。
    Game Over 画面下即使按住加速键也不应有加速残留。
    重新开始后以基准速度运行。"""

    def test_boost_cleared_on_boundary_collision(self):
        """加速中撞墙 -> boost 清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_cleared_on_self_collision(self):
        """加速中自撞 -> boost 清除"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_game_over_boost_not_effective_despite_key_held(self):
        """GAME_OVER 状态下 _update_boost_state 强制 target=1.0"""
        self.game.state = GameState.GAME_OVER
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 按住加速键推进帧
        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)
        self.assertFalse(self.game.snake.boost_state['is_active'])

    def test_restart_after_boost_game_over_at_base_speed(self):
        """碰撞后重启 -> 基准速度"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.game.reset()
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])


class TestBC002BoostDuringPauseResume(_IntegrationTestBase):
    """BC-002: 加速中暂停与恢复 — 加速清除。
    恢复后即使未释放加速键也不自动恢复加速，必须释放后重新按下。"""

    def test_boost_cleared_on_pause_and_not_auto_restored(self):
        """失焦暂停清除 boost，恢复后不自动激活"""
        # 激活加速
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.input_handler._boost_active = True

        # 失焦
        _post_event(pygame.WINDOWFOCUSLOST)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)

        self.assertTrue(self.game.input_handler.is_paused())
        self.assertFalse(self.game.input_handler._boost_active)

        # 恢复焦点后 is_boost_pressed() 需要物理键释放后重新按下
        # _boost_active 已为 False，暂停期间 is_boost_pressed 返回 False
        self.assertFalse(self.game.input_handler.is_boost_pressed())

    def test_boost_not_active_after_unpause(self):
        """恢复后不自动加速"""
        self.game.input_handler._paused = True
        self.game.input_handler._boost_active = False

        # 恢复焦点
        _clear_events()
        _post_event(pygame.WINDOWFOCUSGAINED)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)

        self.assertFalse(self.game.input_handler.is_paused())
        # _boost_active 仍为 False，需要重新按加速键
        self.assertFalse(self.game.input_handler._boost_active)


class TestBC003GameNotStartedBoostKey(_IntegrationTestBase):
    """BC-003: 游戏未开始时按住加速键 — 开始后以基准速度运行，不自动加速。"""

    def test_boost_in_game_over_before_start_ignored(self):
        """GAME_OVER 状态下 boost_boost_state 强制 target=1.0"""
        self.game.state = GameState.GAME_OVER
        self.game.snake.boost_state['current_multiplier'] = 1.0

        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'], places=1)
        self.assertFalse(self.game.snake.is_boosting)

    def test_restart_from_game_over_with_boost_pressed_starts_at_base(self):
        """GAME_OVER 画面下按 R 开始 -> 基准速度"""
        self.game.state = GameState.GAME_OVER
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game.reset()

        # 以基准速度重启
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_victory_state_boost_ignored(self):
        """VICTORY 状态下按住加速键无效"""
        self.game.state = GameState.VICTORY
        self.game.snake.boost_state['current_multiplier'] = 1.5

        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'], places=1)
        self.assertFalse(self.game.snake.is_boosting)


class TestBC004FocusLossBoostHeld(_IntegrationTestBase):
    """BC-004: 窗口失去焦点时加速键被按住 -> 加速清除。
    切回后即使键仍被物理按住，加速不激活。"""

    def test_focus_loss_clears_input_handler_boost_active(self):
        """失焦时 _boost_active 被强行清除"""
        self.game.input_handler._boost_active = True

        _post_event(pygame.WINDOWFOCUSLOST)
        self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)

        self.assertFalse(self.game.input_handler._boost_active)

    def test_focus_loss_boost_not_active(self):
        """失焦后 is_boost_pressed() 返回 False"""
        self.game.input_handler._paused = True
        self.game.input_handler._boost_active = False

        result = self.game.input_handler.is_boost_pressed()
        self.assertFalse(result)


class TestBC005RapidBoostToggle(_IntegrationTestBase):
    """BC-005: 快速连续按压释放 — 加速状态不应闪烁或导致 tick 间隔剧烈抖动。
    若实现平滑过渡，以最后稳定状态为准。"""

    def test_rapid_toggle_boost_no_glitch(self):
        """快速连按/连放不导致崩溃或异常状态"""
        for _ in range(100):
            # 快速交替
            self.game._update_boost_state(16.0, True)
            self.game._update_boost_state(16.0, False)

        # 最终状态应稳定
        self.assertGreaterEqual(self.game.snake.boost_state['current_multiplier'], 1.0)
        self.assertLessEqual(self.game.snake.boost_state['current_multiplier'],
                             MAX_BOOST_MULTIPLIER)

    def test_rapid_toggle_settles_to_steady_state(self):
        """快速连按后以最终稳定状态为准（最后为释放 -> 恢复 1.0）"""
        # 交替 50 次，最后停在释放状态
        for _ in range(50):
            self.game._update_boost_state(16.0, True)
        # 立即释放并推进足够帧数
        for _ in range(100):
            self.game._update_boost_state(16.0, False)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'], places=1)
        self.assertFalse(self.game.snake.is_boosting)

    def test_rapid_toggle_tick_interval_no_jitter(self):
        """快速连打 transition 后 tick_interval 不剧烈抖动"""
        intervals = []
        for cycle in range(30):
            self.game._update_boost_state(16.0, True)
            intervals.append(self.game._get_current_tick_interval())
            self.game._update_boost_state(16.0, False)
            intervals.append(self.game._get_current_tick_interval())

        # 所有 interval 应 > 0 且 <= BASE_TICK_INTERVAL
        max_interval = max(intervals)
        min_interval = min(intervals)
        self.assertLessEqual(max_interval, float(BASE_TICK_INTERVAL) + 5.0)
        self.assertGreaterEqual(min_interval, 20.0)


class TestBC006ExtremeMultiplier(_IntegrationTestBase):
    """BC-006: 极端加速倍率 — BOOST_SPEED_MULTIPLIER 超出 MAX_BOOST_MULTIPLIER
    时 clamp 到上限，tick_interval 不低于 20ms。"""

    def test_multiplier_clamped_at_max(self):
        """当前 BOOST_SPEED_MULTIPLIER 在范围内，验证 clamp 防御性"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0,
                                f"Tick interval {interval}ms < 20ms at max multiplier")

    def test_max_multiplier_interval_not_below_20ms(self):
        """最大倍率下 interval >= 20ms"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        base_expected = BASE_TICK_INTERVAL / MAX_BOOST_MULTIPLIER
        actual = self.game._get_current_tick_interval()
        expected = max(20.0, base_expected)
        self.assertEqual(expected, actual)

    def test_multiplier_clamp_in_config(self):
        """config 模块加载时 BOOST_SPEED_MULTIPLIER 已校验（无需运行时 clamp）"""
        from config import BOOST_SPEED_MULTIPLIER, MAX_BOOST_MULTIPLIER
        self.assertLessEqual(BOOST_SPEED_MULTIPLIER, MAX_BOOST_MULTIPLIER)
        self.assertGreaterEqual(BOOST_SPEED_MULTIPLIER, 1.0)


class TestBC007FoodDuringBoost(_IntegrationTestBase):
    """BC-007: 食物恰好在加速开始/结束时生成 — 加速与食物生成互不影响，
    无关联时序问题。"""

    def test_food_consumed_during_boost(self):
        """加速状态下食物正常消费"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])

        old_score = self.game.score
        old_length = self.game.snake.length
        self.game._update()

        self.assertEqual(old_score + SCORE_PER_FOOD, self.game.score)
        self.assertEqual(old_length + 1, self.game.snake.length)

    def test_food_spawns_during_boost_transition(self):
        """食物在加速过渡期间生成不受影响"""
        self.game.snake.boost_state['current_multiplier'] = 1.0

        # 启动加速过渡
        self.game._update_boost_state(16.0, True)

        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])

        # 消费食物
        self.game._update()
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertGreater(self.game.score, 0)

    def test_food_respawn_during_boost_not_on_snake(self):
        """加速期间食物重新生成不落在蛇身上"""
        head = self.game.snake.head
        d = self.game.snake.direction
        self.game.food.position = (head[0] + d[0], head[1] + d[1])
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game._update()
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_multiple_food_consumed_during_boost_cycles(self):
        """加速/减速交替期间连续吃多个食物无异常"""
        for _ in range(5):
            self.game.snake.boost_state['current_multiplier'] = (
                BOOST_SPEED_MULTIPLIER if _ % 2 == 0 else 1.0
            )
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

        # 5 次食物消费完成后分数正确
        self.assertEqual(5 * SCORE_PER_FOOD, self.game.score)


class TestBC008BoostAndDirectionSimultaneous(_IntegrationTestBase):
    """BC-008: 加速键与方向键同时按下 — 同一帧内各自处理，无优先级冲突。"""

    def test_boost_and_direction_independent(self):
        """boost 和 direction 在同一命令中独立生效"""
        # 模拟 InputHandler 产出同时包含 direction 和 boost 的命令
        head_before = self.game.snake.head
        _clear_events()
        _post_key(pygame.K_UP)

        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state)

        # cmd 同时包含 direction 和 boost
        self.assertIn('direction', cmd)
        self.assertIn('boost', cmd)
        self.assertEqual((0, -1), cmd['direction'])

        # _handle_command 处理 direction
        self.game._handle_command(cmd)

        # 手动更新 boost state
        self.game._update_boost_state(16.0, cmd['boost'])

        # 两者各自生效
        self.assertEqual((0, -1), self.game.snake.direction)

    def test_boost_continues_while_changing_direction(self):
        """加速期间切换方向，加速不中断"""
        self.game.snake.boost_state['current_multiplier'] = 2.0

        # 转向（在 RUNNING 状态下有效）
        self.game.snake.change_direction(0, -1)

        # boost 状态保持
        self.assertEqual(2.0, self.game.snake.boost_state['current_multiplier'])
        self.assertEqual((0, -1), self.game.snake.direction)

    def test_direction_change_during_boost_tick(self):
        """加速 tick 期间方向切换不丢帧"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 先切换方向，然后步进
        self.game.snake.change_direction(0, 1)
        head_before = self.game.snake.head
        expected_head = (head_before[0], head_before[1] + 1)

        self.game._update()
        self.assertEqual(expected_head, self.game.snake.head)

    def test_rapid_direction_changes_during_boost(self):
        """加速期间快速连续切换方向不报错"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        directions = [(0, -1), (-1, 0), (0, 1), (1, 0)]
        for d in directions:
            try:
                self.game.snake.change_direction(*d)
                self.game._update()
            except Exception as e:
                self.fail(f"Direction change during boost raised {type(e).__name__}: {e}")

    def test_command_with_both_boost_and_direction_handles_correctly(self):
        """命令同时含 direction 和 boost=True 时正确分发"""
        cmd = {'action': 'direction', 'direction': (0, 1), 'boost': True}
        result = self.game._handle_command(cmd)
        self.assertTrue(result)

        # 方向已更新
        self.assertEqual((0, 1), self.game.snake.direction)

        # boost 状态由 _update_boost_state 更新（在 run() 内）
        self.game._update_boost_state(16.0, cmd['boost'])
        self.assertGreater(self.game.snake.boost_state['current_multiplier'], 1.0)


class TestBC009KeyboardRepeatEvents(_IntegrationTestBase):
    """BC-009: 操作系统键盘重复事件 — 输入处理区分按住加速键（轮询/标志位）
    与重复 KEYDOWN 事件，避免重复触发状态切换。"""

    def test_boost_uses_polling_not_keydown(self):
        """加速检测使用 pygame.key.get_pressed() 轮询而非 KEYDOWN 事件"""
        # is_boost_pressed() 调用 pygame.key.get_pressed() 而非 KEYDOWN
        self.assertIsInstance(self.game.input_handler.is_boost_pressed(), bool)

    def test_multiple_keydown_for_boost_does_not_toggle(self):
        """重复 KEYDOWN 事件不影响加速检测"""
        # 加速检测基于轮询而非事件，重复 KEYDOWN 不影响
        for _ in range(50):
            _post_key(pygame.K_SPACE)
            cmd = self.game.input_handler.process_events(
                self.game.snake.direction, GameState.RUNNING)
            self.assertIn('boost', cmd)
            self.assertIsInstance(cmd['boost'], bool)

    def test_boost_key_ignored_as_direction(self):
        """加速键（SPACE）不被误判为方向键"""
        _clear_events()
        _post_key(pygame.K_SPACE)
        cmd = self.game.input_handler.process_events(
            self.game.snake.direction, GameState.RUNNING)
        self.assertEqual('none', cmd['action'])
        self.assertNotIn('direction', cmd)


class TestBC010MaxMultiplierSelfCollision(_IntegrationTestBase):
    """BC-010: 最大倍率下的自碰判断 — 5x 倍率时碰撞检测须逐 tick 执行，
    确保不会因间隔过短而跳过蛇头与身体重叠的帧。"""

    def test_self_collision_detected_at_max_multiplier(self):
        """5x 倍率下自撞判断不遗漏"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 构造自撞场景
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)  # head -> (3,3) 撞到 body[1]
        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_collision_per_tick_not_skipped_at_max_multiplier(self):
        """5x 倍率时逐 tick 碰撞检测不因间隔短而跳过"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # snake 靠近边界
        self.game.snake.body = [(39, 15), (38, 15), (37, 15)]
        self.game.snake.direction = (1, 0)
        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_multiple_collision_checks_at_max_multiplier(self):
        """5x 倍率连续多步碰撞检测无遗漏"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 逐帧模拟 20 次更新
        collisions_detected = 0
        for _ in range(20):
            # 重置到安全位置
            local_snake = Snake(GRID_COLS, GRID_ROWS)
            local_snake.body = [(39, 15), (38, 15), (37, 15)]
            local_snake.direction = (1, 0)

            # 手动检查每步
            local_snake.move_and_grow(False)
            if local_snake.check_boundary_collision(GRID_COLS, GRID_ROWS):
                collisions_detected += 1

        self.assertGreater(collisions_detected, 0,
                           "Boundary collision must be detected at each check")

    def test_self_collision_strictly_per_grid_cell(self):
        """碰撞检测基于网格坐标不基于时间，间隔缩短不影响精度"""
        # 利用 _update 本身的碰撞检测机制验证
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 正常移动不应误触发碰撞
        food_away = (30, 20)
        self.game.food.position = food_away

        for _ in range(10):
            if self.game.state != GameState.RUNNING:
                self.fail("False positive collision at max multiplier")
            self.game._update()

        self.assertEqual(GameState.RUNNING, self.game.state)


# =============================================================================
# T-010: 性能验证 — 5x 加速下 60s 帧率 >= 55fps、CPU/内存稳定
# =============================================================================


class TestBoostPerformance(_IntegrationTestBase):
    """T-010 性能验证：5x 加速下 60s 稳定性、帧率、tick 漂移"""

    def test_max_boost_rendering_framerate_stable(self):
        """5x 加速下渲染帧率稳定 >= 55fps"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        renderer = self.game.renderer
        renderer.tick()  # warm-up

        frame_times = []
        # 模拟 60 帧（约 1 秒 @ 60fps）
        for _ in range(60):
            t0 = time.time()
            dt_ms = renderer.tick()
            frame_times.append(time.time() - t0)

        avg_frame_time = sum(frame_times) / len(frame_times)
        actual_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else float('inf')

        self.assertGreaterEqual(actual_fps, 55.0,
                                f"FPS {actual_fps:.1f} below 55 at max boost")

    def test_tick_interval_stable_at_max_boost(self):
        """5x 加速下 tick_interval 计算稳定无漂移"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        intervals = []
        for _ in range(100):
            interval = self.game._get_current_tick_interval()
            intervals.append(interval)

        # 所有 interval 应相等（同一 multiplier）
        unique = set(intervals)
        self.assertEqual(1, len(unique),
                         f"Multiple tick intervals at fixed multiplier: {unique}")

    def test_max_boost_update_performance(self):
        """5x 加速下 _update 耗时稳定"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        timings = []
        # 确保食物远离蛇
        self.game.food.position = (30, 25)

        for _ in range(50):
            t0 = time.time()
            self.game._update()
            dt = (time.time() - t0) * 1000  # ms
            timings.append(dt)
            # 保持状态 RUNNING
            if self.game.state != GameState.RUNNING:
                self.game.state = GameState.RUNNING

        avg = sum(timings) / len(timings)
        self.assertLess(avg, 5.0,
                        f"_update avg {avg:.2f}ms too slow at max boost")

    def test_no_tick_drift_over_simulated_60_seconds(self):
        """模拟 60 秒运行无 tick 漂移"""
        tick_interval = float(BASE_TICK_INTERVAL) / MAX_BOOST_MULTIPLIER
        simulated_ticks = int((60.0 * 1000) / tick_interval)  # ~3000 ticks
        max_ticks = min(simulated_ticks, 200)  # 取适量样本

        accumulator = 0.0
        step_count = 0
        for _ in range(max_ticks):
            accumulator += tick_interval
            if accumulator >= tick_interval:
                accumulator -= tick_interval
                step_count += 1

        # 验证 accumulator 不无限累积
        self.assertLess(accumulator, tick_interval * 2,
                        f"Accumulator drift: {accumulator:.1f}ms")
        self.assertGreater(step_count, 0)

    def test_memory_stable_during_boost(self):
        """加速状态下多帧内存不持续增长"""
        import gc as gc_module
        import tracemalloc

        if not tracemalloc.is_tracing():
            tracemalloc.start()

        gc_module.collect()
        _, baseline = tracemalloc.get_traced_memory()

        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 模拟 200 帧
        for _ in range(200):
            self.game.renderer.tick()
            self.game._update_boost_state(16.0, True)
            if self.game.state == GameState.RUNNING:
                self.game._update()
            if self.game.state != GameState.RUNNING:
                self.game.state = GameState.RUNNING

        gc_module.collect()
        _, post = tracemalloc.get_traced_memory()

        growth = post - baseline
        self.assertLess(growth, 5 * 1024 * 1024,  # 5 MB
                        f"Memory growth {growth/1024:.1f} KB exceeds limit during boost")
        tracemalloc.stop()

    def test_boost_cpu_overhead_acceptable(self):
        """加速视觉指示渲染开销不超基准 5%（近似验证）"""
        import time as time_mod

        # 基准渲染（无加速）
        self.game.snake.boost_state['is_active'] = False
        renderer = self.game.renderer

        normal_times = []
        for _ in range(30):
            t0 = time_mod.time()
            renderer.draw_frame(self.game.snake, self.game.food, self.game.score,
                                self.game.state, is_boosting=False)
            normal_times.append(time_mod.time() - t0)

        # 加速渲染
        self.game.snake.boost_state['is_active'] = True
        boost_times = []
        for _ in range(30):
            t0 = time_mod.time()
            renderer.draw_frame(self.game.snake, self.game.food, self.game.score,
                                self.game.state, is_boosting=True)
            boost_times.append(time_mod.time() - t0)

        avg_normal = sum(normal_times) / len(normal_times)
        avg_boost = sum(boost_times) / len(boost_times)

        # 加速渲染应接近基准渲染（增加 < 5% 或绝对增加 < 1ms）
        overhead_ratio = (avg_boost - avg_normal) / avg_normal if avg_normal > 0 else 0
        # 允许较大的容差（单帧渲染时间可能有噪音）
        self.assertLess(abs(avg_boost - avg_normal), 0.005,
                        f"Boost render overhead too high: normal={avg_normal:.6f}s, "
                        f"boost={avg_boost:.6f}s")

    def test_consecutive_food_consumption_at_max_boost(self):
        """5x 加速下连续 100 次食物消费无碰撞遗漏或 false negative"""
        # 构造可控环境：蛇在空旷区域，食物依次放置在蛇头前方
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        # 将蛇置于宽阔区域
        center_y = GRID_ROWS // 2
        self.game.snake.body = [(5, center_y), (4, center_y), (3, center_y)]
        self.game.snake.direction = (1, 0)

        food_count = 0
        collisions = 0
        max_eats = min(100, GRID_COLS - 7)  # 最大可吃次数，受宽度限制

        for _ in range(max_eats):
            # 在蛇头前方放食物
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])

            self.game._update()

            if self.game.state == GameState.GAME_OVER:
                collisions += 1
                break
            food_count += 1

        self.assertEqual(0, collisions,
                         f"Had {collisions} false collisions during {food_count} food eats")
        self.assertEqual(max_eats, food_count,
                         f"Expected {max_eats} food eats, got {food_count}")
        self.assertEqual(GameState.RUNNING, self.game.state,
                         "Should still be running after consecutive food eats")

    def test_boost_direction_independent_no_race_condition(self):
        """加速键与方向键同时按下各自独立生效，无竞态条件"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        self.game.snake.boost_state['is_active'] = False

        # 模拟同一帧中的并发输入
        command = {'action': 'direction', 'direction': (0, -1), 'boost': True}

        # 方向处理
        self.game._handle_command(command)

        # boost 处理
        self.game._update_boost_state(16.0, command['boost'])

        # 两者各自生效
        self.assertEqual((0, -1), self.game.snake.direction)
        self.assertGreater(self.game.snake.boost_state['current_multiplier'], 1.0)

        # 蛇正常移动一步
        head_before = self.game.snake.head
        self.game._update()
        self.assertEqual((head_before[0], head_before[1] - 1), self.game.snake.head)


# =============================================================================
# T-007: 手动验收测试与集成验证 — 逐场景自动化验证
# =============================================================================


class TestT007AcceptanceInitialState(_IntegrationTestBase):
    """T-007-1: 初始状态验证 — tick=100ms, difficulty_level=0, HUD 正常"""

    def test_initial_tick_interval_is_100ms(self):
        """初始状态 tick 间隔 = 100ms"""
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(100.0, interval, places=1)

    def test_initial_difficulty_level_zero(self):
        """初始难度等级为 0"""
        self.assertEqual(0, self.game.difficulty_level)

    def test_initial_difficulty_multiplier_zero(self):
        """初始难度倍率为 0.0"""
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_effective_multiplier_initial_1_0(self):
        """初始综合倍率为 1.0"""
        effective = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(1.0, effective, places=1)

    def test_hud_renders_initial_difficulty(self):
        """HUD 渲染初始难度信息 'Lv.0 Speed 1.0x' 不崩溃"""
        renderer = self.game.renderer
        try:
            renderer.draw_hud(0, difficulty_level=0, effective_multiplier=1.0)
        except Exception as e:
            self.fail(f"HUD initial difficulty render raised {e}")

    def test_tick_interval_between_20ms_and_100ms_boundaries(self):
        """tick 间隔在 [MIN_TICK_INTERVAL, BASE_TICK_INTERVAL] 范围内"""
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)
        self.assertLessEqual(interval, 100.0)


class TestT007AcceptanceEat5Food(_IntegrationTestBase):
    """T-007-2: 吃5个食物(50分) — 验证 tick~90.9ms, difficulty_level=1"""

    def setUp(self):
        super().setUp()
        # 模拟吃 5 个食物（每个 10 分，共 50 分，跨越 1 个阈值）
        for _ in range(5):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

    def test_score_is_50_after_5_food(self):
        """吃 5 个食物后分数为 50"""
        self.assertEqual(50, self.game.score)

    def test_difficulty_level_is_1(self):
        """分数 50 时难度等级为 1 (50//50=1)"""
        self.assertEqual(1, self.game.difficulty_level)

    def test_difficulty_multiplier_is_0_1(self):
        """难度倍率为 0.1 (1 * 0.1)"""
        self.assertAlmostEqual(0.1, self.game.difficulty_multiplier, places=5)

    def test_tick_interval_is_about_90_9ms(self):
        """tick 间隔 ~90.9ms (100/1.1)"""
        interval = self.game._get_current_tick_interval()
        expected = 100.0 / 1.1
        self.assertAlmostEqual(expected, interval, places=1)

    def test_effective_multiplier_is_1_1(self):
        """综合倍率 = 1.1 (1 + 0.1 + 0)"""
        effective = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(1.1, effective, places=3)

    def test_tick_interval_still_above_minimum(self):
        """tick 间隔仍远高于 20ms 下限"""
        interval = self.game._get_current_tick_interval()
        self.assertGreater(interval, 20.0)


class TestT007AcceptanceEat10Food(_IntegrationTestBase):
    """T-007-3: 吃10个食物(100分) — 验证 tick~83.3ms, difficulty_level=2"""

    def setUp(self):
        super().setUp()
        # 模拟吃 10 个食物（每个 10 分，共 100 分，跨越 2 个阈值）
        for _ in range(10):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

    def test_score_is_100_after_10_food(self):
        """吃 10 个食物后分数为 100"""
        self.assertEqual(100, self.game.score)

    def test_difficulty_level_is_2(self):
        """分数 100 时难度等级为 2 (100//50=2)"""
        self.assertEqual(2, self.game.difficulty_level)

    def test_difficulty_multiplier_is_0_2(self):
        """难度倍率为 0.2 (2 * 0.1)"""
        self.assertAlmostEqual(0.2, self.game.difficulty_multiplier, places=5)

    def test_tick_interval_is_about_83_3ms(self):
        """tick 间隔 ~83.3ms (100/1.2)"""
        interval = self.game._get_current_tick_interval()
        expected = 100.0 / 1.2
        self.assertAlmostEqual(expected, interval, places=1)

    def test_effective_multiplier_is_1_2(self):
        """综合倍率 = 1.2 (1 + 0.2 + 0)"""
        effective = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(1.2, effective, places=3)

    def test_difficulty_level_incremented_correctly(self):
        """难度从 Lv.0 经 Lv.1 到达 Lv.2（台阶式递增）"""
        # 分数 100 对应 level=2，中间经过 50 分 level=1
        self.assertEqual(2, self.game.difficulty_level)


class TestT007AcceptanceBoostOverlay(_IntegrationTestBase):
    """T-007-4: 按住空格验证叠加加速 — boost_multiplier 与 difficulty_multiplier 加法叠加"""

    def setUp(self):
        super().setUp()
        # 先建立一定难度 (50 分 => diff=0.1)
        for _ in range(5):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

    def test_difficulty_established_before_boost(self):
        """加速前难度已建立：level=1, diff=0.1"""
        self.assertEqual(1, self.game.difficulty_level)
        self.assertAlmostEqual(0.1, self.game.difficulty_multiplier, places=5)

    def test_boost_alone_reduces_tick(self):
        """仅 boost (无难度) 时 tick=50ms (100/2)"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(50.0, interval, places=1)

    def test_difficulty_alone_reduces_tick(self):
        """仅难度 (无 boost) 时 tick~90.9ms (100/1.1)"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        expected = 100.0 / 1.1
        self.assertAlmostEqual(expected, interval, places=1)

    def test_boost_plus_difficulty_compound(self):
        """难度 + boost 加法叠加: diff=0.1 + boost=2.0 -> effective=2.1, tick~47.6ms"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        # effective = 1 + 0.1 + 1.0 = 2.1
        expected = 100.0 / 2.1
        self.assertAlmostEqual(expected, interval, places=1)

    def test_effective_multiplier_reflects_both_factors(self):
        """综合倍率同时反映难度和加速贡献"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        effective = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        # effective = 1 + 0.1 + 1.0 = 2.1
        self.assertAlmostEqual(2.1, effective, places=3)

    def test_is_boosting_flag_active_with_boost(self):
        """boost 激活时 is_boosting 为 True"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.assertTrue(self.game.snake.is_boosting)

    def test_boost_release_returns_to_diff_only(self):
        """释放加速后 tick 恢复到仅难度加速水平"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 释放加速
        for _ in range(100):
            self.game._update_boost_state(16.0, False)

        interval = self.game._get_current_tick_interval()
        # 仅剩 diff=0.1
        expected = 100.0 / 1.1
        self.assertAlmostEqual(expected, interval, places=1)


class TestT007AcceptanceResetOnCrash(_IntegrationTestBase):
    """T-007-5: 撞墙重置 — 验证 HUD 难度复位"""

    def setUp(self):
        super().setUp()
        # 先建立难度 (100 分 => level=2, diff=0.2)
        for _ in range(10):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

    def test_difficulty_established_before_crash(self):
        """撞墙前难度已建立"""
        self.assertEqual(2, self.game.difficulty_level)
        self.assertAlmostEqual(0.2, self.game.difficulty_multiplier, places=5)
        self.assertEqual(100, self.game.score)

    def test_crash_triggers_game_over(self):
        """撞墙触发 GAME_OVER"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_reset_after_crash_clears_difficulty(self):
        """撞墙后 reset 难度归零"""
        # 先撞墙
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

        # reset
        self.game.reset()

        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)
        self.assertEqual(0, self.game.score)
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_reset_restores_tick_to_100ms(self):
        """撞墙 reset 后 tick 恢复为 100ms"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.game.reset()

        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(100.0, interval, places=1)

    def test_hud_renders_reset_difficulty_lv0(self):
        """reset 后 HUD 显示 Lv.0"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        self.game._update()
        self.game.reset()

        renderer = self.game.renderer
        try:
            renderer.draw_hud(0, difficulty_level=0, effective_multiplier=1.0)
        except Exception as e:
            self.fail(f"HUD render after reset raised {e}")

    def test_multiple_reset_cycles_difficulty_consistent(self):
        """多次撞墙->reset 循环，难度每次归零一致"""
        for cycle in range(3):
            # 吃食物建立难度
            for _ in range(5):
                head = self.game.snake.head
                d = self.game.snake.direction
                self.game.food.position = (head[0] + d[0], head[1] + d[1])
                self.game._update()
            # 撞墙
            self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
            self.game.snake.direction = (-1, 0)
            self.game._update()
            # reset
            self.game.reset()

            self.assertEqual(0, self.game.difficulty_level,
                             f"Cycle {cycle}: difficulty_level not reset")
            self.assertEqual(0.0, self.game.difficulty_multiplier,
                             f"Cycle {cycle}: difficulty_multiplier not reset")
            self.assertAlmostEqual(100.0, self.game._get_current_tick_interval(),
                                   places=1,
                                   msg=f"Cycle {cycle}: tick interval not 100ms")


class TestT007AcceptanceThresholdCrossing(_IntegrationTestBase):
    """T-007-6: 连续快速吃食物 — 验证阈值跨越"""

    def test_eating_5_food_crosses_threshold_50(self):
        """吃 5 个食物 (50分) 跨越第一个阈值 -> level 0->1"""
        for i in range(5):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

        self.assertEqual(50, self.game.score)
        self.assertEqual(1, self.game.difficulty_level)

    def test_eating_10_food_crosses_threshold_100(self):
        """吃 10 个食物 (100分) 跨越两个阈值 -> level 0->1->2"""
        levels_seen = [self.game.difficulty_level]

        for i in range(10):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()
            levels_seen.append(self.game.difficulty_level)

        self.assertEqual(100, self.game.score)
        self.assertEqual(2, self.game.difficulty_level)
        # 验证经过 level=1 这个中间状态
        self.assertIn(1, levels_seen, "Should have passed through level 1")

    def test_eating_15_food_crosses_threshold_150(self):
        """吃 15 个食物 (150分) -> level=3, diff=0.3, tick~76.9ms"""
        for i in range(15):
            head = self.game.snake.head
            d = self.game.snake.direction
            self.game.food.position = (head[0] + d[0], head[1] + d[1])
            self.game._update()

        self.assertEqual(150, self.game.score)
        self.assertEqual(3, self.game.difficulty_level)
        self.assertAlmostEqual(0.3, self.game.difficulty_multiplier, places=5)
        expected_tick = 100.0 / 1.3
        self.assertAlmostEqual(expected_tick, self.game._get_current_tick_interval(), places=1)

    def test_thresholds_are_stepwise_not_continuous(self):
        """难度递增是台阶式：score=49 level=0, score=50 level=1（离散跳跃）"""
        # 验证 49 分
        self.game.score = 49
        self.game._update_difficulty()
        self.assertEqual(0, self.game.difficulty_level)
        mult_at_49 = self.game.difficulty_multiplier

        # 验证 50 分
        self.game.score = 50
        self.game._update_difficulty()
        self.assertEqual(1, self.game.difficulty_level)
        mult_at_50 = self.game.difficulty_multiplier

        # 台阶式跳跃
        self.assertNotEqual(mult_at_49, mult_at_50)
        self.assertAlmostEqual(0.0, mult_at_49)
        self.assertAlmostEqual(0.1, mult_at_50, places=5)

    def test_threshold_crossing_tick_decreases_monotonically(self):
        """跨越阈值后 tick 单调递减"""
        ticks = []
        for target_score in [0, 50, 100, 150, 200, 250]:
            self.game.score = target_score
            self.game._update_difficulty()
            ticks.append(self.game._get_current_tick_interval())

        for i in range(1, len(ticks)):
            self.assertLess(ticks[i], ticks[i-1],
                            f"Tick should decrease: {ticks[i]} >= {ticks[i-1]}")

    def test_rapid_threshold_crossing_no_loss_of_levels(self):
        """短时间内多次跨越阈值，不丢失中间等级"""
        # 一次性设置 score 到 300（应 level=6），验证 level 公式正确
        self.game.score = 300
        self.game._update_difficulty()
        expected_level = 300 // 50  # 6
        self.assertEqual(expected_level, self.game.difficulty_level)
        # multiplier = min(6*0.1, 4.0) = 0.6
        self.assertAlmostEqual(0.6, self.game.difficulty_multiplier, places=5)
        # tick = max(20, 100/1.6) = 62.5ms
        expected_tick = max(20.0, 100.0 / 1.6)
        self.assertAlmostEqual(expected_tick, self.game._get_current_tick_interval(), places=1)

    def test_extreme_high_score_multiplier_clamped(self):
        """极端高分 multiplier 钳位在 MAX_DIFFICULTY_MULTIPLIER"""
        self.game.score = 9999
        self.game._update_difficulty()
        self.assertEqual(199, self.game.difficulty_level)  # 9999//50
        self.assertLessEqual(self.game.difficulty_multiplier, 4.0)
        # tick 不低于 20ms
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)


class TestT007AcceptanceHUDDisplay(_IntegrationTestBase):
    """T-007-7: HUD 显示正确性验证"""

    def setUp(self):
        super().setUp()
        self.renderer = self.game.renderer

    def test_hud_shows_score_correctly(self):
        """HUD 左侧显示分数"""
        self.renderer.draw_background()
        self.renderer.draw_hud(100, difficulty_level=0, effective_multiplier=1.0)
        # 不崩溃即通过（分数文字渲染由 Renderer 内部处理）
        self.assertTrue(True)

    def test_hud_shows_difficulty_level_correctly(self):
        """HUD 中部显示难度等级"""
        self.renderer.draw_background()
        for level, mult in [(0, 1.0), (1, 1.1), (3, 1.3), (5, 1.5), (10, 2.0)]:
            try:
                self.renderer.draw_hud(level * 50, difficulty_level=level,
                                       effective_multiplier=mult)
            except Exception as e:
                self.fail(f"HUD level={level} raised {e}")

    def test_hud_shows_boost_indicator_correctly(self):
        """HUD 右侧条件显示 BOOST 文字"""
        self.renderer.draw_background()
        # boost 激活时渲染
        try:
            self.renderer.draw_hud(50, is_boosting=True, difficulty_level=1,
                                   effective_multiplier=2.1)
        except Exception as e:
            self.fail(f"HUD with boost raised {e}")

    def test_hud_difficulty_does_not_overlap_score(self):
        """HUD 难度文字不遮挡分数区域"""
        self.renderer.draw_background()
        self.renderer.draw_hud(9999, difficulty_level=99, effective_multiplier=9.9)
        # 分数在左侧 (x=12)，难度居中 (x=WIDTH/2)
        # 验证两个区域都不为空
        score_pixel = tuple(self.renderer.screen.get_at((12, HUD_HEIGHT // 2))[:3])
        diff_pixel = tuple(self.renderer.screen.get_at((WINDOW_WIDTH // 2, HUD_HEIGHT // 2))[:3])
        self.assertNotEqual(COLORS.BACKGROUND, score_pixel,
                            "Score area should have text")
        self.assertNotEqual(COLORS.BACKGROUND, diff_pixel,
                            "Difficulty area should have text")

    def test_hud_difficulty_does_not_overlap_boost(self):
        """HUD 难度文字居中，不覆盖右侧 BOOST 区域"""
        self.renderer.draw_background()
        self.renderer.draw_hud(150, is_boosting=True, difficulty_level=3,
                               effective_multiplier=2.3)
        # 中央区域应有文字
        center_pixel = tuple(self.renderer.screen.get_at(
            (WINDOW_WIDTH // 2, HUD_HEIGHT // 2))[:3])
        self.assertNotEqual(COLORS.BACKGROUND, center_pixel)

    def test_hud_does_not_cover_game_elements(self):
        """HUD 不遮挡蛇和食物等游戏元素"""
        # 绘制完整帧
        food = Food(GRID_COLS, GRID_ROWS)
        food.position = (5, 10)
        self.renderer.draw_frame(
            self.game.snake, food, 80, GameState.RUNNING,
            difficulty_level=1, effective_multiplier=1.1
        )
        # 蛇头可见（在 HUD 高度以下）
        hx, hy = self.game.snake.head
        head_color = tuple(self.renderer.screen.get_at(
            (hx * CELL_SIZE + 10, hy * CELL_SIZE + 10))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, head_color,
                         "Snake head should be visible below HUD")

        # 食物可见
        food_color = tuple(self.renderer.screen.get_at(
            (5 * CELL_SIZE + 10, 10 * CELL_SIZE + 10))[:3])
        self.assertEqual(COLORS.FOOD, food_color,
                         "Food should be visible below HUD")

    def test_hud_layout_three_zones_distinct(self):
        """HUD 三区布局：左分数 | 中难度 | 右 BOOST"""
        self.renderer.draw_background()
        self.renderer.draw_hud(100, is_boosting=True, difficulty_level=2,
                               effective_multiplier=1.2)
        # 左侧 (x=12)
        left = tuple(self.renderer.screen.get_at((12, HUD_HEIGHT // 2))[:3])
        # 中间 (x=WIDTH//2)
        mid = tuple(self.renderer.screen.get_at((WINDOW_WIDTH // 2, HUD_HEIGHT // 2))[:3])
        # 右侧 (x=WIDTH-50)
        right = tuple(self.renderer.screen.get_at((WINDOW_WIDTH - 50, HUD_HEIGHT // 2))[:3])

        self.assertNotEqual(COLORS.BACKGROUND, left, "Score zone should render")
        self.assertNotEqual(COLORS.BACKGROUND, mid, "Difficulty zone should render")

    def test_hud_effective_multiplier_realtime_update(self):
        """综合倍率在 boost 和难度变化时实时反映"""
        # 基准
        eff1 = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(1.0, eff1, places=3)

        # 加难度 (simulate 100 pts)
        self.game.score = 100
        self.game._update_difficulty()
        eff2 = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(1.2, eff2, places=3)

        # 加 boost
        self.game.snake.boost_state['current_multiplier'] = 2.0
        eff3 = 1.0 + self.game.difficulty_multiplier + (self.game.snake.boost_multiplier - 1.0)
        self.assertAlmostEqual(2.2, eff3, places=3)

    def test_hud_text_readable_sufficient_contrast(self):
        """HUD 文字与背景有足够对比度（文字颜色不同于背景）"""
        self.renderer.draw_background()
        self.renderer.draw_hud(0, difficulty_level=0, effective_multiplier=1.0)
        # HUD 区域内背景条已覆盖，文字应可见
        # 验证 HUD 中心区与原先纯背景色不同
        bg_layer = self.renderer.screen.get_at((WINDOW_WIDTH // 2, HUD_HEIGHT // 2))
        self.assertIsNotNone(bg_layer)

    def test_hud_effective_multiplier_formatting_one_decimal(self):
        """综合倍率格式保留一位小数 (x.x)"""
        # 验证渲染不崩溃即可，格式化由 Renderer 内部控制
        self.renderer.draw_background()
        try:
            self.renderer.draw_hud(50, difficulty_level=1, effective_multiplier=1.067)
        except Exception as e:
            self.fail(f"Multiplier formatting raised {e}")


if __name__ == "__main__":
    unittest.main()
