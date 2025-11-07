import websockets
import asyncio
import json
import base64
from PIL import Image
import io
import numpy as np
import torch
import time
import threading
from datetime import datetime

# 全局状态存储，确保在ComfyUI的节点实例化过程中数据不丢失
_global_state = {
    'websocket': None,
    'server_url': "ws://localhost:3079",
    'connection_status': "🔴 未连接",
    'current_image': None,
    'current_element_name': "无",
    'last_message_time': None,
    'message_log': [],
    'is_connecting': False,
    'connection_thread': None,
    'current_base64_data': "",
    'initialized': False,
    # 新增缓存机制
    'cached_image': None,
    'cached_element_name': "无",
    'cached_base64_data': "",
    'cache_updated': False,
    'cache_timestamp': None
}

class LeaferElementReceiver:
    def __init__(self):
        # 使用全局状态而不是实例状态
        global _global_state
        
        # 只在第一次初始化时启动连接
        if not _global_state['initialized']:
            _global_state['initialized'] = True
            self.start_connection()
    
    @property
    def websocket(self):
        return _global_state['websocket']
    
    @websocket.setter
    def websocket(self, value):
        _global_state['websocket'] = value
    
    @property
    def server_url(self):
        return _global_state['server_url']
    
    @server_url.setter
    def server_url(self, value):
        _global_state['server_url'] = value
    
    @property
    def connection_status(self):
        return _global_state['connection_status']
    
    @connection_status.setter
    def connection_status(self, value):
        _global_state['connection_status'] = value
    
    @property
    def current_image(self):
        return _global_state['current_image']
    
    @current_image.setter
    def current_image(self, value):
        _global_state['current_image'] = value
    
    @property
    def current_element_name(self):
        return _global_state['current_element_name']
    
    @current_element_name.setter
    def current_element_name(self, value):
        _global_state['current_element_name'] = value
    
    @property
    def last_message_time(self):
        return _global_state['last_message_time']
    
    @last_message_time.setter
    def last_message_time(self, value):
        _global_state['last_message_time'] = value
    
    @property
    def message_log(self):
        return _global_state['message_log']
    
    @message_log.setter
    def message_log(self, value):
        _global_state['message_log'] = value
    
    @property
    def is_connecting(self):
        return _global_state['is_connecting']
    
    @is_connecting.setter
    def is_connecting(self, value):
        _global_state['is_connecting'] = value
    
    @property
    def connection_thread(self):
        return _global_state['connection_thread']
    
    @connection_thread.setter
    def connection_thread(self, value):
        _global_state['connection_thread'] = value
    
    @property
    def current_base64_data(self):
        return _global_state['current_base64_data']
    
    @current_base64_data.setter
    def current_base64_data(self, value):
        _global_state['current_base64_data'] = value
    
    # 缓存相关属性
    @property
    def cached_image(self):
        return _global_state['cached_image']
    
    @cached_image.setter
    def cached_image(self, value):
        _global_state['cached_image'] = value
    
    @property
    def cached_element_name(self):
        return _global_state['cached_element_name']
    
    @cached_element_name.setter
    def cached_element_name(self, value):
        _global_state['cached_element_name'] = value
    
    @property
    def cached_base64_data(self):
        return _global_state['cached_base64_data']
    
    @cached_base64_data.setter
    def cached_base64_data(self, value):
        _global_state['cached_base64_data'] = value
    
    @property
    def cache_updated(self):
        return _global_state['cache_updated']
    
    @cache_updated.setter
    def cache_updated(self, value):
        _global_state['cache_updated'] = value
    
    @property
    def cache_timestamp(self):
        return _global_state['cache_timestamp']
    
    @cache_timestamp.setter
    def cache_timestamp(self, value):
        _global_state['cache_timestamp'] = value
    
    @property
    def initialized(self):
        return _global_state['initialized']
    
    @initialized.setter
    def initialized(self, value):
        _global_state['initialized'] = value
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_url": ("STRING", {"default": "ws://localhost:3079"}),
                "refresh": ("BOOLEAN", {"default": False}),
                "output_base64": ("BOOLEAN", {"default": False}),
                "force_update": ("INT", {"default": 0, "min": 0, "max": 999999}),
            },
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("element_image", "element_name", "connection_status", "message_log", "base64_data")
    FUNCTION = "receive_element"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Leafer Element Receiver"
    
    # 添加输出缓存控制，确保每次都重新执行
    OUTPUT_NODE = False
    
    def add_log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.message_log.append(log_entry)
        
        # 保持最近20条日志
        if len(self.message_log) > 20:
            self.message_log = self.message_log[-20:]
        
        print(f"[LeaferReceiver] {log_entry}")
    
    def start_connection(self):
        """启动WebSocket连接"""
        if self.is_connecting:
            return
            
        self.is_connecting = True
        self.connection_thread = threading.Thread(target=self.connect_websocket, daemon=True)
        self.connection_thread.start()
    
    def connect_websocket(self):
        """连接WebSocket服务器"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.websocket_handler())
        except Exception as e:
            self.connection_status = f"🔴 连接错误: {str(e)}"
            self.add_log(f"连接错误: {str(e)}")
        finally:
            self.is_connecting = False
    
    async def websocket_handler(self):
        """WebSocket连接处理器"""
        while True:
            try:
                self.add_log(f"正在连接到 {self.server_url}...")
                async with websockets.connect(self.server_url) as websocket:
                    self.websocket = websocket
                    self.connection_status = "🟢 已连接"
                    self.add_log("WebSocket连接成功")
                    
                    # 发送客户端标识
                    await websocket.send(json.dumps({
                        "type": "comfy_node_client"
                    }))
                    self.add_log("已发送ComfyUI节点客户端标识")
                    
                    # 监听消息
                    async for message in websocket:
                        await self.handle_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                self.connection_status = "🔴 连接已断开"
                self.add_log("WebSocket连接已断开")
                self.websocket = None
            except Exception as e:
                self.connection_status = f"🔴 连接错误: {str(e)}"
                self.add_log(f"WebSocket连接错误: {str(e)}")
                self.websocket = None
            
            # 等待5秒后重连
            await asyncio.sleep(5)
            self.add_log("尝试重新连接...")
    
    async def handle_message(self, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'system':
                self.add_log(f"系统消息: {data.get('message', '')}")
            
            elif message_type == 'element_selected':
                self.add_log(f"收到元素选中消息: {data.get('elementName', 'Unknown')}")
                
                # 更新元素信息
                element_name = data.get('elementName', 'Unknown Element')
                self.current_element_name = element_name
                self.last_message_time = datetime.now()
                
                print(f"[LeaferReceiver] 收到元素选中事件: {element_name}")
                print(f"[LeaferReceiver] 完整数据结构: {list(data.keys())}")
                
                # 处理图像数据
                image_data = data.get('image')
                processed_image = None
                base64_data = ""
                
                if image_data:
                    print(f"[LeaferReceiver] 图像数据存在，类型: {type(image_data)}")
                    if isinstance(image_data, str):
                        print(f"[LeaferReceiver] Base64数据长度: {len(image_data)}")
                        print(f"[LeaferReceiver] Base64数据开头: {image_data[:100]}")
                        
                        # 检查是否是有效的Base64格式
                        if image_data.startswith('data:'):
                            print(f"[LeaferReceiver] 检测到data URL格式")
                        elif len(image_data) > 100:
                            print(f"[LeaferReceiver] 检测到纯Base64格式")
                        else:
                            print(f"[LeaferReceiver] 警告: Base64数据可能过短")
                    
                    self.add_log(f"收到图像数据，类型: {type(image_data)}, 长度: {len(image_data) if isinstance(image_data, str) else 'N/A'}")
                    
                    # 保存原始base64数据
                    if isinstance(image_data, str):
                        self.current_base64_data = image_data
                        base64_data = image_data
                        
                        # 尝试处理图像
                        try:
                            print(f"[LeaferReceiver] 开始处理元素选中图像数据...")
                            processed_image = self.process_image_data(image_data)
                            if processed_image is not None:
                                self.current_image = processed_image
                                self.add_log(f"图像处理成功，tensor形状: {processed_image.shape}")
                                print(f"[LeaferReceiver] 元素选中图像处理成功!")
                            else:
                                self.add_log("图像处理返回None，使用占位符")
                                print(f"[LeaferReceiver] 图像处理返回None")
                                processed_image = self.create_placeholder_image()
                                self.current_image = processed_image
                        except Exception as e:
                            self.add_log(f"图像处理异常: {str(e)}")
                            print(f"[LeaferReceiver] 图像处理详细错误: {e}")
                            import traceback
                            traceback.print_exc()
                            processed_image = self.create_placeholder_image()
                            self.current_image = processed_image
                    else:
                        self.add_log(f"错误: 图像数据类型无效: {type(image_data)}")
                        print(f"[LeaferReceiver] 图像数据类型错误: {type(image_data)}")
                        self.current_base64_data = ""
                        self.current_image = self.create_placeholder_image()
                        processed_image = self.create_placeholder_image()
                else:
                    self.add_log("消息中没有图像数据字段")
                    print(f"[LeaferReceiver] 没有图像数据字段")
                    self.current_base64_data = ""
                    self.current_image = self.create_placeholder_image()
                    processed_image = self.create_placeholder_image()
                
                # 立即更新缓存数据
                self.cached_image = processed_image
                self.cached_element_name = element_name
                self.cached_base64_data = base64_data
                self.cache_updated = True
                self.cache_timestamp = time.time()
                print(f"[LeaferReceiver] 缓存已更新(element_selected): {element_name}, 图像: {'有效' if processed_image is not None else '无效'}, Base64长度: {len(base64_data)}")
                self.add_log(f"缓存已更新(element_selected): {element_name}")
            
            elif message_type == 'element_unselected':
                self.add_log("收到元素取消选中消息")
                self.current_element_name = "无"
                self.current_base64_data = ""
                self.current_image = self.create_placeholder_image()
                
                # 清空缓存数据
                self.cached_image = self.create_placeholder_image()
                self.cached_element_name = "无"
                self.cached_base64_data = ""
                self.cache_updated = True
                self.cache_timestamp = time.time()
                self.add_log("缓存已清空(element_unselected)")
            
            elif message_type == 'current_element_response':
                self.add_log(f"收到当前元素响应: {data.get('elementName', 'Unknown')}")
                
                # 更新元素信息
                element_name = data.get('elementName', 'Unknown Element')
                self.current_element_name = element_name
                self.last_message_time = datetime.now()
                
                print(f"[LeaferReceiver] 收到当前元素响应: {element_name}")
                print(f"[LeaferReceiver] 完整数据结构: {list(data.keys())}")
                
                # 处理图像数据
                image_data = data.get('image')
                processed_image = None
                base64_data = ""
                
                if image_data:
                    print(f"[LeaferReceiver] 当前元素图像数据存在，类型: {type(image_data)}")
                    if isinstance(image_data, str):
                        print(f"[LeaferReceiver] 当前元素Base64数据长度: {len(image_data)}")
                        print(f"[LeaferReceiver] 当前元素Base64数据开头: {image_data[:100]}")
                        
                        # 检查是否是有效的Base64格式
                        if image_data.startswith('data:'):
                            print(f"[LeaferReceiver] 当前元素检测到data URL格式")
                        elif len(image_data) > 100:
                            print(f"[LeaferReceiver] 当前元素检测到纯Base64格式")
                        else:
                            print(f"[LeaferReceiver] 当前元素警告: Base64数据可能过短")
                    
                    self.add_log(f"收到当前元素图像数据，类型: {type(image_data)}, 长度: {len(image_data) if isinstance(image_data, str) else 'N/A'}")
                    
                    # 保存原始base64数据
                    if isinstance(image_data, str):
                        self.current_base64_data = image_data
                        base64_data = image_data
                        
                        # 尝试处理图像
                        try:
                            print(f"[LeaferReceiver] 开始处理当前元素图像数据...")
                            processed_image = self.process_image_data(image_data)
                            if processed_image is not None:
                                self.current_image = processed_image
                                self.add_log(f"当前元素图像处理成功，tensor形状: {processed_image.shape}")
                                print(f"[LeaferReceiver] 当前元素图像处理成功!")
                            else:
                                self.add_log("当前元素图像处理返回None，使用占位符")
                                print(f"[LeaferReceiver] 当前元素图像处理返回None")
                                processed_image = self.create_placeholder_image()
                                self.current_image = processed_image
                        except Exception as e:
                            self.add_log(f"当前元素图像处理异常: {str(e)}")
                            print(f"[LeaferReceiver] 当前元素图像处理详细错误: {e}")
                            import traceback
                            traceback.print_exc()
                            processed_image = self.create_placeholder_image()
                            self.current_image = processed_image
                    else:
                        self.add_log(f"错误: 当前元素图像数据类型无效: {type(image_data)}")
                        print(f"[LeaferReceiver] 当前元素图像数据类型错误: {type(image_data)}")
                        self.current_base64_data = ""
                        self.current_image = self.create_placeholder_image()
                        processed_image = self.create_placeholder_image()
                else:
                    self.add_log("当前元素响应中没有图像数据字段")
                    print(f"[LeaferReceiver] 当前元素没有图像数据字段")
                    self.current_base64_data = ""
                    self.current_image = self.create_placeholder_image()
                    processed_image = self.create_placeholder_image()
                
                # 立即更新缓存数据
                self.cached_image = processed_image
                self.cached_element_name = element_name
                self.cached_base64_data = base64_data
                self.cache_updated = True
                self.cache_timestamp = time.time()
                print(f"[LeaferReceiver] 缓存已更新(current_element_response): {element_name}, 图像: {'有效' if processed_image is not None else '无效'}, Base64长度: {len(base64_data)}")
                self.add_log(f"缓存已更新(current_element_response): {element_name}")
            
            else:
                self.add_log(f"收到未知消息类型: {message_type}")
                
        except Exception as e:
            self.add_log(f"消息处理错误: {str(e)}")
    
    def process_image_data(self, image_data):
        """处理Base64图像数据并转换为ComfyUI格式"""
        try:
            print(f"[LeaferReceiver] 开始处理图像数据，原始长度: {len(image_data)}")
            
            # 移除data URL前缀（支持多种格式）
            prefixes = [
                'data:image/png;base64,',
                'data:image/jpeg;base64,',
                'data:image/jpg;base64,',
                'data:image/webp;base64,',
                'data:image/gif;base64,',
                'data:image/bmp;base64,',
                'data:image/tiff;base64,',
                'data:image/svg+xml;base64,',
                'data:image/;base64,',
                'data:;base64,'
            ]
            
            base64_data = image_data
            detected_prefix = None
            for prefix in prefixes:
                if image_data.startswith(prefix):
                    base64_data = image_data[len(prefix):]
                    detected_prefix = prefix
                    break
            
            print(f"[LeaferReceiver] 检测到前缀: {detected_prefix}, Base64数据长度: {len(base64_data)}")
            
            # 验证和清理Base64数据
            base64_data = base64_data.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            if not base64_data:
                raise ValueError("Base64数据为空")
            
            print(f"[LeaferReceiver] 清理后Base64数据长度: {len(base64_data)}")
            print(f"[LeaferReceiver] Base64数据前50字符: {base64_data[:50]}")
            
            # Base64填充修正
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
                print(f"[LeaferReceiver] 添加了 {4 - missing_padding} 个填充字符")
            
            # 验证Base64字符
            import re
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', base64_data):
                # 尝试替换URL安全的Base64字符
                base64_data = base64_data.replace('-', '+').replace('_', '/')
                if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', base64_data):
                    raise ValueError("包含无效的Base64字符")
                print(f"[LeaferReceiver] 转换了URL安全Base64字符")
            
            # Base64解码
            try:
                image_bytes = base64.b64decode(base64_data, validate=True)
                print(f"[LeaferReceiver] Base64解码成功，字节长度: {len(image_bytes)}")
            except Exception as e:
                print(f"[LeaferReceiver] Base64解码失败: {str(e)}")
                # 尝试不验证的解码
                try:
                    image_bytes = base64.b64decode(base64_data, validate=False)
                    print(f"[LeaferReceiver] 非验证Base64解码成功，字节长度: {len(image_bytes)}")
                except Exception as e2:
                    raise ValueError(f"Base64解码完全失败: validate=True({str(e)}), validate=False({str(e2)})")
            
            if len(image_bytes) < 50:
                raise ValueError(f"解码后的图像数据过小: {len(image_bytes)} bytes")
            
            # 检查文件头
            header = image_bytes[:20]
            print(f"[LeaferReceiver] 文件头 (hex): {header.hex()}")
            print(f"[LeaferReceiver] 文件头 (前10字节): {header[:10]}")
            
            # 多种方法尝试加载图像
            image = None
            
            # 方法1: 直接使用PIL加载
            try:
                image = Image.open(io.BytesIO(image_bytes))
                print(f"[LeaferReceiver] PIL直接加载成功: {image.format}, {image.mode}, {image.size}")
            except Exception as e1:
                print(f"[LeaferReceiver] PIL直接加载失败: {e1}")
                
                # 方法2: 检查文件头并强制格式
                try:
                    image = self._load_image_with_header_check(image_bytes)
                    print(f"[LeaferReceiver] 文件头检查加载成功: {image.format}, {image.mode}, {image.size}")
                except Exception as e2:
                    print(f"[LeaferReceiver] 文件头检查加载失败: {e2}")
                    
                    # 方法3: 强制PNG格式加载
                    try:
                        image = self._load_image_force_format(image_bytes, 'PNG')
                        print(f"[LeaferReceiver] 强制PNG加载成功: {image.mode}, {image.size}")
                    except Exception as e3:
                        print(f"[LeaferReceiver] 强制PNG加载失败: {e3}")
                        
                        # 方法4: 强制JPEG格式加载
                        try:
                            image = self._load_image_force_format(image_bytes, 'JPEG')
                            print(f"[LeaferReceiver] 强制JPEG加载成功: {image.mode}, {image.size}")
                        except Exception as e4:
                            print(f"[LeaferReceiver] 强制JPEG加载失败: {e4}")
                            raise ValueError(f"所有图像加载方法都失败: PIL({e1}), Header({e2}), PNG({e3}), JPEG({e4})")
            
            if image is None:
                raise ValueError("图像加载返回None")
            
            # EXIF转换
            try:
                if hasattr(image, '_getexif') and image._getexif() is not None:
                    image = ImageOps.exif_transpose(image)
                    print(f"[LeaferReceiver] EXIF转换完成")
            except Exception as e:
                print(f"[LeaferReceiver] EXIF转换警告: {e}")
            
            # 处理不同的图像模式
            original_mode = image.mode
            print(f"[LeaferReceiver] 原始图像模式: {original_mode}")
            
            if image.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                image = background
                print(f"[LeaferReceiver] RGBA转RGB完成")
            elif image.mode == 'P':
                # 调色板模式转换
                if 'transparency' in image.info:
                    image = image.convert('RGBA')
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                    print(f"[LeaferReceiver] 透明调色板转RGB完成")
                else:
                    image = image.convert('RGB')
                    print(f"[LeaferReceiver] 调色板转RGB完成")
            elif image.mode == 'L':
                # 灰度转RGB
                image = image.convert('RGB')
                print(f"[LeaferReceiver] 灰度转RGB完成")
            elif image.mode == 'I':
                # 32位整数模式处理
                image_array = np.array(image, dtype=np.float32)
                # 归一化到0-255范围
                if image_array.max() > 255:
                    image_array = (image_array / image_array.max() * 255).astype(np.uint8)
                else:
                    image_array = image_array.astype(np.uint8)
                image = Image.fromarray(image_array, mode='L').convert('RGB')
                print(f"[LeaferReceiver] 32位整数模式转RGB完成")
            elif image.mode not in ['RGB']:
                # 其他模式统一转换为RGB
                image = image.convert('RGB')
                print(f"[LeaferReceiver] {original_mode}转RGB完成")
            
            # 验证图像尺寸
            if image.size[0] < 1 or image.size[1] < 1:
                raise ValueError(f"图像尺寸无效: {image.size}")
            
            print(f"[LeaferReceiver] 最终图像: {image.mode}, {image.size}")
            
            # 转换为numpy数组
            image_array = np.array(image, dtype=np.float32) / 255.0
            print(f"[LeaferReceiver] numpy数组形状: {image_array.shape}, 数据类型: {image_array.dtype}")
            
            # 转换为ComfyUI格式的tensor [B,H,W,C]
            if len(image_array.shape) == 2:
                # 灰度图像，添加通道维度
                image_array = np.expand_dims(image_array, axis=-1)
                image_array = np.repeat(image_array, 3, axis=-1)
                print(f"[LeaferReceiver] 灰度图像扩展为3通道")
            elif len(image_array.shape) == 3 and image_array.shape[2] == 1:
                # 单通道图像转为三通道
                image_array = np.repeat(image_array, 3, axis=-1)
                print(f"[LeaferReceiver] 单通道图像扩展为3通道")
            elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # RGBA转RGB（虽然前面已经处理过，但保险起见）
                image_array = image_array[:, :, :3]
                print(f"[LeaferReceiver] RGBA数组转RGB")
            
            # 添加batch维度 [1,H,W,C]
            image_tensor = torch.from_numpy(image_array).unsqueeze(0)
            
            print(f"[LeaferReceiver] 图像处理成功: {original_mode} -> RGB, 尺寸: {image.size}, tensor形状: {image_tensor.shape}")
            return image_tensor
            
        except Exception as e:
            print(f"[LeaferReceiver] 图像处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_image_with_header_check(self, image_bytes):
        """通过检查文件头来加载图像"""
        # 检查常见的图像文件头
        headers = {
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'\xff\xd8\xff': 'JPEG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'RIFF': 'WEBP',
            b'BM': 'BMP'
        }
        
        detected_format = None
        for header, format_name in headers.items():
            if image_bytes.startswith(header):
                detected_format = format_name
                break
        
        if detected_format:
            print(f"[LeaferReceiver] 检测到图像格式: {detected_format}")
        
        return Image.open(io.BytesIO(image_bytes))
    
    def _load_image_force_format(self, image_bytes, force_format=None):
        """强制指定格式加载图像"""
        formats = [force_format] if force_format else ['PNG', 'JPEG', 'WEBP', 'GIF', 'BMP']
        
        for fmt in formats:
            try:
                # 创建BytesIO对象
                img_io = io.BytesIO(image_bytes)
                
                # 尝试直接加载
                img = Image.open(img_io)
                
                # 如果指定了格式，尝试验证
                if force_format:
                    # 强制设置格式并尝试加载
                    img.format = fmt
                    img.load()  # 强制加载以验证格式
                    print(f"[LeaferReceiver] 强制格式 {fmt} 加载成功")
                    return img
                else:
                    # 尝试加载并验证
                    img.load()
                    print(f"[LeaferReceiver] 格式 {fmt} 加载成功")
                    return img
                    
            except Exception as e:
                print(f"[LeaferReceiver] 格式 {fmt} 加载失败: {e}")
                continue
        
        raise ValueError(f"无法以格式 {force_format or '任何已知格式'} 加载图像")
    
    def create_placeholder_image(self):
        """创建占位符图像"""
        # 创建一个灰色占位符图像，格式为 [B,H,W,C]
        placeholder = torch.zeros((1, 256, 256, 3), dtype=torch.float32)
        placeholder[..., :] = 0.5  # 灰色 (0.5在0-1范围内)
        print(f"[LeaferReceiver] 创建占位符图像，形状: {placeholder.shape}")
        return placeholder
    
    async def request_current_element(self):
        """请求当前选中的元素"""
        if self.websocket and self.websocket.open:
            try:
                await self.websocket.send(json.dumps({
                    "type": "request_current_element",
                    "timestamp": int(time.time() * 1000)
                }))
                self.add_log("已发送当前元素请求")
            except Exception as e:
                self.add_log(f"发送当前元素请求失败: {str(e)}")
        else:
            self.add_log("WebSocket未连接，无法发送请求")
    
    def receive_element(self, server_url, refresh, output_base64, force_update):
        """接收元素的主要函数"""
        # 如果服务器URL发生变化，更新并重新连接
        if server_url != self.server_url:
            self.server_url = server_url
            self.add_log(f"服务器URL已更新为: {server_url}")
            if self.websocket:
                asyncio.create_task(self.websocket.close())
        
        # 如果刷新被触发，请求当前元素
        if refresh:
            asyncio.create_task(self.request_current_element())
        
        # 使用缓存的数据而不是当前状态数据
        image_output = self.cached_image if self.cached_image is not None else self.create_placeholder_image()
        element_name = self.cached_element_name
        base64_output = self.cached_base64_data if output_base64 else ""
        
        # 生成日志文本
        log_text = "\n".join(self.message_log[-10:])  # 显示最近10条日志
        
        # 调试信息
        cache_status = "有缓存" if self.cache_updated else "无缓存"
        cache_time = f", 缓存时间: {time.strftime('%H:%M:%S', time.localtime(self.cache_timestamp))}" if self.cache_timestamp else ""
        
        # 添加Base64输出状态提示
        if len(self.cached_base64_data) > 0 and not output_base64:
            self.add_log(f"⚠️ 警告: 有Base64数据({len(self.cached_base64_data)}字符)但output_base64未启用，请在节点设置中启用output_base64以获取完整Base64数据")
        
        self.add_log(f"输出状态 - 元素名: {element_name}, Base64长度: {len(self.cached_base64_data)}, 输出Base64: {output_base64}, 缓存状态: {cache_status}{cache_time}, 强制更新: {force_update}")
        
        # 确保返回的图像是有效的tensor
        if not isinstance(image_output, torch.Tensor):
            self.add_log("警告: 缓存图像无效，使用占位符")
            image_output = self.create_placeholder_image()
        
        return (
            image_output,
            element_name,
            self.connection_status,
            log_text,
            base64_output
        )

# 注册节点
NODE_CLASS_MAPPINGS = {
    "LeaferElementReceiver": LeaferElementReceiver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LeaferElementReceiver": "Leafer Element Receiver",
}