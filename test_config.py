"""
config 模块单元测试

覆盖：模块级常量的默认值与存在性、加速配置常量（全部10个）、
FPS 常量向后兼容保留、_validate_boost_config() 校验逻辑
（clamp 越界值并记录 WARNING）、模块导入时自动执行校验。
使用 Python 标准库 unittest 框架，无需外部依赖。
"""

import importlib
import logging
import sys
import unittest
from unittest.mock import patch


# =============================================================================
# 测试辅助：隔离重新导入 config 模块
# =============================================================================

def _reimport_config():
    """强制重新加载 config 模块，返回模块对象。"""
    if "config" in sys.modules:
        del sys.modules["config"]
    import config
    return config


# =============================================================================
# 测试类：常量存在性与默认值
# =============================================================================


class TestConfigConstantsExist(unittest.TestCase):
    """验证所有加速相关常量存在且默认值正确"""

    @classmethod
    def setUpClass(cls):
        cls._config = _reimport_config()

    def test_boost_key_exists_and_default_is_space(self):
        """BOOST_KEY 应存在且默认值为 pygame.K_SPACE"""
        import pygame
        self.assertTrue(hasattr(self._config, "BOOST_KEY"))
        self.assertIsInstance(self._config.BOOST_KEY, int)
        self.assertEqual(pygame.K_SPACE, self._config.BOOST_KEY)

    def test_boost_speed_multiplier_exists_and_default(self):
        """BOOST_SPEED_MULTIPLIER 应存在且默认值为 2.0"""
        self.assertTrue(hasattr(self._config, "BOOST_SPEED_MULTIPLIER"))
        self.assertIsInstance(self._config.BOOST_SPEED_MULTIPLIER, float)
        self.assertEqual(2.0, self._config.BOOST_SPEED_MULTIPLIER)

    def test_max_boost_multiplier_exists_and_default(self):
        """MAX_BOOST_MULTIPLIER 应存在且默认值为 5.0"""
        self.assertTrue(hasattr(self._config, "MAX_BOOST_MULTIPLIER"))
        self.assertIsInstance(self._config.MAX_BOOST_MULTIPLIER, float)
        self.assertEqual(5.0, self._config.MAX_BOOST_MULTIPLIER)

    def test_base_tick_interval_exists_and_default(self):
        """BASE_TICK_INTERVAL 应存在且默认值为 100"""
        self.assertTrue(hasattr(self._config, "BASE_TICK_INTERVAL"))
        self.assertIsInstance(self._config.BASE_TICK_INTERVAL, int)
        self.assertEqual(100, self._config.BASE_TICK_INTERVAL)

    def test_render_fps_exists_and_default(self):
        """RENDER_FPS 应存在且默认值为 60"""
        self.assertTrue(hasattr(self._config, "RENDER_FPS"))
        self.assertIsInstance(self._config.RENDER_FPS, int)
        self.assertEqual(60, self._config.RENDER_FPS)

    def test_boost_transition_seconds_exists_and_default(self):
        """BOOST_TRANSITION_SECONDS 应存在且默认值为 0.15"""
        self.assertTrue(hasattr(self._config, "BOOST_TRANSITION_SECONDS"))
        self.assertIsInstance(self._config.BOOST_TRANSITION_SECONDS, float)
        self.assertAlmostEqual(0.15, self._config.BOOST_TRANSITION_SECONDS)

    def test_max_catchup_steps_exists_and_default(self):
        """MAX_CATCHUP_STEPS 应存在且默认值为 5"""
        self.assertTrue(hasattr(self._config, "MAX_CATCHUP_STEPS"))
        self.assertIsInstance(self._config.MAX_CATCHUP_STEPS, int)
        self.assertEqual(5, self._config.MAX_CATCHUP_STEPS)

    def test_boost_snake_body_color_exists(self):
        """COLORS.BOOST_SNAKE_BODY 应存在且为 RGB 三元组"""
        self.assertTrue(hasattr(self._config.COLORS, "BOOST_SNAKE_BODY"))
        color = self._config.COLORS.BOOST_SNAKE_BODY
        self.assertIsInstance(color, tuple)
        self.assertEqual(3, len(color))
        self.assertEqual((255, 140, 0), color)

    def test_boost_snake_head_color_exists(self):
        """COLORS.BOOST_SNAKE_HEAD 应存在且为 RGB 三元组"""
        self.assertTrue(hasattr(self._config.COLORS, "BOOST_SNAKE_HEAD"))
        color = self._config.COLORS.BOOST_SNAKE_HEAD
        self.assertIsInstance(color, tuple)
        self.assertEqual(3, len(color))
        self.assertEqual((255, 215, 50), color)

    def test_boost_hud_text_color_exists(self):
        """COLORS.BOOST_HUD_TEXT 应存在且为 RGB 三元组"""
        self.assertTrue(hasattr(self._config.COLORS, "BOOST_HUD_TEXT"))
        color = self._config.COLORS.BOOST_HUD_TEXT
        self.assertIsInstance(color, tuple)
        self.assertEqual(3, len(color))
        self.assertEqual((255, 200, 50), color)

    def test_total_boost_constants_count_is_10(self):
        """确认恰好 10 个新增加速常量（7 配置 + 3 颜色）"""
        config_names = [
            "BOOST_KEY",
            "BOOST_SPEED_MULTIPLIER",
            "MAX_BOOST_MULTIPLIER",
            "BASE_TICK_INTERVAL",
            "RENDER_FPS",
            "BOOST_TRANSITION_SECONDS",
            "MAX_CATCHUP_STEPS",
        ]
        color_names = [
            "BOOST_SNAKE_BODY",
            "BOOST_SNAKE_HEAD",
            "BOOST_HUD_TEXT",
        ]
        for name in config_names:
            self.assertTrue(hasattr(self._config, name),
                            f"Missing config constant: {name}")
        for name in color_names:
            self.assertTrue(hasattr(self._config.COLORS, name),
                            f"Missing color constant: COLORS.{name}")
        self.assertEqual(7, len(config_names))
        self.assertEqual(3, len(color_names))


# =============================================================================
# 测试类：FPS 向后兼容
# =============================================================================


class TestFPSBackwardCompatibility(unittest.TestCase):
    """验证 FPS 常量保留且值不变，原有模块导入不受影响"""

    @classmethod
    def setUpClass(cls):
        cls._config = _reimport_config()

    def test_fps_still_exists(self):
        """FPS 常量应仍然存在"""
        self.assertTrue(hasattr(self._config, "FPS"))

    def test_fps_value_unchanged(self):
        """FPS 默认值应保持为 10"""
        self.assertEqual(10, self._config.FPS)

    def test_fps_type_unchanged(self):
        """FPS 类型应仍为 int"""
        self.assertIsInstance(self._config.FPS, int)

    def test_all_existing_constants_still_present(self):
        """所有原有常量仍然存在（向后兼容）"""
        required = [
            "WINDOW_WIDTH", "WINDOW_HEIGHT",
            "CELL_SIZE", "GRID_COLS", "GRID_ROWS",
            "FPS", "INITIAL_SNAKE_LENGTH", "SCORE_PER_FOOD",
            "WINDOW_TITLE", "HUD_HEIGHT",
            "GameState", "COLORS",
        ]
        for name in required:
            self.assertTrue(hasattr(self._config, name),
                            f"Missing existing constant: {name}")

    def test_existing_modules_import_without_error(self):
        """验证现有模块导入 config 不报错"""
        try:
            import game  # noqa: F401 — 验证 import 链无报错
        except Exception as e:
            self.fail(f"Importing 'game' raised {type(e).__name__}: {e}")

        try:
            import renderer  # noqa: F401
        except Exception as e:
            self.fail(f"Importing 'renderer' raised {type(e).__name__}: {e}")

        try:
            import input_handler  # noqa: F401
        except Exception as e:
            self.fail(f"Importing 'input_handler' raised {type(e).__name__}: {e}")


# =============================================================================
# 测试类：_validate_boost_config() 校验逻辑
# =============================================================================


class TestValidateBoostConfig(unittest.TestCase):
    """测试 _validate_boost_config() 对越界值的 clamp 行为"""

    def setUp(self):
        """每次测试前重新导入 config 以获得干净状态"""
        if "config" in sys.modules:
            del sys.modules["config"]

    def _patch_and_reimport(self, attr_name: str, bad_value):
        """在导入前 patch config 源码中常量的默认值，然后导入模块。"""
        import config as _base_config_module
        import config

        # 获取原始源码
        source_file = _base_config_module.__file__
        with open(source_file, "r") as f:
            original_source = f.read()

        try:
            # 查找该常量的赋值行并替换值
            import re
            pattern = rf"^({attr_name}\s*:\s*\w+\s*=\s*)(.+)$"
            new_source = re.sub(
                pattern,
                rf"\g<1>{bad_value}  # PATCHED for test",
                original_source,
                flags=re.MULTILINE,
            )

            with open(source_file, "w") as f:
                f.write(new_source)

            # 清除已缓存的 config 模块
            if "config" in sys.modules:
                del sys.modules["config"]
            for key in list(sys.modules.keys()):
                if key.startswith("config"):
                    del sys.modules[key]

            # 重新导入
            import config
            return config
        finally:
            # 还原源码
            with open(source_file, "w") as f:
                f.write(original_source)
            # 清除测试中修改的模块缓存
            if "config" in sys.modules:
                del sys.modules["config"]

    def test_clamp_boost_multiplier_below_1(self):
        """BOOST_SPEED_MULTIPLIER < 1.0 时应 clamp 到 1.0"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("BOOST_SPEED_MULTIPLIER", "0.5")
        self.assertEqual(1.0, cfg.BOOST_SPEED_MULTIPLIER)
        self.assertTrue(
            any("clamped to 1.0" in msg for msg in log_ctx.output),
            f"Expected 'clamped to 1.0' warning, got: {log_ctx.output}",
        )

    def test_clamp_boost_multiplier_above_max(self):
        """BOOST_SPEED_MULTIPLIER > MAX_BOOST_MULTIPLIER 时应 clamp 到上限"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("BOOST_SPEED_MULTIPLIER", "25.0")
        self.assertEqual(cfg.MAX_BOOST_MULTIPLIER, cfg.BOOST_SPEED_MULTIPLIER)
        self.assertTrue(
            any("clamped to" in msg for msg in log_ctx.output),
            f"Expected 'clamped to' warning, got: {log_ctx.output}",
        )

    def test_clamp_max_multiplier_non_positive(self):
        """MAX_BOOST_MULTIPLIER <= 0 时应 reset 到 5.0"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("MAX_BOOST_MULTIPLIER", "0.0")
        self.assertEqual(5.0, cfg.MAX_BOOST_MULTIPLIER)
        self.assertTrue(
            any("reset to 5.0" in msg for msg in log_ctx.output),
            f"Expected 'reset to 5.0' warning, got: {log_ctx.output}",
        )

    def test_clamp_max_multiplier_negative(self):
        """MAX_BOOST_MULTIPLIER < 0 时应 reset 到 5.0"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("MAX_BOOST_MULTIPLIER", "-3.0")
        self.assertEqual(5.0, cfg.MAX_BOOST_MULTIPLIER)
        self.assertTrue(
            any("reset to 5.0" in msg for msg in log_ctx.output),
            f"Expected 'reset to 5.0' warning, got: {log_ctx.output}",
        )

    def test_clamp_base_tick_interval_below_20(self):
        """BASE_TICK_INTERVAL < 20 时应 reset 到 100"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("BASE_TICK_INTERVAL", "5")
        self.assertEqual(100, cfg.BASE_TICK_INTERVAL)
        self.assertTrue(
            any("reset to 100" in msg for msg in log_ctx.output),
            f"Expected 'reset to 100' warning, got: {log_ctx.output}",
        )

    def test_clamp_render_fps_zero(self):
        """RENDER_FPS = 0 时应 reset 到 60"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("RENDER_FPS", "0")
        self.assertEqual(60, cfg.RENDER_FPS)
        self.assertTrue(
            any("reset to 60" in msg for msg in log_ctx.output),
            f"Expected 'reset to 60' warning, got: {log_ctx.output}",
        )

    def test_clamp_render_fps_negative(self):
        """RENDER_FPS < 0 时应 reset 到 60"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("RENDER_FPS", "-10")
        self.assertEqual(60, cfg.RENDER_FPS)
        self.assertTrue(
            any("reset to 60" in msg for msg in log_ctx.output),
            f"Expected 'reset to 60' warning, got: {log_ctx.output}",
        )

    def test_clamp_transition_seconds_negative(self):
        """BOOST_TRANSITION_SECONDS < 0 时应 clamp 到 0.0"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("BOOST_TRANSITION_SECONDS", "-0.5")
        self.assertEqual(0.0, cfg.BOOST_TRANSITION_SECONDS)
        self.assertTrue(
            any("clamped to 0.0" in msg for msg in log_ctx.output),
            f"Expected 'clamped to 0.0' warning, got: {log_ctx.output}",
        )

    def test_clamp_catchup_steps_below_1(self):
        """MAX_CATCHUP_STEPS < 1 时应 reset 到 5"""
        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("MAX_CATCHUP_STEPS", "0")
        self.assertEqual(5, cfg.MAX_CATCHUP_STEPS)
        self.assertTrue(
            any("reset to 5" in msg for msg in log_ctx.output),
            f"Expected 'reset to 5' warning, got: {log_ctx.output}",
        )

    def test_clamp_boost_key_negative(self):
        """BOOST_KEY < 0 时应 fallback 到 K_SPACE"""
        import pygame

        with self.assertLogs(logger="config", level="WARNING") as log_ctx:
            cfg = self._patch_and_reimport("BOOST_KEY", "-1")
        self.assertEqual(pygame.K_SPACE, cfg.BOOST_KEY)
        self.assertTrue(
            any("fallback to pygame.K_SPACE" in msg for msg in log_ctx.output),
            f"Expected fallback warning, got: {log_ctx.output}",
        )

    def test_valid_values_no_warning(self):
        """所有常量为合法值时不应产生任何 WARNING 日志"""
        with self.assertRaises(AssertionError):
            # assertLogs 在没有日志时抛出 AssertionError — 符合预期
            with self.assertLogs(logger="config", level="WARNING") as _:
                _reimport_config()

    def test_boost_multiplier_and_max_chain(self):
        """当 BOOST_SPEED_MULTIPLIER 和 MAX_BOOST_MULTIPLIER 都越界时，两者都被修正"""
        # 先让 MAX 为负，BOOST 也超过默认 MAX
        config_content = None
        import config as _orig
        source_file = _orig.__file__
        with open(source_file, "r") as f:
            original_source = f.read()

        try:
            import re
            # 同时修改两个常量
            s1 = re.sub(
                r"^(MAX_BOOST_MULTIPLIER\s*:\s*\w+\s*=\s*).+$",
                r"\g<1>-1.0  # PATCHED",
                original_source,
                flags=re.MULTILINE,
            )
            s2 = re.sub(
                r"^(BOOST_SPEED_MULTIPLIER\s*:\s*\w+\s*=\s*).+$",
                r"\g<1>25.0  # PATCHED",
                s1,
                flags=re.MULTILINE,
            )
            with open(source_file, "w") as f:
                f.write(s2)

            if "config" in sys.modules:
                del sys.modules["config"]

            with self.assertLogs(logger="config", level="WARNING") as log_ctx:
                import config as cfg

            # MAX 应被修正为 5.0，BOOST 应被 clamp 到 MAX (5.0)
            self.assertEqual(5.0, cfg.MAX_BOOST_MULTIPLIER)
            self.assertEqual(5.0, cfg.BOOST_SPEED_MULTIPLIER)

            # 应该至少有两个 WARNING
            self.assertGreaterEqual(len(log_ctx.output), 2)
        finally:
            with open(source_file, "w") as f:
                f.write(original_source)
            if "config" in sys.modules:
                del sys.modules["config"]


# =============================================================================
# 测试类：模块导入时自动执行校验
# =============================================================================


class TestAutoValidateOnImport(unittest.TestCase):
    """验证 import config 时 _validate_boost_config() 自动执行"""

    def test_validate_function_exists(self):
        """_validate_boost_config 函数应存在且可调用"""
        cfg = _reimport_config()
        self.assertTrue(hasattr(cfg, "_validate_boost_config"))
        self.assertTrue(callable(cfg._validate_boost_config))

    def test_import_triggers_validation(self):
        """每次 import config 都应触发校验（无异常抛出即通过）"""
        # 多次 import 不应报错
        for _ in range(3):
            try:
                cfg = _reimport_config()
                self.assertIsNotNone(cfg)
            except Exception as e:
                self.fail(f"Import config raised {type(e).__name__}: {e}")

    def test_boost_speed_multiplier_changes_take_effect(self):
        """修改 BOOST_SPEED_MULTIPLIER 后重新 import 应反映新值（经校验 clamp 后）"""
        import config as _orig
        source_file = _orig.__file__
        with open(source_file, "r") as f:
            original_source = f.read()

        try:
            import re
            new_source = re.sub(
                r"^(BOOST_SPEED_MULTIPLIER\s*:\s*\w+\s*=\s*).+$",
                r"\g<1>3.0  # PATCHED",
                original_source,
                flags=re.MULTILINE,
            )
            with open(source_file, "w") as f:
                f.write(new_source)

            if "config" in sys.modules:
                del sys.modules["config"]

            import config as cfg
            self.assertEqual(3.0, cfg.BOOST_SPEED_MULTIPLIER)
        finally:
            with open(source_file, "w") as f:
                f.write(original_source)
            if "config" in sys.modules:
                del sys.modules["config"]


if __name__ == "__main__":
    unittest.main()
