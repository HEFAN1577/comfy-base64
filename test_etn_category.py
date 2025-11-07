#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有节点是否都统一设置为ETN分类
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_node_categories():
    """测试所有节点的分类是否为ETN"""
    print("[测试] 开始检查所有节点的分类设置...")
    
    # 导入所有节点模块
    try:
        from input_nodes import StringInputNode, FloatInputNode, IntegerInputNode, BooleanInputNode
        from base64_nodes import Base64ImageLoader, Base64MaskLoader
        from workflow_saver_node import WorkflowSaverNode
        from leafer_receiver_node import LeaferElementReceiver
        from minimind_node import MiniMindTextGenerator
        from image_websocket_node import ImageWebSocketOutput
        
        print("[测试] 所有节点模块导入成功")
    except Exception as e:
        print(f"[错误] 导入节点模块失败: {str(e)}")
        return False
    
    # 定义所有需要检查的节点
    nodes_to_check = [
        ("StringInputNode", StringInputNode),
        ("FloatInputNode", FloatInputNode),
        ("IntegerInputNode", IntegerInputNode),
        ("BooleanInputNode", BooleanInputNode),
        ("Base64ImageLoader", Base64ImageLoader),
        ("Base64MaskLoader", Base64MaskLoader),
        ("WorkflowSaverNode", WorkflowSaverNode),
        ("LeaferElementReceiver", LeaferElementReceiver),
        ("MiniMindTextGenerator", MiniMindTextGenerator),
        ("ImageWebSocketOutput", ImageWebSocketOutput),
    ]
    
    all_passed = True
    
    # 检查每个节点的分类
    for node_name, node_class in nodes_to_check:
        try:
            category = getattr(node_class, 'CATEGORY', None)
            if category == "ETN":
                print(f"[✓] {node_name}: 分类正确 (ETN)")
            else:
                print(f"[✗] {node_name}: 分类错误 ({category})，应该是 ETN")
                all_passed = False
        except Exception as e:
            print(f"[✗] {node_name}: 检查分类时出错 - {str(e)}")
            all_passed = False
    
    return all_passed

def test_node_mappings():
    """测试节点映射是否正确"""
    print("\n[测试] 检查节点映射...")
    
    try:
        # 导入__init__.py中的映射
        from __init__ import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
        
        print(f"[测试] 节点类映射数量: {len(NODE_CLASS_MAPPINGS)}")
        print(f"[测试] 节点显示名映射数量: {len(NODE_DISPLAY_NAME_MAPPINGS)}")
        
        # 检查所有映射的节点是否都有ETN分类
        all_etn = True
        for node_key, node_class in NODE_CLASS_MAPPINGS.items():
            category = getattr(node_class, 'CATEGORY', None)
            if category != "ETN":
                print(f"[✗] 映射中的节点 {node_key} 分类不是ETN: {category}")
                all_etn = False
        
        if all_etn:
            print("[✓] 所有映射的节点都使用ETN分类")
        
        return all_etn
        
    except Exception as e:
        print(f"[错误] 检查节点映射失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("ETN分类统一测试")
    print("=" * 50)
    
    # 测试节点分类
    category_test_passed = test_node_categories()
    
    # 测试节点映射
    mapping_test_passed = test_node_mappings()
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"节点分类测试: {'通过' if category_test_passed else '失败'}")
    print(f"节点映射测试: {'通过' if mapping_test_passed else '失败'}")
    
    if category_test_passed and mapping_test_passed:
        print("\n[✓] 所有测试通过！所有节点已成功统一到ETN分类")
        return True
    else:
        print("\n[✗] 部分测试失败，请检查上述错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)