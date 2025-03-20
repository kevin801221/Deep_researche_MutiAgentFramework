// YCM 學術知識蒐集系統腳本

// 全局變量
let websocket = null;
let researchInProgress = false;
let searchHistory = [];

// DOM 元素
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const researchResults = document.getElementById('research-results');
const researchStatus = document.getElementById('research-status');
const researchContent = document.getElementById('research-content');
const summaryContent = document.getElementById('summary-content');
const sourcesList = document.getElementById('sources-list');
const chatSection = document.getElementById('chat-section');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatButton = document.getElementById('chat-button');
const historyList = document.getElementById('history-list');
const websocketStatus = document.getElementById('websocket-status');
const statusIndicator = websocketStatus.querySelector('.status-indicator');
const statusText = websocketStatus.querySelector('.status-text');
const resultContainer = document.getElementById('result-container'); // 新增的 DOM 元素

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加載搜尋歷史
    loadSearchHistory();
    
    // 初始化 WebSocket 連接
    initWebSocket();
    
    // 添加事件監聽器
    searchButton.addEventListener('click', startResearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            startResearch();
        }
    });
    
    chatButton.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
});

// 初始化 WebSocket 連接
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    websocket = new WebSocket(wsUrl);
    
    updateWebSocketStatus('connecting');
    
    websocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        updateWebSocketStatus('online');
    };
    
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    websocket.onclose = () => {
        console.log('WebSocket 連接已關閉');
        updateWebSocketStatus('offline');
        
        // 嘗試重新連接
        setTimeout(() => {
            initWebSocket();
        }, 3000);
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        updateWebSocketStatus('offline');
    };
}

// 更新 WebSocket 狀態
function updateWebSocketStatus(status) {
    statusIndicator.className = 'status-indicator ' + status;
    
    switch (status) {
        case 'online':
            statusText.textContent = '已連接';
            break;
        case 'offline':
            statusText.textContent = '離線';
            break;
        case 'connecting':
            statusText.textContent = '連接中...';
            break;
    }
}

// 處理 WebSocket 消息
function handleWebSocketMessage(data) {
    if (data.type === 'research_update') {
        updateResearchStatus(data);
    } else if (data.type === 'research_complete') {
        completeResearch(data.data);
    } else if (data.type === 'research_error') {
        showResearchError(data.message);
    } else if (data.type === 'chat_message') {
        addChatMessage(data.sender, data.message);
    }
}

// 顯示研究錯誤
function showResearchError(message) {
    researchInProgress = false;
    researchStatus.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
    researchStatus.style.display = 'block';
}

// 開始研究
function startResearch() {
    const query = searchInput.value.trim();
    if (!query) {
        alert('請輸入研究主題或問題');
        return;
    }
    
    // 獲取選中的報告類型
    const reportType = document.querySelector('input[name="reportType"]:checked').value;
    
    // 顯示研究結果區域
    researchResults.style.display = 'block';
    researchStatus.style.display = 'block';
    researchContent.style.display = 'none';
    
    // 清空之前的研究結果
    summaryContent.innerHTML = '';
    sourcesList.innerHTML = '';
    
    // 標記研究進行中
    researchInProgress = true;
    
    // 發送研究請求
    fetch('/api/research', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            report_type: reportType
        })
    })
    .then(response => response.json())
    .then(data => {
        // 研究完成
        completeResearch(data);
        
        // 添加到搜尋歷史
        addToSearchHistory(query);
        
        // 顯示聊天區域
        chatSection.style.display = 'block';
    })
    .catch(error => {
        console.error('研究請求錯誤:', error);
        alert('研究過程中出錯，請稍後再試');
        researchInProgress = false;
    });
}

// 更新研究狀態
function updateResearchStatus(data) {
    if (data.status === 'in_progress') {
        // 確保研究狀態區域可見
        researchStatus.style.display = 'block';
        
        // 添加新的狀態更新
        const statusUpdate = document.createElement('div');
        statusUpdate.className = 'research-status-update';
        
        // 根據消息類型設置不同的圖標和樣式
        let icon = 'info-circle';
        let colorClass = 'text-info';
        
        if (data.message.includes('使用工具')) {
            icon = 'tools';
            colorClass = 'text-primary';
        } else if (data.message.includes('執行動作')) {
            icon = 'cogs';
            colorClass = 'text-success';
        } else if (data.message.includes('研究步驟')) {
            icon = 'search';
            colorClass = 'text-warning';
        }
        
        // 格式化時間戳
        const now = new Date();
        const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        // 設置 HTML 內容
        statusUpdate.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <span class="status-timestamp text-muted me-2">${timestamp}</span>
                <i class="fas fa-${icon} ${colorClass} me-2"></i>
                <span>${data.message}</span>
            </div>
        `;
        
        // 添加到狀態區域
        researchStatus.appendChild(statusUpdate);
        
        // 自動滾動到底部
        researchStatus.scrollTop = researchStatus.scrollHeight;
    }
}

// 完成研究
function completeResearch(result) {
    researchInProgress = false;
    
    // 添加完成消息到研究狀態
    const statusUpdate = document.createElement('div');
    statusUpdate.className = 'research-status-update';
    
    // 格式化時間戳
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    statusUpdate.innerHTML = `
        <div class="d-flex align-items-center mb-2">
            <span class="status-timestamp text-muted me-2">${timestamp}</span>
            <i class="fas fa-check-circle text-success me-2"></i>
            <span>研究已完成！</span>
        </div>
    `;
    
    researchStatus.appendChild(statusUpdate);
    
    // 顯示研究結果
    if (result && result.report) {
        resultContainer.innerHTML = marked.parse(result.report);
        
        // 顯示來源
        if (result.sources && result.sources.length > 0) {
            const sourcesHtml = `
                <h3>參考來源</h3>
                <ul>
                    ${result.sources.map(source => `
                        <li>
                            <a href="${source.url}" target="_blank">${source.title || source.url}</a>
                            ${source.description ? `<p>${source.description}</p>` : ''}
                        </li>
                    `).join('')}
                </ul>
            `;
            resultContainer.innerHTML += sourcesHtml;
        }
        
        // 顯示保存到向量數據庫的狀態
        if (result.saved_to_vector_db) {
            resultContainer.innerHTML += `
                <div class="alert alert-success mt-3" role="alert">
                    <i class="fas fa-database"></i> 研究結果已成功保存到向量數據庫
                </div>
            `;
        }
        
        resultContainer.style.display = 'block';
    } else {
        resultContainer.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <i class="fas fa-exclamation-triangle"></i> 未能獲取研究結果
            </div>
        `;
        resultContainer.style.display = 'block';
    }
    
    // 啟用搜索按鈕
    searchButton.disabled = false;
    searchButton.innerHTML = '開始研究';
}

// 發送聊天消息
function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) {
        return;
    }
    
    // 添加用戶消息到聊天區域
    addChatMessage('user', message);
    
    // 清空輸入框
    chatInput.value = '';
    
    // 如果 WebSocket 連接可用，發送消息
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: 'chat_message',
            message: message
        }));
    } else {
        // 如果 WebSocket 不可用，使用 HTTP 請求
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            addChatMessage('assistant', data.response);
        })
        .catch(error => {
            console.error('聊天請求錯誤:', error);
            addChatMessage('system', '發送消息時出錯，請稍後再試');
        });
    }
}

// 添加聊天消息
function addChatMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}-message`;
    
    if (sender === 'user') {
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>您</strong>
            </div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
    } else if (sender === 'assistant') {
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>研究助手</strong>
            </div>
            <div class="message-content markdown-content">
                ${marked.parse(message)}
            </div>
        `;
    } else {
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>系統</strong>
            </div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageElement);
    
    // 滾動到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加到搜尋歷史
function addToSearchHistory(query) {
    // 檢查是否已存在
    const existingIndex = searchHistory.indexOf(query);
    if (existingIndex !== -1) {
        // 如果已存在，先移除
        searchHistory.splice(existingIndex, 1);
    }
    
    // 添加到歷史的開頭
    searchHistory.unshift(query);
    
    // 限制歷史記錄數量
    if (searchHistory.length > 10) {
        searchHistory.pop();
    }
    
    // 保存到本地存儲
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    
    // 更新顯示
    updateSearchHistoryDisplay();
}

// 加載搜尋歷史
function loadSearchHistory() {
    const savedHistory = localStorage.getItem('searchHistory');
    if (savedHistory) {
        searchHistory = JSON.parse(savedHistory);
        updateSearchHistoryDisplay();
    }
}

// 更新搜尋歷史顯示
function updateSearchHistoryDisplay() {
    historyList.innerHTML = '';
    
    searchHistory.forEach(query => {
        const historyItem = document.createElement('li');
        historyItem.textContent = query;
        historyItem.addEventListener('click', () => {
            searchInput.value = query;
            startResearch();
        });
        
        historyList.appendChild(historyItem);
    });
}

// 清空搜尋歷史
function clearSearchHistory() {
    searchHistory = [];
    localStorage.removeItem('searchHistory');
    updateSearchHistoryDisplay();
}
