"""
贪吃蛇游戏入口模块

使用 try/except 检测 Pygame 是否安装，若未安装则输出安装提示并退出。
初始化 Pygame，创建 Game 实例，启动主循环。
"""

import sys


def main() -> None:
    """游戏入口：检查依赖 -> 初始化 Pygame -> 创建 Game -> 运行 -> 退出。"""
    # 检查 Pygame 依赖
    try:
        import pygame  # noqa: F401 (仅用于依赖检查)
    except ImportError:
        print("Pygame is not installed. Please run: pip install pygame",
              file=sys.stderr)
        sys.exit(1)

    import pygame
    from game import Game

    # 初始化 Pygame
    pygame.init()

    # 创建游戏实例并运行主循环
    try:
        game = Game()
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
