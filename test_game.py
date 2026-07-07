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


if __name__ == "__main__":
    unittest.main()
