import sys
import os
import logging

# 获取项目根目录，确保可以导入core和gui模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 确保GUI模块可被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QLibraryInfo, QTranslator
from main_window import MainWindow

def setup_logging():
    """设置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(PROJECT_ROOT, 'data', 'app.log'), encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("GUI应用启动")
    return logger

def main():
    """
    GUI应用程序的主入口
    """
    # 设置日志记录
    logger = setup_logging()
    
    # 创建Qt应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName("时间追踪器")
    app.setOrganizationName("时间追踪器")
    app.setOrganizationDomain("timetracker.example.com")
    
    # 加载翻译
    translator = QTranslator()
    if translator.load("qt_zh_CN.qm", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    
    # 创建并显示主窗口
    try:
        main_window = MainWindow()
        main_window.show()
        logger.info("主窗口已显示")
        
        # 运行应用程序事件循环
        return app.exec_()
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 