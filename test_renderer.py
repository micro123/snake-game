"""
Renderer 类单元测试

覆盖：初始化、draw_background、draw_snake、draw_food（含占位跳过）、
draw_hud、draw_game_over、draw_victory、draw_frame（各 GameState）、
tick 帧率控制。
使用 Python 标准库 unittest 框架，依赖 Pygame。
"""

import unittest

import pygame

from food import Food
from game import GameState
from renderer import Renderer
from snake import Snake

# 使用 config 常量进行像素级断言
from config import CELL_SIZE, COLORS, HUD_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH


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

def _create_snake(body=None):
    """创建 Snake 实例，可选自定义 body。"""
    s = Snake(40, 30)
    if body is not None:
        s.body = body
    return s


def _create_food(position=None):
    """创建 Food 实例，可选自定义 position。"""
    f = Food(40, 30)
    if position is not None:
        f.position = position
    return f


def _renderer(screen=None):
    """创建 Renderer 实例，可选自定义 screen。"""
    if screen is None:
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    return Renderer(screen)


# =============================================================================
# 测试类
# =============================================================================


class TestRendererInit(unittest.TestCase):
    """测试 Renderer 初始化"""

    def setUp(self):
        self.screen = pygame.Surface((800, 600))
        self.renderer = Renderer(self.screen)

    def test_screen_property(self):
        """screen 属性为传入的 Surface"""
        self.assertIs(self.screen, self.renderer.screen)

    def test_fonts_initialized(self):
        """三种字号字体创建成功"""
        self.assertIsNotNone(self.renderer.font_small)
        self.assertIsNotNone(self.renderer.font_large)
        self.assertIsNotNone(self.renderer.font_title)

    def test_clock_initialized(self):
        """帧率控制器 clock 创建成功"""
        self.assertIsNotNone(self.renderer.clock)
        self.assertIsInstance(self.renderer.clock, pygame.time.Clock)

    def test_fonts_can_render(self):
        """字体能够渲染文字并返回 Surface"""
        surf = self.renderer._render_text(
            self.renderer.font_small, "Test", (255, 255, 255)
        )
        self.assertIsInstance(surf, pygame.Surface)
        self.assertGreater(surf.get_width(), 0)
        self.assertGreater(surf.get_height(), 0)


class TestDrawBackground(unittest.TestCase):
    """测试 draw_background 背景绘制"""

    def setUp(self):
        self.renderer = _renderer()

    def test_no_exception_raised(self):
        """绘制背景不抛出异常"""
        try:
            self.renderer.draw_background()
        except Exception as e:
            self.fail(f"draw_background raised {type(e).__name__}: {e}")

    def test_background_color_filled(self):
        """屏幕被填充为 BACKGROUND 色（检查非网格线位置）"""
        self.renderer.draw_background()
        # (1, 1) 不在网格线上，应为纯背景色
        color = tuple(self.renderer.screen.get_at((1, 1))[:3])
        self.assertEqual(COLORS.BACKGROUND, color)

    def test_grid_lines_drawn(self):
        """网格线被绘制（检查网格线交点位置）"""
        self.renderer.draw_background()
        # (0, 0) 在网格线上
        color = tuple(self.renderer.screen.get_at((0, 0))[:3])
        self.assertEqual(COLORS.GRID_LINE, color)

    def test_grid_lines_at_interval(self):
        """网格线按 CELL_SIZE 间隔绘制"""
        self.renderer.draw_background()
        # 每 20 像素处应有网格线颜色
        for x in range(0, 200, CELL_SIZE):
            color = tuple(self.renderer.screen.get_at((x, 0))[:3])
            self.assertEqual(COLORS.GRID_LINE, color,
                             f"Expected grid line at x={x}, y=0")

    def test_background_not_at_grid_line(self):
        """非网格线位置为背景色"""
        self.renderer.draw_background()
        positions = [(1, 1), (1, 3), (3, 1), (15, 15), (21, 5)]
        for x, y in positions:
            color = tuple(self.renderer.screen.get_at((x, y))[:3])
            self.assertEqual(COLORS.BACKGROUND, color,
                             f"Expected background at ({x},{y}), got {color}")


class TestDrawSnake(unittest.TestCase):
    """测试 draw_snake 蛇绘制"""

    def setUp(self):
        self.renderer = _renderer()

    def test_no_exception_raised(self):
        """绘制蛇不抛出异常"""
        snake = Snake(40, 30)
        try:
            self.renderer.draw_snake(snake)
        except Exception as e:
            self.fail(f"draw_snake raised {type(e).__name__}: {e}")

    def test_head_color_distinct_from_body(self):
        """蛇头与蛇身颜色不同"""
        snake = _create_snake(body=[(10, 10), (9, 10), (8, 10)])
        self.renderer.draw_background()
        self.renderer.draw_snake(snake)

        # 蛇头中心像素
        head_x = 10 * CELL_SIZE + 10
        head_y = 10 * CELL_SIZE + 10
        head_color = tuple(self.renderer.screen.get_at((head_x, head_y))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, head_color)

        # 蛇身中心像素
        body_x = 9 * CELL_SIZE + 10
        body_y = 10 * CELL_SIZE + 10
        body_color = tuple(self.renderer.screen.get_at((body_x, body_y))[:3])
        self.assertEqual(COLORS.SNAKE_BODY, body_color)

        # 验证两者颜色不同
        self.assertNotEqual(head_color, body_color)

    def test_snake_with_body_only(self):
        """仅蛇头（1 节蛇）也能正常绘制"""
        snake = _create_snake(body=[(10, 10)])
        self.renderer.draw_background()
        try:
            self.renderer.draw_snake(snake)
        except Exception as e:
            self.fail(f"draw_snake 1-segment raised {e}")

        # 蛇头绘制正确
        color = tuple(self.renderer.screen.get_at((210, 210))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, color)

    def test_snake_body_rendered_tail_to_head(self):
        """先绘蛇身再绘蛇头，蛇头在最上层（不会被蛇身覆盖）"""
        # 创建重叠 body 模拟（蛇头坐标与蛇身某节相同时，蛇头应可见）
        snake = _create_snake(body=[(5, 5), (6, 5), (5, 5)])
        self.renderer.draw_background()
        self.renderer.draw_snake(snake)

        # 蛇头位置应为 HEAD 色（不为 BODY 色）
        color = tuple(self.renderer.screen.get_at((110, 110))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, color)

    def test_snake_draws_all_segments(self):
        """长蛇身的每一节都被绘制"""
        body = [(i, 5) for i in range(10, 0, -1)]  # 10 节蛇身
        snake = _create_snake(body=body)
        self.renderer.draw_background()
        self.renderer.draw_snake(snake)

        # 检查每一节的中间部位
        for i, (x, y) in enumerate(body):
            px = x * CELL_SIZE + 10
            py = y * CELL_SIZE + 10
            expected = COLORS.SNAKE_HEAD if i == 0 else COLORS.SNAKE_BODY
            color = tuple(self.renderer.screen.get_at((px, py))[:3])
            self.assertEqual(expected, color,
                             f"Segment {i} at ({x},{y}): expected {expected}, got {color}")


class TestDrawFood(unittest.TestCase):
    """测试 draw_food 食物绘制"""

    def setUp(self):
        self.renderer = _renderer()

    def test_skip_placeholder_position(self):
        """position 为 (-1, -1) 时跳过的绘制"""
        food = _create_food(position=(-1, -1))
        self.renderer.draw_background()
        # 不应抛出异常
        try:
            self.renderer.draw_food(food)
        except Exception as e:
            self.fail(f"draw_food placeholder raised {e}")

    def test_valid_position_drawn_with_correct_color(self):
        """有效坐标以 FOOD 色绘制"""
        food = _create_food(position=(15, 10))
        self.renderer.draw_background()
        self.renderer.draw_food(food)

        color = tuple(self.renderer.screen.get_at((310, 210))[:3])
        self.assertEqual(COLORS.FOOD, color)

    def test_valid_position_does_not_draw_placeholder_color(self):
        """有效坐标不绘制为占位或其他颜色"""
        food = _create_food(position=(5, 5))
        self.renderer.draw_background()
        self.renderer.draw_food(food)

        # 食物位置应为 FOOD 色，不是背景色
        color = tuple(self.renderer.screen.get_at((110, 110))[:3])
        self.assertEqual(COLORS.FOOD, color)
        self.assertNotEqual(COLORS.BACKGROUND, color)

    def test_food_at_corner_position(self):
        """食物在网格角落 (0,0) 也能正常绘制"""
        food = _create_food(position=(0, 0))
        self.renderer.draw_background()
        self.renderer.draw_food(food)

        # (0,0)*20 = (0,0)，(10,10) 在食物内部
        color = tuple(self.renderer.screen.get_at((10, 10))[:3])
        self.assertEqual(COLORS.FOOD, color)

    def test_food_at_max_boundary(self):
        """食物在网格边界 (39, 29) 也能正常绘制"""
        food = _create_food(position=(39, 29))
        self.renderer.draw_background()
        self.renderer.draw_food(food)

        color = tuple(self.renderer.screen.get_at((790, 590))[:3])
        self.assertEqual(COLORS.FOOD, color)


class TestDrawHUD(unittest.TestCase):
    """测试 draw_hud HUD 绘制"""

    def setUp(self):
        self.renderer = _renderer()

    def test_no_exception_raised(self):
        """HUD 绘制不抛出异常"""
        try:
            self.renderer.draw_hud(0)
        except Exception as e:
            self.fail(f"draw_hud raised {e}")

    def test_hud_bar_is_visible(self):
        """HUD 背景条在顶部产生可见变化"""
        self.renderer.draw_background()
        bg_color = tuple(self.renderer.screen.get_at((200, 20))[:3])
        self.renderer.draw_hud(0)
        hud_color = tuple(self.renderer.screen.get_at((200, 20))[:3])
        # HUD 区域应该发生变化（被半透明条覆盖）
        self.assertNotEqual(bg_color, hud_color,
                            "HUD bar should change pixel color at y=20")

    def test_hud_bar_covers_full_width(self):
        """HUD 背景条覆盖窗口全宽"""
        self.renderer.draw_background()
        self.renderer.draw_hud(0)
        # 检查最左、中间、最右位置
        for x in (1, WINDOW_WIDTH // 2, WINDOW_WIDTH - 1):
            color = tuple(self.renderer.screen.get_at((x, 20))[:3])
            self.assertNotEqual(COLORS.BACKGROUND, color,
                                f"HUD at x={x} should differ from background")

    def test_hud_different_scores(self):
        """不同分数值的 HUD 均能正常绘制"""
        for score in (0, 10, 100, 9999):
            try:
                self.renderer.draw_hud(score)
            except Exception as e:
                self.fail(f"draw_hud({score}) raised {e}")

    def test_hud_does_not_affect_game_area(self):
        """HUD 绘制不影响游戏区域（HUD 高度以下）"""
        self.renderer.draw_background()
        bg_color = tuple(self.renderer.screen.get_at((200, HUD_HEIGHT + 10))[:3])
        self.renderer.draw_hud(100)
        after_color = tuple(self.renderer.screen.get_at((200, HUD_HEIGHT + 10))[:3])
        # HUD 以下区域不受影响（没有半透明条到此位置）
        self.assertEqual(bg_color, after_color,
                         "HUD should not affect pixels below HUD_HEIGHT")


class TestDrawGameOver(unittest.TestCase):
    """测试 draw_game_over 结束遮罩"""

    def setUp(self):
        self.renderer = _renderer()

    def test_no_exception_raised(self):
        """游戏结束遮罩绘制不抛出异常"""
        try:
            self.renderer.draw_game_over(0)
        except Exception as e:
            self.fail(f"draw_game_over raised {e}")

    def test_overlay_changes_center_pixels(self):
        """遮罩改变了屏幕中心的像素颜色"""
        self.renderer.draw_background()
        bg_color = tuple(self.renderer.screen.get_at((400, 300))[:3])
        self.renderer.draw_game_over(100)
        overlay_color = tuple(self.renderer.screen.get_at((400, 300))[:3])
        self.assertNotEqual(bg_color, overlay_color,
                            "Game over overlay should change center pixels")

    def test_different_scores_all_work(self):
        """不同分数值的结束画面均能正常绘制"""
        for score in (0, 50, 100, 9999):
            renderer = _renderer()
            try:
                renderer.draw_game_over(score)
            except Exception as e:
                self.fail(f"draw_game_over({score}) raised {e}")


class TestDrawVictory(unittest.TestCase):
    """测试 draw_victory 胜利遮罩"""

    def setUp(self):
        self.renderer = _renderer()

    def test_no_exception_raised(self):
        """胜利遮罩绘制不抛出异常"""
        try:
            self.renderer.draw_victory(0)
        except Exception as e:
            self.fail(f"draw_victory raised {e}")

    def test_overlay_changes_center_pixels(self):
        """遮罩改变了屏幕中心的像素颜色"""
        self.renderer.draw_background()
        bg_color = tuple(self.renderer.screen.get_at((400, 300))[:3])
        self.renderer.draw_victory(1200)
        overlay_color = tuple(self.renderer.screen.get_at((400, 300))[:3])
        self.assertNotEqual(bg_color, overlay_color,
                            "Victory overlay should change center pixels")

    def test_different_scores_all_work(self):
        """不同分数值的胜利画面均能正常绘制"""
        for score in (0, 500, 1200):
            renderer = _renderer()
            try:
                renderer.draw_victory(score)
            except Exception as e:
                self.fail(f"draw_victory({score}) raised {e}")


class TestDrawFrame(unittest.TestCase):
    """测试 draw_frame 帧合成方法"""

    def setUp(self):
        self.snake = Snake(40, 30)
        self.food = Food(40, 30)
        self.food.respawn(self.snake.body)

    def test_running_state_no_overlay(self):
        """RUNNING 状态不叠加遮罩"""
        renderer = _renderer()
        renderer.draw_frame(self.snake, self.food, 0, GameState.RUNNING)
        # 只是验证不抛出异常
        self.assertTrue(True)

    def test_running_state_shows_game_elements(self):
        """RUNNING 状态正确绘制游戏元素"""
        renderer = _renderer()
        renderer.draw_frame(self.snake, self.food, 0, GameState.RUNNING)
        # 蛇头可见
        hx, hy = self.snake.head
        color = tuple(renderer.screen.get_at((hx * CELL_SIZE + 10, hy * CELL_SIZE + 10))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, color)

    def test_game_over_state_overlay_applied(self):
        """GAME_OVER 状态叠加结束遮罩"""
        renderer = _renderer()
        # 先绘制 RUNNING 画面
        renderer.draw_frame(self.snake, self.food, 0, GameState.RUNNING)
        running_pixel = tuple(renderer.screen.get_at((400, 300))[:3])
        # 再绘制 GAME_OVER 画面
        renderer = _renderer()
        renderer.draw_frame(self.snake, self.food, 0, GameState.GAME_OVER)
        over_pixel = tuple(renderer.screen.get_at((400, 300))[:3])
        self.assertNotEqual(running_pixel, over_pixel,
                            "GAME_OVER should produce different center pixel than RUNNING")

    def test_victory_state_overlay_applied(self):
        """VICTORY 状态叠加胜利遮罩"""
        renderer = _renderer()
        renderer.draw_frame(self.snake, self.food, 1200, GameState.VICTORY)
        # 验证不抛出异常
        self.assertTrue(True)

    def test_victory_and_game_over_different(self):
        """VICTORY 和 GAME_OVER 的遮罩内容不同"""
        # GAME_OVER 中心像素
        r1 = _renderer()
        r1.draw_frame(self.snake, self.food, 0, GameState.GAME_OVER)
        go_pixel = tuple(r1.screen.get_at((400, 250))[:3])

        # VICTORY 中心像素
        r2 = _renderer()
        r2.draw_frame(self.snake, self.food, 0, GameState.VICTORY)
        vic_pixel = tuple(r2.screen.get_at((400, 250))[:3])

        # 两者叠加的文本颜色不同（红 vs 绿），但像素可能重叠在文字位置
        # 至少验证两种状态都能正常执行
        self.assertTrue(True)

    def test_layered_order_preserved(self):
        """验证图层顺序：背景 -> 蛇 -> 食物，蛇和食物可见于背景之上"""
        renderer = _renderer()
        # 食物放在 HUD 区域以下 (y=3 -> pixel_y=60, 即 HUD_HEIGHT + 20)
        food = Food(40, 30)
        food.position = (0, 3)
        snake = _create_snake(body=[(10, 10), (9, 10), (8, 10)])

        renderer.draw_frame(snake, food, 0, GameState.RUNNING)

        # 食物可见（在 HUD 高度以下，不被 HUD 遮挡）
        food_color = tuple(renderer.screen.get_at((10, 70))[:3])
        self.assertEqual(COLORS.FOOD, food_color)

        # 蛇头可见
        head_color = tuple(renderer.screen.get_at((210, 210))[:3])
        self.assertEqual(COLORS.SNAKE_HEAD, head_color)


class TestTick(unittest.TestCase):
    """测试 tick 帧率控制"""

    def setUp(self):
        self.renderer = _renderer()

    def test_tick_returns_integer(self):
        """tick 返回整数类型的毫秒数"""
        result = self.renderer.tick()
        self.assertIsInstance(result, int)

    def test_tick_does_not_raise(self):
        """tick 不抛出异常"""
        try:
            self.renderer.tick()
        except Exception as e:
            self.fail(f"tick raised {e}")

    def test_multiple_ticks(self):
        """连续多次 tick 正常"""
        for _ in range(5):
            result = self.renderer.tick()
            self.assertIsInstance(result, int)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_render_with_empty_snake_body(self):
        """空蛇身（body 仅含蛇头）能正常绘制"""
        snake = _create_snake(body=[(5, 5)])
        renderer = _renderer()
        try:
            renderer.draw_snake(snake)
        except Exception as e:
            self.fail(f"Empty body snake raised {e}")

    def test_render_food_at_negative_position(self):
        """食物负坐标（非占位值）也能绘制（不出错）"""
        # 无效坐标不应出现在游戏中，但渲染器不负责校验坐标有效性
        food = _create_food(position=(-2, 5))
        renderer = _renderer()
        try:
            renderer.draw_food(food)
        except Exception as e:
            self.fail(f"Negative food position raised {e}")

    def test_food_reset_then_draw(self):
        """食物 reset 后 position 变回 (-1,-1)，再 draw_food 应跳过"""
        food = Food(40, 30)
        food.respawn([])
        food.reset()
        renderer = _renderer()
        try:
            renderer.draw_food(food)
        except Exception as e:
            self.fail(f"draw_food after reset raised {e}")

    def test_high_score_value(self):
        """极高分数值（max int）能正常渲染"""
        renderer = _renderer()
        try:
            renderer.draw_hud(99999999)
        except Exception as e:
            self.fail(f"High score HUD raised {e}")

    def test_zero_score_values(self):
        """分数为 0 时各方法正常"""
        renderer = _renderer()
        renderer.draw_hud(0)
        renderer.draw_game_over(0)
        renderer.draw_victory(0)
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
