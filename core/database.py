"""
数据库管理器 - 统一管理所有插件的数据
支持动态表创建、灵活的数据类型
"""
import sqlite3
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """统一的数据库管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 数据库路径
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_assistant.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 连接池
        self._local = sqlite3.connect(self.db_path, check_same_thread=False)
        self._local.row_factory = sqlite3.Row

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化数据库 - 创建必要的系统表"""
        cursor = self._local.cursor()

        # 插件表 - 记录已注册的插件
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS _system_plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT,
                author TEXT,
                created_at TEXT,
                last_used TEXT,
                config TEXT
            )
        ''')

        # 全局数据表 - 存储全局配置和数据
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS _system_global_data (
                key TEXT PRIMARY KEY,
                value TEXT,
                data_type TEXT,
                updated_at TEXT
            )
        ''')

        # 创建动态数据存储表 - 用于存储各种结构化数据
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS _system_dynamic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                data_key TEXT NOT NULL,
                data_value TEXT,
                data_type TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(category, data_key)
            )
        ''')

        self._local.commit()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = self._local
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL查询"""
        cursor = self._local.cursor()
        cursor.execute(query, params)
        self._local.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """获取所有结果"""
        cursor = self._local.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """获取单条结果"""
        cursor = self._local.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    # ==================== 插件数据管理 ====================

    def register_plugin(self, plugin_id: str, name: str, version: str = "1.0.0", author: str = ""):
        """注册插件"""
        now = datetime.now().isoformat()
        self.execute('''
            INSERT OR REPLACE INTO _system_plugins (id, name, version, author, created_at, last_used)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (plugin_id, name, version, author, now, now))

    def update_plugin_last_used(self, plugin_id: str):
        """更新插件最后使用时间"""
        now = datetime.now().isoformat()
        self.execute('''
            UPDATE _system_plugins SET last_used = ? WHERE id = ?
        ''', (now, plugin_id))

    def get_all_plugins(self) -> List[Dict]:
        """获取所有已注册的插件"""
        rows = self.fetch_all("SELECT * FROM _system_plugins ORDER BY last_used DESC")
        return [dict(row) for row in rows]

    # ==================== 动态表管理 ====================

    def ensure_table(self, table_name: str, columns: Dict[str, str]):
        """
        确保表存在，不存在则创建
        columns: {'列名': '数据类型', ...}
        示例: {'name': 'TEXT', 'value': 'REAL', 'data': 'TEXT'}
        """
        cursor = self._local.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            return

        # 构建建表SQL
        cols_sql = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        cursor.execute(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_sql})")
        self._local.commit()

    def drop_table(self, table_name: str):
        """删除表"""
        # 检查是否为系统表
        if table_name.startswith('_system_'):
            return
        self.execute(f"DROP TABLE IF EXISTS {table_name}")

    # ==================== 通用数据操作 ====================

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """插入数据"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.keys()])
        values = list(data.values())

        cursor = self.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
            tuple(values)
        )
        return cursor.lastrowid

    def update(self, table_name: str, data: Dict[str, Any], where: str, where_params: tuple = ()):
        """更新数据"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + list(where_params)
        self.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where}", tuple(values))

    def delete(self, table_name: str, where: str, where_params: tuple = ()):
        """删除数据"""
        self.execute(f"DELETE FROM {table_name} WHERE {where}", where_params)

    def select(self, table_name: str, columns: str = "*", where: str = None,
               where_params: tuple = (), order_by: str = None, limit: int = None) -> List[sqlite3.Row]:
        """查询数据"""
        query = f"SELECT {columns} FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        return self.fetch_all(query, where_params)

    def select_one(self, table_name: str, columns: str = "*", where: str = None,
                   where_params: tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条数据"""
        results = self.select(table_name, columns, where, where_params, limit=1)
        return results[0] if results else None

    # ==================== 全局数据管理 ====================

    def set_global_data(self, key: str, value: Any, data_type: str = "json"):
        """设置全局数据"""
        now = datetime.now().isoformat()
        if data_type == "json":
            stored_value = json.dumps(value, ensure_ascii=False)
        else:
            stored_value = str(value)

        self.execute('''
            INSERT OR REPLACE INTO _system_global_data (key, value, data_type, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (key, stored_value, data_type, now))

    def get_global_data(self, key: str, default: Any = None, data_type: str = "json") -> Any:
        """获取全局数据"""
        row = self.select_one("_system_global_data", where="key=?", where_params=(key,))
        if not row:
            return default

        value = row['value']
        if data_type == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    # ==================== 动态分类数据 ====================

    def set_dynamic_data(self, category: str, data_key: str, value: Any, data_type: str = "json"):
        """设置动态数据"""
        now = datetime.now().isoformat()
        if data_type == "json":
            stored_value = json.dumps(value, ensure_ascii=False)
        else:
            stored_value = str(value)

        self.execute('''
            INSERT OR REPLACE INTO _system_dynamic_data
            (category, data_key, data_value, data_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (category, data_key, stored_value, data_type, now, now))

    def get_dynamic_data(self, category: str, data_key: str, default: Any = None) -> Any:
        """获取动态数据"""
        row = self.select_one(
            "_system_dynamic_data",
            where="category=? AND data_key=?",
            where_params=(category, data_key)
        )
        if not row:
            return default

        value = row['data_value']
        if row['data_type'] == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_category_data(self, category: str) -> List[Dict]:
        """获取分类下所有数据"""
        rows = self.select(
            "_system_dynamic_data",
            where="category=?",
            where_params=(category,),
            order_by="updated_at DESC"
        )
        return [dict(row) for row in rows]

    # ==================== 批量操作 ====================

    def bulk_insert(self, table_name: str, data_list: List[Dict[str, Any]]):
        """批量插入"""
        if not data_list:
            return

        cursor = self._local.cursor()
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0].keys()])

        for data in data_list:
            values = list(data.values())
            cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", tuple(values))

        self._local.commit()

    def clear_table(self, table_name: str):
        """清空表数据"""
        if table_name.startswith('_system_'):
            return
        self.execute(f"DELETE FROM {table_name}")

    # ==================== 统计查询 ====================

    def count(self, table_name: str, where: str = None, where_params: tuple = ()) -> int:
        """统计数量"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        row = self.fetch_one(query, where_params)
        return row['count'] if row else 0

    def execute_sql(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """执行原生SQL"""
        return self.fetch_all(sql, params)

    def close(self):
        """关闭数据库连接"""
        if self._local:
            self._local.close()
