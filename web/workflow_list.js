import { app } from "../../scripts/app.js";

// 显示通知函数
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ff4444' : '#333333'};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 10000;
        font-family: Arial, sans-serif;
        font-size: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        max-width: 300px;
        word-wrap: break-word;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// 创建工作流列表显示对话框
function createWorkflowListDialog(workflowList) {
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #2a2a2a;
        border: 1px solid #555;
        border-radius: 8px;
        padding: 20px;
        z-index: 10001;
        min-width: 400px;
        max-width: 600px;
        max-height: 70vh;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        color: white;
        font-family: Arial, sans-serif;
    `;

    const title = document.createElement('h3');
    title.textContent = '工作流文件列表';
    title.style.cssText = `
        margin: 0 0 15px 0;
        color: #fff;
        font-size: 18px;
        border-bottom: 1px solid #555;
        padding-bottom: 10px;
    `;
    dialog.appendChild(title);

    try {
        const data = JSON.parse(workflowList);
        
        if (data.success && data.workflows && data.workflows.length > 0) {
            const count = document.createElement('p');
            count.textContent = `共找到 ${data.count} 个工作流文件：`;
            count.style.cssText = `
                margin: 0 0 15px 0;
                color: #ccc;
                font-size: 14px;
            `;
            dialog.appendChild(count);

            const list = document.createElement('ul');
            list.style.cssText = `
                list-style: none;
                padding: 0;
                margin: 0;
            `;

            data.workflows.forEach((filename, index) => {
                const item = document.createElement('li');
                item.style.cssText = `
                    padding: 8px 12px;
                    margin: 5px 0;
                    background: #333;
                    border-radius: 4px;
                    border-left: 3px solid #4CAF50;
                    font-size: 14px;
                    cursor: pointer;
                    transition: background 0.2s;
                `;
                item.textContent = `${index + 1}. ${filename}`;
                
                item.addEventListener('mouseenter', () => {
                    item.style.background = '#444';
                });
                
                item.addEventListener('mouseleave', () => {
                    item.style.background = '#333';
                });
                
                item.addEventListener('click', () => {
                    showNotification(`选择了工作流: ${filename}`);
                });
                
                list.appendChild(item);
            });
            
            dialog.appendChild(list);
        } else {
            const errorMsg = document.createElement('p');
            errorMsg.textContent = data.error || '没有找到工作流文件';
            errorMsg.style.cssText = `
                color: #ff6b6b;
                font-size: 14px;
                text-align: center;
                padding: 20px;
            `;
            dialog.appendChild(errorMsg);
        }
    } catch (e) {
        const errorMsg = document.createElement('p');
        errorMsg.textContent = `解析工作流列表失败: ${e.message}`;
        errorMsg.style.cssText = `
            color: #ff6b6b;
            font-size: 14px;
            text-align: center;
            padding: 20px;
        `;
        dialog.appendChild(errorMsg);
    }

    // 关闭按钮
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '关闭';
    closeBtn.style.cssText = `
        background: #555;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 15px;
        float: right;
        font-size: 14px;
    `;
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(overlay);
    });
    
    closeBtn.addEventListener('mouseenter', () => {
        closeBtn.style.background = '#666';
    });
    
    closeBtn.addEventListener('mouseleave', () => {
        closeBtn.style.background = '#555';
    });
    
    dialog.appendChild(closeBtn);

    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        z-index: 10000;
    `;
    
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
}

// 注册扩展
app.registerExtension({
    name: "Base64Nodes.WorkflowList",
    
    async nodeCreated(node) {
        if (node.comfyClass === "WorkflowListNode") {
            // 为WorkflowListNode添加自定义行为
            const originalOnExecuted = node.onExecuted;
            
            node.onExecuted = function(message) {
                if (originalOnExecuted) {
                    originalOnExecuted.call(this, message);
                }
                
                // 当节点执行完成时，显示工作流列表
                if (message && message.workflow_list) {
                    try {
                        createWorkflowListDialog(message.workflow_list[0]);
                        showNotification('工作流列表获取成功！');
                    } catch (e) {
                        console.error('显示工作流列表失败:', e);
                        showNotification('显示工作流列表失败: ' + e.message, 'error');
                    }
                }
            };
            
            // 添加右键菜单选项
            const originalGetExtraMenuOptions = node.getExtraMenuOptions;
            node.getExtraMenuOptions = function(_, options) {
                if (originalGetExtraMenuOptions) {
                    originalGetExtraMenuOptions.call(this, _, options);
                }
                
                options.push({
                    content: "刷新工作流列表",
                    callback: () => {
                        // 触发节点重新执行
                        if (this.widgets) {
                            const refreshWidget = this.widgets.find(w => w.name === "refresh");
                            if (refreshWidget) {
                                refreshWidget.value = !refreshWidget.value;
                                showNotification('正在刷新工作流列表...');
                            }
                        }
                    }
                });
            };
        }
    }
});