"""
游戏常量配置模块

定义窗口尺寸、网格参数、游戏参数、加速配置、窗口标题、HUD 高度、
GameState 游戏状态枚举及 COLORS 颜色类。
"""

import logging
from enum import Enum, auto

import pygame

# 模块级 logger
_logger = logging.getLogger(__name__)


# =============================================================================
# 游戏状态枚举
# =============================================================================


class GameState(Enum):
    """游戏状态枚举：RUNNING / GAME_OVER / VICTORY"""

    RUNNING = auto()
    """活跃游戏中：蛇移动、输入接受、碰撞检测"""

    GAME_OVER = auto()
    """游戏结束：蛇撞墙或自撞，移动冻结，按 R 重新开始"""

    VICTORY = auto()
    """胜利：棋盘所有格子被蛇身占满，按 R 重新开始"""

# =============================================================================
# 窗口尺寸
# =============================================================================
WINDOW_WIDTH: int = 800
WINDOW_HEIGHT: int = 600

# =============================================================================
# 网格参数 (像素对齐: 800/20=40 列, 600/20=30 行)
# =============================================================================
CELL_SIZE: int = 20
GRID_COLS: int = 40
GRID_ROWS: int = 30

# =============================================================================
# 游戏参数
# =============================================================================
FPS: int = 10  # 保留向后兼容：原有逻辑 tick FPS
INITIAL_SNAKE_LENGTH: int = 3
SCORE_PER_FOOD: int = 10

# =============================================================================
# 加速配置 (Snake Speed Boost)
# =============================================================================

# 加速键绑定 (Pygame 键码)
BOOST_KEY: int = pygame.K_SPACE

# 加速倍率 (默认 2x，范围 [1.0, MAX_BOOST_MULTIPLIER])
BOOST_SPEED_MULTIPLIER: float = 2.0

# 加速倍率上限
MAX_BOOST_MULTIPLIER: float = 5.0

# 基准逻辑 tick 间隔 (ms)，原 FPS=10 对应 1000/10=100ms
BASE_TICK_INTERVAL: int = 100

# 渲染帧率 (固定 60 fps，与逻辑 tick 解耦)
RENDER_FPS: int = 60

# 平滑加速过渡时长 (秒)，0 表示瞬时切换
BOOST_TRANSITION_SECONDS: float = 0.15

# 单帧最大逻辑追赶步数 (防止 spiral-of-death)
MAX_CATCHUP_STEPS: int = 5

# =============================================================================
# 窗口标题
# =============================================================================
WINDOW_TITLE: str = "贪吃蛇"

# =============================================================================
# HUD 信息显示区域高度 (像素)
# =============================================================================
HUD_HEIGHT: int = 40

# =============================================================================
# 颜色定义
# =============================================================================


class COLORS:
    """游戏中使用的全部颜色常量 (RGB / RGBA)"""

    BACKGROUND: tuple[int, int, int] = (10, 10, 30)
    SNAKE_BODY: tuple[int, int, int] = (0, 200, 0)
    SNAKE_HEAD: tuple[int, int, int] = (50, 255, 50)
    FOOD: tuple[int, int, int] = (255, 50, 50)
    GRID_LINE: tuple[int, int, int] = (40, 40, 60)
    TEXT: tuple[int, int, int] = (255, 255, 255)
    OVERLAY_BG: tuple[int, int, int, int] = (0, 0, 0, 180)

    # 加速状态视觉指示颜色
    BOOST_SNAKE_BODY: tuple[int, int, int] = (255, 140, 0)   # 橙色蛇身
    BOOST_SNAKE_HEAD: tuple[int, int, int] = (255, 215, 50)  # 金色蛇头
    BOOST_HUD_TEXT: tuple[int, int, int] = (255, 200, 50)    # 亮金色 HUD 文字


# =============================================================================
# 难度配置 (Difficulty Scaling)
# =============================================================================

# 每多少分提升一级难度
SCORE_THRESHOLD_INTERVAL: int = 50

# 每级难度增加的倍率值
DIFFICULTY_INCREMENT: float = 0.1

# tick 间隔硬下限 (ms)，tick_interval 计算结果的绝对最小值
MIN_TICK_INTERVAL: int = 20

# 难度倍率上限，由 BASE_TICK_INTERVAL / MIN_TICK_INTERVAL - 1.0 自动推导 (默认 4.0)
MAX_DIFFICULTY_MULTIPLIER: float = 4.0

# =============================================================================
# 配置校验 (模块导入时自动执行)
# =============================================================================


def _validate_boost_config() -> None:
    """模块加载时自动校验加速配置常量。

    对越界值进行 clamp 并记录 logging.WARNING，确保运行时参数始终在安全范围内。
    校验顺序考虑了常量间的依赖关系（如 BOOST_SPEED_MULTIPLIER 依赖 MAX_BOOST_MULTIPLIER）。
    """
    global BOOST_SPEED_MULTIPLIER, MAX_BOOST_MULTIPLIER, BASE_TICK_INTERVAL
    global RENDER_FPS, BOOST_TRANSITION_SECONDS, MAX_CATCHUP_STEPS, BOOST_KEY

    # 1. MAX_BOOST_MULTIPLIER (需先校验，后续 BOOST_SPEED_MULTIPLIER 依赖此项)
    if MAX_BOOST_MULTIPLIER <= 0:
        _logger.warning(
            "CFG-001: MAX_BOOST_MULTIPLIER=%.1f <= 0, reset to 5.0",
            MAX_BOOST_MULTIPLIER,
        )
        MAX_BOOST_MULTIPLIER = 5.0

    # 2. BOOST_SPEED_MULTIPLIER: 必须在 [1.0, MAX_BOOST_MULTIPLIER] 区间
    if BOOST_SPEED_MULTIPLIER < 1.0:
        _logger.warning(
            "CFG-001: BOOST_SPEED_MULTIPLIER=%.1f < 1.0, clamped to 1.0",
            BOOST_SPEED_MULTIPLIER,
        )
        BOOST_SPEED_MULTIPLIER = 1.0
    elif BOOST_SPEED_MULTIPLIER > MAX_BOOST_MULTIPLIER:
        _logger.warning(
            "CFG-001: BOOST_SPEED_MULTIPLIER=%.1f > MAX_BOOST_MULTIPLIER=%.1f, clamped to %.1f",
            BOOST_SPEED_MULTIPLIER,
            MAX_BOOST_MULTIPLIER,
            MAX_BOOST_MULTIPLIER,
        )
        BOOST_SPEED_MULTIPLIER = MAX_BOOST_MULTIPLIER

    # 3. BASE_TICK_INTERVAL: 不低于 MIN_TICK_INTERVAL
    if BASE_TICK_INTERVAL < MIN_TICK_INTERVAL:
        _logger.warning(
            "CFG-003: BASE_TICK_INTERVAL=%d < %d, reset to 100",
            BASE_TICK_INTERVAL, MIN_TICK_INTERVAL,
        )
        BASE_TICK_INTERVAL = 100

    # 4. RENDER_FPS: 必须 > 0
    if RENDER_FPS <= 0:
        _logger.warning(
            "RENDER_FPS=%d <= 0, reset to 60",
            RENDER_FPS,
        )
        RENDER_FPS = 60

    # 5. BOOST_TRANSITION_SECONDS: >= 0 (可为 0 表示无过渡)
    if BOOST_TRANSITION_SECONDS < 0:
        _logger.warning(
            "BOOST_TRANSITION_SECONDS=%.3f < 0, clamped to 0.0 (instant transition)",
            BOOST_TRANSITION_SECONDS,
        )
        BOOST_TRANSITION_SECONDS = 0.0

    # 6. MAX_CATCHUP_STEPS: >= 1
    if MAX_CATCHUP_STEPS < 1:
        _logger.warning(
            "MAX_CATCHUP_STEPS=%d < 1, reset to 5",
            MAX_CATCHUP_STEPS,
        )
        MAX_CATCHUP_STEPS = 5

    # 7. BOOST_KEY: 有效 Pygame 键码 (正整数)
    try:
        if not isinstance(BOOST_KEY, int) or BOOST_KEY < 0:
            _logger.warning(
                "CFG-002: BOOST_KEY=%s invalid keycode, fallback to pygame.K_SPACE",
                repr(BOOST_KEY),
            )
            BOOST_KEY = pygame.K_SPACE
    except Exception:
        _logger.warning(
            "CFG-002: BOOST_KEY validation failed, fallback to pygame.K_SPACE",
        )
        BOOST_KEY = pygame.K_SPACE

    # 8. 调用难度配置校验
    _validate_difficulty_config()


def _validate_difficulty_config() -> None:
    """校验难度配置常量，对越界值自动修正并输出 WARNING。

    校验顺序：SCORE_THRESHOLD_INTERVAL -> DIFFICULTY_INCREMENT ->
    MIN_TICK_INTERVAL -> MAX_DIFFICULTY_MULTIPLIER（自动推导）。
    在 _validate_boost_config() 末尾调用，确保导入时自动执行。
    """
    global SCORE_THRESHOLD_INTERVAL, DIFFICULTY_INCREMENT, MIN_TICK_INTERVAL
    global MAX_DIFFICULTY_MULTIPLIER

    # 1. SCORE_THRESHOLD_INTERVAL: >= 1
    if SCORE_THRESHOLD_INTERVAL < 1:
        _logger.warning(
            "CFG-004: SCORE_THRESHOLD_INTERVAL=%d < 1, reset to 50",
            SCORE_THRESHOLD_INTERVAL,
        )
        SCORE_THRESHOLD_INTERVAL = 50

    # 2. DIFFICULTY_INCREMENT: >= 0.0
    if DIFFICULTY_INCREMENT < 0:
        _logger.warning(
            "CFG-005: DIFFICULTY_INCREMENT=%.2f < 0, reset to 0.1",
            DIFFICULTY_INCREMENT,
        )
        DIFFICULTY_INCREMENT = 0.1

    # 3. MIN_TICK_INTERVAL: 0 < MIN_TICK_INTERVAL <= BASE_TICK_INTERVAL
    if MIN_TICK_INTERVAL <= 0 or MIN_TICK_INTERVAL > BASE_TICK_INTERVAL:
        _logger.warning(
            "CFG-006: MIN_TICK_INTERVAL=%d out of range (0, %d], reset to 20",
            MIN_TICK_INTERVAL, BASE_TICK_INTERVAL,
        )
        MIN_TICK_INTERVAL = 20

    # 4. MAX_DIFFICULTY_MULTIPLIER: 自动推导
    # = (BASE_TICK_INTERVAL / MIN_TICK_INTERVAL) - 1.0
    # 保证 1.0 + MAX_DIFFICULTY_MULTIPLIER + boost_extra 对应 tick >= MIN_TICK_INTERVAL
    derived_max = (BASE_TICK_INTERVAL / MIN_TICK_INTERVAL) - 1.0
    if derived_max <= 0:
        _logger.warning(
            "MAX_DIFFICULTY_MULTIPLIER derived=%.1f <= 0 "
            "(BASE=%d MIN=%d), clamp to 0.0",
            derived_max, BASE_TICK_INTERVAL, MIN_TICK_INTERVAL,
        )
        MAX_DIFFICULTY_MULTIPLIER = 0.0
    else:
        MAX_DIFFICULTY_MULTIPLIER = derived_max


# 模块导入时自动执行配置校验
_validate_boost_config()
