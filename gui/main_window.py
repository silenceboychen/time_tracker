from PySide6.QtWidgets import (
    QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QTimeEdit, QDateEdit, QSplitter, QFrame, QStatusBar
)
from PySide6.QtCore import Qt, QTimer, QDate, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction

import sys
import os
import logging
import datetime
from pathlib import Path

# 获取项目根目录，确保可以导入core模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.tracker_service import TimeTrackerService
from core import data_store

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """时间追踪应用的主窗口"""
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle("时间追踪器")
        self.resize(900, 600)
        
        # 初始化追踪服务(但不启动)
        self.tracker_service = None
        self.is_tracking = False
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_data)
        
        # 创建UI
        self.setup_ui()
        self.setup_menu()
        
        # 初始化数据
        self.initialize_db_if_needed()
        self.refresh_data()
        
        # 设置状态栏
        self.statusBar().showMessage("就绪")
        
    def setup_ui(self):
        """设置窗口UI组件"""
        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # 控制区域
        control_layout = QHBoxLayout()
        
        # 追踪控制按钮
        self.btn_start_stop = QPushButton("开始追踪")
        self.btn_start_stop.setMinimumWidth(120)
        self.btn_start_stop.clicked.connect(self.toggle_tracking)
        
        # 刷新按钮
        self.btn_refresh = QPushButton("刷新数据")
        self.btn_refresh.setMinimumWidth(120)
        self.btn_refresh.clicked.connect(self.refresh_data)
        
        # 日期选择器(用于过滤)
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日期:"))
        self.date_selector = QDateEdit()
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        date_layout.addWidget(self.date_selector)
        
        # 应用过滤器
        self.btn_apply_filter = QPushButton("应用过滤")
        self.btn_apply_filter.clicked.connect(self.apply_filters)
        
        # 添加控件到控制布局
        control_layout.addWidget(self.btn_start_stop)
        control_layout.addWidget(self.btn_refresh)
        control_layout.addLayout(date_layout)
        control_layout.addWidget(self.btn_apply_filter)
        control_layout.addStretch()
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 活动表格
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(5)
        self.activities_table.setHorizontalHeaderLabels(["时间", "应用", "窗口标题", "持续时间", "活动类型"])
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activities_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.activities_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.activities_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.activities_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 摘要表格(未来实现应用使用时间统计)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(3)
        self.summary_table.setHorizontalHeaderLabels(["应用", "总时间", "百分比"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 添加标签页
        self.tabs.addTab(self.activities_table, "详细活动")
        self.tabs.addTab(self.summary_table, "活动摘要")
        
        # 状态信息
        self.status_label = QLabel("当前未追踪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFrameShape(QFrame.Panel)
        self.status_label.setFrameShadow(QFrame.Sunken)
        self.status_label.setMinimumHeight(30)
        
        # 添加所有组件到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.status_label)
        
    def setup_menu(self):
        """设置菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        export_action = QAction("导出数据...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menu_bar.addMenu("工具")
        
        settings_action = QAction("设置...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def initialize_db_if_needed(self):
        """确保数据库已初始化"""
        try:
            db_path = data_store.DB_PATH
            if not os.path.exists(db_path):
                logger.info("初始化数据库...")
                data_store.init_db()
                self.statusBar().showMessage("数据库已初始化", 3000)
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            QMessageBox.critical(self, "错误", f"初始化数据库失败: {e}")
            
    def toggle_tracking(self):
        """开始或停止追踪服务"""
        if not self.is_tracking:
            # 开始追踪
            try:
                self.tracker_service = TimeTrackerService(check_interval=5)
                # 创建一个单独的线程来运行追踪服务
                # 注意：此简化实现在当前线程中运行，实际应用中应使用QThread
                # 创建一个定时器来模拟定时更新 - 实际应用中应使用信号/槽通信
                self.update_timer.start(10000)  # 每10秒更新一次UI
                
                # 在实际应用中，应使用类似以下代码:
                # self.tracker_thread = QThread()
                # self.tracker_service.moveToThread(self.tracker_thread)
                # self.tracker_thread.started.connect(self.tracker_service.run)
                # self.tracker_thread.start()
                
                # 模拟开始追踪的效果
                self.is_tracking = True
                self.btn_start_stop.setText("停止追踪")
                self.status_label.setText("正在追踪活动...")
                self.statusBar().showMessage("追踪服务已开始", 3000)
            except Exception as e:
                logger.error(f"启动追踪服务失败: {e}")
                QMessageBox.critical(self, "错误", f"启动追踪服务失败: {e}")
        else:
            # 停止追踪
            try:
                self.update_timer.stop()
                
                # 在实际应用中，应使用类似以下代码:
                # self.tracker_service.stop()
                # self.tracker_thread.quit()
                # self.tracker_thread.wait()
                
                self.is_tracking = False
                self.btn_start_stop.setText("开始追踪")
                self.status_label.setText("当前未追踪")
                self.statusBar().showMessage("追踪服务已停止", 3000)
            except Exception as e:
                logger.error(f"停止追踪服务失败: {e}")
                QMessageBox.critical(self, "错误", f"停止追踪服务失败: {e}")
        
    def refresh_data(self):
        """刷新活动数据表格"""
        try:
            self.statusBar().showMessage("正在刷新数据...")
            
            # 获取活动数据
            activities = data_store.get_activity_summary(limit=50)  # 获取更多条目
            
            # 更新活动表格
            self.activities_table.setRowCount(0)  # 清空表格
            for row_idx, activity in enumerate(activities):
                self.activities_table.insertRow(row_idx)
                
                # 格式化时间戳和持续时间
                timestamp, app_name, window_title, duration_seconds, activity_type = activity
                
                # 创建并设置每个单元格的项目
                time_item = QTableWidgetItem(str(timestamp))
                app_item = QTableWidgetItem(app_name)
                title_item = QTableWidgetItem(window_title)
                
                # 格式化持续时间为分:秒
                minutes, seconds = divmod(duration_seconds, 60)
                duration_str = f"{minutes}分{seconds}秒"
                duration_item = QTableWidgetItem(duration_str)
                
                type_item = QTableWidgetItem(activity_type)
                
                # 添加项目到表格
                self.activities_table.setItem(row_idx, 0, time_item)
                self.activities_table.setItem(row_idx, 1, app_item)
                self.activities_table.setItem(row_idx, 2, title_item)
                self.activities_table.setItem(row_idx, 3, duration_item)
                self.activities_table.setItem(row_idx, 4, type_item)
            
            # 更新摘要表格 (简单实现)
            self.update_summary_table(activities)
            
            self.statusBar().showMessage("数据已刷新", 3000)
        except Exception as e:
            logger.error(f"刷新数据失败: {e}")
            self.statusBar().showMessage(f"刷新数据失败: {e}", 5000)
    
    def update_summary_table(self, activities):
        """更新摘要统计表格"""
        # 按应用程序分组并计算总时间
        app_times = {}
        total_time = 0
        
        for activity in activities:
            _, app_name, _, duration, _ = activity
            if app_name not in app_times:
                app_times[app_name] = 0
            app_times[app_name] += duration
            total_time += duration
        
        # 排序应用程序，按时间降序
        sorted_apps = sorted(app_times.items(), key=lambda x: x[1], reverse=True)
        
        # 更新摘要表格
        self.summary_table.setRowCount(0)
        for row_idx, (app_name, duration) in enumerate(sorted_apps):
            self.summary_table.insertRow(row_idx)
            
            app_item = QTableWidgetItem(app_name)
            
            # 格式化时间为小时:分钟:秒
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            time_item = QTableWidgetItem(time_str)
            
            # 计算百分比
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            percent_item = QTableWidgetItem(f"{percentage:.1f}%")
            
            self.summary_table.setItem(row_idx, 0, app_item)
            self.summary_table.setItem(row_idx, 1, time_item)
            self.summary_table.setItem(row_idx, 2, percent_item)
    
    def apply_filters(self):
        """应用过滤器"""
        # TODO: 实现真正的日期过滤
        self.statusBar().showMessage("日期过滤功能尚未实现", 3000)
    
    def export_data(self):
        """导出数据功能"""
        QMessageBox.information(self, "信息", "导出功能尚未实现")
    
    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "信息", "设置功能尚未实现")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "<h3>时间追踪器</h3>"
                         "<p>版本 0.1</p>"
                         "<p>一个简单的跨平台时间追踪应用</p>"
                         "<p>支持Windows、macOS和Linux</p>")
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.is_tracking:
            reply = QMessageBox.question(self, '确认退出', 
                                       '追踪服务正在运行。确定要退出吗？',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 停止追踪服务
                if self.tracker_service:
                    self.update_timer.stop()
                    # 在实际应用中: self.tracker_service.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 