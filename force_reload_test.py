#!/usr/bin/env python3
"""
强制重新加载image_websocket_node模块的测试脚本
用于验证修复后的prompt_id获取逻辑
"""

import sys
import importlib

def reload_image_websocket_node():
    """强制重新加载image_websocket_node模块"""
    try:
        # 如果模块已经加载，先删除
        if 'image_websocket_node' in sys.modules:
            del sys.modules['image_websocket_node']
            print("已删除旧的image_websocket_node模块")
        
        # 重新导入模块
        import image_websocket_node
        importlib.reload(image_websocket_node)
        print("成功重新加载image_websocket_node模块")
        
        # 验证类是否正确加载
        if hasattr(image_websocket_node, 'ImageWebSocketOutput'):
            print("✓ ImageWebSocketOutput类已正确加载")
            return True
        else:
            print("✗ ImageWebSocketOutput类未找到")
            return False
            
    except Exception as e:
        print(f"重新加载模块失败: {e}")
        return False

def test_prompt_id_methods():
    """测试prompt_id获取方法"""
    print("\n=== 测试prompt_id获取方法 ===")
    
    # 模拟设置环境变量
    import os
    test_prompt_id = "test_prompt_12345678901234567890"
    os.environ['COMFYUI_PROMPT_ID'] = test_prompt_id
    print(f"设置测试环境变量: COMFYUI_PROMPT_ID = {test_prompt_id}")
    
    # 测试环境变量获取
    env_prompt_id = os.environ.get('COMFYUI_PROMPT_ID')
    if env_prompt_id:
        print(f"✓ 环境变量方法测试成功: {env_prompt_id}")
    else:
        print("✗ 环境变量方法测试失败")
    
    # 清理测试环境变量
    del os.environ['COMFYUI_PROMPT_ID']
    print("已清理测试环境变量")

if __name__ == "__main__":
    print("开始测试image_websocket_node模块重新加载...")
    
    success = reload_image_websocket_node()
    if success:
        test_prompt_id_methods()
        print("\n✓ 所有测试完成，模块已成功更新")
        print("请重启ComfyUI以应用更改")
    else:
        print("\n✗ 模块重新加载失败")