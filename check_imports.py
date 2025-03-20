"""
檢查必要的庫是否已安裝
"""

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"{module_name} 已安裝")
        return True
    except ImportError as e:
        print(f"{module_name} 未安裝: {e}")
        return False

# 檢查 FastAPI 相關庫
check_import("fastapi")
check_import("uvicorn")

# 檢查 YCM-Researcher 相關庫
check_import("ycm_researcher")

# 檢查其他必要的庫
check_import("dotenv")
check_import("openai")
check_import("langchain")
