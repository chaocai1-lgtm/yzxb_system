"""
配置文件
存储数据库连接信息和API密钥
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Neo4j配置
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://7eb127cc.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "wE7pV36hqNSo43mpbjTlfzE7n99NWcYABDFqUGvgSrk")

# Elasticsearch配置
ELASTICSEARCH_CLOUD_ID = os.getenv(
    "ELASTICSEARCH_CLOUD_ID",
    "41ed8f6c58a942fb9aea8f6804841099:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ1ZTRhNGI5ZGNlZjc0NDI4YjI3MWEzZDg3YzRmZjY2OCRlZjhhODRlYjliNzc0YjM3ODk0NWQ3ZTQ3OWVkOWRkNQ=="
)
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "x5ZwEPmZewPZlnZIn1Fy3XoQ")

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-bdf96d7f1aa74a53a83ff167f7f2f5a9")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 应用配置
APP_TITLE = "牙周病学自适应学习系统"
APP_ICON = "🦷"

# Neo4j标签
NEO4J_LABEL_PREFIX = "yzbx"  # 牙周病学拼音首字母
