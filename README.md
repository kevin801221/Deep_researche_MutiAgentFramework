# YCM 學術知識蒐集系統

YCM 學術知識蒐集系統是一個基於 GPT-Researcher 的學術研究工具，專為 YCM 公司設計。它能夠幫助研究人員快速收集、整理和分析學術文獻，並將結果存儲到 RAG 向量數據庫中，以便後續查詢和使用。

## 功能特點

- **學術研究**：利用 GPT-Researcher 的核心功能進行深入的學術研究
- **多源搜索**：支持 Arxiv、Semantic Scholar 和 Tavily 等多個學術和網絡搜索源
- **RAG 集成**：與 YCM 的 RAG 向量數據庫無縫集成，實現知識的永久存儲和檢索
- **互動界面**：提供友好的用戶界面，支持研究查詢和結果瀏覽
- **實時通信**：通過 WebSocket 提供實時研究進度和聊天功能

## 安裝與配置

### 前提條件

- Python 3.9 或更高版本
- 已安裝 GPT-Researcher（位於父目錄）
- OpenAI API 密鑰
- （可選）Tavily API 密鑰用於網絡搜索

### 安裝步驟

1. 克隆本倉庫：

```bash
git clone https://github.com/your-organization/YCM_Academic_Researcher.git
cd YCM_Academic_Researcher
```

2. 安裝依賴：

```bash
pip install -r requirements.txt
```

3. 配置環境變量：

將 `.env.example` 文件複製為 `.env`，並填寫必要的配置信息：

```bash
cp .env.example .env
# 編輯 .env 文件，填寫 API 密鑰和其他配置
```

## 使用方法

1. 啟動服務器：

```bash
python main.py
```

2. 在瀏覽器中訪問：

```
http://localhost:8000
```

3. 在搜索框中輸入您的研究主題或問題，選擇報告類型，然後點擊"研究"按鈕。

4. 系統將開始收集和分析相關資料，並在完成後顯示研究結果。

5. 您可以通過聊天界面與研究助手互動，提出關於研究結果的問題。

## 與 RAG 系統集成

YCM 學術知識蒐集系統可以與多種向量數據庫集成，包括 Chroma、Pinecone 和 Qdrant。默認情況下，它使用 Chroma 作為本地向量存儲。

要配置向量數據庫集成，請在 `.env` 文件中設置以下變量：

```
VECTOR_DB_TYPE=chroma  # 可選: chroma, pinecone, qdrant
VECTOR_DB_URL=your_vector_db_url
VECTOR_DB_API_KEY=your_vector_db_api_key
VECTOR_DB_NAMESPACE=ycm_academic
```

## 項目結構

```
YCM_Academic_Researcher/
├── backend/                # 後端代碼
│   └── server/             # 服務器相關代碼
│       └── websocket_manager.py  # WebSocket 管理
├── frontend/               # 前端代碼
│   ├── static/             # 靜態資源
│   │   ├── scripts.js      # JavaScript 代碼
│   │   └── styles.css      # CSS 樣式
│   └── index.html          # 主頁面
├── ycm_integration/        # YCM 集成代碼
│   └── rag_connector.py    # RAG 連接器
├── logs/                   # 日誌目錄
├── outputs/                # 輸出目錄
├── .env.example            # 環境變量示例
├── main.py                 # 主入口點
└── README.md               # 說明文檔
```

## 依賴項

本項目依賴於以下主要庫和工具：

- FastAPI：用於 Web 服務器和 API
- GPT-Researcher：用於學術研究功能
- LangChain：用於向量存儲和文檔處理
- OpenAI API：用於生成研究報告和嵌入

完整的依賴列表可在 `requirements.txt` 文件中找到。

## 貢獻與支持

如有問題或建議，請聯繫 YCM 技術支持團隊。
