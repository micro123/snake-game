# 贪吃蛇 (Snake Game)

基于 Pygame 实现的经典贪吃蛇游戏。玩家使用键盘方向键控制蛇的移动方向，吃到食物后蛇身增长并获得分数。蛇撞到墙壁或自身时游戏结束。

## 环境要求

- Python 3.x
- Pygame >= 2.0

## 安装

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux / macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

游戏窗口尺寸固定为 800x600 像素，启动即玩，无需额外配置。

## 操作说明

| 按键 | 功能 |
|------|------|
| 方向键 (上/下/左/右) | 控制蛇的移动方向 |
| R | 游戏结束后重新开始 |
| Q | 游戏结束后退出 |
| 关闭窗口 | 任意时刻退出游戏 |

### 注意事项

- 蛇不能直接反向移动（例如向右移动时无法直接左转），反向输入会被忽略。
- 同一帧内按下多个方向键时，只有最后一个有效方向键生效。
- 窗口失去焦点时游戏自动暂停，重新获得焦点后恢复。

## 游戏规则

- 蛇初始长度为 3 节，默认向右移动。
- 每吃到一个食物，蛇身增长 1 节，分数增加 10 分。
- 食物随机出现在未被蛇身占据的空白格子中。
- 蛇头撞到游戏区域边界（四面墙壁）时游戏结束。
- 蛇头撞到自身身体任意一节时游戏结束。
- 当蛇身占满所有格子时，玩家胜利。

## 文件结构

| 文件 | 说明 |
|------|------|
| `main.py` | 程序入口：检查 Pygame 依赖、初始化、启动主循环 |
| `config.py` | 常量配置：窗口尺寸、网格参数、颜色定义、GameState 枚举 |
| `game.py` | 游戏协调器：组件管理、状态机、主循环编排 |
| `snake.py` | Snake 实体：蛇身坐标管理、移动、方向切换、碰撞检测 |
| `food.py` | Food 实体：食物位置管理与随机生成 |
| `renderer.py` | 渲染层：图层化绘制（背景/网格/蛇/食物/HUD/遮罩）、帧率控制 |
| `input_handler.py` | 输入处理：键盘事件映射、反向拦截、焦点检测 |
| `requirements.txt` | Python 依赖清单 |
| `test_snake.py` | Snake 类单元测试 |
| `test_food.py` | Food 类单元测试 |
| `test_renderer.py` | Renderer 类单元测试 |
| `test_input_handler.py` | InputHandler 类单元测试 |
| `test_game.py` | Game 类单元测试 |
| `test_main.py` | main 入口点单元测试 |

### 架构说明

项目采用分层架构，核心模块之间的依赖关系如下：

```
main.py          # 入口点
  └── game.py    # 游戏协调器
        ├── snake.py         # 蛇逻辑（纯 Python，无 Pygame 依赖）
        ├── food.py          # 食物逻辑（纯 Python，无 Pygame 依赖）
        ├── renderer.py      # 渲染层（封装 Pygame 绘制调用）
        └── input_handler.py # 输入处理（封装 Pygame 事件处理）
config.py         # 常量定义（所有模块共享，无 Pygame 依赖）
```

- `snake.py` 和 `food.py` 是纯逻辑模块，不依赖 Pygame，可独立测试。
- `renderer.py` 和 `input_handler.py` 封装 Pygame 相关调用，通过抽象隔离游戏逻辑与底层 API。
- `config.py` 集中管理所有常量，避免魔术数字散布各处。
- `game.py` 中的 `Game` 类作为协调器，持有全部组件并编排主循环。

## 运行测试

```bash
# 运行全部测试
python -m pytest test_*.py -v

# 或使用内置 unittest
python -m unittest discover -v
```
