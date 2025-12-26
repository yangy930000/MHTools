"""
汇率历史图表插件
显示汇率变化趋势，支持鼠标交互操作
"""
from core.plugin_system import BasePlugin
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta


class RateHistoryPlugin(BasePlugin):
    """汇率历史图表插件"""

    PLUGIN_ID = "rate_history"
    PLUGIN_NAME = "汇率K线"
    PLUGIN_VERSION = "2.0.0"
    PLUGIN_AUTHOR = "MHTools"
    PLUGIN_DESCRIPTION = "汇率历史图表，支持鼠标交互和均线显示"

    # 颜色配置
    COLORS = {
        'line': '#26a69a',    # 价格线绿色
        'ma7': '#ef5350',     # MA7 红色
        'ma15': '#ffca28',    # MA15 黄色
        'ma30': '#42a5f5',    # MA30 蓝色
        'dot': '#5c7cfa',     # 数据点蓝色
        'bg': '#ffffff',
        'text': '#333333',
        'grid': '#e0e0e0'
    }

    def __init__(self, db, main_window):
        super().__init__(db, main_window)
        self._init_database()
        self._create_ui()
        self._generate_test_data()
        self._update_chart()

    def _init_database(self):
        """初始化数据库表（幂等操作）"""
        try:
            existing = self.db.select_one("sqlite_master",
                where="type=? AND name=?",
                where_params=("table", "rate_history"))
            if existing:
                return
        except Exception:
            pass

        try:
            self.db.execute_sql("""
                CREATE TABLE IF NOT EXISTS rate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    price REAL NOT NULL
                )
            """)
        except Exception:
            try:
                self.db.execute_sql("DROP TABLE IF EXISTS rate_history")
                self.db.execute_sql("""
                    CREATE TABLE rate_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        price REAL NOT NULL
                    )
                """)
            except Exception as e:
                print(f"创建 rate_history 表失败: {e}")

    def _create_ui(self):
        """创建UI"""
        self._widget = QWidget()
        layout = QVBoxLayout(self._widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题和周期选择
        header_layout = QHBoxLayout()

        title_label = QLabel("汇率走势图")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)

        header_layout.addSpacerItem(QSpacerItem(40, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # 周期选择按钮
        self._period_buttons = {}
        self._period_group = QButtonGroup()

        periods = [("7天", 7), ("15天", 15), ("30天", 30)]
        for text, days in periods:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(days == 7)
            btn.setFixedSize(60, 30)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #5c7cfa;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    color: #5c7cfa;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #5c7cfa;
                    color: white;
                }
                QPushButton:hover:!checked {
                    background-color: #e7f5ff;
                }
            """)
            self._period_buttons[days] = btn
            self._period_group.addButton(btn)
            header_layout.addWidget(btn)

        self._period_group.buttonClicked.connect(self._on_period_change)
        layout.addLayout(header_layout)

        # 创建图表
        self._create_chart()
        layout.addWidget(self._canvas)

        # 状态信息
        self._status_label = QLabel("移动鼠标查看详情 | 滚轮缩放 | 左键拖拽平移")
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

    def _create_chart(self):
        """创建图表"""
        self._figure = Figure(figsize=(8, 5), dpi=100, facecolor=self.COLORS['bg'])
        self._ax = self._figure.add_subplot(111)
        self._ax.set_facecolor(self.COLORS['bg'])

        # 设置图表样式
        self._ax.spines['top'].set_visible(False)
        self._ax.spines['right'].set_visible(False)
        self._ax.spines['left'].set_color(self.COLORS['grid'])
        self._ax.spines['bottom'].set_color(self.COLORS['grid'])
        self._ax.tick_params(colors=self.COLORS['text'])
        self._ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.4f}'))

        self._canvas = FigureCanvas(self._figure)
        self._canvas.setStyleSheet("background: white; border-radius: 4px;")

        # 鼠标交互
        self._canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self._canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self._canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self._canvas.mpl_connect('scroll_event', self._on_mouse_wheel)

        # 状态变量
        self._is_panning = False
        self._pan_start_x = None
        self._last_xlim = None
        self._current_period = 7

    def _generate_test_data(self):
        """生成测试数据"""
        existing = self.db.select("rate_history", order_by="date DESC", limit=1)
        if existing:
            return

        # 生成60天随机测试数据
        base_rate = 7.2
        data_count = 60

        for i in range(data_count):
            date = datetime.now() - timedelta(days=data_count - i)
            price = round(base_rate + np.random.uniform(-0.3, 0.3), 4)

            self.db.insert("rate_history", {
                "date": date.strftime("%Y-%m-%d"),
                "price": price
            })

    def _load_data(self, days=7):
        """加载指定天数的数据"""
        data = self.db.select(
            "rate_history",
            order_by="date ASC",
            limit=days
        )
        return data if data else []

    def _calculate_ma(self, prices, period):
        """计算移动平均线"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(np.nan)
            else:
                ma_values.append(np.mean(prices[i-period+1:i+1]))
        return ma_values

    def _update_chart(self, days=None):
        """更新图表"""
        if days is None:
            days = self._current_period

        data = self._load_data(days)
        if not data:
            self._ax.clear()
            self._ax.text(0.5, 0.5, "暂无数据", ha='center', va='center', transform=self._ax.transAxes)
            self._canvas.draw()
            return

        # 提取数据
        dates = [datetime.strptime(row[1], "%Y-%m-%d") for row in data]
        prices = [row[2] for row in data]

        # 计算均线
        ma7 = self._calculate_ma(prices, 7)
        ma15 = self._calculate_ma(prices, 15)
        ma30 = self._calculate_ma(prices, 30)

        # 清除图表
        self._ax.clear()
        self._ax.set_facecolor(self.COLORS['bg'])

        x_positions = np.arange(len(dates))

        # 绘制价格折线
        self._ax.plot(x_positions, prices, color=self.COLORS['line'], linewidth=2, label='价格', alpha=0.9)

        # 绘制数据点
        self._ax.scatter(x_positions, prices, color=self.COLORS['dot'], s=30, zorder=5, alpha=0.8)

        # 绘制均线
        self._ax.plot(x_positions, ma7, color=self.COLORS['ma7'], linewidth=1.5, label='MA7', alpha=0.9)
        self._ax.plot(x_positions, ma15, color=self.COLORS['ma15'], linewidth=1.5, label='MA15', alpha=0.9)
        self._ax.plot(x_positions, ma30, color=self.COLORS['ma30'], linewidth=1.5, label='MA30', alpha=0.9)

        # 设置坐标轴
        self._ax.set_xlim(-0.5, len(dates) - 0.5)
        y_min = min(prices) * 0.998
        y_max = max(prices) * 1.002
        self._ax.set_ylim(y_min, y_max)

        # 格式化x轴日期
        self._ax.set_xticks(x_positions[::max(1, len(dates)//7)])
        self._ax.set_xticklabels([d.strftime("%m-%d") for d in dates[::max(1, len(dates)//7)]], rotation=45)

        # 图例
        legend_elements = [
            Line2D([0], [0], color=self.COLORS['line'], linewidth=2, label='价格'),
            Line2D([0], [0], color=self.COLORS['ma7'], linewidth=1.5, label='MA7'),
            Line2D([0], [0], color=self.COLORS['ma15'], linewidth=1.5, label='MA15'),
            Line2D([0], [0], color=self.COLORS['ma30'], linewidth=1.5, label='MA30')
        ]
        self._ax.legend(handles=legend_elements, loc='upper left', fontsize=8)

        # 网格
        self._ax.grid(True, alpha=0.3, linestyle='--', color=self.COLORS['grid'])
        self._ax.spines['top'].set_visible(False)
        self._ax.spines['right'].set_visible(False)

        self._canvas.draw()

        # 保存当前数据引用用于tooltip
        self._chart_data = {
            'dates': dates,
            'prices': prices,
            'ma7': ma7,
            'ma15': ma15,
            'ma30': ma30
        }

    def _on_period_change(self, button):
        """周期切换"""
        for days, btn in self._period_buttons.items():
            if btn == button:
                self._current_period = days
                self._update_chart()
                self._status_label.setText(f"已切换至 {days} 天视图")
                break

    def _on_mouse_move(self, event):
        """鼠标移动 - 显示tooltip"""
        if not event.inaxes or not hasattr(self, '_chart_data'):
            return

        x = event.xdata
        if x is None:
            return

        idx = int(round(x))
        if 0 <= idx < len(self._chart_data['dates']):
            data = self._chart_data
            date_str = data['dates'][idx].strftime("%Y-%m-%d")
            price = data['prices'][idx]

            ma7_val = data['ma7'][idx]
            ma15_val = data['ma15'][idx]
            ma30_val = data['ma30'][idx]

            ma7_str = f"{ma7_val:.4f}" if not np.isnan(ma7_val) else "N/A"
            ma15_str = f"{ma15_val:.4f}" if not np.isnan(ma15_val) else "N/A"
            ma30_str = f"{ma30_val:.4f}" if not np.isnan(ma30_val) else "N/A"

            tooltip_text = f"日期: {date_str}\n价格: {price:.4f}\nMA7: {ma7_str}\nMA15: {ma15_str}\nMA30: {ma30_str}"

            self._canvas.setToolTip(tooltip_text)
            self._status_label.setText(f"日期: {date_str} | 价格: {price:.4f}")

    def _on_mouse_press(self, event):
        """鼠标按下 - 开始拖拽"""
        if event.button == event.button.LEFT and event.inaxes:
            self._is_panning = True
            self._pan_start_x = event.xdata
            self._last_xlim = self._ax.get_xlim()

    def _on_mouse_release(self, event):
        """鼠标释放 - 结束拖拽"""
        self._is_panning = False

    def _on_mouse_wheel(self, event):
        """鼠标滚轮 - 缩放"""
        if not event.inaxes:
            return

        base_scale = 1.1
        scale_factor = base_scale if event.step > 0 else 1 / base_scale

        current_xlim = self._ax.get_xlim()
        x_data = event.xdata
        x_range = current_xlim[1] - current_xlim[0]
        new_range = x_range * scale_factor

        if new_range < 3:
            return
        if new_range > len(self._chart_data['dates']) * 1.5:
            return

        new_xlim = [x_data - new_range * (x_data - current_xlim[0]) / x_range,
                   x_data + new_range * (current_xlim[1] - x_data) / x_range]

        self._ax.set_xlim(new_xlim)
        self._canvas.draw()

    def get_ui(self):
        return self._widget
