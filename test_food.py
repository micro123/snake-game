"""
Food 类单元测试

覆盖：初始化占位位置、respawn 正常生成、respawn 满棋盘返回 False、
respawn 不落在占用格子上、reset 重置占位。
使用 Python 标准库 unittest 框架，无需外部依赖。
"""

import unittest

from food import Food


class TestFoodInit(unittest.TestCase):
    """测试 Food 初始化状态"""

    def test_initial_position_is_placeholder(self):
        """初始 position 为 (-1, -1) 占位值"""
        food = Food(40, 30)
        self.assertEqual((-1, -1), food.position)

    def test_grid_params_stored(self):
        """_grid_cols 和 _grid_rows 被正确存储"""
        food = Food(40, 30)
        self.assertEqual(40, food._grid_cols)
        self.assertEqual(30, food._grid_rows)

    def test_initial_position_not_in_grid(self):
        """(-1, -1) 不属于有效网格范围，明确表明确未生成"""
        food = Food(40, 30)
        self.assertNotIn(food.position, {
            (x, y) for x in range(40) for y in range(30)
        })


class TestRespawn(unittest.TestCase):
    """测试 respawn 方法"""

    def setUp(self):
        self.food = Food(40, 30)

    def test_respawn_returns_true_on_success(self):
        """正常情况有可用格子时返回 True"""
        result = self.food.respawn([])
        self.assertTrue(result)

    def test_respawn_updates_position(self):
        """respawn 后 position 不再是 (-1, -1)"""
        self.food.respawn([])
        self.assertNotEqual((-1, -1), self.food.position)

    def test_respawn_position_within_grid(self):
        """生成的食物坐标在有效网格范围内"""
        for _ in range(50):  # 多次测试确保随机结果始终有效
            food = Food(40, 30)
            food.respawn([(10, 10)])
            x, y = food.position
            self.assertTrue(0 <= x < 40)
            self.assertTrue(0 <= y < 30)

    def test_respawn_not_in_occupied_cells(self):
        """食物不会生成在已占据的格子上"""
        occupied = [(5, 5), (6, 5), (7, 5), (8, 5), (9, 5)]
        for _ in range(50):
            food = Food(40, 30)
            food.respawn(occupied)
            self.assertNotIn(food.position, occupied)

    def test_respawn_not_in_occupied_single_cell(self):
        """占用单格子时食物不落在该格"""
        food = Food(40, 30)
        food.respawn([(0, 0)])
        self.assertNotEqual((0, 0), food.position)

    def test_respawn_with_large_occupied_set(self):
        """占用大量格子仍能正常生成"""
        # 占满除一格外的全部格子
        all_except_one = {
            (x, y) for x in range(40) for y in range(30)
        } - {(39, 29)}
        food = Food(40, 30)
        result = food.respawn(all_except_one)
        self.assertTrue(result)
        self.assertEqual((39, 29), food.position)

    def test_respawn_randomly_distributed(self):
        """多次生成食物，验证坐标在一定次数内出现变化（非固定位置）"""
        positions = set()
        occupied = [(10, 10)]
        for _ in range(100):
            food = Food(40, 30)
            food.respawn(occupied)
            positions.add(food.position)
        # 在 40*30-1 = 1199 个可用格子中，100 次生成应出现多个不同位置
        self.assertGreater(len(positions), 1, "Food should appear at different positions")


class TestRespawnBoardFull(unittest.TestCase):
    """测试 respawn 满棋盘场景"""

    def test_respawn_returns_false_when_board_full(self):
        """全部格子被占据时，respawn 返回 False"""
        food = Food(3, 3)
        all_cells = [(x, y) for x in range(3) for y in range(3)]
        result = food.respawn(all_cells)
        self.assertFalse(result)

    def test_respawn_position_unchanged_when_board_full(self):
        """满棋盘时 position 保持原值不变"""
        food = Food(3, 3)
        original_position = food.position
        all_cells = [(x, y) for x in range(3) for y in range(3)]
        food.respawn(all_cells)
        self.assertEqual(original_position, food.position)

    def test_respawn_board_full_unmodified_position(self):
        """满棋盘且 position 已设置有效值时也保持不变"""
        food = Food(3, 3)
        # 先生成一次
        food.respawn([])
        self.assertNotEqual((-1, -1), food.position)
        last_position = food.position
        # 再满棋盘调用
        all_cells = [(x, y) for x in range(3) for y in range(3)]
        result = food.respawn(all_cells)
        self.assertFalse(result)
        self.assertEqual(last_position, food.position)

    def test_respawn_large_board_full(self):
        """40x30 满棋盘场景"""
        food = Food(40, 30)
        all_cells = [(x, y) for x in range(40) for y in range(30)]
        result = food.respawn(all_cells)
        self.assertFalse(result)

    def test_respawn_with_duplicates_in_occupied(self):
        """occupied_cells 含有重复项时集合差运算不受影响"""
        food = Food(3, 3)
        occupied = [(0, 0), (0, 0), (0, 1)]  # 含重复
        result = food.respawn(occupied)
        self.assertTrue(result)
        self.assertNotIn(food.position, [(0, 0), (0, 1)])


class TestReset(unittest.TestCase):
    """测试 reset 方法"""

    def test_reset_restores_placeholder(self):
        """reset 将 position 重置为 (-1, -1)"""
        food = Food(40, 30)
        food.respawn([])
        self.assertNotEqual((-1, -1), food.position)
        food.reset()
        self.assertEqual((-1, -1), food.position)

    def test_reset_idempotent(self):
        """多次 reset 结果一致"""
        food = Food(40, 30)
        food.respawn([(10, 10)])
        food.reset()
        self.assertEqual((-1, -1), food.position)
        food.reset()
        self.assertEqual((-1, -1), food.position)

    def test_reset_from_initial_state(self):
        """从初始 (-1, -1) 状态 reset 仍为 (-1, -1)"""
        food = Food(40, 30)
        food.reset()
        self.assertEqual((-1, -1), food.position)


class TestFoodEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_respawn_minimum_grid(self):
        """最小网格 1x1"""
        food = Food(1, 1)
        # 无占用 -> 只有 (0,0) 可用
        result = food.respawn([])
        self.assertTrue(result)
        self.assertEqual((0, 0), food.position)

    def test_respawn_minimum_grid_full(self):
        """最小网格 1x1 满"""
        food = Food(1, 1)
        result = food.respawn([(0, 0)])
        self.assertFalse(result)

    def test_respawn_occupied_as_set(self):
        """occupied_cells 传入 set 类型也能正常工作"""
        food = Food(40, 30)
        occupied = {(5, 5), (6, 5), (7, 5)}
        result = food.respawn(occupied)
        self.assertTrue(result)
        self.assertNotIn(food.position, occupied)

    def test_respawn_occupied_as_tuple(self):
        """occupied_cells 传入 tuple 类型也能正常工作"""
        food = Food(40, 30)
        occupied = ((5, 5), (6, 5), (7, 5))
        result = food.respawn(occupied)
        self.assertTrue(result)
        self.assertNotIn(food.position, occupied)

    def test_respawn_method_callable(self):
        """验证 Food 实例具有 respawn 和 reset 方法"""
        food = Food(40, 30)
        self.assertTrue(callable(food.respawn))
        self.assertTrue(callable(food.reset))

    def test_position_attribute_exists(self):
        """验证 position 属性存在"""
        food = Food(40, 30)
        self.assertTrue(hasattr(food, 'position'))


if __name__ == "__main__":
    unittest.main()
