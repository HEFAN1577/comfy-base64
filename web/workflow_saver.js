import { app } from "../../scripts/app.js";

// 存储上次保存的工作流名称
let lastSavedWorkflowName = localStorage.getItem('lastWorkflowName') || 'workflow';

// 存储当前导入的工作流名称
let currentImportedWorkflowName = null;

// 显示通知函数
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #333333;
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

// 通过WebSocket获取工作流列表
async function fetchWorkflowList() {
    try {
        const websocket = new WebSocket('ws://localhost:3078/ws');
        
        return new Promise((resolve, reject) => {
            websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                // 发送获取工作流列表请求
                const request = {
                    type: 'get_workflow_list',
                    timestamp: new Date().toISOString()
                };
                websocket.send(JSON.stringify(request));
            };
            
            websocket.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data);
                    if (response.type === 'workflow_list') {
                        resolve({
                            success: true,
                            workflows: response.workflows || [],
                            count: response.workflows ? response.workflows.length : 0
                        });
                    } else {
                        reject(new Error('收到意外响应格式'));
                    }
                } catch (e) {
                    reject(new Error('解析响应失败: ' + e.message));
                }
                websocket.close();
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                reject(new Error('WebSocket连接失败'));
            };
            
            websocket.onclose = (event) => {
                if (event.code !== 1000) {
                    reject(new Error('WebSocket连接异常关闭'));
                }
            };
            
            // 设置超时
            setTimeout(() => {
                if (websocket.readyState === WebSocket.CONNECTING || websocket.readyState === WebSocket.OPEN) {
                    websocket.close();
                    reject(new Error('请求超时'));
                }
            }, 5000);
        });
    } catch (error) {
        throw new Error('创建WebSocket连接失败: ' + error.message);
    }
}

// 创建工作流列表显示对话框
function createWorkflowListDialog(workflowData) {
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

    if (workflowData.success && workflowData.workflows && workflowData.workflows.length > 0) {
        const count = document.createElement('p');
        count.textContent = `共找到 ${workflowData.count} 个工作流文件：`;
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

        const workflowsToDisplay = workflowData.workflowsWithNames || workflowData.workflows.map(filename => ({
        filename: filename,
        displayName: filename.replace('.json', '')
    }));
    
    workflowsToDisplay.forEach((workflowInfo, index) => {
        const filename = workflowInfo.filename || workflowInfo;
        const displayName = workflowInfo.displayName || (typeof workflowInfo === 'string' ? workflowInfo.replace('.json', '') : filename.replace('.json', ''));
            const item = document.createElement('li');
            item.style.cssText = `
                padding: 8px 12px;
                margin: 5px 0;
                background: #333;
                border-radius: 4px;
                border-left: 3px solid #4CAF50;
                font-size: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: background 0.2s;
            `;
            
            // 创建文件名显示区域
            const nameSpan = document.createElement('span');
            nameSpan.textContent = `${index + 1}. ${displayName}`;
            nameSpan.style.cssText = `
                cursor: pointer;
                flex: 1;
                padding-right: 10px;
            `;
            
            // 添加文件名提示
            if (displayName !== filename.replace('.json', '')) {
                nameSpan.title = `文件名: ${filename}`;
            }
            
            // 创建按钮容器
            const buttonContainer = document.createElement('div');
            buttonContainer.style.cssText = `
                display: flex;
                gap: 5px;
            `;
            
            // 创建导入按钮
            const importBtn = document.createElement('button');
            importBtn.textContent = '导入';
            importBtn.style.cssText = `
                background: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 12px;
            `;
            

            
            // 鼠标悬停效果
            item.addEventListener('mouseenter', () => {
                item.style.background = '#444';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.background = '#333';
            });
            
            // 点击文件名导入工作流
            nameSpan.addEventListener('click', async () => {
                try {
                    showNotification(`正在导入工作流: ${filename}`);
                    await importWorkflow(filename);
                } catch (error) {
                    console.error('导入工作流失败:', error);
                    showNotification(`导入工作流失败: ${error.message}`, 'error');
                }
            });
            
            // 导入按钮点击事件
            importBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                try {
                    showNotification(`正在导入工作流: ${filename}`);
                    await importWorkflow(filename);
                } catch (error) {
                    console.error('导入工作流失败:', error);
                    showNotification(`导入工作流失败: ${error.message}`, 'error');
                }
            });
            
            // 组装元素
            buttonContainer.appendChild(importBtn);
            item.appendChild(nameSpan);
            item.appendChild(buttonContainer);
            
            list.appendChild(item);
        });
        
        dialog.appendChild(list);
    } else {
        const errorMsg = document.createElement('p');
        errorMsg.textContent = workflowData.error || '没有找到工作流文件';
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

// 通过WebSocket获取单个工作流内容
async function fetchWorkflowContent(filename) {
    try {
        const websocket = new WebSocket('ws://localhost:3078/ws');
        
        return new Promise((resolve, reject) => {
            websocket.onopen = () => {
                console.log('WebSocket连接已建立，获取工作流内容:', filename);
                // 发送获取工作流内容请求
                const request = {
                    type: 'get_workflow_content',
                    filename: filename,
                    timestamp: new Date().toISOString()
                };
                websocket.send(JSON.stringify(request));
            };
            
            websocket.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data);
                    if (response.type === 'workflow_content') {
                        if (response.content) {
                            resolve(response.content);
                        } else {
                            reject(new Error('工作流内容为空'));
                        }
                    } else if (response.type === 'error') {
                        reject(new Error(response.message || '获取工作流内容失败'));
                    } else {
                        reject(new Error('收到意外响应格式'));
                    }
                } catch (e) {
                    reject(new Error('解析响应失败: ' + e.message));
                }
                websocket.close();
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                reject(new Error('WebSocket连接失败'));
            };
            
            websocket.onclose = (event) => {
                if (event.code !== 1000) {
                    reject(new Error('WebSocket连接异常关闭'));
                }
            };
            
            // 设置超时
            setTimeout(() => {
                if (websocket.readyState === WebSocket.CONNECTING || websocket.readyState === WebSocket.OPEN) {
                    websocket.close();
                    reject(new Error('请求超时'));
                }
            }, 10000);
        });
    } catch (error) {
        throw new Error('创建WebSocket连接失败: ' + error.message);
    }
}

// 将API格式工作流转换为前端格式
// 将API格式的输入转换为前端widget值
function convertInputsToWidgets(nodeType, inputValues) {
    const widgets = [];
    
    switch (nodeType) {
        case 'KSampler':
            // KSampler的正确参数顺序：seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise
            const kSamplerDefaults = {
                seed: 0,
                control_after_generate: "randomize",
                steps: 20,
                cfg: 8.0,
                sampler_name: "euler",
                scheduler: "normal",
                denoise: 1.0
            };
            
            // 从输入值中提取参数
            const kSamplerParams = {};
            inputValues.forEach(input => {
                kSamplerParams[input.name] = input.value;
            });
            
            // 按正确顺序添加参数，直接使用API工作流中的值
            widgets.push(kSamplerParams.seed !== undefined ? kSamplerParams.seed : kSamplerDefaults.seed);
            widgets.push(kSamplerParams.control_after_generate !== undefined ? kSamplerParams.control_after_generate : kSamplerDefaults.control_after_generate);
            widgets.push(kSamplerParams.steps !== undefined ? kSamplerParams.steps : kSamplerDefaults.steps);
            widgets.push(kSamplerParams.cfg !== undefined ? kSamplerParams.cfg : kSamplerDefaults.cfg);
            widgets.push(kSamplerParams.sampler_name !== undefined ? kSamplerParams.sampler_name : kSamplerDefaults.sampler_name);
            widgets.push(kSamplerParams.scheduler !== undefined ? kSamplerParams.scheduler : kSamplerDefaults.scheduler);
            widgets.push(kSamplerParams.denoise !== undefined ? kSamplerParams.denoise : kSamplerDefaults.denoise);
            break;
            
        case 'CheckpointLoaderSimple':
            const ckptName = inputValues.find(input => input.name === 'ckpt_name');
            widgets.push(ckptName ? ckptName.value : '');
            break;
            
        case 'EmptyLatentImage':
            const width = inputValues.find(input => input.name === 'width');
            const height = inputValues.find(input => input.name === 'height');
            const batchSize = inputValues.find(input => input.name === 'batch_size');
            widgets.push(width ? width.value : 512);
            widgets.push(height ? height.value : 512);
            widgets.push(batchSize ? batchSize.value : 1);
            break;
            
        case 'CLIPTextEncode':
            const text = inputValues.find(input => input.name === 'text');
            widgets.push(text ? text.value : '');
            break;
            
        default:
            // 对于其他节点类型，按原始顺序添加值
            inputValues.forEach(input => {
                widgets.push(input.value);
            });
            break;
    }
    
    return widgets;
}

function convertApiToFrontendFormat(apiWorkflow) {
    const frontendWorkflow = {
        last_node_id: 0,
        last_link_id: 0,
        nodes: [],
        links: [],
        groups: [],
        config: {},
        extra: {},
        version: 0.4
    };
    
    const nodeIdMap = new Map();
    let nodeCounter = 1;
    let linkCounter = 1;
    
    // 第一遍：创建所有节点
    Object.entries(apiWorkflow).forEach(([nodeId, nodeData]) => {
        const frontendNodeId = nodeCounter++;
        nodeIdMap.set(nodeId, frontendNodeId);
        
        const frontendNode = {
            id: frontendNodeId,
            type: nodeData.class_type,
            pos: [Math.random() * 400 + 100, Math.random() * 300 + 100], // 随机位置
            size: [210, 78],
            flags: {},
            order: frontendNodeId,
            mode: 0,
            inputs: [],
            outputs: [],
            properties: {},
            widgets_values: []
        };
        
        // 添加标题
        if (nodeData._meta && nodeData._meta.title) {
            frontendNode.title = nodeData._meta.title;
        }
        
        // 处理输入
        if (nodeData.inputs) {
            const widgetValues = [];
            const inputConnections = [];
            
            Object.entries(nodeData.inputs).forEach(([inputName, inputValue]) => {
                if (Array.isArray(inputValue) && inputValue.length === 2) {
                    // 这是一个连接引用 [source_node_id, output_index]
                    inputConnections.push({
                        name: inputName,
                        type: "*",
                        link: null // 稍后处理连接
                    });
                } else {
                    // 这是一个直接值，需要根据节点类型正确映射
                    widgetValues.push({ name: inputName, value: inputValue });
                }
            });
            
            // 添加连接输入
            frontendNode.inputs = inputConnections;
            
            // 根据节点类型正确映射widget值
            frontendNode.widgets_values = convertInputsToWidgets(nodeData.class_type, widgetValues);
        }
        
        frontendWorkflow.nodes.push(frontendNode);
        frontendWorkflow.last_node_id = Math.max(frontendWorkflow.last_node_id, frontendNodeId);
    });
    
    // 第二遍：处理连接
    Object.entries(apiWorkflow).forEach(([nodeId, nodeData]) => {
        const targetNodeId = nodeIdMap.get(nodeId);
        const targetNode = frontendWorkflow.nodes.find(n => n.id === targetNodeId);
        
        if (nodeData.inputs) {
            let inputIndex = 0;
            Object.entries(nodeData.inputs).forEach(([inputName, inputValue]) => {
                if (Array.isArray(inputValue) && inputValue.length === 2) {
                    const [sourceNodeId, outputIndex] = inputValue;
                    const sourceFrontendNodeId = nodeIdMap.get(sourceNodeId.toString());
                    
                    if (sourceFrontendNodeId) {
                        const linkId = linkCounter++;
                        
                        // 创建连接
                        frontendWorkflow.links.push([
                            linkId,
                            sourceFrontendNodeId,
                            outputIndex,
                            targetNodeId,
                            inputIndex,
                            "*"
                        ]);
                        
                        // 更新目标节点的输入连接
                        if (targetNode.inputs[inputIndex]) {
                            targetNode.inputs[inputIndex].link = linkId;
                        }
                        
                        // 确保源节点有足够的输出
                        const sourceNode = frontendWorkflow.nodes.find(n => n.id === sourceFrontendNodeId);
                        if (sourceNode) {
                            while (sourceNode.outputs.length <= outputIndex) {
                                sourceNode.outputs.push({
                                    name: `output_${sourceNode.outputs.length}`,
                                    type: "*",
                                    links: []
                                });
                            }
                            sourceNode.outputs[outputIndex].links.push(linkId);
                        }
                        
                        frontendWorkflow.last_link_id = Math.max(frontendWorkflow.last_link_id, linkId);
                    }
                    inputIndex++;
                }
            });
        }
    });
    
    return frontendWorkflow;
}

// 创建导入方式选择对话框
function createImportMethodDialog(filename, workflowContent) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 90%;
        `;
        
        content.innerHTML = `
            <h3 style="margin: 0 0 20px 0; color: #333; text-align: center;">选择导入方式</h3>
            <p style="margin: 0 0 20px 0; color: #666; line-height: 1.5;">工作流: <strong>${filename}</strong></p>
            <p style="margin: 0 0 25px 0; color: #666; line-height: 1.5; font-size: 14px;">
                <strong>自动化导入</strong>：直接在ComfyUI界面中导入，避免节点连接断开问题（推荐）<br>
                <strong>传统导入</strong>：在当前界面导入，可能出现节点连接断开
            </p>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <button id="autoImport" style="
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                ">自动化导入（推荐）</button>
                <button id="traditionalImport" style="
                    padding: 12px 24px;
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                ">传统导入</button>
                <button id="cancelImport" style="
                    padding: 12px 24px;
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                ">取消</button>
            </div>
        `;
        
        dialog.appendChild(content);
        document.body.appendChild(dialog);
        
        // 添加按钮事件
        content.querySelector('#autoImport').onclick = () => {
            document.body.removeChild(dialog);
            resolve('auto');
        };
        
        content.querySelector('#traditionalImport').onclick = () => {
            document.body.removeChild(dialog);
            resolve('traditional');
        };
        
        content.querySelector('#cancelImport').onclick = () => {
            document.body.removeChild(dialog);
            resolve('cancel');
        };
        
        // 点击背景关闭
        dialog.onclick = (e) => {
            if (e.target === dialog) {
                document.body.removeChild(dialog);
                resolve('cancel');
            }
        };
    });
}

// 导入工作流到ComfyUI
// 检测是否在Electron环境中
function isElectronEnvironment() {
    return typeof window !== 'undefined' && window.require && window.require('electron');
}

// Electron环境下的浏览器自动化导入
async function importWorkflowViaElectron(workflowContent) {
    try {
        const { shell } = window.require('electron');
        const fs = window.require('fs');
        const path = window.require('path');
        const os = window.require('os');
        
        // 创建临时文件
        const tempDir = os.tmpdir();
        const tempFilePath = path.join(tempDir, `workflow_${Date.now()}.json`);
        
        // 写入工作流数据
        fs.writeFileSync(tempFilePath, JSON.stringify(workflowContent, null, 2));
        
        // 打开ComfyUI并自动导入
        const comfyUrl = `http://localhost:8188?import=${encodeURIComponent(tempFilePath)}`;
        await shell.openExternal(comfyUrl);
        
        // 清理临时文件（延迟删除，确保ComfyUI有时间读取）
        setTimeout(() => {
            try {
                fs.unlinkSync(tempFilePath);
            } catch (e) {
                console.warn('清理临时文件失败:', e);
            }
        }, 5000);
        
        return true;
    } catch (error) {
        console.error('Electron环境导入失败:', error);
        return false;
    }
}

// 浏览器环境下的自动化导入
async function importWorkflowViaBrowser(workflowContent) {
    try {
        console.log('开始浏览器自动化导入...');
        
        // 检查ComfyUI app对象是否可用
        if (!app || typeof app.loadGraphData !== 'function') {
            throw new Error('ComfyUI app对象不可用或loadGraphData方法不存在');
        }
        
        // 检测工作流格式并转换
        let frontendWorkflow;
        if (workflowContent.nodes && Array.isArray(workflowContent.nodes)) {
            // 已经是前端格式
            console.log('检测到前端格式工作流');
            frontendWorkflow = workflowContent;
        } else {
            // 是API格式，需要转换
            console.log('检测到API格式工作流，开始转换...');
            frontendWorkflow = convertApiToFrontendFormat(workflowContent);
            console.log('转换后的前端格式工作流:', frontendWorkflow);
        }
        
        // 清空当前画布
        if (app.graph) {
            app.graph.clear();
        }
        
        // 直接在当前页面导入工作流
        console.log('开始导入工作流到当前ComfyUI页面...');
        app.loadGraphData(frontendWorkflow);
        
        // 刷新画布显示
        if (app.canvas) {
            app.canvas.setDirty(true, true);
        }
        
        // 触发画布重绘
        if (app.graph) {
            app.graph.setDirtyCanvas(true, true);
        }
        
        console.log('浏览器自动化导入完成');
        return true;
        
    } catch (error) {
        console.error('浏览器环境导入失败:', error);
        return false;
    }
}

async function importWorkflow(filename) {
    try {
        // 1. 获取工作流内容
        const workflowContent = await fetchWorkflowContent(filename);
        console.log('获取到工作流内容:', workflowContent);
        
        // 2. 验证工作流格式
        if (!workflowContent || typeof workflowContent !== 'object') {
            throw new Error('工作流内容格式无效');
        }
        
        // 3. 直接使用自动化导入（优先）
        let importSuccess = false;
        
        // 检测环境并选择导入方式
        if (isElectronEnvironment()) {
            console.log('检测到Electron环境，使用Electron自动化导入...');
            importSuccess = await importWorkflowViaElectron(workflowContent);
        } else {
            console.log('使用浏览器自动化导入...');
            importSuccess = await importWorkflowViaBrowser(workflowContent);
        }
        
        if (importSuccess) {
            // 记录当前导入的工作流名称
            currentImportedWorkflowName = filename;
            
            // 更新保存按钮状态
            if (window.updateSaveButtonState) {
                window.updateSaveButtonState();
            }
            
            showNotification(`工作流 "${filename}" 导入成功！`, 'success');
            console.log('自动化导入完成:', filename);
            return;
        } else {
            console.log('自动化导入失败，尝试传统导入方式...');
        }
        
        // 4. 传统导入方式（备用）
        console.log('使用传统导入方式...');
        
        // 检查ComfyUI app对象是否可用
        if (!app || typeof app.loadGraphData !== 'function') {
            throw new Error('ComfyUI app对象不可用或loadGraphData方法不存在');
        }
        
        // 5. 检测工作流格式
        if (workflowContent.nodes && Array.isArray(workflowContent.nodes)) {
            // 前端格式，直接导入
            console.log('检测到前端格式工作流，直接导入');
            
            // 清空当前画布
            if (app.graph) {
                app.graph.clear();
            }
            
            // 导入工作流
            console.log('开始导入工作流到ComfyUI...');
            app.loadGraphData(workflowContent);
        } else {
            // API格式，使用浏览器自动化导入（模拟拖拽）
            console.log('检测到API格式工作流，使用浏览器自动化导入...');
            const browserImportSuccess = await importWorkflowViaBrowser(workflowContent);
            
            if (!browserImportSuccess) {
                throw new Error('API格式工作流导入失败，请尝试直接拖拽到ComfyUI界面');
            }
        }
        
        // 8. 刷新画布显示
        if (app.canvas) {
            app.canvas.setDirty(true, true);
        }
        
        // 9. 触发画布重绘
        if (app.graph) {
            app.graph.setDirtyCanvas(true, true);
        }
        
        // 记录当前导入的工作流名称
        currentImportedWorkflowName = filename;
        
        // 更新保存按钮状态
        if (window.updateSaveButtonState) {
            window.updateSaveButtonState();
        }
        
        showNotification(`工作流 "${filename}" 导入成功（传统方式）！`, 'success');
        console.log('传统方式工作流导入完成:', filename);
        
    } catch (error) {
        console.error('导入工作流失败:', error);
        throw error;
    }
}

// 保存工作流更改
async function saveWorkflowChanges(filename) {
    try {
        // 检查ComfyUI app对象是否可用
        if (!app || !app.graph) {
            throw new Error('ComfyUI app对象不可用');
        }
        
        // 获取当前工作流数据
        const currentWorkflow = app.graph.serialize();
        console.log('当前工作流数据:', currentWorkflow);
        
        // 转换为HTTP API格式（使用新的异步API方法）
        const httpApiWorkflow = await convertNormalWorkflowToHttpFormatAsync(currentWorkflow);
        console.log('转换后的HTTP API格式:', httpApiWorkflow);
        
        // 通过WebSocket发送保存请求
        const websocket = new WebSocket('ws://localhost:3078/ws');
        
        return new Promise((resolve, reject) => {
            websocket.onopen = () => {
                console.log('WebSocket连接已建立，准备发送保存请求');
                // 发送保存工作流更改请求
                const request = {
                    type: 'save_workflow_changes',
                    filename: filename,
                    workflow_data: httpApiWorkflow,
                    timestamp: new Date().toISOString()
                };
                websocket.send(JSON.stringify(request));
            };
            
            websocket.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data);
                    console.log('收到WebSocket响应:', response);
                    
                    if (response.type === 'save_workflow_changes_response') {
                        if (response.success) {
                            showNotification(`工作流 "${filename}" 保存成功！`, 'success');
                            resolve(response);
                        } else {
                            throw new Error(response.error || '保存失败');
                        }
                    } else if (response.type === 'error') {
                        throw new Error(response.message || '服务器错误');
                    }
                } catch (parseError) {
                    console.error('解析WebSocket响应失败:', parseError);
                    reject(new Error('解析服务器响应失败'));
                }
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket连接错误:', error);
                reject(new Error('WebSocket连接失败'));
            };
            
            websocket.onclose = () => {
                console.log('WebSocket连接已关闭');
            };
            
            // 设置超时
            setTimeout(() => {
                if (websocket.readyState !== WebSocket.CLOSED) {
                    websocket.close();
                    reject(new Error('保存请求超时'));
                }
            }, 10000);
        });
        
    } catch (error) {
        console.error('保存工作流更改失败:', error);
        throw error;
    }
}

// 显示工作流列表
async function showWorkflowList() {
    try {
        showNotification('正在获取工作流列表...');
        const workflowData = await fetchWorkflowList();
        
        // 获取工作流的实际名称
        const workflowsWithNames = [];
        for (const filename of workflowData.workflows) {
            try {
                const content = await fetchWorkflowContent(filename);
                let displayName = filename.replace('.json', '');
                
                // 尝试从工作流内容中提取名称
                if (content && content.extra && content.extra.ds && content.extra.ds.workflow_name) {
                    displayName = content.extra.ds.workflow_name;
                } else if (content && content.workflow && content.workflow.extra && content.workflow.extra.ds && content.workflow.extra.ds.workflow_name) {
                    displayName = content.workflow.extra.ds.workflow_name;
                }
                
                workflowsWithNames.push({
                    filename: filename,
                    displayName: displayName
                });
            } catch (error) {
                console.warn(`无法获取工作流 ${filename} 的名称:`, error);
                workflowsWithNames.push({
                    filename: filename,
                    displayName: filename.replace('.json', '')
                });
            }
        }
        
        const enhancedWorkflowData = {
            ...workflowData,
            workflowsWithNames: workflowsWithNames
        };
        
        createWorkflowListDialog(enhancedWorkflowData);
        showNotification('工作流列表获取成功！');
    } catch (error) {
        console.error('获取工作流列表失败:', error);
        showNotification('获取工作流列表失败: ' + error.message, 'error');
    }
}

// 获取API路径配置
function getApiPath() {
    // 使用固定的API路径，不再支持自定义设置
    return '/Base64Nodes/save_workflow';
}

// 测试API连接
async function testApiConnection() {
    try {
        const apiPath = getApiPath();
        console.log('测试API连接:', apiPath);
        
        // 发送一个简单的OPTIONS请求来测试连接
        const response = await fetch(apiPath, {
            method: 'OPTIONS'
        });
        
        console.log('API测试响应状态:', response.status, response.statusText);
        return true; // OPTIONS请求通常会返回，说明服务器可达
    } catch (error) {
        console.error('API连接测试失败:', error);
        return false;
    }
}

// 工作流格式转换函数：将普通工作流转换为HTTP API格式
// 新的异步转换函数，使用HTTP API
async function convertNormalWorkflowToHttpFormatAsync(normalWorkflow) {
    console.log('🔄 开始使用API转换工作流格式...');
    
    try {
        // 通过HTTP API获取工作流模板进行转换
        const response = await fetch('http://localhost:3078/api/workflow_templates');
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const apiData = await response.json();
        if (!apiData.success) {
            throw new Error(`API返回错误: ${apiData.error}`);
        }
        
        console.log('📡 成功获取API数据，开始转换...');
        
        // 使用本地转换逻辑作为备用方案
        return convertNormalWorkflowToHttpFormatLocal(normalWorkflow);
        
    } catch (error) {
        console.warn('⚠️ API转换失败，使用本地转换:', error.message);
        // 如果API失败，回退到本地转换
        return convertNormalWorkflowToHttpFormatLocal(normalWorkflow);
    }
}

// 本地转换函数（原有逻辑）
function convertNormalWorkflowToHttpFormatLocal(normalWorkflow) {
    console.log('🔄 开始本地转换工作流格式...');
    
    if (!normalWorkflow || !normalWorkflow.nodes || !normalWorkflow.links) {
        throw new Error('普通工作流数据不完整，缺少nodes或links');
    }
    
    const httpFormat = {};
    const links = normalWorkflow.links || [];
    
    // 创建链接映射表：link_id -> [source_node_id, source_slot, target_node_id, target_slot, type]
     const linkMap = {};
     links.forEach(link => {
         if (Array.isArray(link) && link.length >= 6) {
             const [linkId, sourceNodeId, sourceSlot, targetNodeId, targetSlot, type] = link;
             linkMap[linkId] = { sourceNodeId, sourceSlot, targetNodeId, targetSlot, type };
         }
     });
     
     console.log('🔗 链接详情:', links.slice(0, 3).map(link => ({
         linkId: link[0],
         from: `${link[1]}:${link[2]}`,
         to: `${link[3]}:${link[4]}`,
         type: link[5]
     })));
    
    console.log('📋 链接映射表创建完成，共', Object.keys(linkMap).length, '个链接');
    
    // 转换每个节点
    normalWorkflow.nodes.forEach(node => {
        if (node.mode === 2) {
            // 跳过禁用的节点
            console.log(`⏭️ 跳过禁用节点 ${node.id} (${node.type})`);
            return;
        }
        
        const httpNode = {
            class_type: node.type,
            inputs: {}
        };
        
        // 处理输入连接
        if (node.inputs && Array.isArray(node.inputs)) {
            node.inputs.forEach((input, inputIndex) => {
                if (input.link !== null && input.link !== undefined) {
                    // 这是一个连接输入
                    const linkInfo = linkMap[input.link];
                    if (linkInfo) {
                        httpNode.inputs[input.name] = [linkInfo.sourceNodeId.toString(), linkInfo.sourceSlot];
                    }
                }
            });
        }
        
        // 处理widget值（从widgets_values映射到inputs）
        if (node.widgets_values && Array.isArray(node.widgets_values)) {
            // 需要根据节点类型和输入定义来正确映射widget值
            // 这里使用一个简化的映射策略
            const widgetInputMapping = getWidgetInputMapping(node.type, node.inputs, node.widgets_values);
            Object.assign(httpNode.inputs, widgetInputMapping);
        }
        
        // 添加元数据（可选）
        if (node.title && node.title !== node.type) {
            httpNode._meta = { title: node.title };
        }
        
        httpFormat[node.id.toString()] = httpNode;
    });
    
    console.log('✅ 工作流格式转换完成，共转换', Object.keys(httpFormat).length, '个节点');
    return httpFormat;
}

// 保持向后兼容的同步函数
function convertNormalWorkflowToHttpFormat(normalWorkflow) {
    return convertNormalWorkflowToHttpFormatLocal(normalWorkflow);
}

// 获取widget到input的映射
function getWidgetInputMapping(nodeType, nodeInputs, widgetValues) {
    const mapping = {};
    
    if (!widgetValues || !Array.isArray(widgetValues)) {
        return mapping;
    }
    
    // 根据节点类型进行特殊处理
    switch (nodeType) {
        case 'KSampler':
            // KSampler的widget映射
            if (widgetValues.length >= 7) {
                mapping.seed = widgetValues[0];
                // widgetValues[1] 通常是 "randomize" 或 "fixed"
                mapping.steps = widgetValues[2];
                mapping.cfg = widgetValues[3];
                mapping.sampler_name = widgetValues[4];
                mapping.scheduler = widgetValues[5];
                mapping.denoise = widgetValues[6];
            }
            break;
            
        case 'CheckpointLoaderSimple':
            if (widgetValues.length >= 1) {
                mapping.ckpt_name = widgetValues[0];
            }
            break;
            
        case 'EmptyLatentImage':
            if (widgetValues.length >= 3) {
                mapping.width = widgetValues[0];
                mapping.height = widgetValues[1];
                mapping.batch_size = widgetValues[2];
            }
            break;
            
        case 'CLIPTextEncode':
            if (widgetValues.length >= 1) {
                mapping.text = widgetValues[0];
            }
            break;
            
        case 'SaveImage':
            if (widgetValues.length >= 1) {
                mapping.filename_prefix = widgetValues[0];
            }
            break;
            
        case 'ImageWebSocketOutput':
            if (widgetValues.length >= 1) {
                mapping.prompt = widgetValues[0];
            }
            break;
            
        // 新增节点类型支持
        case 'VAELoader':
            if (widgetValues.length >= 1) {
                mapping.vae_name = widgetValues[0];
            }
            break;
            
        case 'DualCLIPLoader':
            if (widgetValues.length >= 4) {
                mapping.clip_name1 = widgetValues[0];
                mapping.clip_name2 = widgetValues[1];
                mapping.type = widgetValues[2];
                mapping.device = widgetValues[3];
            }
            break;
            
        case 'FluxGuidance':
            if (widgetValues.length >= 1) {
                mapping.guidance = widgetValues[0];
            }
            break;
            
        case 'NunchakuFluxDiTLoader':
            if (widgetValues.length >= 7) {
                mapping.model_path = widgetValues[0];
                mapping.cache_threshold = widgetValues[1];
                mapping.attention = widgetValues[2];
                mapping.cpu_offload = widgetValues[3];
                mapping.device_id = widgetValues[4];
                mapping.data_type = widgetValues[5];
                mapping.i2f_mode = widgetValues[6];
            }
            break;
            
        case 'NunchakuFluxLoraLoader':
            if (widgetValues.length >= 2) {
                mapping.lora_name = widgetValues[0];
                mapping.lora_strength = widgetValues[1];
            }
            break;
            
        case 'ReferenceLatent':
            // ReferenceLatent通常没有widget值，主要通过连接工作
            // 如果有widget值，按通用方式处理
            break;
            
        case 'ConditioningZeroOut':
        case 'VAEDecode':
            // 这些节点通常没有widget值，主要通过连接工作
            break;
            
        default:
            // 通用映射：尝试根据输入定义映射
            if (nodeInputs && Array.isArray(nodeInputs)) {
                let widgetIndex = 0;
                nodeInputs.forEach(input => {
                    if (input.link === null || input.link === undefined) {
                        // 这是一个widget输入
                        if (widgetIndex < widgetValues.length) {
                            mapping[input.name] = widgetValues[widgetIndex];
                            widgetIndex++;
                        }
                    }
                });
            }
            break;
    }
    
    return mapping;
}

// 创建liner风格对话框
function createLinerDialog(title, defaultValue = '') {
    return new Promise((resolve) => {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        `;
        
        // 创建对话框容器
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: linear-gradient(135deg, #333333 0%, #1a1a1a 100%);
            border-radius: 16px;
            padding: 2px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            animation: slideIn 0.3s ease-out;
        `;
        
        // 创建内容区域
        const content = document.createElement('div');
        content.style.cssText = `
            background: #1a1a1a;
            border-radius: 14px;
            padding: 24px;
            min-width: 320px;
            max-width: 400px;
        `;
        
        // 创建标题
        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        titleElement.style.cssText = `
            margin: 0 0 16px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            text-align: center;
        `;
        
        // 创建输入框
        const input = document.createElement('input');
        input.type = 'text';
        input.value = defaultValue;
        input.style.cssText = `
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #444444;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            outline: none;
            transition: all 0.2s ease;
            box-sizing: border-box;
            background: #2a2a2a;
            color: #ffffff;
        `;
        
        // 输入框焦点效果
        input.addEventListener('focus', () => {
            input.style.borderColor = '#667eea';
            input.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.2)';
        });
        
        input.addEventListener('blur', () => {
            input.style.borderColor = '#444444';
            input.style.boxShadow = 'none';
        });
        
        // 创建按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            display: flex;
            gap: 12px;
            margin-top: 20px;
            justify-content: flex-end;
        `;
        
        // 创建取消按钮
        const cancelButton = document.createElement('button');
        cancelButton.textContent = '取消';
        cancelButton.style.cssText = `
            padding: 10px 20px;
            border: 1px solid #555555;
            border-radius: 6px;
            background: #2a2a2a;
            color: #cccccc;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        
        // 创建确认按钮
        const confirmButton = document.createElement('button');
        confirmButton.textContent = '保存';
        confirmButton.style.cssText = `
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        
        // 按钮悬停效果
        cancelButton.addEventListener('mouseenter', () => {
            cancelButton.style.background = '#3a3a3a';
            cancelButton.style.borderColor = '#666666';
        });
        
        cancelButton.addEventListener('mouseleave', () => {
            cancelButton.style.background = '#2a2a2a';
            cancelButton.style.borderColor = '#555555';
        });
        
        confirmButton.addEventListener('mouseenter', () => {
            confirmButton.style.transform = 'translateY(-1px)';
            confirmButton.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
        });
        
        confirmButton.addEventListener('mouseleave', () => {
            confirmButton.style.transform = 'translateY(0)';
            confirmButton.style.boxShadow = 'none';
        });
        
        // 事件处理
        const closeDialog = (result) => {
            overlay.style.animation = 'fadeOut 0.2s ease-in';
            setTimeout(() => {
                document.body.removeChild(overlay);
                resolve(result);
            }, 200);
        };
        
        cancelButton.addEventListener('click', () => closeDialog(null));
        confirmButton.addEventListener('click', () => {
            const value = input.value.trim();
            if (value) {
                closeDialog(value);
            } else {
                input.style.borderColor = '#ef4444';
                input.focus();
            }
        });
        
        // 回车键确认
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                confirmButton.click();
            } else if (e.key === 'Escape') {
                cancelButton.click();
            }
        });
        
        // 点击遮罩关闭
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeDialog(null);
            }
        });
        
        // 组装对话框
        buttonContainer.appendChild(cancelButton);
        buttonContainer.appendChild(confirmButton);
        content.appendChild(titleElement);
        content.appendChild(input);
        content.appendChild(buttonContainer);
        dialog.appendChild(content);
        overlay.appendChild(dialog);
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: scale(0.9) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }
            @keyframes fadeOut {
                from {
                    opacity: 1;
                }
                to {
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        
        // 显示对话框
        document.body.appendChild(overlay);
        input.focus();
        input.select();
    });
}

// 保存工作流函数
async function saveWorkflow() {
    try {
        // 使用liner风格对话框让用户输入文件名
        const filename = await createLinerDialog('保存工作流', lastSavedWorkflowName);
        if (!filename) {
            showNotification('保存已取消', 'info');
            return;
        }
        
        // 保存当前输入的名称到localStorage
        lastSavedWorkflowName = filename;
        localStorage.setItem('lastWorkflowName', filename);
        
        showNotification('开始保存工作流...', 'info');
        
        // 首先检查画布状态
        console.log('=== 工作流保存调试信息 ===');
        console.log('画布节点数量:', app.graph ? app.graph.nodes.length : 0);
        console.log('画布链接数量:', app.graph ? app.graph.links.length : 0);
        
        if (app.graph && app.graph.nodes) {
            console.log('画布节点详情:');
            app.graph.nodes.forEach((node, index) => {
                console.log(`  节点 ${index}: ID=${node.id}, 类型=${node.type}, 模式=${node.mode}`);
            });
        }
        
        // 获取当前工作流 - 使用ComfyUI HTTP API格式
        console.log('=== 调用 app.graphToPrompt() 前的状态检查 ===');
        console.log('app 对象存在:', !!app);
        console.log('app.graphToPrompt 函数存在:', typeof app.graphToPrompt);
        console.log('app.graph 存在:', !!app.graph);
        
        // 检查画布的详细状态
        if (app.graph) {
            console.log('画布详细状态:');
            console.log('  - 节点数组:', app.graph.nodes);
            console.log('  - 链接数组:', app.graph.links);
            console.log('  - 画布配置:', app.graph.config);
            console.log('  - 画布状态:', app.graph.status);
            
            // 检查每个节点的连接状态
            if (app.graph.nodes && app.graph.nodes.length > 0) {
                console.log('节点连接状态检查:');
                app.graph.nodes.forEach((node, index) => {
                    console.log(`  节点${index} [${node.id}] ${node.type}:`);
                    console.log(`    - 模式: ${node.mode} (0=正常, 2=禁用)`);
                    console.log(`    - 输入:`, node.inputs);
                    console.log(`    - 输出:`, node.outputs);
                    console.log(`    - 属性:`, node.properties);
                    console.log(`    - 组件值:`, node.widgets_values);
                    
                    // 检查输入连接
                    if (node.inputs) {
                        node.inputs.forEach((input, inputIndex) => {
                            console.log(`      输入${inputIndex} [${input.name}]: 连接=${input.link}`);
                        });
                    }
                });
            }
        }
        
        // 尝试手动验证工作流的可执行性
        console.log('=== 工作流可执行性检查 ===');
        try {
            // 检查是否有输出节点
            const outputNodes = app.graph ? app.graph.nodes.filter(node => 
                node.mode !== 2 && (node.type === 'SaveImage' || node.type.includes('Output'))
            ) : [];
            console.log('输出节点数量:', outputNodes.length);
            console.log('输出节点:', outputNodes.map(n => `${n.id}:${n.type}`));
            
            // 检查是否有必需的基础节点
            const checkpointNodes = app.graph ? app.graph.nodes.filter(node => 
                node.mode !== 2 && node.type.includes('Checkpoint')
            ) : [];
            console.log('Checkpoint节点数量:', checkpointNodes.length);
            
        } catch (checkError) {
            console.log('工作流检查出错:', checkError);
        }
        
        // 检查 app.graphToPrompt 函数的详细信息
        console.log('=== 🔍 app.graphToPrompt 函数分析 ===');
        console.log('📋 函数类型:', typeof app.graphToPrompt);
        console.log('📋 app对象方法数量:', Object.getOwnPropertyNames(app).filter(name => typeof app[name] === 'function').length);
        console.log('📋 关键方法存在性:', {
            graphToPrompt: typeof app.graphToPrompt,
            queuePrompt: typeof app.queuePrompt,
            loadGraphData: typeof app.loadGraphData
        });
        
        let promptData;
        
        // 🚨 新的工作流获取策略：先导出普通工作流，再转换为HTTP API格式
        console.log('🚨🚨🚨 === 开始工作流数据获取和转换 === 🚨🚨🚨');
        console.log('🔧 调用前状态检查:');
        console.log('  - app存在:', !!app);
        console.log('  - app.graph存在:', !!(app && app.graph));
        console.log('  - 画布节点数:', app && app.graph ? app.graph.nodes.length : 'N/A');
        
        let normalWorkflow;
        let httpWorkflow;
        
        try {
            // 第一步：导出普通工作流格式
            console.log('📋 步骤1: 导出普通工作流格式...');
            if (!app || !app.graph) {
                throw new Error('app或app.graph不存在');
            }
            
            // 使用app.graph.serialize()获取完整的工作流数据
            normalWorkflow = app.graph.serialize();
            console.log('✅ 普通工作流导出成功!');
            console.log('📊 普通工作流信息:', {
                hasNodes: !!(normalWorkflow && normalWorkflow.nodes),
                hasLinks: !!(normalWorkflow && normalWorkflow.links),
                nodeCount: normalWorkflow && normalWorkflow.nodes ? normalWorkflow.nodes.length : 0,
                linkCount: normalWorkflow && normalWorkflow.links ? normalWorkflow.links.length : 0
            });
            
            // 第二步：转换为HTTP API格式
             console.log('🔄 步骤2: 转换为HTTP API格式...');
             httpWorkflow = convertNormalWorkflowToHttpFormat(normalWorkflow);
             console.log('✅ HTTP API格式转换成功!');
             console.log('📊 HTTP工作流信息:', {
                 type: typeof httpWorkflow,
                 nodeCount: httpWorkflow ? Object.keys(httpWorkflow).length : 0,
                 firstKeys: httpWorkflow ? Object.keys(httpWorkflow).slice(0, 3) : []
             });
             
             // 详细显示转换结果的前几个节点
             if (httpWorkflow && Object.keys(httpWorkflow).length > 0) {
                 console.log('🔍 转换结果预览:');
                 Object.keys(httpWorkflow).slice(0, 2).forEach(nodeId => {
                     console.log(`  节点 ${nodeId}:`, {
                         class_type: httpWorkflow[nodeId].class_type,
                         inputCount: Object.keys(httpWorkflow[nodeId].inputs || {}).length,
                         inputs: httpWorkflow[nodeId].inputs
                     });
                 });
             }
            
            // 将转换后的数据包装成promptData格式
            promptData = {
                output: httpWorkflow,
                workflow: normalWorkflow
            };
            
        } catch (conversionError) {
            console.error('❌ 工作流获取/转换失败!');
            console.error('🔥 错误详情:', {
                name: conversionError.name,
                message: conversionError.message,
                stack: conversionError.stack ? conversionError.stack.split('\n').slice(0, 3) : 'N/A'
            });
            
            // 回退到原始方法
            console.log('🔄 回退到原始app.graphToPrompt()方法...');
            try {
                promptData = app.graphToPrompt();
                console.log('✅ 回退方法成功!');
            } catch (fallbackError) {
                console.error('❌ 回退方法也失败了:', fallbackError.message);
                throw new Error(`所有工作流获取方法都失败了: ${conversionError.message}`);
            }
        }
        
        // 🚨 强制输出：promptData 分析
        console.log('🚨🚨🚨 === promptData 详细分析 === 🚨🚨🚨');
        console.log('📊 基本信息:', {
            type: typeof promptData,
            isNull: promptData === null,
            isUndefined: promptData === undefined,
            isTruthy: !!promptData
        });
        
        if (promptData) {
            console.log('✅ promptData 存在!');
            console.log('🔑 promptData 键:', Object.keys(promptData));
            console.log('📏 JSON 长度:', JSON.stringify(promptData).length);
            
            if (promptData.output) {
                console.log('✅ promptData.output 存在!');
                console.log('📊 output 信息:', {
                    type: typeof promptData.output,
                    keyCount: Object.keys(promptData.output).length,
                    firstKeys: Object.keys(promptData.output).slice(0, 5)
                });
            } else {
                console.log('❌ promptData.output 不存在或为空');
            }
            
            if (promptData.workflow) {
                console.log('✅ promptData.workflow 存在!');
                console.log('📊 workflow 键:', Object.keys(promptData.workflow));
            } else {
                console.log('⚠️ promptData.workflow 不存在或为空');
            }
        } else {
            console.log('❌ promptData 为空或未定义!');
        }
        
        console.log('=== 最终获取的数据分析 ===');
        console.log('返回值详细信息:');
        console.log('  - 返回值:', promptData);
        console.log('  - 返回值类型:', typeof promptData);
        console.log('  - 是否为null:', promptData === null);
        console.log('  - 是否为undefined:', promptData === undefined);
        if (promptData) {
            console.log('  - JSON字符串长度:', JSON.stringify(promptData).length);
            console.log('  - JSON字符串预览:', JSON.stringify(promptData, null, 2).substring(0, 500) + '...');
        }
        
        console.log('获取到的prompt数据:', promptData);
        console.log('prompt数据类型:', typeof promptData);
        console.log('prompt数据键:', promptData ? Object.keys(promptData) : 'null')
        
        if (!promptData) {
            // 提供更详细的错误信息
            const nodeCount = app.graph ? app.graph.nodes.length : 0;
            const enabledNodes = app.graph ? app.graph.nodes.filter(node => node.mode !== 2).length : 0;
            
            let errorMsg = '无法获取工作流数据。';
            if (nodeCount === 0) {
                errorMsg += ' 画布中没有节点，请添加节点后重试。';
            } else if (enabledNodes === 0) {
                errorMsg += ` 画布中有 ${nodeCount} 个节点，但都处于禁用状态（模式2）。请启用至少一个节点。`;
            } else {
                errorMsg += ` 画布中有 ${nodeCount} 个节点（${enabledNodes} 个启用），但 app.graphToPrompt() 返回空值。请检查节点连接和配置。`;
            }
            
            throw new Error(errorMsg);
        }
        
        // 根据ComfyUI文档，app.graphToPrompt()返回的结构是：
        // { output: object, workflow: object }
        // 其中output是HTTP API格式的工作流数据（节点ID到节点数据映射）
        let workflow;
        
        console.log('🚨🚨🚨 === 工作流数据格式判断 === 🚨🚨🚨');
        
        if (promptData.output && typeof promptData.output === 'object') {
            // 标准情况：使用output字段（HTTP API格式）
            workflow = promptData.output;
            console.log('✅ 使用prompt.output作为工作流数据（标准HTTP API格式）');
            console.log('📊 output数据节点数量:', Object.keys(workflow).length);
            console.log('📋 output数据示例:', Object.keys(workflow).slice(0, 2).reduce((obj, key) => {
                obj[key] = workflow[key];
                return obj;
            }, {}));
        } else if (typeof promptData === 'object' && !promptData.output && !promptData.workflow) {
            // 备用情况：promptData本身就是工作流对象
            workflow = promptData;
            console.log('✅ 使用prompt本身作为工作流数据（备用格式）');
            console.log('📊 promptData节点数量:', Object.keys(workflow).length);
        } else {
            console.error('❌ 意外的prompt数据结构:', promptData);
            console.log('🔍 promptData类型:', typeof promptData);
            console.log('🔍 promptData.output存在:', !!promptData.output);
            console.log('🔍 promptData.workflow存在:', !!promptData.workflow);
            console.log('🔍 promptData所有键:', Object.keys(promptData));
            throw new Error('获取到的工作流数据格式不正确。期望的格式：{output: object, workflow: object}');
        }
        
        console.log('🚨🚨🚨 === 最终工作流数据确认 === 🚨🚨🚨');
        console.log('🎯 最终工作流数据状态:', {
            exists: !!workflow,
            type: typeof workflow,
            nodeCount: workflow ? Object.keys(workflow).length : 0,
            isObject: workflow && typeof workflow === 'object',
            hasKeys: workflow ? Object.keys(workflow).length > 0 : false
        });
        
        // 打印前几个节点的信息用于调试
        if (workflow && typeof workflow === 'object') {
            const nodeIds = Object.keys(workflow).slice(0, 3);
            console.log('🔍 前几个节点ID:', nodeIds);
            console.log('🔍 前几个节点详情:');
            nodeIds.forEach(id => {
                console.log(`  节点 ${id}:`, {
                    class_type: workflow[id].class_type || 'unknown',
                    hasInputs: !!(workflow[id].inputs),
                    inputCount: workflow[id].inputs ? Object.keys(workflow[id].inputs).length : 0
                });
            });
        }
        
        // 如果工作流数据仍然有问题，输出完整的调试信息
        if (!workflow || Object.keys(workflow).length === 0) {
            console.log('=== 完整调试信息 ===');
            console.log('app.graph:', app.graph);
            console.log('app.graph.nodes:', app.graph ? app.graph.nodes : 'null');
            console.log('app.graph.links:', app.graph ? app.graph.links : 'null');
            
            if (app.graph && app.graph.nodes) {
                console.log('详细节点信息:');
                app.graph.nodes.forEach(node => {
                    console.log(`节点 ${node.id} (${node.type}):`, {
                        mode: node.mode,
                        inputs: node.inputs,
                        outputs: node.outputs,
                        properties: node.properties,
                        widgets_values: node.widgets_values
                    });
                });
            }
        }
        
        // 验证工作流数据不为空且格式正确
        if (!workflow || typeof workflow !== 'object') {
            throw new Error('工作流数据无效，请确保画布中有节点');
        }
        
        const nodeIds = Object.keys(workflow);
        if (nodeIds.length === 0) {
            throw new Error('工作流数据为空，请确保画布中有节点并且节点已正确配置');
        }
        
        // 验证节点数据格式（HTTP API格式应该包含class_type和inputs）
        let validNodes = 0;
       let invalidNodeDetails = [];
        
        console.log('=== 节点有效性验证 ===');
        for (const nodeId of nodeIds) {
            const node = workflow[nodeId];
            console.log(`检查节点 ${nodeId}:`, {
                存在: !!node,
                类型: typeof node,
                有class_type: !!(node && node.class_type),
                class_type值: node ? node.class_type : 'N/A',
                有inputs: !!(node && node.inputs),
                inputs数量: node && node.inputs ? Object.keys(node.inputs).length : 0
            });
            
            if (node && typeof node === 'object' && node.class_type) {
                validNodes++;
            } else {
                invalidNodeDetails.push({
                    nodeId,
                    reason: !node ? '节点不存在' : 
                           typeof node !== 'object' ? '节点不是对象' : 
                           !node.class_type ? '缺少class_type属性' : '未知原因'
                });
            }
        }
        
        console.log(`总节点数: ${nodeIds.length}, 有效节点数: ${validNodes}`);
        if (invalidNodeDetails.length > 0) {
            console.log('无效节点详情:', invalidNodeDetails);
        }
        
        if (validNodes === 0) {
             // 分析可能的原因
             const nodeCount = app.graph ? app.graph.nodes.length : 0;
             const enabledNodes = app.graph ? app.graph.nodes.filter(node => node.mode !== 2).length : 0;
             
             let errorMsg = '没有找到有效的节点数据。';
             
             if (nodeCount > 0 && enabledNodes > 0) {
                 // 检查节点是否有必要的输入连接
                 const nodesWithoutInputs = app.graph.nodes.filter(node => {
                     return node.mode !== 2 && node.inputs && node.inputs.length > 0 && 
                            !node.inputs.some(input => input.link !== null);
                 }).length;
                 
                 if (nodesWithoutInputs > 0) {
                     errorMsg += ` 发现 ${nodesWithoutInputs} 个节点缺少必要的输入连接。`;
                 }
                 
                 errorMsg += ' 可能的原因：1) 节点缺少必要的输入连接 2) 节点配置不完整 3) 工作流中存在循环依赖。请检查所有节点的连接和配置。';
             } else {
                 errorMsg += ' 请确保工作流包含正确配置和启用的节点。';
             }
             
             throw new Error(errorMsg);
         }
        
        // 发送到后端API
        const apiPath = getApiPath();
        console.log('正在发送请求到:', apiPath);
        console.log('请求数据:', { filename: filename, workflow_data_keys: Object.keys(workflow || {}) });
        
        const response = await fetch(apiPath, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                workflow_data: workflow  // 发送纯工作流数据
            })
        });
        
        console.log('响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('服务器错误响应:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('服务器响应:', result);
        
        if (result.success) {
            let message = `工作流已保存到: ${result.save_directory}\\${filename}`;
            if (result.websocket_sent) {
                message += ' 并已发送到Leafer应用';
            } else {
                message += ' (WebSocket发送失败)';
            }
            showNotification(message, 'success');
        } else {
            showNotification(`保存失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('保存工作流时出错:', error);
        
        // 提供故障排除指南
        console.log('=== 故障排除指南 ===');
        console.log('1. 确保画布中至少有一个节点');
        console.log('2. 确保节点处于启用状态（右键节点 -> Mode -> Always）');
        console.log('3. 确保必要的节点有输入连接');
        console.log('4. 尝试点击 "Queue Prompt" 按钮测试工作流是否可执行');
        console.log('5. 检查浏览器控制台的详细错误信息');
        console.log('6. 如果问题持续，请尝试重新加载页面');
        
        // 显示用户友好的错误信息
        let userMessage = error.message;
        if (error.message.includes('工作流数据为空')) {
            // 输出完整的诊断信息
            console.log('=== 完整诊断报告（工作流数据为空）===');
            console.log('1. 画布基本信息:');
            console.log('   - 节点总数:', app.graph ? app.graph.nodes.length : 0);
            console.log('   - 链接总数:', app.graph ? app.graph.links.length : 0);
            console.log('   - 画布状态:', app.graph ? '存在' : '不存在');
            
            if (app.graph && app.graph.nodes) {
                console.log('2. 节点详细状态:');
                app.graph.nodes.forEach((node, index) => {
                    console.log(`   节点${index} [ID:${node.id}]:`, {
                        类型: node.type,
                        模式: node.mode,
                        标题: node.title,
                        位置: `(${node.pos[0]}, ${node.pos[1]})`,
                        输入数: node.inputs ? node.inputs.length : 0,
                        输出数: node.outputs ? node.outputs.length : 0,
                        属性: node.properties,
                        组件值: node.widgets_values
                    });
                });
            }
            
            console.log('3. 建议检查项目:');
            console.log('   - 确认所有节点都已正确配置');
            console.log('   - 检查是否有节点处于错误状态');
            console.log('   - 验证节点间的连接是否完整');
            console.log('   - 尝试手动执行工作流（Queue Prompt）');
            
            userMessage += '\n\n💡 解决建议：\n1. 确保画布中有节点且已启用\n2. 检查节点连接是否正确\n3. 尝试先点击"Queue Prompt"测试工作流\n4. 查看浏览器控制台的详细诊断信息';
        }
        
        showNotification(`保存失败: ${userMessage}`, 'error');
    }
}

// 注册ComfyUI扩展
app.registerExtension({
    name: "Base64Nodes.WorkflowSaver",
    
    async setup() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }
        
        // 创建悬浮按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            position: fixed;
            top: 70px;
            left: 70px;
            z-index: 9999;
            display: flex;
            gap: 5px;
        `;
        
        // 创建主保存按钮
        const floatingButton = document.createElement('button');
        floatingButton.innerHTML = `
            <svg width="32" height="32" viewBox="0 0 756.89 756.89" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <style>
                        .cls-1 {
                            fill: #181818;
                        }
                        .cls-1, .cls-2 {
                            stroke-width: 0px;
                        }
                        .cls-2 {
                            fill: #346eff;
                        }
                    </style>
                </defs>
                <circle class="cls-1" cx="378.44" cy="378.44" r="378.44"/>
                <path class="cls-2" d="M426.73,289.03l142.52,89.41-142.52,89.41v-178.82M398.26,208.89c-7.58-.01-14.86,3-20.22,8.36-5.36,5.37-8.37,12.63-8.36,20.22v281.96c0,7.58,3.01,14.86,8.37,20.22,5.37,5.36,12.63,8.37,20.22,8.36,5.35-.01,10.59-1.54,15.1-4.41l224.72-140.98c8.31-5.22,13.36-14.35,13.36-24.16s-5.04-18.95-13.36-24.17l-224.72-140.98c-4.52-2.87-9.75-4.4-15.1-4.41h0ZM215.39,208.89h54.26v339.11h-54.26V208.89ZM215.39,208.89"/>
            </svg>
        `;
        floatingButton.style.cssText = `
            background: transparent;
            border: none;
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            user-select: none;
            width: 52px;
            height: 52px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // 设置按钮已移除，不再需要自定义API路径
        
        // 悬停效果
        floatingButton.addEventListener('mouseenter', () => {
            floatingButton.style.transform = 'scale(1.1)';
            floatingButton.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
        });
        
        floatingButton.addEventListener('mouseleave', () => {
            floatingButton.style.transform = 'scale(1)';
            floatingButton.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        });
        
        // 点击效果
        floatingButton.addEventListener('mousedown', () => {
            floatingButton.style.transform = 'scale(0.95)';
        });
        
        floatingButton.addEventListener('mouseup', () => {
            floatingButton.style.transform = 'scale(1.1)';
        });
        
        // 设置按钮相关代码已移除
        
        // 点击事件 - 改为显示工作流列表
        floatingButton.addEventListener('click', showWorkflowList);
        
        // 创建保存更改按钮
        const saveChangesButton = document.createElement('button');
        saveChangesButton.innerHTML = `
            <svg width="32" height="32" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path fill="#ffffff" d="M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3M19,19H5V5H16.17L19,7.83V19M12,12C10.34,12 9,13.34 9,15C9,16.66 10.34,18 12,18C13.66,18 15,16.66 15,15C15,13.34 13.66,12 12,12M6,6V10H15V6H6Z"/>
            </svg>
        `;
        saveChangesButton.style.cssText = `
            background: #28a745;
            border: none;
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            user-select: none;
            width: 52px;
            height: 52px;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0.5;
        `;
        
        // 初始状态为禁用
        saveChangesButton.disabled = true;
        saveChangesButton.title = '请先导入工作流';
        
        // 悬停效果
        saveChangesButton.addEventListener('mouseenter', () => {
            if (!saveChangesButton.disabled) {
                saveChangesButton.style.transform = 'scale(1.1)';
                saveChangesButton.style.boxShadow = '0 6px 20px rgba(40, 167, 69, 0.4)';
            }
        });
        
        saveChangesButton.addEventListener('mouseleave', () => {
            if (!saveChangesButton.disabled) {
                saveChangesButton.style.transform = 'scale(1)';
                saveChangesButton.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
            }
        });
        
        // 点击效果
        saveChangesButton.addEventListener('mousedown', () => {
            if (!saveChangesButton.disabled) {
                saveChangesButton.style.transform = 'scale(0.95)';
            }
        });
        
        saveChangesButton.addEventListener('mouseup', () => {
            if (!saveChangesButton.disabled) {
                saveChangesButton.style.transform = 'scale(1.1)';
            }
        });
        
        // 点击事件 - 保存当前工作流更改
        saveChangesButton.addEventListener('click', async () => {
            if (saveChangesButton.disabled || !currentImportedWorkflowName) {
                showNotification('请先导入工作流才能保存更改', 'error');
                return;
            }
            
            try {
                showNotification(`正在保存工作流更改: ${currentImportedWorkflowName}`);
                await saveWorkflowChanges(currentImportedWorkflowName);
            } catch (error) {
                console.error('保存工作流更改失败:', error);
                showNotification(`保存工作流更改失败: ${error.message}`, 'error');
            }
        });
        
        // 全局函数：更新保存按钮状态
        window.updateSaveButtonState = function() {
            if (currentImportedWorkflowName) {
                saveChangesButton.disabled = false;
                saveChangesButton.style.opacity = '1';
                saveChangesButton.style.cursor = 'pointer';
                saveChangesButton.title = `保存对 "${currentImportedWorkflowName}" 的更改`;
            } else {
                saveChangesButton.disabled = true;
                saveChangesButton.style.opacity = '0.5';
                saveChangesButton.style.cursor = 'not-allowed';
                saveChangesButton.title = '请先导入工作流';
            }
        };
        
        // 添加按钮到容器
        buttonContainer.appendChild(floatingButton);
        buttonContainer.appendChild(saveChangesButton);
        
        // 添加到页面
        document.body.appendChild(buttonContainer);
        
        console.log('工作流保存悬浮按钮已创建');
    }
});