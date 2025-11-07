#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from websocket_image_sender import WebSocketImageSender
import torch

def test_image_send():
    print("开始测试图像发送...")
    
    # 创建节点实例
    node = WebSocketImageSender()
    
    # 创建测试图像
    test_image = torch.rand(1, 512, 512, 3)
    
    # 发送图像
    result = node.send_images_websocket(
        images=test_image,
        source_name="test_source",
        metadata='{"test": "data"}',
        websocket_url="ws://localhost:3078/image-ws"
    )
    
    print("测试完成，图像已发送")
    return result

if __name__ == "__main__":
    test_image_send()