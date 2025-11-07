import json
import os
from datetime import datetime
import folder_paths
from aiohttp import web
import aiohttp
from server import PromptServer
import websockets
import asyncio

class WorkflowSaverNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "save_directory": ("STRING", {
                    "default": "c:\\Users\\Administrator\\Documents\\workflows",
                    "multiline": False
                }),
                "filename_prefix": ("STRING", {
                    "default": "workflow",
                    "multiline": False
                }),
                "auto_timestamp": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "trigger": ("*", {}),  # 可以连接任何输出来触发保存
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("saved_path",)
    FUNCTION = "save_workflow"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Workflow Saver"
    OUTPUT_NODE = True

    def save_workflow(self, save_directory, filename_prefix, auto_timestamp, prompt=None, extra_pnginfo=None, trigger=None):
        try:
            # 确保保存目录存在
            os.makedirs(save_directory, exist_ok=True)
            
            # 生成文件名
            if auto_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{timestamp}.json"
            else:
                filename = f"{filename_prefix}.json"
            
            filepath = os.path.join(save_directory, filename)
            
            # 调试信息：打印prompt的内容和类型
            print(f"接收到的prompt类型: {type(prompt)}")
            print(f"接收到的prompt内容: {prompt}")
            
            # 准备ComfyUI HTTP API格式的工作流数据
            # 根据ComfyUI文档，HTTP API格式应该直接是prompt对象（节点ID到节点数据的映射）
            if prompt and isinstance(prompt, dict) and len(prompt) > 0:
                workflow_data = prompt
                print(f"使用prompt作为工作流数据，节点数量: {len(prompt)}")
            else:
                print("警告: prompt为空或无效，保存空工作流")
                workflow_data = {}
            
            # 保存工作流文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)
            
            print(f"工作流已保存到: {filepath}")
            print(f"保存的数据大小: {len(json.dumps(workflow_data))} 字符")
            return (filepath,)
            
        except Exception as e:
            error_msg = f"保存工作流时出错: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg,)

class WorkflowListNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "refresh": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "trigger": ("*", {}),  # 可以连接任何输出来触发刷新
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("workflow_list",)
    FUNCTION = "get_workflow_list"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Workflow List"
    OUTPUT_NODE = True

    def get_workflow_list(self, refresh, trigger=None):
        try:
            # 通过WebSocket获取工作流列表
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                workflow_list = loop.run_until_complete(self.fetch_workflow_list())
                return (json.dumps(workflow_list, ensure_ascii=False),)
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"获取工作流列表时出错: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (error_msg,)
    
    async def fetch_workflow_list(self):
        try:
            # WebSocket服务器地址
            websocket_url = "ws://localhost:3078/ws"
            
            async with websockets.connect(websocket_url) as websocket:
                # 发送获取工作流列表请求
                request_message = {
                    "type": "get_workflow_list",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(request_message))
                
                # 等待响应
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "workflow_list":
                    workflow_files = response_data.get("workflows", [])
                    print(f"从主应用获取到工作流列表: {workflow_files}")
                    return {
                        "success": True,
                        "workflows": workflow_files,
                        "count": len(workflow_files)
                    }
                else:
                    print(f"收到意外响应: {response_data}")
                    return {
                        "success": False,
                        "error": "收到意外响应格式",
                        "workflows": []
                    }
                    
        except Exception as e:
            print(f"WebSocket获取工作流列表失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflows": []
            }

# FloatingWorkflowSaver节点已移除，现在使用全局悬浮按钮

# 注册节点
NODE_CLASS_MAPPINGS = {
    "WorkflowSaverNode": WorkflowSaverNode,
    "WorkflowListNode": WorkflowListNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WorkflowSaverNode": "Workflow Saver",
    "WorkflowListNode": "Workflow List",
}

# 通过WebSocket发送工作流到Leafer应用
async def send_workflow_to_leafer(workflow_data, filename):
    try:
        # WebSocket服务器地址
        websocket_url = "ws://localhost:3078"
        
        # 首先发送路径查询请求
        async with websockets.connect(websocket_url) as websocket:
            # 查询工作流保存路径
            path_query = {
                "type": "get_workflow_path"
            }
            await websocket.send(json.dumps(path_query))
            
            # 等待路径响应
            path_response = await websocket.recv()
            path_data = json.loads(path_response)
            
            # 获取动态路径，如果没有返回则使用默认路径
            workflow_path = path_data.get("workflow_path", "c:\\Users\\Administrator\\Documents\\GitHub\\MMX\\workflow\\files")
            print(f"从Leafer应用获取的工作流路径: {workflow_path}")
            
            # 准备发送的数据 - 发送ComfyUI HTTP API格式的工作流数据
            message = {
                "type": "workflow_save",
                "filename": filename,
                "workflow_data": workflow_data,  # ComfyUI HTTP API格式的工作流数据
                "save_path": workflow_path
            }
            
            # 发送工作流数据
            await websocket.send(json.dumps(message))
            print(f"工作流已通过WebSocket发送到Leafer应用: {filename}")
            return True, workflow_path
            
    except Exception as e:
        print(f"WebSocket发送失败: {str(e)}")
        return False, None

# Web API路由处理函数
async def save_workflow_api(request):
    try:
        print("收到工作流保存请求")
        data = await request.json()
        print(f"请求数据类型: {type(data)}")
        print(f"请求数据键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        filename = data.get('filename', 'workflow.json')
        workflow_data = data.get('workflow_data', {})
        
        print(f"文件名: {filename}")
        print(f"工作流数据类型: {type(workflow_data)}")
        print(f"工作流数据大小: {len(workflow_data) if isinstance(workflow_data, dict) else 'N/A'}")
        
        # 验证工作流数据
        if not workflow_data or not isinstance(workflow_data, dict):
            print("警告: 接收到的工作流数据为空或格式不正确")
            return web.json_response({
                "success": False,
                "error": "工作流数据为空或格式不正确",
                "message": "请确保画布中有节点并且节点已正确配置"
            }, status=400, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            })
        
        # 确保文件名以.json结尾
        if not filename.endswith('.json'):
            filename += '.json'
        
        # 通过WebSocket发送到Leafer应用并获取动态路径
        websocket_success, dynamic_path = await send_workflow_to_leafer(workflow_data, filename)
        
        # 使用动态获取的路径，如果失败则使用默认路径
        save_directory = dynamic_path if dynamic_path else "c:\\Users\\Administrator\\Documents\\GitHub\\MMX\\workflow\\files"
        
        print(f"保存目录: {save_directory}")
        print(f"文件名: {filename}")
        
        # 确保保存目录存在
        os.makedirs(save_directory, exist_ok=True)
        
        # 完整文件路径
        filepath = os.path.join(save_directory, filename)
        
        # 保存ComfyUI HTTP API格式的工作流数据到本地
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, indent=2, ensure_ascii=False)
        
        print(f"工作流已保存到本地: {filepath}")
        
        return web.json_response({
            "success": True,
            "filepath": filepath,
            "save_directory": save_directory,
            "websocket_sent": websocket_success,
            "message": "工作流保存成功" + (" 并已发送到Leafer应用" if websocket_success else " 但WebSocket发送失败")
        }, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
        
    except Exception as e:
        print(f"API保存工作流时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            "success": False,
            "error": str(e),
            "message": "工作流保存失败"
        }, status=500, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

# 注册Web API路由
def register_api_routes():
    try:
        # 确保PromptServer实例存在
        if hasattr(PromptServer, 'instance') and PromptServer.instance:
            # 注册POST路由
            PromptServer.instance.routes.post("/Base64Nodes/save_workflow")(save_workflow_api)
            # 注册OPTIONS路由用于CORS预检
            PromptServer.instance.routes.options("/Base64Nodes/save_workflow")(handle_options)
            print("工作流保存API路由已注册: /Base64Nodes/save_workflow")
        else:
            print("PromptServer实例不可用，稍后重试路由注册")
    except Exception as e:
        print(f"注册API路由时出错: {str(e)}")
        import traceback
        traceback.print_exc()

# OPTIONS请求处理函数
async def handle_options(request):
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

# 获取工作流模板的HTTP API函数
async def get_workflow_templates_from_api():
    """通过HTTP API获取工作流模板列表"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:3078/api/workflow_templates') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        return data.get('templates', [])
                    else:
                        print(f"获取工作流模板失败: {data.get('error')}")
                        return []
                else:
                    print(f"HTTP请求失败，状态码: {response.status}")
                    return []
    except Exception as e:
        print(f"获取工作流模板时出错: {str(e)}")
        return []

# 转换前端工作流为HTTP API格式的改进版本
def convert_frontend_to_http_api_format(frontend_workflow):
    """将前端工作流格式转换为HTTP API格式"""
    try:
        if not frontend_workflow or not isinstance(frontend_workflow, dict):
            raise ValueError("无效的前端工作流数据")
        
        nodes = frontend_workflow.get('nodes', [])
        links = frontend_workflow.get('links', [])
        
        if not nodes:
            raise ValueError("工作流中没有节点")
        
        # 创建链接映射表
        link_map = {}
        for link in links:
            if isinstance(link, list) and len(link) >= 6:
                link_id, source_node_id, source_slot, target_node_id, target_slot, link_type = link[:6]
                link_map[link_id] = {
                    'source_node_id': source_node_id,
                    'source_slot': source_slot,
                    'target_node_id': target_node_id,
                    'target_slot': target_slot,
                    'type': link_type
                }
        
        http_api_format = {}
        
        # 转换每个节点
        for node in nodes:
            if not isinstance(node, dict):
                continue
                
            node_id = str(node.get('id', ''))
            node_type = node.get('type', '')
            
            if not node_id or not node_type:
                continue
            
            # 跳过禁用的节点
            if node.get('mode') == 2:
                continue
            
            http_node = {
                'class_type': node_type,
                'inputs': {}
            }
            
            # 处理输入连接
            inputs = node.get('inputs', [])
            for i, input_def in enumerate(inputs):
                if isinstance(input_def, dict):
                    input_name = input_def.get('name', f'input_{i}')
                    link_id = input_def.get('link')
                    
                    if link_id is not None and link_id in link_map:
                        link_info = link_map[link_id]
                        http_node['inputs'][input_name] = [
                            str(link_info['source_node_id']),
                            link_info['source_slot']
                        ]
            
            # 处理widget值
            widgets_values = node.get('widgets_values', [])
            if widgets_values:
                # 简化的widget映射策略
                widget_inputs = node.get('widgets', [])
                for j, widget in enumerate(widget_inputs):
                    if isinstance(widget, dict) and j < len(widgets_values):
                        widget_name = widget.get('name', f'widget_{j}')
                        if widget_name not in http_node['inputs']:
                            http_node['inputs'][widget_name] = widgets_values[j]
            
            # 添加元数据
            if node.get('title') and node['title'] != node_type:
                http_node['_meta'] = {'title': node['title']}
            
            http_api_format[node_id] = http_node
        
        print(f"成功转换工作流，包含 {len(http_api_format)} 个节点")
        return http_api_format
        
    except Exception as e:
        print(f"转换工作流格式时出错: {str(e)}")
        raise e

# 立即注册路由
register_api_routes()

# Web扩展相关
WEB_DIRECTORY = "web"