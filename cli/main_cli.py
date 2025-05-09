import argparse
import sys
import os
import logging
import sqlite3

# Adjust Python's import path to find modules in the parent directory (project root)
# This allows 'from core import ...' to work when cli/main_cli.py is part of the execution flow initiated from main.py
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_DIR)

from core import data_store
from core.tracker_service import TimeTrackerService

logger = logging.getLogger(__name__) # Get a logger for the CLI module
# Configure logging for the CLI part if needed, or rely on root logger config
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def view_summary(args):
    """Displays a summary of logged activities based on provided arguments."""
    limit = args.limit
    print(f"\n--- 最近活动摘要（最后 {limit} 条）---")
    try:
        # Ensure DB is initialized before trying to read (though 'initdb' command is preferred for explicit init)
        # data_store.init_db() # Optionally, ensure DB exists, or let it fail if not initialized
        summary = data_store.get_activity_summary(limit=limit)
        if not summary:
            print("尚未记录任何活动。运行 'python main.py initdb' 然后 'python main.py run'。")
            return
        
        print(f"{'时间戳':<20} | {'应用名称':<25} | {'窗口标题':<50} | {'持续时间(秒)':<12} | {'类型'}")
        print("-" * 120)
        for row_data in summary:
            if isinstance(row_data, (list, tuple)) and len(row_data) == 5:
                timestamp, app_name, window_title, duration_seconds, activity_type = row_data
                print(
                    f"{str(timestamp):<20} | {app_name[:25]:<25} | {window_title[:50]:<50} | {duration_seconds:<12} | {activity_type}"
                )
            else:
                logger.warning(f"跳过数据库中格式错误的记录：{row_data}")

    except sqlite3.OperationalError as e:
        logger.error(f"数据库错误：{e}。请确保使用 'python main.py initdb' 初始化数据库")
    except Exception as e:
        logger.error(f"获取摘要时出错：{e}", exc_info=True)
    print("--- 摘要结束 ---")

def run_tracker_foreground(args):
    """Runs the tracker service in the foreground."""
    print(f"在前台启动时间追踪服务。间隔：{args.interval}秒。按Ctrl+C停止。")
    try:
        service = TimeTrackerService(check_interval=args.interval)
        service.run()
    except Exception as e:
        logger.error(f"无法启动或运行追踪服务：{e}", exc_info=True)
        print("无法启动追踪服务。查看日志获取详细信息。")

def initialize_database(args):
    """Command to explicitly initialize the database."""
    print("初始化数据库...")
    try:
        data_store.init_db()
        print("数据库初始化完成。")
    except Exception as e:
        logger.error(f"初始化数据库失败：{e}", exc_info=True)
        print("数据库初始化失败。查看日志获取详细信息。")

def main():
    """Main entry point for the CLI application."""
    # Check if args were parsed by main.py (parent process)
    # If not, parse them directly
    if len(sys.argv) > 1 and hasattr(sys, 'argv'):
        parser = argparse.ArgumentParser(description="时间追踪器 CLI - 管理和运行时间追踪服务。")
        
        # 为向后兼容性添加verbose标志
        parser.add_argument("--verbose", "-v", action="store_true", help="启用详细日志记录以便调试。")
        
        subparsers = parser.add_subparsers(title="commands", dest="command", help="可用命令")
        
        # 初始化数据库命令
        init_db_parser = subparsers.add_parser("initdb", help="初始化追踪器数据库。")
        init_db_parser.set_defaults(func=initialize_database)
        
        # 查看摘要命令
        view_parser = subparsers.add_parser("view", help="查看已记录活动的摘要。")
        view_parser.add_argument("-l", "--limit", type=int, default=10, help="要显示的最近条目数（默认：10）。")
        view_parser.set_defaults(func=view_summary)
        
        # 运行追踪器命令（前台）
        run_parser = subparsers.add_parser("run", help="在前台运行追踪器服务（按Ctrl+C停止）。")
        run_parser.add_argument("-i", "--interval", type=int, default=5, help="活动检查间隔（秒，默认：5）。")
        run_parser.set_defaults(func=run_tracker_foreground)
        
        args = parser.parse_args()
        
        # 根据verbose标志设置根记录器的级别
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("CLI为所有模块启用了详细日志记录。")
        else:
            logging.getLogger().setLevel(logging.INFO)
            
        if hasattr(args, 'func') and args.func:
            if args.command:
                logger.debug(f"执行命令：{args.command}，参数：{args}")
            args.func(args)
        else:
            # 如果没有给出命令，打印帮助
            if not hasattr(args, 'command') or not args.command:
                logger.debug("未提供命令，打印帮助。")
                parser.print_help()
    else:
        # 如果没有命令行参数，并且是通过main.py调用的（以下代码不会运行）
        # main.py应该已经处理了这个情况
        if len(sys.argv) <= 1:
            print("请提供命令：initdb, view 或 run")
            print("使用 --help 获取更多信息")
            return 1
    
    return 0

if __name__ == "__main__":
    # This allows running main_cli.py directly for testing CLI components,
    # though the primary entry point is expected to be main.py from the project root.
    print("直接运行CLI模块...")
    sys.exit(main()) 