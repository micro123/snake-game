"""
Snake 类单元测试

覆盖：初始化状态、move_and_grow 增长/保持长度、change_direction 反向拦截、
check_boundary_collision 边界检测、check_self_collision 自撞检测、reset 重置。
使用 Python 标准库 unittest 框架，无需外部依赖。
"""

import unittest

from snake import Snake


class TestSnakeInit(unittest.TestCase):
    """测试 Snake 初始化状态"""

    def test_initial_length_is_3_by_default(self):
        snake = Snake(40, 30)
        self.assertEqual(3, snake.length)

    def test_initial_length_custom(self):
        snake = Snake(40, 30, initial_length=5)
        self.assertEqual(5, snake.length)

    def test_initial_body_has_no_gaps(self):
        """蛇身各节之间连续无间隙"""
        snake = Snake(40, 30)
        for i in range(len(snake.body) - 1):
            x1, y1 = snake.body[i]
            x2, y2 = snake.body[i + 1]
            gap = abs(x1 - x2) + abs(y1 - y2)
            self.assertEqual(1, gap, f"Gap between {snake.body[i]} and {snake.body[i+1]}")

    def test_initial_head_at_center_column(self):
        """蛇头位于网格水平中心附近"""
        snake = Snake(40, 30)
        head_x, head_y = snake.head
        self.assertEqual(20, head_x, f"Expected head.x=20, got {head_x}")  # 40//2
        self.assertEqual(15, head_y, f"Expected head.y=15, got {head_y}")  # 30//2

    def test_initial_direction_right(self):
        snake = Snake(40, 30)
        self.assertEqual((1, 0), snake.direction)

    def test_initial_body_order_head_first(self):
        """body[0] 为蛇头，坐标最靠右（向右方向时）"""
        snake = Snake(40, 30)
        self.assertEqual((20, 15), snake.body[0])
        self.assertEqual((19, 15), snake.body[1])
        self.assertEqual((18, 15), snake.body[2])

    def test_init_raises_value_error_if_grid_too_small(self):
        with self.assertRaises(ValueError):
            Snake(2, 30, initial_length=3)

    def test_head_property_returns_body_index_0(self):
        snake = Snake(40, 30)
        self.assertEqual(snake.body[0], snake.head)

    def test_length_property_matches_body_len(self):
        snake = Snake(40, 30)
        self.assertEqual(len(snake.body), snake.length)


class TestMoveAndGrow(unittest.TestCase):
    """测试 move_and_grow 操作"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_move_without_grow_maintains_length(self):
        original_length = self.snake.length
        original_tail = self.snake.body[-1]
        self.snake.move_and_grow(False)
        self.assertEqual(original_length, self.snake.length)
        # 旧的尾部被弹出，新尾部是原来的倒数第二节
        self.assertEqual((19, 15), self.snake.body[-1])

    def test_move_with_grow_increases_length(self):
        original_length = self.snake.length
        original_tail = self.snake.body[-1]
        self.snake.move_and_grow(True)
        self.assertEqual(original_length + 1, self.snake.length)
        # 尾部保留不动
        self.assertEqual(original_tail, self.snake.body[-1])

    def test_move_advances_head_in_current_direction(self):
        old_head = self.snake.head
        self.snake.move_and_grow(False)
        expected_head = (old_head[0] + 1, old_head[1] + 0)  # direction = (1, 0)
        self.assertEqual(expected_head, self.snake.head)

    def test_move_and_grow_false_pops_correct_tail(self):
        """移动不增长时，尾部弹出后 body 对应原第1到倒数第2节"""
        original_body = list(self.snake.body)
        self.snake.move_and_grow(False)
        # body[0] 为新的 head，body[1:] 应与 original_body[:-1] 一致
        expected_body_tail = original_body[:-1]
        actual_body_tail = self.snake.body[1:]
        self.assertEqual(expected_body_tail, actual_body_tail)

    def test_move_and_grow_true_keeps_tail(self):
        """移动增长时，尾部完整保留"""
        original_body = list(self.snake.body)
        self.snake.move_and_grow(True)
        # 原 body 整体保留在 body[1:]
        self.assertEqual(original_body, self.snake.body[1:])

    def test_multi_move_length_stays_same(self):
        """连续多帧移动不增长，长度保持不变"""
        for _ in range(5):
            self.snake.move_and_grow(False)
        self.assertEqual(3, self.snake.length)

    def test_multi_move_grow_each_frame(self):
        """连续每帧增长"""
        for i in range(5):
            self.snake.move_and_grow(True)
        self.assertEqual(3 + 5, self.snake.length)


class TestChangeDirection(unittest.TestCase):
    """测试 change_direction 操作"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_reverse_horizontal_rejected(self):
        """向右(1,0)时不能直接左转(-1,0)"""
        self.assertEqual((1, 0), self.snake.direction)
        result = self.snake.change_direction(-1, 0)
        self.assertFalse(result)
        self.assertEqual((1, 0), self.snake.direction)

    def test_reverse_vertical_rejected(self):
        """先转向上并移动一步，再尝试直接掉头（模拟实际游戏跨帧场景）"""
        self.snake.change_direction(0, -1)
        self.snake.move_and_grow(False)  # 蛇实际向上移动，committed_direction 更新为 UP
        result = self.snake.change_direction(0, 1)
        self.assertFalse(result)
        self.assertEqual((0, -1), self.snake.direction)

    def test_valid_direction_accepted(self):
        """有效方向输入返回 True 并更新方向"""
        result = self.snake.change_direction(0, -1)  # 向右 -> 向上
        self.assertTrue(result)
        self.assertEqual((0, -1), self.snake.direction)

    def test_invalid_direction_rejected(self):
        """无效方向（非上下左右）被拒绝"""
        result = self.snake.change_direction(1, 1)
        self.assertFalse(result)
        self.assertEqual((1, 0), self.snake.direction)

    def test_same_direction_accepted(self):
        """同方向输入被接受（不改变方向）"""
        result = self.snake.change_direction(1, 0)
        self.assertTrue(result)
        self.assertEqual((1, 0), self.snake.direction)

    def test_all_valid_directions(self):
        """遍历所有四个方向，正常切换"""
        directions = [(0, -1), (-1, 0), (0, 1), (1, 0)]
        for d in directions:
            self.snake = Snake(40, 30)
            # 先通过 move_and_grow 设置 committed_direction 到正交方向
            orth = (d[1], d[0])  # e.g. d=(0,-1) -> orthogonal (1,0)
            self.snake.direction = orth
            self.snake.move_and_grow(True)  # 更新 committed_direction
            self.assertTrue(self.snake.change_direction(*d))
            self.assertEqual(d, self.snake.direction)

    def test_turn_up_then_left(self):
        """向右->向上并移动一步->向左 正常通过（模拟跨帧合法转弯）"""
        self.snake.change_direction(0, -1)  # 上
        self.snake.move_and_grow(False)  # 蛇实际向上移动
        result = self.snake.change_direction(-1, 0)  # 左
        self.assertTrue(result)
        self.assertEqual((-1, 0), self.snake.direction)

    def test_zero_zero_direction_rejected(self):
        """(0, 0) 不是有效方向"""
        result = self.snake.change_direction(0, 0)
        self.assertFalse(result)
        self.assertEqual((1, 0), self.snake.direction)


class TestCheckBoundaryCollision(unittest.TestCase):
    """测试 check_boundary_collision 边界碰撞检测"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_no_collision_when_in_bounds(self):
        self.assertFalse(self.snake.check_boundary_collision(40, 30))

    def test_collision_when_head_left_of_grid(self):
        self.snake.body[0] = (-1, 15)
        self.assertTrue(self.snake.check_boundary_collision(40, 30))

    def test_collision_when_head_right_of_grid(self):
        self.snake.body[0] = (40, 15)  # cols=40, 有效范围 0-39
        self.assertTrue(self.snake.check_boundary_collision(40, 30))

    def test_collision_when_head_above_grid(self):
        self.snake.body[0] = (20, -1)
        self.assertTrue(self.snake.check_boundary_collision(40, 30))

    def test_collision_when_head_below_grid(self):
        self.snake.body[0] = (20, 30)  # rows=30, 有效范围 0-29
        self.assertTrue(self.snake.check_boundary_collision(40, 30))

    def test_no_collision_at_boundary_edge(self):
        """蛇头在边界边缘 (0,0) 应该不撞墙"""
        self.snake.body[0] = (0, 0)
        self.assertFalse(self.snake.check_boundary_collision(40, 30))

    def test_no_collision_at_boundary_max(self):
        """蛇头在边界边缘 (39, 29) 应该不撞墙"""
        self.snake.body[0] = (39, 29)
        self.assertFalse(self.snake.check_boundary_collision(40, 30))

    def test_collision_detection_uses_head_only(self):
        """只检查蛇头，蛇身出界不会被判定为碰撞"""
        self.snake.body[0] = (39, 29)  # 头在界内
        self.snake.body[1] = (40, 29)  # 身体出界
        self.assertFalse(self.snake.check_boundary_collision(40, 30))


class TestCheckSelfCollision(unittest.TestCase):
    """测试 check_self_collision 自撞检测"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_no_self_collision_initially(self):
        self.assertFalse(self.snake.check_self_collision())

    def test_self_collision_when_head_hits_body(self):
        """蛇头坐标与蛇身某节重合"""
        # 模拟蛇头移动到蛇身位置
        self.snake.body = [(19, 15), (20, 15), (19, 15), (18, 15)]
        # head(19,15) 出现在 body[1:] 中
        self.assertTrue(self.snake.check_self_collision())

    def test_no_self_collision_when_length_one(self):
        """单节蛇不会自撞（body[1:] 为空）"""
        self.snake.body = [(10, 10)]
        self.assertFalse(self.snake.check_self_collision())

    def test_self_collision_false_when_no_overlap(self):
        """蛇头不与身体任何部分重合"""
        self.snake.body = [(21, 15), (20, 15), (19, 15)]
        self.assertFalse(self.snake.check_self_collision())

    def test_self_collision_long_body(self):
        """长蛇身自撞"""
        body = [(10, 10)]  # head
        body.extend([(9, 10), (8, 10), (7, 10), (10, 10), (6, 10)])
        self.snake.body = body
        self.assertTrue(self.snake.check_self_collision())


class TestBoostState(unittest.TestCase):
    """测试 boost_state 属性、is_boosting / boost_multiplier 只读 property"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_boost_state_initial_values(self):
        """初始化后 boost_state 为默认值"""
        self.assertFalse(self.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.snake.boost_state['current_multiplier'])

    def test_is_boosting_defaults_false(self):
        self.assertFalse(self.snake.is_boosting)

    def test_boost_multiplier_defaults_to_one(self):
        self.assertEqual(1.0, self.snake.boost_multiplier)

    def test_is_boosting_reflects_boost_state(self):
        """is_boosting property 正确反映 boost_state['is_active']"""
        self.snake.boost_state['is_active'] = True
        self.assertTrue(self.snake.is_boosting)
        self.snake.boost_state['is_active'] = False
        self.assertFalse(self.snake.is_boosting)

    def test_boost_multiplier_reflects_current_multiplier(self):
        """boost_multiplier property 正确反映 current_multiplier"""
        self.snake.boost_state['current_multiplier'] = 2.5
        self.assertEqual(2.5, self.snake.boost_multiplier)

    def test_boost_multiplier_never_below_one(self):
        """boost_multiplier 保证 >= 1.0，即使内部值被设为小于 1.0"""
        self.snake.boost_state['current_multiplier'] = 0.5
        self.assertEqual(1.0, self.snake.boost_multiplier)

        self.snake.boost_state['current_multiplier'] = -1.0
        self.assertEqual(1.0, self.snake.boost_multiplier)

    def test_boost_multiplier_at_boundary_one(self):
        """boost_multiplier 在 current_multiplier=1.0 时返回 1.0"""
        self.snake.boost_state['current_multiplier'] = 1.0
        self.assertEqual(1.0, self.snake.boost_multiplier)

    def test_boost_multiplier_large_value(self):
        """boost_multiplier 处理大倍数"""
        self.snake.boost_state['current_multiplier'] = 5.0
        self.assertEqual(5.0, self.snake.boost_multiplier)


class TestReset(unittest.TestCase):
    """测试 reset 重置功能"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_reset_restores_initial_body(self):
        original_body = list(self.snake.body)
        # 修改蛇状态
        self.snake.move_and_grow(False)
        self.snake.move_and_grow(True)
        self.snake.change_direction(0, -1)
        # 重置
        self.snake.reset()
        self.assertEqual(original_body, self.snake.body)

    def test_reset_restores_direction(self):
        self.snake.change_direction(0, -1)
        self.snake.reset()
        self.assertEqual((1, 0), self.snake.direction)

    def test_reset_restores_length(self):
        self.snake.move_and_grow(True)
        self.snake.move_and_grow(True)
        self.snake.reset()
        self.assertEqual(3, self.snake.length)

    def test_reset_restores_boost_state(self):
        """reset() 后 boost_state 复位为初始值"""
        self.snake.boost_state['is_active'] = True
        self.snake.boost_state['current_multiplier'] = 2.0
        self.snake.reset()
        self.assertFalse(self.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.snake.boost_state['current_multiplier'])
        self.assertFalse(self.snake.is_boosting)
        self.assertEqual(1.0, self.snake.boost_multiplier)

    def test_reset_boost_state_when_inactive(self):
        """reset() 在不活跃加速状态下仍正确复位 boost_state"""
        self.snake.boost_state['is_active'] = False
        self.snake.boost_state['current_multiplier'] = 1.0
        self.snake.reset()
        self.assertFalse(self.snake.boost_state['is_active'])
        self.assertEqual(1.0, self.snake.boost_state['current_multiplier'])

    def test_multiple_resets_idempotent(self):
        """多次 reset 结果一致（reset 在已修改状态下也正确恢复到初始）"""
        self.snake.move_and_grow(False)
        self.snake.change_direction(0, -1)
        self.snake.reset()
        first_reset_body = list(self.snake.body)
        first_reset_dir = self.snake.direction
        # 再次修改并重置
        self.snake.move_and_grow(True)
        self.snake.change_direction(0, 1)
        self.snake.reset()
        second_reset_body = list(self.snake.body)
        second_reset_dir = self.snake.direction
        self.assertEqual(first_reset_body, second_reset_body)
        self.assertEqual(first_reset_dir, second_reset_dir)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_move_and_grow_false_followed_by_true(self):
        """交替增长"""
        snake = Snake(40, 30)
        snake.move_and_grow(False)
        self.assertEqual(3, snake.length)
        snake.move_and_grow(True)
        self.assertEqual(4, snake.length)
        snake.move_and_grow(False)
        self.assertEqual(4, snake.length)

    def test_direction_change_before_any_move(self):
        """初始未移动时更改方向"""
        snake = Snake(40, 30)
        self.assertTrue(snake.change_direction(0, -1))
        snake.move_and_grow(False)
        self.assertEqual((20, 14), snake.head)

    def test_boundary_collision_after_move(self):
        """模拟蛇向右移动到边界外"""
        snake = Snake(40, 30)
        snake.body = [(39, 15), (38, 15), (37, 15)]
        snake.move_and_grow(False)  # head -> (40, 15)
        self.assertTrue(snake.check_boundary_collision(40, 30))

    def test_self_collision_after_turn_into_self(self):
        """模拟蛇转向自身导致自撞：经典U型掉头场景"""
        snake = Snake(6, 6, initial_length=4)
        # 设置 body 为 L 形：头在 (3,3)，向上走到(3,2)再左转到(2,2)再向下(2,3)
        snake.body = [(2, 3), (2, 2), (3, 2), (3, 3)]
        snake.direction = (0, 1)  # 向下
        snake.move_and_grow(False)  # head -> (2, 4)
        self.assertFalse(snake.check_self_collision())
        # 继续向下
        snake.change_direction(0, 1)  # already heading down
        snake.move_and_grow(False)

    def test_collision_checks_use_current_head_position(self):
        """碰撞检测基于 move_and_grow 后的头部位置"""
        snake = Snake(40, 30)
        # 蛇头移到接近边界
        snake.body = [(38, 15), (37, 15), (36, 15)]
        self.assertFalse(snake.check_boundary_collision(40, 30))
        snake.move_and_grow(False)  # (39, 15)
        self.assertFalse(snake.check_boundary_collision(40, 30))
        snake.move_and_grow(False)  # (40, 15) -> 出界
        self.assertTrue(snake.check_boundary_collision(40, 30))


class TestSnakeCommittedDirection(unittest.TestCase):
    """测试 committed_direction 属性及其跨帧反向拦截"""

    def setUp(self):
        self.snake = Snake(40, 30)

    def test_committed_direction_initial_value_matches_direction(self):
        """committed_direction 初始值与 direction 一致（均为向右）"""
        self.assertEqual((1, 0), self.snake.committed_direction)
        self.assertEqual(self.snake.direction, self.snake.committed_direction)

    def test_committed_direction_updated_after_move_and_grow(self):
        """move_and_grow() 后 committed_direction 更新为移动时的 direction"""
        self.snake.change_direction(0, -1)  # 转向 UP
        self.snake.move_and_grow(False)     # 物理移动
        self.assertEqual((0, -1), self.snake.committed_direction)

    def test_committed_direction_unchanged_after_change_direction_only(self):
        """仅调用 change_direction 不移动时 committed_direction 不变"""
        original = self.snake.committed_direction
        self.snake.change_direction(0, -1)  # 转向 UP，但不移动
        self.assertEqual(original, self.snake.committed_direction)
        self.assertEqual((1, 0), self.snake.committed_direction)

    def test_committed_direction_updated_each_move(self):
        """每次 move_and_grow 后 committed_direction 同步更新"""
        # 初始向右
        self.snake.move_and_grow(False)
        self.assertEqual((1, 0), self.snake.committed_direction)

        # 转向上并移动
        self.snake.change_direction(0, -1)
        self.snake.move_and_grow(False)
        self.assertEqual((0, -1), self.snake.committed_direction)

        # 转向左并移动
        self.snake.change_direction(-1, 0)
        self.snake.move_and_grow(True)  # grow=True 也应正常更新
        self.assertEqual((-1, 0), self.snake.committed_direction)

    def test_committed_direction_reset_on_reset(self):
        """reset() 后 committed_direction 重置为 (1, 0)"""
        self.snake.change_direction(0, -1)
        self.snake.move_and_grow(False)
        self.assertEqual((0, -1), self.snake.committed_direction)

        self.snake.reset()
        self.assertEqual((1, 0), self.snake.committed_direction)
        self.assertEqual(self.snake.direction, self.snake.committed_direction)

    def test_reverse_blocked_with_committed_after_move(self):
        """移动后反向检测基于 committed_direction：上行后 DOWN 被拦截"""
        self.snake.change_direction(0, -1)   # UP
        self.snake.move_and_grow(False)       # committed = UP
        result = self.snake.change_direction(0, 1)  # DOWN → reverse of UP
        self.assertFalse(result)
        self.assertEqual((0, -1), self.snake.direction)

    def test_orthogonal_allowed_with_committed_after_move(self):
        """移动后正交方向基于 committed_direction 正常放行"""
        self.snake.change_direction(0, -1)   # UP
        self.snake.move_and_grow(False)       # committed = UP
        result = self.snake.change_direction(-1, 0)  # LEFT → orthogonal to UP
        self.assertTrue(result)
        self.assertEqual((-1, 0), self.snake.direction)

    def test_cross_frame_reverse_intercept_without_update(self):
        """跨帧反向拦截：帧1 LEFT 被接受（方向变为LEFT但无_update），
        帧2 DOWN 基于 committed=UP 仍被拦截"""
        # 蛇初始 committed=(1,0)，先转为 UP 并移动
        self.snake.change_direction(0, -1)   # direction=UP
        self.snake.move_and_grow(False)       # committed=UP

        # 帧1：按 LEFT，process_events(committed=UP) 放行 LEFT
        # LEFT 不是 UP 的反向 → 被接受
        self.assertTrue(self.snake.change_direction(-1, 0))
        # direction 变为 LEFT，但 committed 仍为 UP（未执行 move_and_grow）

        # 帧2：按 DOWN，process_events(committed=UP) 应拦截
        # committed 仍为 UP，DOWN 是 UP 的反向 → 应拦截
        self.assertFalse(self.snake.change_direction(0, 1))
        self.assertEqual((-1, 0), self.snake.direction)  # 方向不变

    def test_legitimate_l_turn_after_move(self):
        """合法 L 形转弯：上行→LEFT→移动→DOWN 正常通过"""
        # 初始向右，转向上并移动以建立 L 形拐弯基础
        self.snake.change_direction(0, -1)   # UP
        self.snake.move_and_grow(False)       # committed=UP, head上移

        # 左转并移动（合法的正交转弯）
        self.snake.change_direction(-1, 0)   # LEFT
        self.snake.move_and_grow(False)       # committed=LEFT

        # 再下转（正交于LEFT，合法）
        result = self.snake.change_direction(0, 1)  # DOWN
        self.assertTrue(result)
        self.assertEqual((0, 1), self.snake.direction)


if __name__ == "__main__":
    unittest.main()
