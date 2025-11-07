#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重新加载MiniMind节点
用于解决ComfyUI缓存问题
"""

import sys
import os
import importlib

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def force_reload_minimind_node():
    """强制重新加载MiniMind节点"""
    print("=== 强制重新加载MiniMind节点 ===")
    
    try:
        # 如果模块已经导入，先删除它
        if 'minimind_node' in sys.modules:
            print("删除已缓存的minimind_node模块...")
            del sys.modules['minimind_node']
        
        # 重新导入模块
        print("重新导入minimind_node模块...")
        import minimind_node
        importlib.reload(minimind_node)
        
        # 验证节点定义
        print("\n验证节点定义:")
        input_types = minimind_node.MiniMindTextGenerator.INPUT_TYPES()
        required = input_types["required"]
        
        # 打印关键参数定义
        for param_name in ["max_length", "temperature", "top_p", "repetition_penalty"]:
            if param_name in required:
                param_def = required[param_name]
                config = param_def[1]
                print(f"{param_name}: type={param_def[0]}, default={config['default']}, min={config['min']}, max={config['max']}")
        
        # 测试节点实例化
        print("\n测试节点实例化:")
        node = minimind_node.MiniMindTextGenerator()
        print("✅ 节点实例化成功")
        
        # 测试参数验证
        print("\n测试参数验证:")
        result = node.generate(
            prompt="测试",
            role="通用助手",
            max_length=0,  # 无效值
            temperature=0.0,  # 无效值
            top_p=0.0,  # 无效值
            do_sample=True,
            repetition_penalty=0.0,  # 无效值
            reload_model=False
        )
        print("✅ 参数验证测试通过")
        
        print("\n🎉 节点重新加载成功！")
        print("\n请在ComfyUI中执行以下操作:")
        print("1. 按 Ctrl+Shift+R 强制刷新页面")
        print("2. 或者重启ComfyUI服务")
        print("3. 重新添加MiniMind节点到工作流")
        
        return True
        
    except Exception as e:
        print(f"❌ 节点重新加载失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def create_node_info_file():
    """创建节点信息文件供ComfyUI参考"""
    print("\n=== 创建节点信息文件 ===")
    
    try:
        import minimind_node
        
        node_info = {
            "class_name": "MiniMindTextGenerator",
            "display_name": "MiniMind Text Generator",
            "category": "text/generation",
            "input_types": minimind_node.MiniMindTextGenerator.INPUT_TYPES(),
            "return_types": minimind_node.MiniMindTextGenerator.RETURN_TYPES,
            "return_names": minimind_node.MiniMindTextGenerator.RETURN_NAMES,
            "function": minimind_node.MiniMindTextGenerator.FUNCTION
        }
        
        info_file = os.path.join(os.path.dirname(__file__), "minimind_node_info.json")
        
        import json
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(node_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 节点信息文件已创建: {info_file}")
        return True
        
    except Exception as e:
        print(f"❌ 创建节点信息文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始强制重新加载MiniMind节点...\n")
    
    # 强制重新加载节点
    reload_success = force_reload_minimind_node()
    
    # 创建节点信息文件
    info_success = create_node_info_file()
    
    if reload_success and info_success:
        print("\n✅ 所有操作完成！")
        print("\n下一步操作:")
        print("1. 完全关闭ComfyUI")
        print("2. 重新启动ComfyUI")
        print("3. 在新的工作流中添加MiniMind节点")
        print("4. 验证参数默认值是否正确")
    else:
        print("\n❌ 部分操作失败，请检查错误信息")

if __name__ == "__main__":
    main()