"""
main 模块单元测试

测试入口点 main() 函数：Pygame 缺失时的提示与退出（sys.exit(1)）、
正常启动流程结构验证（try/finally 保障、调用链）、
__name__ == '__main__' 保护、requirements.txt 内容。
使用 Python 标准库 unittest 框架，不依赖 Pygame 安装。
"""

import inspect
import os
import builtins
import sys
import unittest
from unittest.mock import MagicMock, patch


# =============================================================================
# 测试辅助
# =============================================================================


def _make_selective_import_fail(target_module: str):
    """创建一个选择性 import 拦截函数，仅对指定模块抛出 ImportError。"""
    original_import = builtins.__import__

    def selective_import(name, *args, **kwargs):
        if name == target_module:
            raise ImportError(f"No module named '{target_module}'")
        return original_import(name, *args, **kwargs)

    return selective_import


# =============================================================================
# 测试类：Pygame 缺失场景（运行时测试，不需要 Pygame）
# =============================================================================


class TestMainImportError(unittest.TestCase):
    """测试 Pygame 未安装时的行为（运行时验证）"""

    def test_missing_pygame_exits_with_code_1(self):
        """Pygame 缺失时 sys.exit(1) 被调用"""
        from main import main

        with patch(
            'builtins.__import__',
            side_effect=_make_selective_import_fail('pygame'),
        ):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(1, ctx.exception.code)

    def test_missing_pygame_prints_hint_to_stderr(self):
        """Pygame 缺失时向 stderr 输出 pip install 提示"""
        from main import main

        with patch(
            'builtins.__import__',
            side_effect=_make_selective_import_fail('pygame'),
        ):
            with patch.object(sys.stderr, 'write') as mock_write:
                with self.assertRaises(SystemExit):
                    main()
                calls = [c[0][0] for c in mock_write.call_args_list]
                combined = ''.join(calls)
                self.assertIn('pip install pygame', combined)

    def test_missing_pygame_does_not_attempt_init(self):
        """Pygame 缺失时 sys.exit(1) 阻止后续代码执行"""
        from main import main

        with patch(
            'builtins.__import__',
            side_effect=_make_selective_import_fail('pygame'),
        ):
            with self.assertRaises(SystemExit):
                main()
            # 如果 sys.exit 被 patch 了仍会走到后续逻辑，需要实际抛出
            self.assertTrue(True)  # 到达这里说明 SystemExit 被正确抛出


# =============================================================================
# 测试类：main() 源代码结构验证（不执行 main，仅检查代码结构）
# =============================================================================


class TestMainStructure(unittest.TestCase):
    """通过源代码检查验证 main.py 的代码结构符合设计规格"""

    @classmethod
    def setUpClass(cls):
        """读取 main 模块的源代码"""
        from main import main
        cls._source = inspect.getsource(main)

    def test_has_try_except_for_import_error(self):
        """main() 包含 try/except ImportError 用于依赖检查"""
        self.assertIn('try:', self._source,
                      "main() must have try block for pygame import")
        self.assertIn('ImportError', self._source,
                      "main() must catch ImportError")

    def test_has_finally_block_with_pygame_quit(self):
        """main() 包含 finally 块调用 pygame.quit()"""
        self.assertIn('finally:', self._source,
                      "main() must have a finally block")
        self.assertIn('pygame.quit()', self._source,
                      "finally must call pygame.quit()")

    def test_has_pygame_init_before_try(self):
        """pygame.init() 在 try/finally 块之前调用"""
        init_pos = self._source.find('pygame.init()')
        # 使用 rfind 找到第二个 try 块（try/finally 的 try），
        # 因为第一个 try 是 try/except ImportError
        try_pos = self._source.rfind('try:')
        self.assertGreater(init_pos, -1, "pygame.init() not found")
        self.assertGreater(try_pos, -1, "try not found")
        self.assertLess(init_pos, try_pos,
                        "pygame.init() must appear before try/finally block")

    def test_has_game_instantiation_inside_try(self):
        """Game() 实例化在 try 块内"""
        self.assertIn('Game()', self._source,
                      "main() must instantiate Game")

    def test_has_game_run_inside_try(self):
        """game.run() 在 try 块内（受 finally 保护）"""
        self.assertIn('.run()', self._source,
                      "main() must call game.run()")

    def test_has_pip_install_hint_in_import_error(self):
        """ImportError 处理中包含 pip install 提示"""
        self.assertIn('pip install pygame', self._source,
                      "main() must show pip install hint")

    def test_has_sys_exit_in_import_error(self):
        """ImportError 处理中包含 sys.exit(1)"""
        self.assertIn('sys.exit(1)', self._source,
                      "main() must call sys.exit(1) on ImportError")

    def test_try_block_contains_game_run(self):
        """验证 try 块包含 Game 实例化和 run 调用"""
        try_start = self._source.find('try:')
        finally_pos = self._source.find('finally:')
        try_block = self._source[try_start:finally_pos]

        self.assertIn('Game()', try_block,
                      "Game() must be inside try block")
        self.assertIn('.run()', try_block,
                      "run() must be inside try block")

    def test_finally_block_contains_pygame_quit(self):
        """验证 finally 块包含 pygame.quit()"""
        finally_start = self._source.find('finally:')
        finally_block = self._source[finally_start:]

        self.assertIn('pygame.quit()', finally_block,
                      "finally block must contain pygame.quit()")


# =============================================================================
# 测试类：__name__ == '__main__' 保护
# =============================================================================


class TestMainGuard(unittest.TestCase):
    """测试 __name__ == '__main__' 保护"""

    def test_main_not_called_on_import(self):
        """导入 main 模块时不应自动执行 main()"""
        # 通过检查模块级别的源代码来验证 guard 存在
        with open(os.path.join(os.path.dirname(__file__), 'main.py'), 'r') as f:
            module_source = f.read()

        # 双引号或单引号均接受
        has_guard = ("__name__ == '__main__'" in module_source or
                     '__name__ == "__main__"' in module_source)
        self.assertTrue(has_guard,
                        "main.py must have __name__ == '__main__' guard")
        self.assertIn('main()', module_source,
                      "main.py must call main() under the guard")

    def test_main_is_callable_function(self):
        """main 应为可调用函数"""
        from main import main as main_func
        self.assertTrue(callable(main_func))

    def test_main_has_docstring(self):
        """main 函数应有文档字符串"""
        from main import main as main_func
        self.assertIsNotNone(main_func.__doc__)
        self.assertGreater(len(main_func.__doc__), 0)

    def test_main_has_return_type_annotation(self):
        """main 函数应有返回类型注解 -> None"""
        from main import main as main_func
        annotations = getattr(main_func, '__annotations__', {})
        self.assertIn('return', annotations,
                      "main() should have return type annotation")


# =============================================================================
# 测试类：requirements.txt
# =============================================================================


class TestRequirementsFile(unittest.TestCase):
    """测试 requirements.txt 内容"""

    def setUp(self):
        self._req_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'requirements.txt'
        )

    def test_file_exists(self):
        """requirements.txt 文件存在"""
        self.assertTrue(
            os.path.exists(self._req_path),
            f"requirements.txt not found at {self._req_path}"
        )

    def test_contains_pygame(self):
        """requirements.txt 包含 pygame 依赖"""
        with open(self._req_path, 'r') as f:
            content = f.read()
        self.assertIn('pygame', content,
                      "requirements.txt must contain 'pygame'")

    def test_version_specifier_is_gte_2(self):
        """pygame 版本说明符应为 >=2.0 而非固定版本"""
        with open(self._req_path, 'r') as f:
            content = f.read()

        self.assertNotIn(
            'pygame==', content,
            "requirements.txt should use >=, not == for pygame version"
        )
        self.assertIn(
            'pygame>=2.0', content,
            "requirements.txt must contain 'pygame>=2.0'"
        )

    def test_no_other_dependencies(self):
        """验证文件中 pygame 是唯一的依赖项"""
        with open(self._req_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(
            1, len(lines),
            f"requirements.txt should have exactly 1 dependency, got {lines}"
        )


# =============================================================================
# 测试类：模块级别源码检查
# =============================================================================


class TestMainModuleLevel(unittest.TestCase):
    """检查 main.py 模块级别的代码质量"""

    def test_file_starts_with_docstring(self):
        """main.py 应有模块级文档字符串"""
        import main
        self.assertIsNotNone(main.__doc__)
        self.assertGreater(len(main.__doc__), 10,
                           "Module docstring is too short or missing")

    def test_only_imports_sys_at_module_level(self):
        """模块级别只应导入 sys（pygame 在函数内导入）"""
        with open(os.path.join(os.path.dirname(__file__), 'main.py'), 'r') as f:
            source = f.read()

        # 确认模块级 import 只有 sys
        # 在 main() 函数定义之前检索 import 语句
        func_def_pos = source.find('def main()')
        module_level = source[:func_def_pos]

        self.assertIn('import sys', module_level,
                      "Module level should import sys")
        # pygame 不应当在模块级别导入
        self.assertNotIn('import pygame', module_level,
                         "Module level should NOT import pygame")

    def test_main_function_is_async_safe(self):
        """main() 是同步函数"""
        import main
        self.assertFalse(inspect.iscoroutinefunction(main.main),
                         "main() should be synchronous")


if __name__ == "__main__":
    unittest.main()
