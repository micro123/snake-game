"""
InputHandler 类单元测试

覆盖：初始化暂停状态、方向键映射、反向拦截、QUIT 事件、R/Q 键仅在
GAME_OVER/VICTORY 时生效、per-frame 单方向缓冲、焦点丢失/恢复、空队列返回、
非方向键忽略、_is_reverse 静态方法。

使用 Python 标准库 unittest 框架，依赖 Pygame。
"""

import unittest

import pygame

from game import GameState
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

def _post_event(event_type: int, **attrs) -> None:
    """向 Pygame 事件队列投递一个事件。

    Args:
        event_type: Pygame 事件类型（如 pygame.KEYDOWN）
        **attrs: 事件属性（如 key=pygame.K_UP）
    """
    pygame.event.post(pygame.event.Event(event_type, **attrs))


def _post_window_event(subtype: int) -> None:
    """投递一个窗口焦点事件。

    注意：Pygame 中焦点变化是独立事件类型（WINDOWFOCUSLOST / WINDOWFOCUSGAINED），
    而非 WINDOWEVENT 子类型。

    Args:
        subtype: 焦点事件类型（pygame.WINDOWFOCUSLOST 或 pygame.WINDOWFOCUSGAINED）
    """
    pygame.event.post(pygame.event.Event(subtype))


def _post_key(key: int) -> None:
    """投递一个键盘按下事件。

    Args:
        key: Pygame 键码（如 pygame.K_UP）
    """
    _post_event(pygame.KEYDOWN, key=key)


def _clear_queue() -> None:
    """清空 Pygame 事件队列。"""
    pygame.event.clear()


# =============================================================================
# 测试类
# =============================================================================


class TestInputHandlerInit(unittest.TestCase):
    """测试 InputHandler 初始化"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_initially_not_paused(self):
        """初始化后暂停标志为 False"""
        self.assertFalse(self.handler.is_paused())

    def test_is_paused_method_returns_bool(self):
        """is_paused 返回布尔值"""
        self.assertIsInstance(self.handler.is_paused(), bool)

    def test_paused_attribute_tracks_state(self):
        """_paused 属性正确初始化为 False"""
        self.assertFalse(self.handler._paused)


class TestDirectionMapping(unittest.TestCase):
    """测试方向键到方向向量的映射"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_up_maps_to_negative_y(self):
        """K_UP -> (0, -1)"""
        self.assertEqual((0, -1), self.handler.DIRECTION_MAP[pygame.K_UP])

    def test_down_maps_to_positive_y(self):
        """K_DOWN -> (0, 1)"""
        self.assertEqual((0, 1), self.handler.DIRECTION_MAP[pygame.K_DOWN])

    def test_left_maps_to_negative_x(self):
        """K_LEFT -> (-1, 0)"""
        self.assertEqual((-1, 0), self.handler.DIRECTION_MAP[pygame.K_LEFT])

    def test_right_maps_to_positive_x(self):
        """K_RIGHT -> (1, 0)"""
        self.assertEqual((1, 0), self.handler.DIRECTION_MAP[pygame.K_RIGHT])

    def test_direction_map_has_four_entries(self):
        """方向映射表恰好包含四个方向键"""
        self.assertEqual(4, len(self.handler.DIRECTION_MAP))


class TestProcessEventsDirection(unittest.TestCase):
    """测试方向键的事件处理"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_up_key_returns_direction_up(self):
        """按上键返回 (0, -1) 方向命令"""
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, -1), cmd['direction'])

    def test_down_key_returns_direction_down(self):
        """按下键返回 (0, 1) 方向命令"""
        _post_key(pygame.K_DOWN)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, 1), cmd['direction'])

    def test_left_key_returns_direction_left(self):
        """按左键返回 (-1, 0) 方向命令"""
        _post_key(pygame.K_LEFT)
        cmd = self.handler.process_events((0, -1), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((-1, 0), cmd['direction'])

    def test_right_key_returns_direction_right(self):
        """按右键返回 (1, 0) 方向命令"""
        _post_key(pygame.K_RIGHT)
        cmd = self.handler.process_events((0, -1), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((1, 0), cmd['direction'])

    def test_direction_command_has_no_extra_keys(self):
        """方向命令仅含 action 和 direction 两个键"""
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual({'action', 'direction'}, set(cmd.keys()))


class TestReverseIntercept(unittest.TestCase):
    """测试反向拦截"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_reverse_horizontal_rejected(self):
        """向右移动时按左键被拦截"""
        _post_key(pygame.K_LEFT)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])
        self.assertNotIn('direction', cmd)

    def test_reverse_vertical_rejected(self):
        """向下移动时按上键被拦截"""
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((0, 1), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_reverse_left_rejected(self):
        """向左移动时按右键被拦截"""
        _post_key(pygame.K_RIGHT)
        cmd = self.handler.process_events((-1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_reverse_up_rejected(self):
        """向上移动时按下键被拦截"""
        _post_key(pygame.K_DOWN)
        cmd = self.handler.process_events((0, -1), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_non_reverse_accepted(self):
        """正交方向输入不被拦截"""
        # 向右移动时按上键（正交，非反向）
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, -1), cmd['direction'])


class TestQuitEvent(unittest.TestCase):
    """测试 QUIT 事件处理"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_quit_event_returns_quit_action(self):
        """QUIT 事件返回 quit 命令"""
        _post_event(pygame.QUIT)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('quit', cmd['action'])
        self.assertNotIn('direction', cmd)

    def test_quit_event_in_game_over(self):
        """GAME_OVER 状态下 QUIT 事件仍返回 quit"""
        _post_event(pygame.QUIT)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('quit', cmd['action'])

    def test_quit_event_in_victory(self):
        """VICTORY 状态下 QUIT 事件仍返回 quit"""
        _post_event(pygame.QUIT)
        cmd = self.handler.process_events((1, 0), GameState.VICTORY)
        self.assertEqual('quit', cmd['action'])

    def test_quit_takes_priority_over_other_events(self):
        """QUIT 事件优先级最高，即使同时有其他事件也返回 quit"""
        _post_key(pygame.K_UP)
        _post_event(pygame.QUIT)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('quit', cmd['action'])


class TestRKey(unittest.TestCase):
    """测试 R 键重新开始"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_r_key_in_game_over_returns_restart(self):
        """GAME_OVER 状态下按 R 返回 restart"""
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('restart', cmd['action'])

    def test_r_key_in_victory_returns_restart(self):
        """VICTORY 状态下按 R 返回 restart"""
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.VICTORY)
        self.assertEqual('restart', cmd['action'])

    def test_r_key_in_running_is_ignored(self):
        """RUNNING 状态下按 R 被忽略"""
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_restart_command_has_no_direction(self):
        """restart 命令不含 direction 键"""
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertNotIn('direction', cmd)
        self.assertEqual({'action'}, set(cmd.keys()))


class TestQKey(unittest.TestCase):
    """测试 Q 键退出"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_q_key_in_game_over_returns_quit(self):
        """GAME_OVER 状态下按 Q 返回 quit"""
        _post_key(pygame.K_q)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('quit', cmd['action'])

    def test_q_key_in_victory_returns_quit(self):
        """VICTORY 状态下按 Q 返回 quit"""
        _post_key(pygame.K_q)
        cmd = self.handler.process_events((1, 0), GameState.VICTORY)
        self.assertEqual('quit', cmd['action'])

    def test_q_key_in_running_is_ignored(self):
        """RUNNING 状态下按 Q 被忽略"""
        _post_key(pygame.K_q)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_q_quit_command_has_no_direction(self):
        """Q 键 quit 命令不含 direction 键"""
        _post_key(pygame.K_q)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertNotIn('direction', cmd)
        self.assertEqual({'action'}, set(cmd.keys()))


class TestDirectionBuffering(unittest.TestCase):
    """测试 per-frame 单方向缓冲"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_last_direction_wins_multiple_keys(self):
        """同帧多个方向键，取最后有效者"""
        # current_direction = (0, 1) (向下), K_LEFT 和 K_RIGHT 均为有效正交方向
        _post_key(pygame.K_LEFT)
        _post_key(pygame.K_RIGHT)
        cmd = self.handler.process_events((0, 1), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((1, 0), cmd['direction'])

    def test_last_direction_wins_three_keys(self):
        """同帧按三个方向键，取最后有效者（跳过反向键）"""
        # current_direction = (0, 1) (向下)
        # K_RIGHT 有效, K_UP 反向被忽略, K_LEFT 有效 -> 最后有效者 K_LEFT
        _post_key(pygame.K_RIGHT)
        _post_key(pygame.K_UP)     # 反向 (当前向下)，被忽略
        _post_key(pygame.K_LEFT)
        cmd = self.handler.process_events((0, 1), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((-1, 0), cmd['direction'])

    def test_reverse_interleaved_with_valid(self):
        """反向键夹杂在有效键之间，最后有效者胜出"""
        _post_key(pygame.K_UP)     # valid
        _post_key(pygame.K_DOWN)   # reverse (heading right, down is not reverse actually)
        # Wait, (1,0) vs (0,1) is not reverse. Let me fix this test.
        # If heading right (1,0), reverse is left (-1,0).
        # Up (0,-1), Down (0,1), Left (-1,0) are all different.
        _post_key(pygame.K_LEFT)   # reverse of right
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        # LEFT is reverse so ignored; last non-reverse is DOWN
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, 1), cmd['direction'])

    def test_all_reverse_keys_returns_none(self):
        """同帧所有方向键均为反向时返回 none"""
        _post_key(pygame.K_LEFT)   # reverse of (1, 0)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_same_key_repeated(self):
        """同帧多次按同一方向键"""
        _post_key(pygame.K_UP)
        _post_key(pygame.K_UP)
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, -1), cmd['direction'])

    def test_multiple_reverse_keys_all_ignored(self):
        """多个反向键全部被忽略"""
        _post_key(pygame.K_LEFT)    # reverse of right
        _post_key(pygame.K_LEFT)    # reverse of right
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_valid_then_reverse_then_valid(self):
        """有效键 -> 反向键 -> 有效键，最后有效者胜出"""
        _post_key(pygame.K_UP)      # valid (0, -1)
        _post_key(pygame.K_LEFT)    # reverse of (1, 0)
        _post_key(pygame.K_DOWN)    # valid (0, 1)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('direction', cmd['action'])
        self.assertEqual((0, 1), cmd['direction'])


class TestFocusEvents(unittest.TestCase):
    """测试窗口焦点事件"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_focus_lost_sets_paused(self):
        """失焦事件设置 _paused 为 True"""
        _post_window_event(pygame.WINDOWFOCUSLOST)
        self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertTrue(self.handler.is_paused())

    def test_focus_gained_clears_paused(self):
        """聚焦事件设置 _paused 为 False"""
        self.handler._paused = True
        _post_window_event(pygame.WINDOWFOCUSGAINED)
        self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertFalse(self.handler.is_paused())

    def test_focus_lost_returns_pause_action(self):
        """失焦返回 pause 命令"""
        _post_window_event(pygame.WINDOWFOCUSLOST)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('pause', cmd['action'])

    def test_focus_gained_returns_resume_action(self):
        """聚焦返回 resume 命令"""
        _post_window_event(pygame.WINDOWFOCUSGAINED)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('resume', cmd['action'])

    def test_focus_lost_lose_direction(self):
        """失焦时同时按方向键，返回 pause 而非 direction"""
        _post_key(pygame.K_UP)
        _post_window_event(pygame.WINDOWFOCUSLOST)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('pause', cmd['action'])

    def test_focus_lost_then_regained(self):
        """先失焦再聚焦"""
        _post_window_event(pygame.WINDOWFOCUSLOST)
        _post_window_event(pygame.WINDOWFOCUSGAINED)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('resume', cmd['action'])

    def test_pause_command_has_no_direction(self):
        """pause 命令不含 direction 键"""
        _post_window_event(pygame.WINDOWFOCUSLOST)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertNotIn('direction', cmd)

    def test_resume_command_has_no_direction(self):
        """resume 命令不含 direction 键"""
        _post_window_event(pygame.WINDOWFOCUSGAINED)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertNotIn('direction', cmd)


class TestNoEvents(unittest.TestCase):
    """测试空事件队列"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_empty_queue_returns_none(self):
        """无事件时返回 none 命令"""
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_none_command_has_no_direction(self):
        """none 命令不含 direction 键"""
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertNotIn('direction', cmd)

    def test_empty_queue_in_game_over(self):
        """GAME_OVER 状态空队列返回 none"""
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('none', cmd['action'])

    def test_empty_queue_in_victory(self):
        """VICTORY 状态空队列返回 none"""
        cmd = self.handler.process_events((1, 0), GameState.VICTORY)
        self.assertEqual('none', cmd['action'])


class TestNonDirectionKeys(unittest.TestCase):
    """测试非方向键被忽略"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_space_key_ignored(self):
        """空格键被忽略"""
        _post_key(pygame.K_SPACE)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_escape_key_ignored(self):
        """ESC 键被忽略"""
        _post_key(pygame.K_ESCAPE)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_enter_key_ignored(self):
        """回车键被忽略"""
        _post_key(pygame.K_RETURN)
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])

    def test_alpha_keys_ignored(self):
        """字母键（非R/Q功能键）被忽略"""
        for key in (pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_d):
            _clear_queue()
            _post_key(key)
            cmd = self.handler.process_events((1, 0), GameState.RUNNING)
            self.assertEqual('none', cmd['action'],
                             f"Key {key} should be ignored in RUNNING")

    def test_non_direction_keys_in_game_over_not_affect(self):
        """GAME_OVER 状态非功能键被忽略（返回 none）"""
        _post_key(pygame.K_SPACE)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('none', cmd['action'])


class TestIsReverse(unittest.TestCase):
    """测试 _is_reverse 静态方法"""

    def test_reverse_horizontal(self):
        """水平方向互为反向"""
        self.assertTrue(InputHandler._is_reverse((-1, 0), (1, 0)))
        self.assertTrue(InputHandler._is_reverse((1, 0), (-1, 0)))

    def test_reverse_vertical(self):
        """垂直方向互为反向"""
        self.assertTrue(InputHandler._is_reverse((0, 1), (0, -1)))
        self.assertTrue(InputHandler._is_reverse((0, -1), (0, 1)))

    def test_not_reverse_orthogonal(self):
        """正交方向不是反向"""
        self.assertFalse(InputHandler._is_reverse((0, -1), (1, 0)))
        self.assertFalse(InputHandler._is_reverse((1, 0), (0, -1)))
        self.assertFalse(InputHandler._is_reverse((-1, 0), (0, 1)))

    def test_same_direction_not_reverse(self):
        """相同方向不是反向"""
        self.assertFalse(InputHandler._is_reverse((1, 0), (1, 0)))
        self.assertFalse(InputHandler._is_reverse((0, -1), (0, -1)))

    def test_zero_vector_not_reverse(self):
        """零向量不是任何方向的反向"""
        self.assertFalse(InputHandler._is_reverse((0, 0), (1, 0)))
        self.assertFalse(InputHandler._is_reverse((1, 0), (0, 0)))


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        _clear_queue()
        self.handler = InputHandler()

    def test_r_key_followed_by_direction_in_game_over(self):
        """GAME_OVER 状态先按 R 再按方向键，R 优先（实际上是最后事件胜出）"""
        _post_key(pygame.K_r)
        _post_key(pygame.K_UP)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        # UP is the last event, but direction is still valid in end state
        self.assertEqual('direction', cmd['action'])

    def test_direction_followed_by_r_in_game_over(self):
        """GAME_OVER 状态先按方向键再按 R，R 胜出"""
        _post_key(pygame.K_UP)
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('restart', cmd['action'])

    def test_q_key_followed_by_r_in_game_over(self):
        """GAME_OVER 状态先按 Q 再按 R，R 胜出（最后事件胜出）"""
        _post_key(pygame.K_q)
        _post_key(pygame.K_r)
        cmd = self.handler.process_events((1, 0), GameState.GAME_OVER)
        self.assertEqual('restart', cmd['action'])

    def test_events_consumed_after_process(self):
        """process_events 耗尽事件队列"""
        _post_key(pygame.K_UP)
        self.handler.process_events((1, 0), GameState.RUNNING)
        # 队列应为空
        self.assertFalse(pygame.event.get())

    def test_quit_event_consumed(self):
        """QUIT 事件后队列中的其他事件也被消耗"""
        _post_key(pygame.K_UP)
        _post_event(pygame.QUIT)
        self.handler.process_events((1, 0), GameState.RUNNING)
        # QUIT 立即返回，但迭代可能已消耗了前面的 UP 事件
        # 关键在于不崩，队列已清空
        self.assertFalse(pygame.event.get())

    def test_direction_applies_in_all_states(self):
        """方向键在所有游戏状态下都返回方向命令"""
        for state in (GameState.RUNNING, GameState.GAME_OVER, GameState.VICTORY):
            _clear_queue()
            self.handler = InputHandler()
            _post_key(pygame.K_UP)
            cmd = self.handler.process_events((1, 0), state)
            self.assertEqual('direction', cmd['action'])

    def test_focus_paused_persists_across_frames(self):
        """暂停标志在帧间保持"""
        _post_window_event(pygame.WINDOWFOCUSLOST)
        self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertTrue(self.handler.is_paused())

        # 下一帧无事件，暂停状态保持
        cmd = self.handler.process_events((1, 0), GameState.RUNNING)
        self.assertEqual('none', cmd['action'])
        self.assertTrue(self.handler.is_paused())

    def test_multiple_handlers_independent(self):
        """多个 InputHandler 实例的暂停状态相互独立"""
        h1 = InputHandler()
        h2 = InputHandler()

        _clear_queue()
        _post_window_event(pygame.WINDOWFOCUSLOST)
        h1.process_events((1, 0), GameState.RUNNING)

        self.assertTrue(h1.is_paused())
        self.assertFalse(h2.is_paused())


if __name__ == "__main__":
    unittest.main()
