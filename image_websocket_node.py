import torch
import numpy as np
import base64
import json
import requests
import time
from io import BytesIO
from PIL import Image
from typing import Optional, Dict, Any
import threading

# 全局变量用于存储当前执行的工作流
_current_workflow_data = threading.local()

def set_current_workflow(workflow_data):
    """设置当前线程的工作流数据"""
    _current_workflow_data.workflow = workflow_data

def get_current_workflow():
    """获取当前线程的工作流数据"""
    return getattr(_current_workflow_data, 'workflow', None)

class ImageWebSocketOutput:
    """通过HTTP请求发送图像和节点ID到React Flow的输出节点"""
    
    def __init__(self):
        self.proxy_url = "http://localhost:3078"
        self.connection_status = "就绪"
        self.last_error = ""
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "react_node_id": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入React Flow节点ID"
                }),
            },
            "optional": {
                "proxy_url": ("STRING", {
                    "default": "http://localhost:3078",
                    "multiline": False
                }),
                "workflow_data": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "工作流JSON数据（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("images", "connection_status", "message_log")
    FUNCTION = "send_image"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Image WebSocket Output"
    OUTPUT_NODE = True
    
    def tensor_to_base64(self, tensor):
        """将tensor转换为base64字符串"""
        try:
            # 确保tensor在正确的范围内 [0, 1]
            if tensor.max() > 1.0:
                tensor = tensor / 255.0
            
            # 转换为numpy数组并调整到[0, 255]范围
            numpy_image = (tensor.squeeze().cpu().numpy() * 255).astype(np.uint8)
            
            # 如果是单通道图像，转换为RGB
            if len(numpy_image.shape) == 2:
                numpy_image = np.stack([numpy_image] * 3, axis=-1)
            elif len(numpy_image.shape) == 3 and numpy_image.shape[2] == 1:
                numpy_image = np.repeat(numpy_image, 3, axis=2)
            
            # 创建PIL图像
            pil_image = Image.fromarray(numpy_image)
            
            # 转换为base64
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
        except Exception as e:
            print(f"[ImageWebSocketOutput] 转换图像为base64失败: {e}")
            return None
    
    def send_http_message(self, message, proxy_url):
        """通过HTTP POST发送消息到proxy_server"""
        try:
            # 构建完整的URL
            url = f"{proxy_url}/api/image-message"
            
            # 发送POST请求
            response = requests.post(
                url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"[ImageWebSocketOutput] HTTP消息发送成功: {message.get('type', 'unknown')}")
                return True
            else:
                print(f"[ImageWebSocketOutput] HTTP请求失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ImageWebSocketOutput] HTTP请求异常: {e}")
            self.last_error = str(e)
            return False
        except Exception as e:
            print(f"[ImageWebSocketOutput] 发送HTTP消息失败: {e}")
            self.last_error = str(e)
            return False
        
    def send_image(self, images, react_node_id, proxy_url="http://localhost:3078", workflow_data=""):
        """发送图像到proxy_server"""
        message_log = []
        
        try:
            # 验证输入
            if not react_node_id or react_node_id.strip() == "":
                error_msg = "React节点ID不能为空"
                message_log.append(f"错误: {error_msg}")
                print(f"[ImageWebSocketOutput] {error_msg}")
                return (images, "错误: 节点ID为空", "\n".join(message_log))
            
            if images is None or len(images) == 0:
                error_msg = "没有输入图像"
                message_log.append(f"错误: {error_msg}")
                print(f"[ImageWebSocketOutput] {error_msg}")
                return (images, "错误: 无图像", "\n".join(message_log))
            
            # 更新proxy URL
            self.proxy_url = proxy_url
            
            # 处理图像批次
            success_count = 0
            for i, image_tensor in enumerate(images):
                try:
                    # 转换图像为base64
                    image_base64 = self.tensor_to_base64(image_tensor)
                    if image_base64 is None:
                        error_msg = f"图像 {i+1} 转换失败"
                        message_log.append(f"错误: {error_msg}")
                        print(f"[ImageWebSocketOutput] {error_msg}")
                        continue
                    
                    # 准备工作流数据
                    workflow_info = None
                    
                    # 首先尝试从手动输入获取工作流数据
                    if workflow_data and workflow_data.strip():
                        try:
                            workflow_info = json.loads(workflow_data.strip())
                        except json.JSONDecodeError:
                            print(f"[ImageWebSocketOutput] 工作流数据JSON格式无效，将作为字符串发送")
                            workflow_info = workflow_data.strip()
                    
                    # 如果没有手动输入的工作流数据，尝试自动获取当前工作流
                    if workflow_info is None:
                        # 方法1: 从线程本地存储获取
                        try:
                            workflow_info = get_current_workflow()
                            if workflow_info:
                                print(f"[ImageWebSocketOutput] 从线程本地存储获取到工作流数据")
                        except Exception as e:
                            print(f"[ImageWebSocketOutput] 从线程本地存储获取工作流数据失败: {e}")
                        
                        # 方法2: 尝试从PromptServer获取当前执行的工作流
                        if workflow_info is None:
                            try:
                                from server import PromptServer
                                prompt_server = PromptServer.instance
                                if hasattr(prompt_server, 'prompt_queue') and prompt_server.prompt_queue:
                                    # 尝试不同的方法获取当前项
                                    current_item = None
                                    if hasattr(prompt_server.prompt_queue, 'get_current'):
                                        current_item = prompt_server.prompt_queue.get_current()
                                    elif hasattr(prompt_server.prompt_queue, 'currently_running'):
                                        current_item = prompt_server.prompt_queue.currently_running
                                    elif hasattr(prompt_server.prompt_queue, 'queue') and prompt_server.prompt_queue.queue:
                                        # 获取队列中的第一个项目
                                        current_item = prompt_server.prompt_queue.queue[0] if prompt_server.prompt_queue.queue else None
                                    
                                    if current_item and len(current_item) > 2:
                                        workflow_info = current_item[2]  # 工作流数据通常在索引2
                                        print(f"[ImageWebSocketOutput] 从PromptServer获取到工作流数据")
                            except Exception as e:
                                print(f"[ImageWebSocketOutput] 从PromptServer获取工作流数据失败: {e}")
                                
                        # 方法3: 如果方法1和2失败，尝试从execution模块获取
                        if workflow_info is None:
                            try:
                                import execution
                                if hasattr(execution, 'current_prompt') and execution.current_prompt is not None:
                                    workflow_info = execution.current_prompt
                                    print(f"[ImageWebSocketOutput] 从execution模块获取到工作流数据")
                            except Exception as e:
                                print(f"[ImageWebSocketOutput] 从execution模块获取工作流数据失败: {e}")
                        
                        # 方法4: 尝试通过inspect模块获取调用栈中的工作流信息
                        if workflow_info is None:
                            try:
                                import inspect
                                # 遍历调用栈寻找可能包含工作流数据的帧
                                for frame_info in inspect.stack():
                                    frame_locals = frame_info.frame.f_locals
                                    frame_globals = frame_info.frame.f_globals
                                    
                                    # 查找可能的工作流数据变量
                                    for var_name in ['prompt', 'workflow', 'workflow_data', 'current_prompt']:
                                        if var_name in frame_locals and frame_locals[var_name]:
                                            workflow_info = frame_locals[var_name]
                                            print(f"[ImageWebSocketOutput] 从调用栈获取到工作流数据 (变量: {var_name})")
                                            break
                                        elif var_name in frame_globals and frame_globals[var_name]:
                                            workflow_info = frame_globals[var_name]
                                            print(f"[ImageWebSocketOutput] 从全局变量获取到工作流数据 (变量: {var_name})")
                                            break
                                    
                                    if workflow_info:
                                        break
                            except Exception as e:
                                print(f"[ImageWebSocketOutput] 从调用栈获取工作流数据失败: {e}")
                        
                        if workflow_info is None:
                            print(f"[ImageWebSocketOutput] 无法自动获取工作流数据，将不包含工作流信息")
                    
                    # 尝试获取当前的prompt_id
                    prompt_id = None
                    print(f"[ImageWebSocketOutput] 开始获取prompt_id...")
                    
                    # 方法1: 从execution模块获取当前prompt_id
                    try:
                        import execution
                        print(f"[ImageWebSocketOutput] 检查execution模块...")
                        if hasattr(execution, 'current_prompt_id') and execution.current_prompt_id:
                            prompt_id = execution.current_prompt_id
                            print(f"[ImageWebSocketOutput] 从execution.current_prompt_id获取到: {prompt_id}")
                        elif hasattr(execution, 'current_execution') and execution.current_execution:
                            if hasattr(execution.current_execution, 'prompt_id'):
                                prompt_id = execution.current_execution.prompt_id
                                print(f"[ImageWebSocketOutput] 从execution.current_execution.prompt_id获取到: {prompt_id}")
                        else:
                            print(f"[ImageWebSocketOutput] execution模块中没有找到prompt_id相关属性")
                    except Exception as e:
                        print(f"[ImageWebSocketOutput] 从execution模块获取prompt_id失败: {e}")
                    
                    # 方法2: 从PromptServer获取已移除（性能优化）
                    
                    # 方法3: 尝试从全局变量或环境变量获取
                    if prompt_id is None:
                        try:
                            import os
                            env_prompt_id = os.environ.get('COMFYUI_PROMPT_ID')
                            if env_prompt_id:
                                prompt_id = env_prompt_id
                                print(f"[ImageWebSocketOutput] 从环境变量获取到prompt_id: {prompt_id}")
                        except Exception as e:
                            print(f"[ImageWebSocketOutput] 从环境变量获取prompt_id失败: {e}")
                    
                    # 方法4: 尝试从调用栈中查找prompt_id (优化性能)
                    if prompt_id is None:
                        try:
                            import inspect
                            # 限制搜索深度以提高性能
                            stack_frames = inspect.stack()[:10]  # 只检查前10层调用栈
                            for frame_info in stack_frames:
                                frame_locals = frame_info.frame.f_locals
                                frame_globals = frame_info.frame.f_globals
                                
                                # 查找可能的prompt_id变量
                                for var_name in ['prompt_id', 'current_prompt_id', 'id', 'execution_id']:
                                    if var_name in frame_locals and frame_locals[var_name]:
                                        potential_id = frame_locals[var_name]
                                        if isinstance(potential_id, str) and len(potential_id) > 10:  # 简单验证
                                            prompt_id = potential_id
                                            print(f"[ImageWebSocketOutput] 从调用栈获取到prompt_id (变量: {var_name}): {prompt_id}")
                                            break
                                    elif var_name in frame_globals and frame_globals[var_name]:
                                        potential_id = frame_globals[var_name]
                                        if isinstance(potential_id, str) and len(potential_id) > 10:  # 简单验证
                                            prompt_id = potential_id
                                            print(f"[ImageWebSocketOutput] 从全局变量获取到prompt_id (变量: {var_name}): {prompt_id}")
                                            break
                                
                                if prompt_id:
                                    break
                        except Exception as e:
                            print(f"[ImageWebSocketOutput] 从调用栈获取prompt_id失败: {e}")
                    
                    # 准备HTTP消息
                    http_message = {
                        "type": "image_websocket_output",
                        "react_node_id": react_node_id.strip(),
                        "image_data": image_base64,
                        "timestamp": int(time.time() * 1000),
                        "image_index": i,
                        "workflow_data": workflow_info,
                        "prompt_id": prompt_id
                    }
                    
                    if prompt_id:
                        print(f"[ImageWebSocketOutput] 包含prompt_id: {prompt_id}")
                    else:
                        print(f"[ImageWebSocketOutput] 未能获取prompt_id")
                    
                    # 发送HTTP请求
                    print(f"[ImageWebSocketOutput] 发送图像 {i+1}/{len(images)} 到节点 {react_node_id}")
                    send_success = self.send_http_message(http_message, proxy_url)
                    
                    if send_success:
                        success_count += 1
                        success_msg = f"图像 {i+1} 发送成功"
                        message_log.append(success_msg)
                        print(f"[ImageWebSocketOutput] {success_msg}")
                    else:
                        error_msg = f"图像 {i+1} 发送失败: {self.last_error}"
                        message_log.append(f"错误: {error_msg}")
                        print(f"[ImageWebSocketOutput] {error_msg}")
                    
                except Exception as e:
                    error_msg = f"处理图像 {i+1} 失败: {str(e)}"
                    message_log.append(f"错误: {error_msg}")
                    print(f"[ImageWebSocketOutput] {error_msg}")
                    continue
            
            # 返回结果
            if success_count > 0:
                if success_count == len(images):
                    status = "发送成功"
                else:
                    status = "部分发送成功"
            else:
                status = "发送失败"
            
            return (images, status, "\n".join(message_log))
            
        except Exception as e:
            error_msg = f"发送图像失败: {str(e)}"
            message_log.append(f"错误: {error_msg}")
            print(f"[ImageWebSocketOutput] {error_msg}")
            return (images, f"错误: {str(e)}", "\n".join(message_log))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageWebSocketOutput": ImageWebSocketOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageWebSocketOutput": "Image WebSocket Output",
}

# 导出辅助函数供其他模块使用
__all__ = ['ImageWebSocketOutput', 'set_current_workflow', 'get_current_workflow']