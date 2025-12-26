# 游戏助手核心框架
from .database import DatabaseManager
from .plugin_system import PluginManager, BasePlugin
from .main_window import MainWindow

__version__ = "1.0.0"
__all__ = ["DatabaseManager", "PluginManager", "BasePlugin", "MainWindow"]
