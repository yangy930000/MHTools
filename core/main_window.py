"""
主窗口 - 框架的UI入口
"""
import os
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QToolBar, QLabel, QLineEdit, QPushButton, QFrame, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QTabBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import (
    QIcon, QAction, QFont, QFontDatabase, QPixmap, QPainter, QColor
)


"""
主窗口 - 框架的UI入口
"""
import os
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QToolBar, QLabel, QLineEdit, QPushButton, QFrame, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QTabBar, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMarginsF
from PyQt6.QtGui import (
    QIcon, QAction, QFont, QFontDatabase, QPixmap, QPainter, QColor,
    QLinearGradient, QPalette
)


# ==================== 颜色主题 ====================
class Theme:
    """应用主题配色"""
    # 主色调 - 柔和的蓝紫色
    PRIMARY = "#5c7cfa"           # 主题蓝紫色
    PRIMARY_HOVER = "#4263eb"     # 悬停颜色
    PRIMARY_LIGHT = "#748ffc"     # 浅色

    # 背景色 - 柔和的灰白色，不刺眼
    BG_DARK = "#212529"           # 深色（用于极深色场景）
    BG_MAIN = "#f1f3f5"           # 主背景 - 柔和灰白
    BG_CARD = "#ffffff"           # 卡片白色
    BG_INPUT = "#f8f9fa"          # 输入框背景

    # 文字色 - 深灰色而非纯黑，更柔和
    TEXT_PRIMARY = "#343a40"      # 主文字 - 深灰
    TEXT_SECONDARY = "#6c757d"    # 次要文字 - 中灰
    TEXT_LIGHT = "#adb5bd"        # 浅色文字

    # 功能色
    SUCCESS = "#40c057"           # 成功绿
    WARNING = "#fab005"           # 警告黄
    DANGER = "#fa5252"            # 危险红
    INFO = "#228be6"              # 信息蓝

    # 边框和分割 - 柔和的灰色
    BORDER = "#dee2e6"
    BORDER_LIGHT = "#e9ecef"

    # 渐变色
    GRADIENT_START = "#5c7cfa"
    GRADIENT_END = "#748ffc"


class GlobalHeader(QWidget):
    """全局数据/功能栏 - 位于UI顶部"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(56)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # 标题
        title = QLabel("游戏助手")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet(f"color: {Theme.BORDER};")
        layout.addWidget(separator)

        # 创建三个全局数据输入框
        self._create_input_field(layout, "RMB汇率", "rmb_rate", "元/万", 80)
        self._create_input_field(layout, "体力成本", "stamina_cost", "梦幻币/点", 110)
        self._create_input_field(layout, "活力成本", "energy_cost", "梦幻币/点", 110)

        # 弹性空间
        layout.addStretch()

        # 整体背景
        self.setStyleSheet(f"""
            GlobalHeader {{
                background-color: {Theme.BG_CARD};
                border-bottom: 1px solid {Theme.BORDER_LIGHT};
            }}
        """)

    def _create_input_field(self, layout, label_text, key, unit, width):
        """创建单个数据输入框"""
        container = QFrame()
        container.setFixedHeight(36)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 0 8px;
            }}
        """)

        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(6)

        # 标签
        label = QLabel(label_text)
        label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY};")
        h_layout.addWidget(label)

        # 输入框
        edit = QLineEdit()
        edit.setFixedWidth(width)
        edit.setFixedHeight(28)
        edit.setPlaceholderText("0")
        edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 13px;
                color: {Theme.TEXT_PRIMARY};
                background-color: {Theme.BG_CARD};
            }}
            QLineEdit:focus {{
                border-color: {Theme.PRIMARY};
            }}
        """)
        # 连接回车和失去焦点事件保存数据
        edit.editingFinished.connect(lambda: self._save_data(key, edit))
        h_layout.addWidget(edit)

        # 单位
        unit_label = QLabel(unit)
        unit_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_LIGHT};")
        h_layout.addWidget(unit_label)

        layout.addWidget(container)

        # 保存引用
        if not hasattr(self, '_inputs'):
            self._inputs = {}
        self._inputs[key] = edit

    def load_data(self):
        """从数据库加载数据"""
        if not self.main_window:
            return

        db = self.main_window.db

        # 确保历史记录表存在
        db.ensure_table("rmb_rate_history", {
            "rate": "REAL NOT NULL",
            "record_date": "TEXT NOT NULL"
        })

        # 加载三个数据
        data_keys = ['rmb_rate', 'stamina_cost', 'energy_cost']
        for key in data_keys:
            value = db.get_global_data(f"global_{key}", "")
            if value and key in self._inputs:
                self._inputs[key].setText(str(value))

    def _save_data(self, key, edit):
        """保存数据到数据库"""
        value = edit.text().strip()
        if not value:
            return

        if not self.main_window or not self.main_window.db:
            return

        try:
            db = self.main_window.db

            # RMB汇率需要记录历史
            if key == 'rmb_rate':
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")

                # 保存最新值
                db.set_global_data(f"global_{key}", value)

                # 检查今天是否已有记录，有则更新，无则插入
                existing = db.select_one(
                    "rmb_rate_history",
                    where="record_date=?",
                    where_params=(today,)
                )
                if existing:
                    db.update("rmb_rate_history", {"rate": value}, "record_date=?", (today,))
                else:
                    db.insert("rmb_rate_history", {"rate": value, "record_date": today})

            else:
                db.set_global_data(f"global_{key}", value)
        except Exception:
            # 数据库可能已关闭，忽略错误
            pass

    def get_rmb_rate(self):
        """获取RMB汇率"""
        return self._inputs['rmb_rate'].text().strip()

    def get_stamina_cost(self):
        """获取体力成本"""
        return self._inputs['stamina_cost'].text().strip()

    def get_energy_cost(self):
        """获取活力成本"""
        return self._inputs['energy_cost'].text().strip()

    def get_rmb_rate_date(self):
        """获取RMB汇率更新日期"""
        if self.main_window:
            return self.main_window.db.get_global_data("global_rmb_rate_date", "")
        return ""


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 导入核心组件
        from .database import DatabaseManager
        from .plugin_system import PluginManager

        # 初始化管理器
        self.db = DatabaseManager()
        self.plugin_manager = PluginManager(self.db, self)

        # 设置窗口属性
        self.setWindowTitle("游戏助手")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 设置样式
        self._apply_global_styles()

        # 创建UI
        self._create_menu_bar()
        self._create_central_widget()

        # 加载插件
        self._load_plugins()

    def _apply_global_styles(self):
        """应用全局样式"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Theme.BG_MAIN};
            }}
            QWidget {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: 14px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {Theme.BG_CARD};
                padding-top: 8px;
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 2px;
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_CARD};
                color: {Theme.PRIMARY};
                border-bottom: 2px solid {Theme.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Theme.BG_CARD};
                color: {Theme.PRIMARY};
            }}
            QStatusBar {{
                background-color: {Theme.BG_CARD};
                border-top: 1px solid {Theme.BORDER};
                color: {Theme.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QMenuBar {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                padding: 6px 12px;
                border: none;
                border-bottom: 1px solid {Theme.BORDER};
            }}
            QMenuBar::item:selected {{
                background-color: rgba(99, 102, 241, 0.1);
                color: {Theme.PRIMARY};
                border-radius: 4px;
            }}
            QMenu {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.PRIMARY};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.BORDER};
                margin: 4px 0;
            }}
            /* 通用按钮样式 */
            QPushButton {{
                font-family: 'Microsoft YaHei', sans-serif;
            }}
        """)

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        refresh_action = QAction("刷新插件", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_plugins)
        file_menu.addAction(refresh_action)

        export_action = QAction("导出数据", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        settings_action = QAction("设置", self)
        settings_action.setShortcut("Ctrl+S")
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # 标题栏和标签页之间的间距

        # 全局标题栏
        self.header = GlobalHeader(self)
        layout.addWidget(self.header)

        # 标签页部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        # 禁用关闭按钮
        self.tab_widget.setTabsClosable(False)
        # 禁用拖拽排序
        self.tab_widget.setMovable(False)

        layout.addWidget(self.tab_widget)

        # 状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().addPermanentWidget(QLabel("游戏助手 v1.0.0"))

    def _load_plugins(self):
        """加载所有插件"""
        # 发现插件
        plugin_ids = self.plugin_manager.discover_plugins()

        # 加载插件并创建标签页
        for plugin_id in plugin_ids:
            plugin = self.plugin_manager.load_plugin(plugin_id)
            if plugin:
                self._add_plugin_tab(plugin)

        # 如果没有插件，添加一个欢迎页面
        if self.tab_widget.count() == 0:
            self._add_welcome_tab()

        self.statusBar().showMessage(f"已加载 {len(self.plugin_manager.get_all_plugins())} 个插件")

    def _add_plugin_tab(self, plugin):
        """添加插件标签页"""
        ui = plugin.get_ui()
        if ui:
            # 创建标签页
            index = self.tab_widget.addTab(ui, plugin.PLUGIN_NAME)
            self.tab_widget.setCurrentIndex(index)

            # 存储插件引用
            self.tab_widget.tabBar().setTabData(index, {
                'plugin_id': plugin.PLUGIN_ID
            })

    def _add_welcome_tab(self):
        """添加欢迎页面"""
        from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(20)

        # 欢迎图标区域
        icon_frame = QFrame()
        icon_frame.setFixedSize(120, 120)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.GRADIENT_START},
                    stop:1 {Theme.GRADIENT_END}
                );
                border-radius: 24px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(30, 30, 30, 30)
        icon_label = QLabel("🎮")
        icon_label.setStyleSheet("font-size: 60px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 欢迎标题
        welcome_label = QLabel("欢迎使用游戏助手！")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(welcome_label)

        # 副标题
        subtitle = QLabel("您的游戏数据管理专家")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {Theme.TEXT_SECONDARY};
                margin-bottom: 20px;
            }}
        """)
        layout.addWidget(subtitle)

        # 功能介绍卡片
        cards_frame = QFrame()
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setSpacing(20)

        features = [
            ("📦", "插件系统", "轻松扩展功能"),
            ("💾", "数据管理", "统一数据库存储"),
            ("🎨", "美观界面", "现代化设计风格"),
        ]

        for icon, title, desc in features:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_INPUT};
                    border-radius: 12px;
                    padding: 20px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 32px;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_lbl)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: bold;
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {Theme.TEXT_SECONDARY};
                }}
            """)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(desc_lbl)

            cards_layout.addWidget(card)

        layout.addWidget(cards_frame)

        # 提示信息
        tip_label = QLabel("💡 提示：在 plugins 目录下创建新插件来扩展功能")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.BG_INPUT};
                padding: 12px 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
        """)
        layout.addWidget(tip_label)

        layout.addStretch()

        self.tab_widget.addTab(widget, "欢迎")

    def _close_tab(self, index):
        """关闭标签页"""
        # 保留最后一个标签页
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "提示", "至少保留一个标签页")
            return

        self.tab_widget.removeTab(index)

        # 如果没有标签页了，添加欢迎页
        if self.tab_widget.count() == 0:
            self._add_welcome_tab()

    def search_plugins(self, query: str):
        """搜索插件"""
        if not query:
            return

        # 在标签页中搜索
        for i in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(i)
            if query.lower() in tab_text.lower():
                self.tab_widget.setCurrentIndex(i)
                break

        self.statusBar().showMessage(f"搜索: {query}")

    def refresh_plugins(self):
        """刷新插件"""
        # 清除所有标签页
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # 重新加载插件
        self._load_plugins()
        self.statusBar().showMessage("插件已刷新")

    def export_data(self):
        """导出数据"""
        from PyQt6.QtWidgets import QFileDialog
        from .database import DatabaseManager

        db = DatabaseManager()

        # 获取所有插件数据
        plugins = self.plugin_manager.get_all_plugins()

        # 弹出导出对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "game_assistant_backup.db",
            "SQLite Database (*.db);;All Files (*)"
        )

        if file_path:
            import shutil
            shutil.copy(db.db_path, file_path)
            QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")

    def open_settings(self):
        """打开设置"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setFixedSize(400, 300)

        layout = QFormLayout(dialog)

        # 主题设置
        theme_combo = QComboBox()
        theme_combo.addItems(["浅色", "深色", "跟随系统"])
        layout.addRow("主题:", theme_combo)

        # 字体大小
        font_size = QSpinBox()
        font_size.setRange(10, 24)
        font_size.setValue(14)
        layout.addRow("字体大小:", font_size)

        # 自动刷新
        auto_refresh = QComboBox()
        auto_refresh.addItems(["关闭", "每分钟", "每5分钟", "每30分钟"])
        layout.addRow("自动刷新:", auto_refresh)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "设置", "设置已保存（重启生效）")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "<h2>游戏助手</h2>"
            "<p>版本: 1.0.0</p>"
            "<p>一个功能强大的游戏数据管理工具</p>"
            "<p>通过插件系统扩展功能</p>"
        )

    def closeEvent(self, event):
        """关闭窗口事件"""
        # 卸载所有插件
        for plugin in self.plugin_manager.get_all_plugins():
            try:
                plugin.on_unload()
            except Exception:
                pass

        # 关闭数据库
        self.db.close()

        event.accept()

    def get_global_data(self, key: str, default=None):
        """获取全局数据"""
        return self.db.get_global_data(key, default)

    def set_global_data(self, key: str, value):
        """设置全局数据"""
        self.db.set_global_data(key, value)

    # ===== 全局数据便捷访问方法 =====

    def get_rmb_rate(self) -> str:
        """获取RMB汇率"""
        return self.header.get_rmb_rate() if self.header else ""

    def get_stamina_cost(self) -> str:
        """获取体力成本"""
        return self.header.get_stamina_cost() if self.header else ""

    def get_energy_cost(self) -> str:
        """获取活力成本"""
        return self.header.get_energy_cost() if self.header else ""

    def get_rmb_rate_date(self) -> str:
        """获取RMB汇率更新日期"""
        return self.header.get_rmb_rate_date() if self.header else ""
