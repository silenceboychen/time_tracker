# Python 时间追踪器

一个简单的时间追踪应用程序，用于监控应用程序使用情况。设计为跨平台（Windows、macOS、Linux）。

## 项目结构

```
time_tracker/
├── core/                     # 核心逻辑 (活动监控, 数据存储, 服务)
│   ├── __init__.py
│   ├── activity_monitor.py   # 监控活动窗口
│   ├── data_store.py         # 处理 SQLite 数据库
│   ├── tracker_service.py    # 主要服务逻辑
│   └── utils.py              # 工具函数 (例如，平台检测)
├── cli/                      # 命令行界面
│   ├── __init__.py
│   └── main_cli.py
├── gui/                      # 图形用户界面
│   ├── __init__.py
│   ├── main_window.py        # 主窗口实现
│   └── app.py                # GUI应用入口
├── data/                     # SQLite 数据库文件将存储在此处
│   └── time_tracker.db       # (自动创建)
├── tests/                    # 测试的占位符
│   └── __init__.py
├── main.py                   # 应用程序的主入口点
├── README.md                 # 本文件
└── requirements.txt          # Python 包依赖
```

## 功能 (当前版本)

*   追踪活动的应用程序窗口和标题。
*   将活动持续时间记录到本地 SQLite 数据库。
*   提供命令行界面 (CLI) 用于：
    *   初始化数据库。
    *   在前台运行追踪器服务。
    *   查看已记录活动的摘要。
*   提供图形用户界面 (GUI) 用于：
    *   开始/停止追踪服务。
    *   查看详细活动记录。
    *   按应用程序查看使用时间统计。

## 先决条件

*   Python 3.7+
*   `uv` (推荐, 用于环境和包管理) 或 `pip` (用于包管理)
*   GUI 模式需要 PySide6 (PyQt6 的开源版本)

## 安装步骤

1.  **创建项目目录和文件：**
    您可以手动创建上面列出的文件，或者如果这是一个 git 仓库，则克隆它。

2.  **导航到项目根目录 `time_tracker/`**。

3.  **使用 uv 创建虚拟环境 (推荐)：**
    如果您还没有安装 uv，请先[安装 uv](https://github.com/astral-sh/uv#installation)。
    ```bash
    uv venv
    # Windows 系统
    # .\.venv\Scripts\activate
    # macOS/Linux 系统
    # source .venv/bin/activate
    ```
    如果您希望使用传统的 `venv`：
    ```bash
    python -m venv .venv 
    # Windows 系统
    # .\.venv\Scripts\activate
    # macOS/Linux 系统
    # source .venv/bin/activate
    ```

4.  **安装依赖 (使用 uv)：**
    ```bash
    uv pip install -r requirements.txt
    ```
    或者使用 pip:
    ```bash
    pip install -r requirements.txt
    ```
    **特定平台依赖：**
    `requirements.txt` 文件列出了 `psutil` 和 `PySide6`。您还需要用于活动窗口检测的特定平台库，这些库应手动安装：
    *   **Windows:** `pywin32`
        ```bash
        pip install pywin32
        # 或者使用 uv
        # uv pip install pywin32
        ```
    *   **macOS:** `pyobjc-core`, `pyobjc-framework-Cocoa`, 和 `pyobjc-framework-Quartz`
        ```bash
        pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz
        # 或者使用 uv
        # uv pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz
        ```
        *注意：在 macOS 上，您可能需要在"系统设置" -> "隐私与安全性" -> "辅助功能"中为您的终端或 IDE 授予辅助功能权限，以便应用程序正确识别窗口标题。*
    *   **Linux (X11):** `python-xlib`
        ```bash
        pip install python-xlib
        # 或者使用 uv
        # uv pip install python-xlib
        ```
        *注意：这主要适用于 X11。Wayland 对活动窗口和标题检测的支持更为复杂，可能需要不同的方法（例如，可用的 DBus 接口）。*

## 使用方法

所有命令均从根目录 `time_tracker` 运行。

### CLI 模式

1.  **初始化数据库 (首次运行时执行)：**
    这将创建 `data/time_tracker.db` 文件和必要的表。
    ```bash
    python main.py initdb
    ```

2.  **运行追踪器服务 (前台)：**
    这将开始监控您的活动并记录。按 `Ctrl+C` 停止。
    ```bash
    python main.py run
    # 使用不同的检查间隔运行 (例如，每 2 秒)：
    # python main.py run --interval 2
    ```
    服务会将信息记录到控制台和数据库中。

3.  **查看活动摘要：**
    显示最近记录的活动。
    ```bash
    python main.py view
    # 查看更多条目 (例如，最近 20 条)：
    # python main.py view --limit 20
    ```

### GUI 模式

1.  **启动图形用户界面：**
    ```bash
    python main.py --gui
    # 或使用简写形式:
    # python main.py -g
    ```

2.  **GUI 功能：**
    *   **开始/停止追踪**：点击主界面上的"开始追踪"按钮开始监控活动，再次点击停止。
    *   **查看活动**：应用将在表格中显示最近的活动记录。
    *   **活动摘要**：切换到"活动摘要"标签页查看按应用程序分组的使用时间统计。
    *   **刷新数据**：点击"刷新数据"按钮手动更新显示。
    *   **日期过滤**：选择日期并应用过滤器查看特定日期的活动（待实现功能）。

## 工作原理

*   **`core/activity_monitor.py`**: 使用特定平台的 API 定期检查当前活动的窗口及其标题。
*   **`core/tracker_service.py`**:
    *   将当前活动窗口与先前记录的窗口进行比较。
    *   如果发生更改，则计算先前活动所花费的时间并记录。
    *   开始计时新活动。
*   **`core/data_store.py`**: 管理一个 SQLite 数据库 (`data/time_tracker.db`) 来存储 `activity_log` 记录。每条记录包括时间戳、应用程序名称、窗口标题、持续时间和活动类型。
*   **`cli/main_cli.py`**: 提供命令行参数以与追踪器交互。
*   **`gui/main_window.py`**: 实现图形用户界面，包括活动表格显示和基本的统计视图。

## 未来增强功能

*   **后台服务：** 在每个操作系统上将追踪器作为正常的后台守护进程/服务运行。
*   **改进的空闲检测：** 使用全局键盘/鼠标侦听器实现更强大的空闲检测。
*   **应用程序分类：** 允许用户为应用程序定义类别。
*   **数据导出：** 支持将数据导出为CSV或其他格式。
*   **日期过滤：** 根据日期过滤和查看活动数据。
*   **报告和图表：** 提供使用情况的可视化图表。
*   **配置文件：** 用于设置。
*   **自定义分类：** 允许用户对活动进行自定义分类和标记。
*   **Wayland 支持 (Linux)：** 改进 Wayland 的活动窗口检测。

## 故障排除

*   **特定平台库的 "ModuleNotFoundError"：** 确保您已为您的操作系统安装了正确的库。
*   **权限 (macOS)：** 如果窗口标题未正确检测，请检查辅助功能权限。
*   **X11 错误 (Linux)：** 如果在 Wayland 上，`python-xlib` 可能无法按预期工作。
*   **GUI 启动错误：** 如果启动 GUI 时出现错误，确保已安装 `PySide6`（`pip install PySide6`）。 