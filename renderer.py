"""
渲染器 (Renderer) 模块

封装所有 Pygame 绘制调用。图层化渲染：背景 -> 网格线 -> 蛇身 -> 食物 -> HUD -> 遮罩。
管理 pygame.time.Clock 实现帧率控制。

使用 pygame._freetype (C 扩展) 进行字体渲染，规避 pygame 2.6.1 中
pygame.font / pygame.freetype 模块间的循环导入问题。
"""

import pygame
import pygame._freetype

from config import (
    CELL_SIZE,
    COLORS,
    HUD_HEIGHT,
    RENDER_FPS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from food import Food
from game import GameState
from snake import Snake


class Renderer:
    """渲染层：封装所有 Pygame 绘制调用，按图层顺序渲染游戏画面。

    Attributes:
        screen: Pygame 窗口 Surface
        font_small: 小号字体 (用于 HUD 和提示文字)
        font_large: 大号字体 (用于得分显示)
        font_title: 标题字体 (用于 GAME OVER / YOU WIN)
        clock: Pygame 帧率控制器
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """初始化渲染器。

        初始化 FreeType 字体引擎，创建三种字号字体和帧率控制时钟。

        Args:
            screen: Pygame 显示 Surface（窗口）
        """
        self.screen = screen

        # 初始化 FreeType (规避 pygame.font 循环导入问题)
        pygame._freetype.init()

        # 创建三种字号字体 (None = 使用内置默认字体)
        self.font_small = pygame._freetype.Font(None, 28)
        self.font_large = pygame._freetype.Font(None, 48)
        self.font_title = pygame._freetype.Font(None, 72)

        self.clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _render_text(
        self,
        font: pygame._freetype.Font,
        text: str,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        """使用 FreeType 字体渲染文字，返回文本 Surface。

        _freetype.Font.render() 返回 (surface, rect) 元组，本方法仅返回 surface。

        Args:
            font: FreeType 字体对象
            text: 要渲染的文字
            color: 文字颜色 (RGB)

        Returns:
            渲染后的文本 Surface
        """
        surface, _ = font.render(text, color)
        return surface

    # ------------------------------------------------------------------
    # 单层绘制方法
    # ------------------------------------------------------------------

    def draw_background(self) -> None:
        """绘制背景：填充背景色并绘制网格线。

        先填充背景色，再绘制横纵网格线（颜色较淡，仅作视觉辅助）。
        """
        self.screen.fill(COLORS.BACKGROUND)

        # 纵向网格线
        for col in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(
                self.screen, COLORS.GRID_LINE, (col, 0), (col, WINDOW_HEIGHT)
            )

        # 横向网格线
        for row in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(
                self.screen, COLORS.GRID_LINE, (0, row), (WINDOW_WIDTH, row)
            )

    def draw_snake(self, snake: Snake, is_boosting: bool = False) -> None:
        """绘制蛇：先绘制蛇身（尾到头），再绘制蛇头以区分颜色。

        蛇身使用 SNAKE_BODY 色，蛇头使用 SNAKE_HEAD 色。
        从 body[1:] 遍历蛇身各节，最后绘制 body[0] 蛇头。

        当 is_boosting=True 时，蛇身使用 BOOST_SNAKE_BODY 色，蛇头使用 BOOST_SNAKE_HEAD 色，
        提供加速状态的视觉反馈。

        Args:
            snake: Snake 实例，提供 body 坐标列表
            is_boosting: 是否处于加速状态，默认 False
        """
        # 加速状态下使用不同颜色
        body_color = COLORS.BOOST_SNAKE_BODY if is_boosting else COLORS.SNAKE_BODY
        head_color = COLORS.BOOST_SNAKE_HEAD if is_boosting else COLORS.SNAKE_HEAD

        # 蛇身（除蛇头外）
        for segment in snake.body[1:]:
            rect = pygame.Rect(
                segment[0] * CELL_SIZE,
                segment[1] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(self.screen, body_color, rect)

        # 蛇头 (body[0])
        if snake.body:
            head_x, head_y = snake.head
            head_rect = pygame.Rect(
                head_x * CELL_SIZE,
                head_y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            pygame.draw.rect(self.screen, head_color, head_rect)

    def draw_food(self, food: Food) -> None:
        """绘制食物：检查占位值 (-1, -1) 后才绘制。

        若 food.position == (-1, -1) 则跳过，不进行绘制。
        正常的食物以 FOOD 色绘制为实心矩形。

        Args:
            food: Food 实例，提供 position 坐标
        """
        if food.position == (-1, -1):
            return

        x, y = food.position
        rect = pygame.Rect(
            x * CELL_SIZE,
            y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(self.screen, COLORS.FOOD, rect)

    def draw_hud(
        self,
        score: int,
        is_boosting: bool = False,
        difficulty_level: int = 0,
        effective_multiplier: float = 1.0,
    ) -> None:
        """绘制 HUD：左侧分数、居中难度信息、右侧 BOOST 文字（条件）。

        先绘制深色半透明背景条（HUD_HEIGHT 高度通栏），
        布局：左 "Score: X" | 中 "Lv.N  Speed Mx" | 右 "BOOST"（条件）。

        Args:
            score: 当前分数值
            is_boosting: 是否处于加速状态，默认 False
            difficulty_level: 当前难度等级编号，默认 0
            effective_multiplier: 当前综合速度倍率，默认 1.0
        """
        # HUD 背景条 (深色，半透明)
        hud_bg = pygame.Surface((WINDOW_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 160))
        self.screen.blit(hud_bg, (0, 0))

        # 分数文字 (左侧对齐，垂直居中)
        score_text = self._render_text(
            self.font_small, f"Score: {score}", COLORS.TEXT
        )
        text_rect = score_text.get_rect()
        text_rect.midleft = (12, HUD_HEIGHT // 2)
        self.screen.blit(score_text, text_rect)

        # 难度信息文字 (居中，垂直居中)
        difficulty_text = self._render_text(
            self.font_small,
            f"Lv.{difficulty_level}  Speed {effective_multiplier:.1f}x",
            COLORS.TEXT,
        )
        diff_rect = difficulty_text.get_rect()
        diff_rect.center = (WINDOW_WIDTH // 2, HUD_HEIGHT // 2)
        self.screen.blit(difficulty_text, diff_rect)

        # 加速状态指示文字 (右侧对齐，垂直居中)
        if is_boosting:
            boost_text = self._render_text(
                self.font_small, "BOOST", COLORS.BOOST_HUD_TEXT
            )
            boost_rect = boost_text.get_rect()
            boost_rect.midright = (WINDOW_WIDTH - 12, HUD_HEIGHT // 2)
            self.screen.blit(boost_text, boost_rect)

    def draw_game_over(self, score: int) -> None:
        """绘制游戏结束遮罩：半透明背景 + GAME OVER 文字 + 最终得分 + 操作提示。

        Args:
            score: 最终得分
        """
        self._draw_overlay()

        # GAME OVER 标题 (红色)
        title = self._render_text(
            self.font_title, "GAME OVER", (255, 50, 50)
        )
        title_rect = title.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 70)
        )
        self.screen.blit(title, title_rect)

        # 最终得分
        score_text = self._render_text(
            self.font_large, f"Score: {score}", COLORS.TEXT
        )
        score_rect = score_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
        self.screen.blit(score_text, score_rect)

        # 操作提示
        hint = self._render_text(
            self.font_small,
            "Press R to Restart  |  Press Q to Quit",
            COLORS.TEXT,
        )
        hint_rect = hint.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70)
        )
        self.screen.blit(hint, hint_rect)

    def draw_victory(self, score: int) -> None:
        """绘制胜利遮罩：半透明背景 + YOU WIN 文字 + 最终得分 + 操作提示。

        Args:
            score: 最终得分
        """
        self._draw_overlay()

        # YOU WIN 标题 (绿色)
        title = self._render_text(
            self.font_title, "YOU WIN!", (50, 255, 50)
        )
        title_rect = title.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 70)
        )
        self.screen.blit(title, title_rect)

        # 最终得分
        score_text = self._render_text(
            self.font_large, f"Score: {score}", COLORS.TEXT
        )
        score_rect = score_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
        self.screen.blit(score_text, score_rect)

        # 操作提示
        hint = self._render_text(
            self.font_small,
            "Press R to Restart  |  Press Q to Quit",
            COLORS.TEXT,
        )
        hint_rect = hint.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70)
        )
        self.screen.blit(hint, hint_rect)

    def _draw_overlay(self) -> None:
        """绘制半透明遮罩 (内部方法)。

        创建全屏半透明 Surface 并 blit 到屏幕上。
        """
        overlay = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill(COLORS.OVERLAY_BG)
        self.screen.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    # 帧合成方法
    # ------------------------------------------------------------------

    def draw_frame(
        self,
        snake: Snake,
        food: Food,
        score: int,
        state: GameState,
        is_boosting: bool = False,
        difficulty_level: int = 0,
        effective_multiplier: float = 1.0,
    ) -> None:
        """按图层顺序合成并绘制完整帧。

        绘制顺序：
        1. draw_background   — 背景色 + 网格线
        2. draw_snake        — 蛇身（尾到头） + 蛇头
        3. draw_food         — 食物（跳过占位）
        4. draw_hud          — 顶部 HUD（分数 + 难度 + BOOST）
        5. 条件遮罩          — 根据 GameState 叠加 game_over / victory

        Args:
            snake: Snake 实例
            food: Food 实例
            score: 当前分数
            state: 游戏状态枚举 (RUNNING / GAME_OVER / VICTORY)
            is_boosting: 是否处于加速状态，默认 False
            difficulty_level: 当前难度等级编号，默认 0
            effective_multiplier: 当前综合速度倍率，默认 1.0
        """
        self.draw_background()
        self.draw_snake(snake, is_boosting)
        self.draw_food(food)
        self.draw_hud(score, is_boosting, difficulty_level, effective_multiplier)

        if state == GameState.GAME_OVER:
            self.draw_game_over(score)
        elif state == GameState.VICTORY:
            self.draw_victory(score)
        # RUNNING 状态不叠加任何遮罩

    # ------------------------------------------------------------------
    # 帧率控制
    # ------------------------------------------------------------------

    def tick(self) -> int:
        """控制帧率：调用 clock.tick(RENDER_FPS) 限制每秒帧数。

        渲染帧率固定为 RENDER_FPS (默认 60 fps)，
        与逻辑 tick 间隔 (BASE_TICK_INTERVAL) 解耦。

        Returns:
            自上次 tick 以来经过的时间（毫秒）
        """
        return self.clock.tick(RENDER_FPS)
