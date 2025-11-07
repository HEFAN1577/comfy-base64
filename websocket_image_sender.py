import torch
import numpy as np
from PIL import Image
import base64
import io
import json
import websockets
import asyncio
import threading
from datetime import datetime

class WebSocketImageSender:
    """
    ComfyUI节点：通过WebSocket发送图像到 ws://localhost:3078/image-ws
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "optional": {
                "source_name": ("STRING", {"default": "ComfyUI"}),
                "metadata": ("STRING", {"default": "{}"}),
                "websocket_url": ("STRING", {"default": "ws://localhost:3078/image-ws"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "send_images_websocket"
    CATEGORY = "ETN/WebSocket"
    OUTPUT_NODE = True
    
    def send_images_websocket(self, images, source_name="ComfyUI", metadata="{}", websocket_url="ws://localhost:3078/image-ws"):
        """
        通过WebSocket发送图像并透传原始图像
        """
        try:
            # 解析元数据
            try:
                metadata_dict = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata_dict = {"raw_metadata": metadata}
            
            # 处理图像批次
            for i, image_tensor in enumerate(images):
                # 转换张量为PIL图像
                if len(image_tensor.shape) == 3:
                    # 单张图像 (H, W, C)
                    image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                else:
                    # 批次中的图像
                    image_np = (image_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                
                pil_image = Image.fromarray(image_np)
                
                # 转换为base64
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # 发送到WebSocket服务器
                try:
                    # 发送图像数据
                    message = {
                        "type": "image_data",
                        "image": image_base64,
                        "timestamp": datetime.now().isoformat(),
                        "source": source_name,
                        "metadata": {
                            **metadata_dict,
                            "batch_index": i,
                            "total_images": len(images),
                            "image_size": f"{pil_image.width}x{pil_image.height}",
                            "format": "PNG"
                        }
                    }
                    
                    # 使用 websockets 库发送数据
                    self._send_websocket_sync(websocket_url, json.dumps(message))
                    
                    print(f"[WebSocketImageSender] 图像 {i+1}/{len(images)} 发送成功到 {websocket_url}")
                        
                except Exception as e:
                    print(f"[WebSocketImageSender] WebSocket发送错误: {e}")
            
            # 透传原始图像
            return (images,)
            
        except Exception as e:
            print(f"[WebSocketImageSender] 处理错误: {e}")
            # 即使出错也要透传图像
            return (images,)
    
    async def _send_websocket_message(self, websocket_url, message):
        """
        使用 websockets 库发送消息的异步方法
        """
        try:
            # 设置连接超时和ping参数
            async with websockets.connect(
                websocket_url,
                open_timeout=10,  # 连接超时10秒
                close_timeout=5,  # 关闭超时5秒
                ping_interval=20, # ping间隔20秒
                ping_timeout=10   # ping超时10秒
            ) as websocket:
                await websocket.send(message)
                print(f"[WebSocketImageSender] 消息发送成功到 {websocket_url}")
        except Exception as e:
            raise e
    
    def _send_websocket_sync(self, websocket_url, message):
        """同步方式发送 WebSocket 消息"""
        def run_async():
            try:
                asyncio.run(self._send_websocket_message(websocket_url, message))
            except Exception as e:
                print(f"[WebSocketImageSender] WebSocket发送错误: {e}")
        
        # 在新线程中运行异步代码
        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join()  # 等待线程完成

# 节点映射
NODE_CLASS_MAPPINGS = {
    "WebSocketImageSender": WebSocketImageSender
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WebSocketImageSender": "WebSocket Image Sender"
}