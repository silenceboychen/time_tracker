import sys
import os
import logging
import argparse

# Ensure the project root is in sys.path so that 'cli', 'core' and 'gui' can be imported.
# This is particularly important if main.py is the entry point and it needs to find its sibling packages.
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_DIR)

def setup_logging(verbose=False):
    """配置日志记录"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="时间追踪器 - 跨平台活动监控应用")
    
    # 顶级参数
    parser.add_argument("--verbose", "-v", action="store_true", help="启用详细日志记录")
    parser.add_argument("--gui", "-g", action="store_true", help="启动图形界面模式")
    
    # 子命令（仅在CLI模式下有效）
    subparsers = parser.add_subparsers(title="commands", dest="command", help="可用命令")
    
    # 初始化数据库命令
    init_db_parser = subparsers.add_parser("initdb", help="初始化追踪器数据库")
    
    # 查看摘要命令
    view_parser = subparsers.add_parser("view", help="查看已记录活动的摘要")
    view_parser.add_argument("-l", "--limit", type=int, default=10, help="要显示的最近条目数（默认：10）")
    
    # 运行追踪器命令（前台）
    run_parser = subparsers.add_parser("run", help="在前台运行追踪器服务（按Ctrl+C停止）")
    run_parser.add_argument("-i", "--interval", type=int, default=5, help="活动检查间隔（秒，默认：5）")
    
    return parser.parse_args()

def main():
    """应用程序主入口点"""
    args = parse_args()
    logger = setup_logging(args.verbose)
    
    # 创建data目录如果不存在
    data_dir = os.path.join(PROJECT_ROOT_DIR, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logger.info(f"创建数据目录: {data_dir}")
    
    try:
        if args.gui:
            # GUI模式
            logger.info("启动GUI模式")
            from gui.app import main as run_gui
            return run_gui()
        else:
            # CLI模式
            logger.info("启动CLI模式")
            from cli.main_cli import main as run_cli
            return run_cli()
    except ImportError as e:
        if "PySide6" in str(e) and args.gui:
            logger.critical("无法导入PySide6。请确保已安装PySide6: 'pip install PySide6'")
            print("错误: 启动GUI模式需要安装PySide6。请运行: pip install PySide6")
        else:
            logger.critical(f"导入错误: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.critical(f"应用程序启动过程中发生意外错误: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 