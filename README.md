# 游戏助手框架 (Game Assistant Framework)

一个基于插件架构的游戏数据管理工具框架。

## 功能特点

- **美观UI** - 使用PyQt6构建现代化界面
- **插件系统** - 功能通过插件实现，热插拔
- **统一数据库** - 所有插件数据使用同一个SQLite数据库管理
- **标签页管理** - 通过标签页组织和切换各个功能
- **全局数据区** - 顶部全局数据/功能栏

## 项目结构

```
MHTools/
├── main.py                 # 程序入口
├── core/                   # 核心框架
│   ├── __init__.py
│   ├── database.py         # 数据库管理器
│   ├── plugin_system.py    # 插件系统
│   └── main_window.py      # 主窗口
├── plugins/                # 插件目录
│   ├── demo_plugin/        # 示例插件 - 数据记录器
│   └── inventory_plugin/   # 示例插件 - 物品管理
├── data/                   # 数据存储
│   └── game_assistant.db   # SQLite数据库
├── requirements.txt        # 依赖
└── README.md              # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

## 开发新插件

### 插件基本结构

```python
from core.plugin_system import BasePlugin
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyPlugin(BasePlugin):
    PLUGIN_ID = "my_plugin"
    PLUGIN_NAME = "我的插件"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_AUTHOR = "你的名字"
    PLUGIN_DESCRIPTION = "插件描述"

    def __init__(self, db, main_window):
        super().__init__(db, main_window)
        self._init_database()
        self._create_ui()

    def _init_database(self):
        # 初始化数据库表
        self.db.ensure_table("my_table", {
            "name": "TEXT NOT NULL",
            "value": "INTEGER DEFAULT 0"
        })

    def get_ui(self) -> QWidget:
        return self._widget

    def _create_ui(self):
        self._widget = QWidget()
        layout = QVBoxLayout(self._widget)
        layout.addWidget(QLabel("我的插件UI"))
```

### 创建新插件步骤

1. 在 `plugins/` 目录下创建新文件夹，如 `my_plugin/`
2. 创建 `__init__.py` 文件，编写插件代码
3. 插件会 **自动加载**，无需修改框架代码

### 插件可用方法

| 方法 | 说明 |
|------|------|
| `self.db.insert(table, data)` | 插入数据 |
| `self.db.update(table, data, where, params)` | 更新数据 |
| `self.db.delete(table, where, params)` | 删除数据 |
| `self.db.select(table, ...)` | 查询数据 |
| `self.db.ensure_table(name, columns)` | 确保表存在 |
| `self.get_global_data(key, default)` | 获取全局数据 |
| `self.set_global_data(key, value)` | 设置全局数据 |
| `self.get_settings()` | 获取插件设置 |
| `self.save_settings(settings)` | 保存插件设置 |

## 数据库使用示例

### 创建表
```python
self.db.ensure_table("player_stats", {
    "player_name": "TEXT NOT NULL",
    "level": "INTEGER DEFAULT 1",
    "gold": "INTEGER DEFAULT 0",
    "play_time": "INTEGER DEFAULT 0"
})
```

### 插入数据
```python
self.db.insert("player_stats", {
    "player_name": "玩家1",
    "level": 10,
    "gold": 1000
})
```

### 查询数据
```python
rows = self.db.select("player_stats",
    where="level >= ?",
    where_params=(5,),
    order_by="gold DESC"
)
```

## 注意事项

- 插件ID必须唯一
- 插件文件夹名和PLUGIN_ID可以不同
- 数据库表名建议使用插件ID前缀避免冲突
- 不要修改core目录下的文件

## 许可证

MIT License
