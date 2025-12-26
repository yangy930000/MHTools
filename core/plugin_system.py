"""
插件系统 - 动态加载和管理插件
"""
import os
import sys
import importlib
import inspect
from typing import Type, Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """插件基类 - 所有插件必须继承此类"""

    # 插件基本信息 - 子类必须覆盖
    PLUGIN_ID = "base_plugin"           # 唯一标识符
    PLUGIN_NAME = "Base Plugin"         # 显示名称
    PLUGIN_VERSION = "1.0.0"            # 版本号
    PLUGIN_AUTHOR = "Unknown"           # 作者
    PLUGIN_DESCRIPTION = ""             # 插件描述

    def __init__(self, db_manager, main_window):
        """
        初始化插件

        Args:
            db_manager: 数据库管理器实例
            main_window: 主窗口实例（可用于访问全局数据等）
        """
        self.db = db_manager
        self.main_window = main_window
        self._enabled = True

        # 注册插件
        self.db.register_plugin(
            self.PLUGIN_ID,
            self.PLUGIN_NAME,
            self.PLUGIN_VERSION,
            self.PLUGIN_AUTHOR
        )

    @property
    def is_enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled

    @abstractmethod
    def get_ui(self):
        """
        返回插件的UI组件（QWidget）
        主框架会调用此方法获取插件的界面
        """
        pass

    def on_load(self):
        """插件加载时调用 - 可重写"""
        self.db.update_plugin_last_used(self.PLUGIN_ID)

    def on_unload(self):
        """插件卸载时调用 - 可重写"""
        pass

    def on_tab_selected(self):
        """当插件所在标签页被选中时调用 - 可重写"""
        pass

    def get_global_data(self, key: str, default: Any = None) -> Any:
        """获取全局数据"""
        return self.db.get_global_data(key, default)

    def set_global_data(self, key: str, value: Any):
        """设置全局数据"""
        self.db.set_global_data(key, value)

    def get_settings(self) -> Dict:
        """获取插件设置"""
        return self.get_global_data(f"plugin_{self.PLUGIN_ID}_settings", {})

    def save_settings(self, settings: Dict):
        """保存插件设置"""
        self.set_global_data(f"plugin_{self.PLUGIN_ID}_settings", settings)


class PluginManager:
    """插件管理器"""

    def __init__(self, db_manager, main_window):
        self.db = db_manager
        self.main_window = main_window
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}

        # 插件目录
        self.plugins_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "plugins"
        )

    def discover_plugins(self) -> List[str]:
        """发现并加载插件"""
        plugin_ids = []

        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return plugin_ids

        # 遍历插件目录
        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)

            # 检查是否是有效的插件目录
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, "__init__.py")

                if os.path.exists(init_file):
                    try:
                        # 动态导入插件模块
                        module_name = f"plugins.{item}"

                        # 刷新时先清除旧的模块缓存
                        if module_name in sys.modules:
                            del sys.modules[module_name]

                        # 使用 importlib 直接导入
                        module = importlib.import_module(module_name)

                        # 查找插件类
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if (issubclass(obj, BasePlugin) and
                                obj != BasePlugin and
                                hasattr(obj, 'PLUGIN_ID')):
                                self._plugin_classes[obj.PLUGIN_ID] = obj
                                plugin_ids.append(obj.PLUGIN_ID)
                                print(f"发现插件: {obj.PLUGIN_NAME} v{obj.PLUGIN_VERSION}")

                    except Exception as e:
                        print(f"加载插件 {item} 失败: {e}")

        return plugin_ids

    def load_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """加载指定插件"""
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]

        plugin_class = self._plugin_classes.get(plugin_id)
        if not plugin_class:
            return None

        try:
            # 创建插件实例
            plugin = plugin_class(self.db, self.main_window)
            self._plugins[plugin_id] = plugin

            # 调用加载回调
            plugin.on_load()

            print(f"插件 {plugin.PLUGIN_NAME} 加载成功")
            return plugin

        except Exception as e:
            print(f"实例化插件 {plugin_id} 失败: {e}")
            return None

    def unload_plugin(self, plugin_id: str):
        """卸载插件"""
        plugin = self._plugins.get(plugin_id)
        if plugin:
            try:
                plugin.on_unload()
            except Exception as e:
                print(f"插件卸载回调失败: {e}")

            del self._plugins[plugin_id]
            print(f"插件 {plugin.PLUGIN_NAME} 已卸载")

    def get_all_plugins(self) -> List[BasePlugin]:
        """获取所有已加载的插件"""
        return list(self._plugins.values())

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """获取指定插件"""
        return self._plugins.get(plugin_id)

    def reload_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """重新加载插件"""
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id)

    def get_plugin_tabs(self) -> List[Dict]:
        """获取所有插件的标签页信息"""
        tabs = []
        for plugin in self._plugins.values():
            tabs.append({
                'id': plugin.PLUGIN_ID,
                'name': plugin.PLUGIN_NAME,
                'description': plugin.PLUGIN_DESCRIPTION,
                'ui': plugin.get_ui()
            })
        return tabs
