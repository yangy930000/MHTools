#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏助手 - 主入口文件

运行此文件启动游戏助手程序
"""

import sys
import os

# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("游戏助手")
    app.setOrganizationName("MHTools")
    app.setWindowIcon(QIcon.fromTheme("applications-games"))

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
