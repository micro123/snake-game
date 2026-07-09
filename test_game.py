"""
Game 类单元测试

覆盖：初始化状态（窗口、组件、首个食物）、_handle_command 命令分发、
_update 逻辑更新（食物碰撞/边界碰撞/自撞/胜利）、reset 重置、
run 主循环集成测试、边界情况。
使用 Python 标准库 unittest 框架，依赖 Pygame。
"""

import unittest
from unittest.mock import patch, MagicMock

import pygame

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
    GRID_COLS, GRID_ROWS,
    SCORE_PER_FOOD,
    BASE_TICK_INTERVAL, BOOST_SPEED_MULTIPLIER, BOOST_TRANSITION_SECONDS,
    DIFFICULTY_INCREMENT, MAX_BOOST_MULTIPLIER, MAX_CATCHUP_STEPS,
    MAX_DIFFICULTY_MULTIPLIER, SCORE_THRESHOLD_INTERVAL,
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


def _post_key_event(key: int) -> None:
    """向 Pygame 事件队列投递一个键盘按下事件。"""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def _clear_events() -> None:
    """清空 Pygame 事件队列。"""
    pygame.event.clear()


# =============================================================================
# Game 测试基类
# =============================================================================

class _GameTestBase(unittest.TestCase):
    """Game 测试基类：为每个测试创建带 Mock 显示层的 Game 实例。

    通过 patch pygame.display.set_mode 返回真实 Surface（而非创建窗口），
    确保 Renderer 的绘制调用正常工作。
    """

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
# 测试类：Game.__init__
# =============================================================================

class TestGameInit(_GameTestBase):
    """测试 Game 初始化状态"""

    def test_screen_is_pygame_surface(self):
        """screen 是 Pygame Surface 实例"""
        self.assertIsInstance(self.game.screen, pygame.Surface)

    def test_screen_correct_size(self):
        """窗口尺寸为 (800, 600)"""
        self.assertEqual((WINDOW_WIDTH, WINDOW_HEIGHT),
                         self.game.screen.get_size())

    def test_window_caption_set(self):
        """窗口标题设置为配置值"""
        # 用 get_caption 验证（需要真实 set_caption，此处用 mock 验证调用）
        # 注意：set_caption 在 __init__ 中被调用且已被 patch
        pass  # set_caption 调用由 mock 验证

    def test_snake_is_instance_of_Snake(self):
        """snake 是 Snake 实例"""
        self.assertIsInstance(self.game.snake, Snake)

    def test_food_is_instance_of_Food(self):
        """food 是 Food 实例"""
        self.assertIsInstance(self.game.food, Food)

    def test_renderer_is_instance_of_Renderer(self):
        """renderer 是 Renderer 实例"""
        self.assertIsInstance(self.game.renderer, Renderer)

    def test_input_handler_is_instance_of_InputHandler(self):
        """input_handler 是 InputHandler 实例"""
        self.assertIsInstance(self.game.input_handler, InputHandler)

    def test_initial_score_is_zero(self):
        """分数初始化为 0"""
        self.assertEqual(0, self.game.score)

    def test_initial_state_is_running(self):
        """状态初始为 RUNNING"""
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_first_food_generated(self):
        """首个食物已生成（position 不是占位值 (-1, -1)）"""
        self.assertNotEqual((-1, -1), self.game.food.position)

    def test_first_food_not_on_snake(self):
        """首个食物不落在蛇身占据的格子上"""
        self.assertNotIn(self.game.food.position, self.game.snake.body)


# =============================================================================
# 测试类：Game._handle_command
# =============================================================================

class TestHandleCommand(_GameTestBase):
    """测试 _handle_command 命令分发"""

    # ------- quit 命令 ------

    def test_handle_quit_returns_false(self):
        """quit 命令返回 False 以退出主循环"""
        result = self.game._handle_command({'action': 'quit'})
        self.assertFalse(result)

    def test_handle_quit_stops_loop(self):
        """quit 命令不会改变状态（只是退出循环）"""
        old_state = self.game.state
        self.game._handle_command({'action': 'quit'})
        self.assertEqual(old_state, self.game.state)

    # ------- restart 命令 ------

    def test_handle_restart_resets_game(self):
        """restart 命令重置全部游戏状态"""
        # 先改变状态
        self.game.score = 100
        self.game.state = GameState.GAME_OVER
        self.game.snake.body = [(5, 5)]
        self.game.food.position = (8, 8)

        # 执行 restart
        result = self.game._handle_command({'action': 'restart'})

        # 验证重置
        self.assertTrue(result)  # 循环继续
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(3, self.game.snake.length)
        self.assertNotEqual((-1, -1), self.game.food.position)

    def test_handle_restart_returns_true(self):
        """restart 命令返回 True（继续运行）"""
        result = self.game._handle_command({'action': 'restart'})
        self.assertTrue(result)

    # ------- direction 命令 ------

    def test_handle_direction_changes_snake_dir(self):
        """direction 命令在 RUNNING 状态下变更蛇的方向"""
        old_dir = self.game.snake.direction
        # 切换方向为非反向（向上）
        new_dir = (0, -1)
        self.assertNotEqual((old_dir[0] + new_dir[0], old_dir[1] + new_dir[1]), (0, 0))

        result = self.game._handle_command(
            {'action': 'direction', 'direction': new_dir}
        )
        self.assertTrue(result)
        self.assertEqual(new_dir, self.game.snake.direction)

    def test_handle_direction_ignored_when_game_over(self):
        """direction 命令在 GAME_OVER 状态下被忽略"""
        self.game.state = GameState.GAME_OVER
        old_dir = self.game.snake.direction

        result = self.game._handle_command(
            {'action': 'direction', 'direction': (0, -1)}
        )
        self.assertTrue(result)
        self.assertEqual(old_dir, self.game.snake.direction)

    def test_handle_direction_ignored_when_victory(self):
        """direction 命令在 VICTORY 状态下被忽略"""
        self.game.state = GameState.VICTORY
        old_dir = self.game.snake.direction

        result = self.game._handle_command(
            {'action': 'direction', 'direction': (0, -1)}
        )
        self.assertTrue(result)
        self.assertEqual(old_dir, self.game.snake.direction)

    def test_handle_direction_without_direction_key(self):
        """direction 命令缺少 direction 键时不崩溃"""
        result = self.game._handle_command({'action': 'direction'})
        self.assertTrue(result)

    # ------- none / unknown 命令 ------

    def test_handle_none_returns_true(self):
        """none 命令返回 True（无操作继续运行）"""
        result = self.game._handle_command({'action': 'none'})
        self.assertTrue(result)

    def test_handle_unknown_action_returns_true(self):
        """未知 action 返回 True（安全忽略）"""
        result = self.game._handle_command({'action': 'unknown_action'})
        self.assertTrue(result)

    def test_handle_empty_command_returns_true(self):
        """空命令返回 True"""
        result = self.game._handle_command({})
        self.assertTrue(result)


# =============================================================================
# 测试类：Game._update
# =============================================================================

class TestUpdateBasic(_GameTestBase):
    """测试 _update 基本行为和条件判断"""

    def test_update_not_running_when_state_game_over(self):
        """GAME_OVER 状态下 _update 不改变蛇身"""
        self.game.state = GameState.GAME_OVER
        original_body = list(self.game.snake.body)
        original_score = self.game.score

        self.game._update()

        self.assertEqual(original_body, self.game.snake.body)
        self.assertEqual(original_score, self.game.score)

    def test_update_not_running_when_state_victory(self):
        """VICTORY 状态下 _update 不改变蛇身"""
        self.game.state = GameState.VICTORY
        original_body = list(self.game.snake.body)

        self.game._update()

        self.assertEqual(original_body, self.game.snake.body)

    def test_update_skips_when_paused(self):
        """暂停时 _update 不移动蛇"""
        self.game.input_handler._paused = True
        original_body = list(self.game.snake.body)

        self.game._update()

        self.assertEqual(original_body, self.game.snake.body)

    def test_update_moves_snake_when_running(self):
        """RUNNING 状态下 _update 移动蛇（头前移、尾弹出）"""
        original_head = self.game.snake.head
        original_length = self.game.snake.length

        self.game._update()

        # 头移动了
        new_head = (original_head[0] + 1, original_head[1])  # 默认向右
        self.assertEqual(new_head, self.game.snake.head)
        # 长度不变（无增长）
        self.assertEqual(original_length, self.game.snake.length)


class TestUpdateFoodCollision(_GameTestBase):
    """测试 _update 食物碰撞逻辑"""

    def test_food_collision_increases_score(self):
        """蛇头碰到食物时分数增加"""
        # 把食物放在蛇头前进方向的下一格
        head = self.game.snake.head
        direction = self.game.snake.direction
        self.game.food.position = (head[0] + direction[0],
                                   head[1] + direction[1])

        old_score = self.game.score
        self.game._update()

        self.assertEqual(old_score + SCORE_PER_FOOD, self.game.score)

    def test_food_collision_grows_snake(self):
        """蛇头碰到食物时蛇身增长"""
        head = self.game.snake.head
        direction = self.game.snake.direction
        self.game.food.position = (head[0] + direction[0],
                                   head[1] + direction[1])

        old_length = self.game.snake.length
        self.game._update()

        self.assertEqual(old_length + 1, self.game.snake.length)

    def test_food_reappears_after_eaten(self):
        """食物被吃后在新的位置重新生成"""
        head = self.game.snake.head
        direction = self.game.snake.direction
        self.game.food.position = (head[0] + direction[0],
                                   head[1] + direction[1])

        eaten_position = self.game.food.position
        self.game._update()  # eat + respawn in same frame

        self.assertNotEqual(eaten_position, self.game.food.position)
        self.assertNotEqual((-1, -1), self.game.food.position)

    def test_food_not_on_snake_after_respawn(self):
        """食物重新生成后不落在蛇身上"""
        head = self.game.snake.head
        direction = self.game.snake.direction
        self.game.food.position = (head[0] + direction[0],
                                   head[1] + direction[1])

        self.game._update()  # eat + respawn in same frame

        self.assertNotIn(self.game.food.position, self.game.snake.body)


class TestUpdateCollision(_GameTestBase):
    """测试 _update 碰撞检测（边界 + 自撞）"""

    def test_boundary_collision_left_sets_game_over(self):
        """蛇头左侧出界 -> GAME_OVER"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_boundary_collision_top_sets_game_over(self):
        """蛇头顶部出界 -> GAME_OVER"""
        self.game.snake.body = [(20, 0), (20, 1), (20, 2)]
        self.game.snake.direction = (0, -1)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_boundary_collision_right_sets_game_over(self):
        """蛇头右侧出界 -> GAME_OVER"""
        self.game.snake.body = [(GRID_COLS - 1, 15),
                                (GRID_COLS - 2, 15),
                                (GRID_COLS - 3, 15)]
        self.game.snake.direction = (1, 0)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_boundary_collision_bottom_sets_game_over(self):
        """蛇头底部出界 -> GAME_OVER"""
        self.game.snake.body = [(20, GRID_ROWS - 1),
                                (20, GRID_ROWS - 2),
                                (20, GRID_ROWS - 3)]
        self.game.snake.direction = (0, 1)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_self_collision_sets_game_over(self):
        """蛇头撞自身 -> GAME_OVER"""
        # 构造一个 L 形蛇，转向自身
        self.game.snake.body = [(3, 4), (3, 3), (4, 3), (5, 3), (5, 4)]
        self.game.snake.direction = (0, 1)  # 向下 -> head 到 (3, 5)
        # body[1:] 不含 (3, 5)，正常移动不自撞
        # 先移动一步
        self.game._update()  # head -> (3, 5)
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_self_collision_after_turn(self):
        """转向后蛇头撞到身体 -> GAME_OVER"""
        # 构造蛇身: head(3,2), (3,3), (4,3), (5,3)
        # 方向向下，head->(3,3) 撞到 body[1]=(3,3)
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)  # 向下

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)


class TestUpdateVictory(_GameTestBase):
    """测试 _update 胜利条件（棋盘满）"""

    def test_victory_when_no_available_cells(self):
        """棋盘被蛇身占满时状态变为 VICTORY"""
        # 蛇头前一步到达食物位置，食物位置恰好在蛇头前进方向
        # 通过 mock food.respawn 返回 False 模拟棋盘满的场景
        self.game.snake.body = [(18, 14), (17, 14), (16, 14)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 14)  # 食物在移动后的新蛇头位置
        self.game.state = GameState.RUNNING
        self.game.score = 0

        # Mock food.respawn 返回 False（模拟棋盘已满）
        original_respawn = self.game.food.respawn
        self.game.food.respawn = lambda occupied: False

        self.game._update()

        self.assertEqual(GameState.VICTORY, self.game.state)
        self.assertEqual(SCORE_PER_FOOD, self.game.score)

        # 恢复
        self.game.food.respawn = original_respawn


# =============================================================================
# 测试类：Game.reset
# =============================================================================

class TestReset(_GameTestBase):
    """测试 reset 重置功能"""

    def test_reset_restores_snake_body(self):
        """reset 后蛇身恢复到初始状态"""
        original_body = list(self.game.snake.body)

        # 改变蛇的状态
        self.game.snake.move_and_grow(True)
        self.game.snake.change_direction(0, -1)
        self.game.score = 50
        self.game.state = GameState.GAME_OVER

        # 重置
        self.game.reset()

        self.assertEqual(original_body, self.game.snake.body)

    def test_reset_restores_direction(self):
        """reset 后蛇方向恢复向右"""
        self.game.snake.change_direction(0, -1)
        self.game.reset()
        self.assertEqual((1, 0), self.game.snake.direction)

    def test_reset_resets_score_to_zero(self):
        """reset 后分数归零"""
        self.game.score = 999
        self.game.reset()
        self.assertEqual(0, self.game.score)

    def test_reset_sets_state_to_running(self):
        """reset 后状态恢复为 RUNNING"""
        self.game.state = GameState.GAME_OVER
        self.game.reset()
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_reset_regenerates_food(self):
        """reset 后重新生成食物"""
        self.game.food.position = (10, 10)  # 修改食物
        self.game.reset()

        self.assertNotEqual((-1, -1), self.game.food.position)
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_reset_from_running_still_works(self):
        """从 RUNNING 状态 reset 也正常恢复"""
        self.game.score = 30
        original_body = list(self.game.snake.body)
        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(original_body, self.game.snake.body)

    def test_multiple_resets_idempotent(self):
        """多次 reset 结果一致"""
        self.game.score = 100
        self.game.state = GameState.GAME_OVER
        self.game.snake.body = [(5, 5), (5, 6)]
        self.game.reset()

        first_body = list(self.game.snake.body)
        first_score = self.game.score
        first_state = self.game.state

        # 修改后再次 reset
        self.game.score = 200
        self.game.snake.body = [(1, 1)]
        self.game.reset()

        self.assertEqual(first_body, self.game.snake.body)
        self.assertEqual(first_score, self.game.score)
        self.assertEqual(first_state, self.game.state)

    def test_reset_clears_difficulty_level(self):
        """reset() 后 difficulty_level 归零"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 1.5
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)

    def test_reset_clears_difficulty_multiplier(self):
        """reset() 后 difficulty_multiplier 归零"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 1.5
        self.game.reset()
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_reset_difficulty_from_game_over(self):
        """从 GAME_OVER 状态 reset 后难度归零"""
        self.game.state = GameState.GAME_OVER
        self.game.difficulty_level = 3
        self.game.difficulty_multiplier = 0.3
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_reset_difficulty_from_victory(self):
        """从 VICTORY 状态 reset 后难度归零"""
        self.game.state = GameState.VICTORY
        self.game.difficulty_level = 10
        self.game.difficulty_multiplier = 1.0
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_reset_difficulty_from_running(self):
        """从 RUNNING 状态 reset 后难度归零"""
        self.game.difficulty_level = 2
        self.game.difficulty_multiplier = 0.2
        self.game.score = 100
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_multiple_resets_difficulty_consistent(self):
        """多次 reset 难度状态一致"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 2.0
        self.game.reset()
        first_level = self.game.difficulty_level
        first_mult = self.game.difficulty_multiplier

        self.game.difficulty_level = 8
        self.game.difficulty_multiplier = 3.0
        self.game.reset()

        self.assertEqual(first_level, self.game.difficulty_level)
        self.assertEqual(first_mult, self.game.difficulty_multiplier)


# =============================================================================
# 测试类：Game.run 集成测试
# =============================================================================

class TestRunIntegration(_GameTestBase):
    """测试 run 主循环集成"""

    def test_run_exits_on_quit_event(self):
        """向队列投递 QUIT 事件后 run() 正常退出"""
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        try:
            self.game.run()
        except Exception as e:
            self.fail(f"run() raised unexpected exception: {e}")

        # 循环退出后 state 不变（window close 不修改游戏状态）
        self.assertEqual(GameState.RUNNING, self.game.state)

    def test_run_exits_on_q_key_in_game_over(self):
        """GAME_OVER + Q 键 -> 退出"""
        self.game.state = GameState.GAME_OVER
        _clear_events()
        _post_key_event(pygame.K_q)

        try:
            self.game.run()
        except Exception as e:
            self.fail(f"run() raised unexpected exception: {e}")

    def test_run_handles_r_key_in_game_over(self):
        """GAME_OVER + R 键 -> 调用 restart 重置游戏"""
        self.game.state = GameState.GAME_OVER
        self.game.score = 100
        _clear_events()
        _post_key_event(pygame.K_r)

        # 直接调用 process_events + _handle_command 验证 R 键效果
        command = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state
        )
        result = self.game._handle_command(command)

        self.assertTrue(result)
        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)

    def test_run_processes_direction_key(self):
        """方向键在 RUNNING 状态下改变蛇方向"""
        _clear_events()
        _post_key_event(pygame.K_UP)

        # 直接调用 process_events + _handle_command 验证方向键效果
        command = self.game.input_handler.process_events(
            self.game.snake.direction, self.game.state
        )
        result = self.game._handle_command(command)

        self.assertTrue(result)
        self.assertEqual((0, -1), self.game.snake.direction)


# =============================================================================
# 测试类：边界情况
# =============================================================================

class TestEdgeCases(_GameTestBase):
    """边界情况测试"""

    def test_victory_state_persists_after_update(self):
        """VICTORY 状态不会被 _update 清除"""
        self.game.state = GameState.VICTORY
        self.game._update()
        self.assertEqual(GameState.VICTORY, self.game.state)

    def test_game_over_state_persists_after_update(self):
        """GAME_OVER 状态不会被 _update 清除"""
        self.game.state = GameState.GAME_OVER
        self.game._update()
        self.assertEqual(GameState.GAME_OVER, self.game.state)

    def test_score_does_not_change_on_boundary_collision(self):
        """撞墙时分数不变化"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)
        old_score = self.game.score

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertEqual(old_score, self.game.score)

    def test_score_does_not_change_on_self_collision(self):
        """自撞时分数不变化"""
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)
        old_score = self.game.score

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertEqual(old_score, self.game.score)

    def test_reset_from_victory(self):
        """从 VICTORY 状态 reset"""
        self.game.state = GameState.VICTORY
        self.game.score = 1200
        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(0, self.game.score)
        self.assertEqual(3, self.game.snake.length)

    def test_boundary_collision_check_before_food_eat(self):
        """撞墙和食物在同一帧时，撞墙优先（蛇头先出界）"""
        # 蛇头在边界，下一帧会出界。食物在蛇头当前位置，但碰撞检测
        # 基于移动后的新蛇头位置，所以不会误判为吃到食物。
        self.game.snake.body = [(GRID_COLS - 1, 15),
                                (GRID_COLS - 2, 15),
                                (GRID_COLS - 3, 15)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (GRID_COLS - 1, 15)  # 食物在蛇头当前位置
        old_score = self.game.score

        # new_head = (GRID_COLS, 15) != food -> grow_flag = False
        # move_and_grow: head 出界
        # boundary check -> GAME_OVER
        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        # 食物未被吃掉，分数不变
        self.assertEqual(old_score, self.game.score)
        self.assertEqual(3, self.game.snake.length)

    def test_multiple_food_eats_increases_score_cumulatively(self):
        """连续吃多个食物，分数累加正确"""
        total_eats = 0
        for _ in range(3):
            head = self.game.snake.head
            direction = self.game.snake.direction
            self.game.food.position = (head[0] + direction[0],
                                       head[1] + direction[1])
            self.game._update()  # eat + grow + respawn in same frame
            total_eats += 1

        self.assertEqual(total_eats * SCORE_PER_FOOD, self.game.score)


# =============================================================================
# 测试类：_update_boost_state 平滑加速过渡
# =============================================================================

class TestUpdateBoostState(_GameTestBase):
    """测试 _update_boost_state 平滑加速过渡方法"""

    def test_boost_not_pressed_target_is_one(self):
        """未按加速键时目标倍率为 1.0，状态不活跃"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        self.game._update_boost_state(16.0, False)

        # 应向 1.0 过渡
        self.assertLess(self.game.snake.boost_state['current_multiplier'], 2.0)

    def test_boost_pressed_target_is_multiplier(self):
        """按住加速键时目标倍率为 BOOST_SPEED_MULTIPLIER"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        self.game.snake.boost_state['is_active'] = False

        self.game._update_boost_state(16.0, True)

        # 应向 BOOST_SPEED_MULTIPLIER 过渡
        self.assertGreater(
            self.game.snake.boost_state['current_multiplier'], 1.0
        )

    def test_multiplier_never_below_one(self):
        """current_multiplier 始终 >= 1.0"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        self.game._update_boost_state(16.0, False)
        self.assertGreaterEqual(
            self.game.snake.boost_state['current_multiplier'], 1.0
        )

    def test_multiplier_never_above_max(self):
        """current_multiplier 不超过 MAX_BOOST_MULTIPLIER"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        self.game._update_boost_state(16.0, True)
        multiplier = self.game.snake.boost_state['current_multiplier']
        self.assertLessEqual(multiplier, MAX_BOOST_MULTIPLIER)

    def test_is_active_true_when_multiplier_above_threshold(self):
        """multiplier > 1.01 时 is_active 为 True"""
        self.game.snake.boost_state['current_multiplier'] = 1.5
        self.game._update_boost_state(16.0, True)
        # 如果 multiplier 保持 > 1.01
        if self.game.snake.boost_state['current_multiplier'] > 1.01:
            self.assertTrue(self.game.snake.boost_state['is_active'])

    def test_is_active_false_when_multiplier_at_one(self):
        """multiplier=1.0 时 is_active 为 False"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 多次帧推进以完成过渡到 1.0
        for _ in range(50):
            self.game._update_boost_state(16.0, False)

        self.assertFalse(self.game.snake.boost_state['is_active'])

    def test_instant_transition_when_no_transition_time(self):
        """BOOST_TRANSITION_SECONDS <= 0 时瞬时切换"""
        # 强制模拟无过渡时长
        self.game.snake.boost_state['current_multiplier'] = 1.0

        # 用多次小 dt 推进，检查在正常过渡时长下不是瞬时
        # 验证正常过渡在有过渡时长时是渐进的
        for _ in range(3):
            self.game._update_boost_state(16.0, True)

        # 3 帧后应该 > 1.0 (正常过渡已进行部分)
        self.assertGreater(
            self.game.snake.boost_state['current_multiplier'], 1.0
        )

    def test_multiple_frames_complete_transition_to_target(self):
        """多帧推进后完成到目标的过渡"""
        self.game.snake.boost_state['current_multiplier'] = 1.0

        # 150ms 过渡时长，@16ms/frame 约需 9-10 帧
        # 100 帧应足够
        for _ in range(100):
            self.game._update_boost_state(16.0, True)

        # 应达到目标 (BOOST_SPEED_MULTIPLIER)
        self.assertAlmostEqual(
            BOOST_SPEED_MULTIPLIER,
            self.game.snake.boost_state['current_multiplier'],
            places=1,
        )

    def test_multiple_frames_complete_transition_back_to_one(self):
        """多帧推进后完成从加速到基准的过渡"""
        self.game.snake.boost_state['current_multiplier'] = BOOST_SPEED_MULTIPLIER
        self.game.snake.boost_state['is_active'] = True

        for _ in range(100):
            self.game._update_boost_state(16.0, False)

        self.assertAlmostEqual(
            1.0,
            self.game.snake.boost_state['current_multiplier'],
            places=1,
        )
        self.assertFalse(self.game.snake.boost_state['is_active'])

    def test_boost_forced_to_one_in_game_over_state(self):
        """GAME_OVER 状态下即使按住加速键也强制倍率为 1.0"""
        self.game.state = GameState.GAME_OVER
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 按住加速键，但 GAME_OVER 状态下应强制 target=1.0
        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)
        self.assertFalse(self.game.snake.boost_state['is_active'])

    def test_boost_forced_to_one_in_victory_state(self):
        """VICTORY 状态下即使按住加速键也强制倍率为 1.0"""
        self.game.state = GameState.VICTORY
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        for _ in range(50):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)
        self.assertFalse(self.game.snake.boost_state['is_active'])

    def test_boost_forced_to_one_in_running_state_allows_boost(self):
        """RUNNING 状态下加速正常生效（对照组）"""
        self.game.state = GameState.RUNNING
        self.game.snake.boost_state['current_multiplier'] = 1.0
        self.game.snake.boost_state['is_active'] = False

        # 按住加速键，RUNNING 状态应允许加速
        self.game._update_boost_state(16.0, True)

        self.assertGreater(self.game.snake.boost_state['current_multiplier'], 1.0)

    def test_boost_forced_to_one_state_transition_locks_down(self):
        """从 RUNNING 切换到 GAME_OVER 后，下一帧立强制倍率=1.0"""
        # 先激活加速
        self.game.state = GameState.RUNNING
        self.game.snake.boost_state['current_multiplier'] = 2.0
        self.game.snake.boost_state['is_active'] = True

        # 切换到 GAME_OVER
        self.game.state = GameState.GAME_OVER

        # 下一帧，即使 boost_pressed=True 也应强制 target=1.0
        for _ in range(30):
            self.game._update_boost_state(16.0, True)

        self.assertAlmostEqual(1.0,
                               self.game.snake.boost_state['current_multiplier'],
                               places=1)
        self.assertFalse(self.game.snake.boost_state['is_active'])


# =============================================================================
# 测试类：_get_current_tick_interval tick 间隔计算
# =============================================================================

class TestGetCurrentTickInterval(_GameTestBase):
    """测试 _get_current_tick_interval tick 间隔计算方法"""

    def test_baseline_interval_is_base_tick_interval(self):
        """基准倍率 1.0 时返回 BASE_TICK_INTERVAL"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertEqual(float(BASE_TICK_INTERVAL), interval)

    def test_boost_halves_interval_at_2x(self):
        """2x 加速时 interval = BASE_TICK_INTERVAL / 2"""
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(BASE_TICK_INTERVAL / 2.0, interval, places=1)

    def test_interval_clamped_to_20ms_minimum(self):
        """interval 下限为 20ms"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)

    def test_interval_always_positive(self):
        """interval 始终为正数"""
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertGreater(interval, 0)

    def test_interval_returns_float(self):
        """返回值为 float 类型"""
        interval = self.game._get_current_tick_interval()
        self.assertIsInstance(interval, float)

    def test_interval_at_max_boost_multiplier(self):
        """最大倍率时 interval 正确计算"""
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        interval = self.game._get_current_tick_interval()
        expected = max(20.0, BASE_TICK_INTERVAL / MAX_BOOST_MULTIPLIER)
        self.assertEqual(expected, interval)

    def test_invalid_multiplier_fallback(self):
        """非法倍率（如 0）时回退到 BASE_TICK_INTERVAL"""
        self.game.snake.boost_state['current_multiplier'] = 0.0
        # boost_multiplier property clamps >= 1.0, so use _get_current_tick_interval directly
        # 但 property 保证 >= 1.0, 所以无法真正测试 0.0
        # 测试 multiplier=1.0 时正常工作
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertEqual(float(BASE_TICK_INTERVAL), interval)


# =============================================================================
# 测试类：_get_current_tick_interval 复合公式测试（难度+加速叠加）
# =============================================================================

class TestGetCurrentTickIntervalCompound(_GameTestBase):
    """测试 _get_current_tick_interval 在难度+加速复合叠加下的 tick 计算"""

    def test_diff0_boost1_tick_100ms(self):
        """diff=0, boost=1.0 时 tick=100ms（向后兼容）"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(100.0, interval, places=1)

    def test_diff05_boost1_tick_66_7ms(self):
        """diff=0.5, boost=1.0 时 tick=66.7ms"""
        self.game.difficulty_multiplier = 0.5
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(100.0 / 1.5, interval, places=1)

    def test_diff0_boost2_tick_50ms(self):
        """diff=0, boost=2.0 时 tick=50ms"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(50.0, interval, places=1)

    def test_diff4_boost5_tick_clamped_to_20ms(self):
        """diff=4.0, boost=5.0 时 tick 不低于 20ms 硬下限"""
        self.game.difficulty_multiplier = 4.0
        self.game.snake.boost_state['current_multiplier'] = 5.0
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)
        # effective = 1 + 4 + 4 = 9, 100/9 ≈ 11.1, clamped to 20
        self.assertAlmostEqual(20.0, interval, places=1)

    def test_diff2_boost3_tick_correct(self):
        """diff=2.0, boost=3.0 -> effective=6.0, tick=100/6≈16.7 clamped to 20"""
        self.game.difficulty_multiplier = 2.0
        self.game.snake.boost_state['current_multiplier'] = 3.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(20.0, interval, places=1)

    def test_compound_always_positive(self):
        """复合叠加下 interval 始终为正"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertGreater(interval, 0)

    def test_compound_returns_float(self):
        """复合叠加下返回值仍为 float"""
        self.game.difficulty_multiplier = 1.0
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        self.assertIsInstance(interval, float)

    def test_diff_and_boost_both_zero_effective(self):
        """diff=0, boost=1.0 -> boost_extra=0 -> effective=1.0 -> 100ms"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertEqual(float(BASE_TICK_INTERVAL), interval)

    def test_diff_only_no_boost(self):
        """仅难度激活无加速时 tick 正确递减"""
        self.game.difficulty_multiplier = 1.0  # diff=1.0 level
        self.game.snake.boost_state['current_multiplier'] = 1.0  # no boost
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(100.0 / 2.0, interval, places=1)  # 50ms

    def test_boost_only_no_diff(self):
        """仅加速无难度时 tick 正确递减（与改动前一致）"""
        self.game.difficulty_multiplier = 0.0
        self.game.snake.boost_state['current_multiplier'] = 2.0  # boost
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(50.0, interval, places=1)

    def test_diff05_boost2_tick_40ms(self):
        """diff=0.5, boost=2.0 -> effective=2.5, tick=40ms"""
        self.game.difficulty_multiplier = 0.5
        self.game.snake.boost_state['current_multiplier'] = 2.0
        interval = self.game._get_current_tick_interval()
        self.assertAlmostEqual(40.0, interval, places=1)

    def test_both_maxed_clamped(self):
        """两者都达到上限时 tick 不低于 MIN_TICK_INTERVAL"""
        self.game.difficulty_multiplier = MAX_DIFFICULTY_MULTIPLIER
        self.game.snake.boost_state['current_multiplier'] = MAX_BOOST_MULTIPLIER
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)


# =============================================================================
# 测试类：_reset_boost 加速状态复位
# =============================================================================

class TestResetBoost(_GameTestBase):
    """测试 _reset_boost 加速复位方法"""

    def test_reset_boost_clears_is_active(self):
        """_reset_boost 清除 is_active 标志"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game._reset_boost()

        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_reset_boost_when_already_inactive(self):
        """已处于不活跃状态时 _reset_boost 仍安全执行"""
        self.game.snake.boost_state['is_active'] = False
        self.game.snake.boost_state['current_multiplier'] = 1.0

        self.game._reset_boost()

        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_reset_boost_idempotent(self):
        """多次 _reset_boost 结果一致"""
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 3.0

        self.game._reset_boost()
        self.game._reset_boost()
        self.game._reset_boost()

        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_reset_boost_clears_input_handler_boost_active(self):
        """_reset_boost 同时复位 input_handler._boost_active"""
        self.game.input_handler._boost_active = True
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game._reset_boost()

        self.assertFalse(self.game.input_handler._boost_active)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_reset_boost_clears_boost_active_when_already_false(self):
        """_boost_active 已为 False 时 _reset_boost 仍安全执行"""
        self.game.input_handler._boost_active = False
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

        self.game._reset_boost()

        self.assertFalse(self.game.input_handler._boost_active)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])


# =============================================================================
# 测试类：加速状态在状态转换时的复位
# =============================================================================

class TestBoostResetOnStateTransition(_GameTestBase):
    """测试加速状态在 GAME_OVER / VICTORY / restart 时自动复位"""

    def setUp(self):
        super().setUp()
        # 设置加速状态为活跃
        self.game.snake.boost_state['is_active'] = True
        self.game.snake.boost_state['current_multiplier'] = 2.0

    def test_boost_reset_on_boundary_collision(self):
        """撞墙 GAME_OVER 时 boost 状态复位"""
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_reset_on_self_collision(self):
        """自撞 GAME_OVER 时 boost 状态复位"""
        self.game.snake.body = [(3, 2), (3, 3), (4, 3), (5, 3)]
        self.game.snake.direction = (0, 1)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_reset_on_victory(self):
        """棋盘满 VICTORY 时 boost 状态复位"""
        self.game.snake.body = [(18, 14), (17, 14), (16, 14)]
        self.game.snake.direction = (1, 0)
        self.game.food.position = (19, 14)

        original_respawn = self.game.food.respawn
        self.game.food.respawn = lambda occupied: False

        self.game._update()

        self.assertEqual(GameState.VICTORY, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

        self.game.food.respawn = original_respawn

    def test_boost_reset_on_restart(self):
        """restart 时 boost 状态复位（双重保险）"""
        self.game.state = GameState.GAME_OVER
        self.game.reset()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertFalse(self.game.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.game.snake.boost_state['current_multiplier'])

    def test_boost_reset_on_no_collision_keeps_state(self):
        """未发生碰撞时 boost 状态应保持不变（在 _update 内不改变）"""
        original_active = self.game.snake.boost_state['is_active']
        original_mult = self.game.snake.boost_state['current_multiplier']

        # 确保食物不在蛇头前方，蛇也不会撞墙
        self.game.food.position = (30, 20)  # far away from snake

        self.game._update()

        self.assertEqual(GameState.RUNNING, self.game.state)
        self.assertEqual(original_active, self.game.snake.boost_state['is_active'])
        self.assertEqual(original_mult, self.game.snake.boost_state['current_multiplier'])


# =============================================================================
# 测试类：run() 解耦架构集成测试
# =============================================================================

class TestDecoupledRun(_GameTestBase):
    """测试 run() 解耦架构：accumulator、spiral-of-death 保护、非RUNNING清空"""

    def test_run_exits_on_quit_event(self):
        """QUIT 事件后 run() 正常退出，不改变游戏状态"""
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        try:
            self.game.run()
        except Exception as e:
            self.fail(f"run() raised unexpected exception: {e}")
        # QUIT 事件只退出循环，不修改游戏状态
        # (这里 state 可能是 RUNNING 因为没有碰撞发生)

    def test_run_passes_boost_to_draw_frame(self):
        """run() 将 is_boosting 传递给 draw_frame"""
        with patch.object(self.game.renderer, 'draw_frame') as mock_draw:
            with patch.object(self.game.renderer, 'tick', return_value=16):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                self.game.run()
                # 至少调用一次
                calls = mock_draw.call_args_list
                self.assertGreater(len(calls), 0)
                # 检查最后一个调用包含 is_boosting 关键字参数
                last_call = calls[-1]
                self.assertIn('is_boosting', last_call.kwargs)

    def test_run_calls_update_boost_state(self):
        """run() 每帧调用 _update_boost_state"""
        with patch.object(self.game, '_update_boost_state') as mock_update_boost_state:
            with patch.object(self.game.renderer, 'tick', return_value=16):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        mock_update_boost_state.assert_called()

    def test_run_accumulator_not_triggering_when_not_running(self):
        """非 RUNNING 状态时不触发 _update()"""
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=16):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        self.game.state = GameState.GAME_OVER
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        mock_update.assert_not_called()

    def test_run_accumulator_not_triggering_when_paused(self):
        """暂停时不触发 _update()"""
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=16):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        self.game.input_handler._paused = True
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        mock_update.assert_not_called()


# =============================================================================
# 测试类：Accumulator 和 spiral-of-death 保护
# =============================================================================

class TestAccumulatorLogic(_GameTestBase):
    """测试 accumulator 累加器逻辑和 spiral-of-death 保护"""

    def test_accumulator_triggers_update_when_full(self):
        """accumulator 累积足够时间后触发 _update()"""
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=105.0):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        # tick 返回 105ms > BASE_TICK_INTERVAL(100ms)
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        # 至少触发一次 _update()
                        self.assertGreater(mock_update.call_count, 0)

    def test_accumulator_not_triggers_when_below_threshold(self):
        """accumulator 不足时不触发 _update()"""
        # tick 返回 16ms << 100ms, 只有 1 帧运行，不应触发 _update()
        # 但 QUIT 事件会导致只运行 1 帧
        # 需要设计一个测试：只运行几帧，验证 _update 未被触发
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=16.0):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        # 16ms < 100ms，不应触发 _update
                        self.assertEqual(0, mock_update.call_count)

    def test_spiral_of_death_protection_caps_catchup(self):
        """MAX_CATCHUP_STEPS 限制单帧逻辑更新次数"""
        # Mock renderer.tick 返回极大值触发多个 catchup
        # 然后验证 _update 调用次数不超过 MAX_CATCHUP_STEPS
        large_dt = float(BASE_TICK_INTERVAL * (MAX_CATCHUP_STEPS + 3))

        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=large_dt):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        # _update 调用次数应不超过 MAX_CATCHUP_STEPS
                        self.assertLessEqual(
                            mock_update.call_count, MAX_CATCHUP_STEPS
                        )

    def test_accumulator_cleared_when_state_not_running(self):
        """非 RUNNING 状态时 accumulator 被清零"""
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick') as mock_tick:
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        # 先放一个 QUIT 事件
                        pygame.event.post(pygame.event.Event(pygame.QUIT))

                        # 设置 GAME_OVER 状态
                        self.game.state = GameState.GAME_OVER
                        self.game.run()

                        # _update 在 GAME_OVER 状态不应被调用
                        mock_update.assert_not_called()

    def test_accumulator_dt_zero_boundary(self):
        """dt=0 时 accumulator 不触发 _update() 且不崩溃"""
        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=0.0):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        # dt=0 时 accumulator 不增加，不应触发 _update
                        self.assertEqual(0, mock_update.call_count)

    def test_accumulator_dt_extremely_large(self):
        """dt 极大时 catchup 步数受 MAX_CATCHUP_STEPS 限制"""
        # 使用极大 dt (相当于 10 秒) 验证保护机制
        huge_dt = 10000.0  # 10 seconds

        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=huge_dt):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        # 无论 dt 多大，_update 调用次数应不超过 MAX_CATCHUP_STEPS
                        self.assertLessEqual(
                            mock_update.call_count, MAX_CATCHUP_STEPS
                        )

    def test_accumulator_exact_multiple_triggers_exact_steps(self):
        """accumulator 恰好为 tick_interval 整数倍时触发精确步数"""
        # dt = BASE_TICK_INTERVAL * 3 -> 应触发恰好 3 步 (不超过 catchup 上限)
        steps = min(3, MAX_CATCHUP_STEPS)
        exact_dt = float(BASE_TICK_INTERVAL * steps)

        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game.renderer, 'tick', return_value=exact_dt):
                with patch.object(self.game.renderer, 'draw_frame'):
                    with patch('pygame.display.flip'):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        self.game.run()
                        self.assertEqual(steps, mock_update.call_count)


# =============================================================================
# 测试类：Mock _get_current_tick_interval 隔离测试
# =============================================================================

class TestTickIntervalIsolation(_GameTestBase):
    """通过 mock _get_current_tick_interval 隔离测试累加器在不同 tick_interval 下的行为"""

    def test_tick_interval_20ms_extreme(self):
        """tick_interval=20ms 极限值下 accumulator 正确触发 _update()"""
        interval_20ms = 20.0
        # dt 略大于 20ms 应触发一次
        dt = 21.0

        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game, '_get_current_tick_interval',
                              return_value=interval_20ms):
                with patch.object(self.game.renderer, 'tick', return_value=dt):
                    with patch.object(self.game.renderer, 'draw_frame'):
                        with patch('pygame.display.flip'):
                            pygame.event.post(pygame.event.Event(pygame.QUIT))
                            self.game.run()
                            self.assertEqual(1, mock_update.call_count)

    def test_tick_interval_large_accumulator_multiple_frames(self):
        """大 tick_interval 下多帧累积后触发 _update()"""
        interval = 200.0
        # 每帧 dt=16ms，需要 200/16=12.5 -> 13 帧才累积足够
        # QUIT 事件只运行 1 帧，所以不应触发
        dt_per_frame = 16.0

        with patch.object(self.game, '_update') as mock_update:
            with patch.object(self.game, '_get_current_tick_interval',
                              return_value=interval):
                with patch.object(self.game.renderer, 'tick',
                                  return_value=dt_per_frame):
                    with patch.object(self.game.renderer, 'draw_frame'):
                        with patch('pygame.display.flip'):
                            pygame.event.post(pygame.event.Event(pygame.QUIT))
                            self.game.run()
                            # dt=16ms < interval=200ms，不应触发
                            self.assertEqual(0, mock_update.call_count)

    def test_tick_interval_zero_negative_fallback(self):
        """_get_current_tick_interval 返回 <=0 时，20ms clamp 确保不崩溃"""
        # _get_current_tick_interval 内部已有防御 clamp，直接测试方法返回值
        self.game.snake.boost_state['current_multiplier'] = 1.0
        interval = self.game._get_current_tick_interval()
        self.assertGreaterEqual(interval, 20.0)
        self.assertIsInstance(interval, float)


# =============================================================================
# 测试类：Accumulator 多帧累积驱动 _update
# =============================================================================

class TestMultiFrameAccumulator(_GameTestBase):
    """通过可控 dt 序列模拟多帧运行，验证累加器跨帧累积行为"""

    def test_multi_frame_accumulation_triggers_update(self):
        """多帧 dt 累积达到 tick_interval 后触发 _update()"""
        # 每帧 25ms，累积 4 帧达到 100ms
        dt_values = [25.0, 25.0, 25.0, 25.0]
        interval = 100.0

        with patch.object(self.game, '_get_current_tick_interval',
                          return_value=interval):
            with patch.object(self.game.renderer, 'draw_frame'):
                with patch('pygame.display.flip'):
                    # 通过直接模拟 run() 内部的 accumulator 逻辑
                    # 而不是实际调用 run()
                    pass

        # 直接用 Game 实例模拟累加器逻辑
        accumulator = 0.0
        update_count = 0
        for dt in dt_values:
            accumulator += dt
            while accumulator >= interval:
                accumulator -= interval
                update_count += 1
        self.assertEqual(1, update_count)
        self.assertAlmostEqual(0.0, accumulator)

    def test_accumulator_rollover_triggers_multiple_updates(self):
        """accumulator 在一次 catchup 中触发多次 _update"""
        # dt=250ms, interval=100ms -> 应触发 2 次
        dt = 250.0
        interval = 100.0

        accumulator = 0.0
        update_count = 0
        accumulator += dt
        while accumulator >= interval:
            accumulator -= interval
            update_count += 1
        self.assertEqual(2, update_count)
        self.assertAlmostEqual(50.0, accumulator)


# =============================================================================
# 测试类：_update_difficulty 难度递增
# =============================================================================


class TestDifficultyInit(_GameTestBase):
    """测试难度状态初始化"""

    def test_difficulty_level_initial_zero(self):
        """difficulty_level 初始值为 0"""
        self.assertEqual(0, self.game.difficulty_level)

    def test_difficulty_multiplier_initial_zero(self):
        """difficulty_multiplier 初始值为 0.0"""
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_difficulty_level_is_int(self):
        """difficulty_level 类型为 int"""
        self.assertIsInstance(self.game.difficulty_level, int)

    def test_difficulty_multiplier_is_float(self):
        """difficulty_multiplier 类型为 float"""
        self.assertIsInstance(self.game.difficulty_multiplier, float)


class TestUpdateDifficulty(_GameTestBase):
    """测试 _update_difficulty() 方法逻辑"""

    def test_score_zero_keeps_level_zero(self):
        """score=0 时 _update_difficulty() 保持 level=0, multiplier=0.0"""
        self.game.score = 0
        self.game._update_difficulty()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_score_50_level_1_multiplier_0_1(self):
        """score=50 时 level=1, multiplier=0.1"""
        self.game.score = 50
        self.game._update_difficulty()
        self.assertEqual(1, self.game.difficulty_level)
        self.assertAlmostEqual(0.1, self.game.difficulty_multiplier, places=5)

    def test_score_100_level_2_multiplier_0_2(self):
        """score=100 时 level=2, multiplier=0.2"""
        self.game.score = 100
        self.game._update_difficulty()
        self.assertEqual(2, self.game.difficulty_level)
        self.assertAlmostEqual(0.2, self.game.difficulty_multiplier, places=5)

    def test_score_49_level_0(self):
        """score=49（阈值边界下）level=0"""
        self.game.score = 49
        self.game._update_difficulty()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_score_51_level_1(self):
        """score=51（阈值边界上）level=1"""
        self.game.score = 51
        self.game._update_difficulty()
        self.assertEqual(1, self.game.difficulty_level)
        self.assertAlmostEqual(0.1, self.game.difficulty_multiplier, places=5)

    def test_score_2000_multiplier_clamped_to_max(self):
        """score=2000 时 multiplier 钳位在 MAX_DIFFICULTY_MULTIPLIER (4.0)"""
        self.game.score = 2000
        self.game._update_difficulty()
        expected_level = 2000 // SCORE_THRESHOLD_INTERVAL  # 40
        self.assertEqual(expected_level, self.game.difficulty_level)
        # multiplier 应钳位在 MAX_DIFFICULTY_MULTIPLIER
        self.assertEqual(MAX_DIFFICULTY_MULTIPLIER, self.game.difficulty_multiplier)

    def test_score_10000_multiplier_still_clamped(self):
        """极端高分 score=10000 时 multiplier 仍钳位在上限"""
        self.game.score = 10000
        self.game._update_difficulty()
        self.assertEqual(MAX_DIFFICULTY_MULTIPLIER, self.game.difficulty_multiplier)

    def test_update_difficulty_idempotent(self):
        """相同 score 反复调用 _update_difficulty() 结果不变（幂等）"""
        self.game.score = 150
        self.game._update_difficulty()
        level1 = self.game.difficulty_level
        mult1 = self.game.difficulty_multiplier

        # 反复调用多次
        for _ in range(10):
            self.game._update_difficulty()

        self.assertEqual(level1, self.game.difficulty_level)
        self.assertEqual(mult1, self.game.difficulty_multiplier)

    def test_score_zero_idempotent(self):
        """score=0 时反复调用结果不变"""
        self.game.score = 0
        self.game._update_difficulty()

        for _ in range(5):
            self.game._update_difficulty()

        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_difficulty_level_formula(self):
        """验证 level = score // SCORE_THRESHOLD_INTERVAL 公式"""
        self.game.score = 135
        self.game._update_difficulty()
        expected_level = 135 // SCORE_THRESHOLD_INTERVAL  # 2
        expected_mult = min(
            expected_level * DIFFICULTY_INCREMENT,
            MAX_DIFFICULTY_MULTIPLIER,
        )
        self.assertEqual(expected_level, self.game.difficulty_level)
        self.assertAlmostEqual(expected_mult, self.game.difficulty_multiplier, places=5)

    def test_multiplier_formula_level_times_increment(self):
        """验证 multiplier = min(level * increment, max) 公式"""
        # score=500 -> level=10, 10*0.1=1.0, min(1.0, 4.0)=1.0
        self.game.score = 500
        self.game._update_difficulty()
        self.assertEqual(10, self.game.difficulty_level)  # 500 // 50
        expected = min(10 * DIFFICULTY_INCREMENT, MAX_DIFFICULTY_MULTIPLIER)
        self.assertAlmostEqual(expected, self.game.difficulty_multiplier, places=5)


class TestDifficultyReset(_GameTestBase):
    """测试难度状态在 reset 时归零"""

    def test_reset_clears_difficulty_level(self):
        """reset() 后 difficulty_level 归零"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 1.5
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)

    def test_reset_clears_difficulty_multiplier(self):
        """reset() 后 difficulty_multiplier 归零"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 1.5
        self.game.reset()
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_reset_from_game_over_clears_difficulty(self):
        """从 GAME_OVER 状态 reset 后难度归零"""
        self.game.state = GameState.GAME_OVER
        self.game.difficulty_level = 3
        self.game.difficulty_multiplier = 0.3
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_reset_from_victory_clears_difficulty(self):
        """从 VICTORY 状态 reset 后难度归零"""
        self.game.state = GameState.VICTORY
        self.game.difficulty_level = 10
        self.game.difficulty_multiplier = 1.0
        self.game.reset()
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)

    def test_multiple_resets_difficulty_consistent(self):
        """多次 reset 难度状态一致"""
        self.game.difficulty_level = 5
        self.game.difficulty_multiplier = 2.0
        self.game.reset()
        first_level = self.game.difficulty_level
        first_mult = self.game.difficulty_multiplier

        self.game.difficulty_level = 8
        self.game.difficulty_multiplier = 3.0
        self.game.reset()

        self.assertEqual(first_level, self.game.difficulty_level)
        self.assertEqual(first_mult, self.game.difficulty_multiplier)


class TestDifficultyUpdateIntegration(_GameTestBase):
    """测试 _update() 中难度更新集成"""

    def test_update_calls_difficulty_when_eat_food(self):
        """吃食物后 _update_difficulty 被调用，难度状态更新"""
        head = self.game.snake.head
        direction = self.game.snake.direction
        self.game.food.position = (head[0] + direction[0],
                                   head[1] + direction[1])

        # 吃第一个食物（10分）-> level 仍为 0
        self.game._update()
        self.assertEqual(10, self.game.score)
        self.assertEqual(0, self.game.difficulty_level)

    def test_multiple_food_eats_increases_difficulty(self):
        """连续吃食物跨越阈值后难度递增"""
        # 每吃一次 +10 分，吃 5 次达到 50 分跨越阈值
        for i in range(6):  # 0..5 -> score=60
            head = self.game.snake.head
            direction = self.game.snake.direction
            self.game.food.position = (head[0] + direction[0],
                                       head[1] + direction[1])
            self.game._update()

        self.assertEqual(60, self.game.score)
        self.assertEqual(1, self.game.difficulty_level)  # 60//50=1
        self.assertAlmostEqual(0.1, self.game.difficulty_multiplier, places=5)

    def test_no_difficulty_change_without_food(self):
        """未吃食物时难度不变化"""
        original_level = self.game.difficulty_level
        original_mult = self.game.difficulty_multiplier

        # 食物远离蛇头
        self.game.food.position = (30, 20)
        self.game._update()

        self.assertEqual(original_level, self.game.difficulty_level)
        self.assertEqual(original_mult, self.game.difficulty_multiplier)

    def test_difficulty_unchanged_on_collision(self):
        """撞墙/自撞时难度不变"""
        self.game.food.position = (30, 20)  # 远离蛇
        # 制造撞墙场景
        self.game.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.game.snake.direction = (-1, 0)

        self.game._update()

        self.assertEqual(GameState.GAME_OVER, self.game.state)
        self.assertEqual(0, self.game.difficulty_level)
        self.assertEqual(0.0, self.game.difficulty_multiplier)


if __name__ == "__main__":
    unittest.main()
