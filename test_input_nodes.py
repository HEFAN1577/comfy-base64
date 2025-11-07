#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新增的输入节点功能
验证字符串输入节点和浮点数输入节点是否正常工作
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from input_nodes import StringInputNode, FloatInputNode, IntegerInputNode, BooleanInputNode

def test_string_input_node():
    """测试字符串输入节点"""
    print("\n=== 测试字符串输入节点 ===")
    
    node = StringInputNode()
    
    # 测试INPUT_TYPES
    input_types = node.INPUT_TYPES()
    print(f"INPUT_TYPES: {input_types}")
    assert "required" in input_types
    assert "text" in input_types["required"]
    assert input_types["required"]["text"][0] == "STRING"
    print("✓ INPUT_TYPES 验证通过")
    
    # 测试基本功能
    test_cases = [
        "Hello World",
        "这是中文测试",
        "",
        "多行\n文本\n测试",
        "特殊字符!@#$%^&*()",
        None,
        123,
        ["list", "test"]
    ]
    
    for i, test_input in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_input)}")
        result = node.process_text(test_input)
        print(f"结果: {repr(result[0])}")
        assert isinstance(result, tuple)
        assert len(result) == 1
        assert isinstance(result[0], str)
    
    print("✓ 字符串输入节点测试通过")

def test_float_input_node():
    """测试浮点数输入节点"""
    print("\n=== 测试浮点数输入节点 ===")
    
    node = FloatInputNode()
    
    # 测试INPUT_TYPES
    input_types = node.INPUT_TYPES()
    print(f"INPUT_TYPES: {input_types}")
    assert "required" in input_types
    assert "value" in input_types["required"]
    assert input_types["required"]["value"][0] == "FLOAT"
    assert "optional" in input_types
    assert "precision" in input_types["optional"]
    print("✓ INPUT_TYPES 验证通过")
    
    # 测试基本功能
    test_cases = [
        (3.14159, 2),
        (0.0, 0),
        (-123.456, 3),
        (42, 1),
        ("3.14", 2),
        (None, 2),
        ("invalid", 2)
    ]
    
    for i, (value, precision) in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: value={repr(value)}, precision={precision}")
        result = node.process_float(value, precision)
        print(f"结果: float={result[0]}, string='{result[1]}'")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], str)
    
    print("✓ 浮点数输入节点测试通过")

def test_integer_input_node():
    """测试整数输入节点"""
    print("\n=== 测试整数输入节点 ===")
    
    node = IntegerInputNode()
    
    # 测试INPUT_TYPES
    input_types = node.INPUT_TYPES()
    print(f"INPUT_TYPES: {input_types}")
    assert "required" in input_types
    assert "value" in input_types["required"]
    assert input_types["required"]["value"][0] == "INT"
    print("✓ INPUT_TYPES 验证通过")
    
    # 测试基本功能
    test_cases = [42, 0, -123, 3.14, "456", None, "invalid"]
    
    for i, test_input in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_input)}")
        result = node.process_int(test_input)
        print(f"结果: int={result[0]}, string='{result[1]}'")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], str)
    
    print("✓ 整数输入节点测试通过")

def test_boolean_input_node():
    """测试布尔值输入节点"""
    print("\n=== 测试布尔值输入节点 ===")
    
    node = BooleanInputNode()
    
    # 测试INPUT_TYPES
    input_types = node.INPUT_TYPES()
    print(f"INPUT_TYPES: {input_types}")
    assert "required" in input_types
    assert "value" in input_types["required"]
    assert input_types["required"]["value"][0] == "BOOLEAN"
    print("✓ INPUT_TYPES 验证通过")
    
    # 测试基本功能
    test_cases = [True, False, "true", "false", "1", "0", 1, 0, None, "yes", "no"]
    
    for i, test_input in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_input)}")
        result = node.process_bool(test_input)
        print(f"结果: bool={result[0]}, string='{result[1]}', int={result[2]}")
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], int)
    
    print("✓ 布尔值输入节点测试通过")

def test_node_mappings():
    """测试节点映射"""
    print("\n=== 测试节点映射 ===")
    
    from input_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    
    expected_nodes = [
        "StringInputNode",
        "FloatInputNode", 
        "IntegerInputNode",
        "BooleanInputNode"
    ]
    
    print(f"NODE_CLASS_MAPPINGS: {list(NODE_CLASS_MAPPINGS.keys())}")
    print(f"NODE_DISPLAY_NAME_MAPPINGS: {NODE_DISPLAY_NAME_MAPPINGS}")
    
    for node_name in expected_nodes:
        assert node_name in NODE_CLASS_MAPPINGS, f"缺少节点: {node_name}"
        assert node_name in NODE_DISPLAY_NAME_MAPPINGS, f"缺少显示名称: {node_name}"
        
        # 验证节点类可以实例化
        node_class = NODE_CLASS_MAPPINGS[node_name]
        node_instance = node_class()
        assert hasattr(node_instance, 'INPUT_TYPES')
        assert callable(getattr(node_instance, 'INPUT_TYPES'))
    
    print("✓ 节点映射验证通过")

def test_integration():
    """集成测试"""
    print("\n=== 集成测试 ===")
    
    # 测试字符串 -> 浮点数转换
    string_node = StringInputNode()
    float_node = FloatInputNode()
    
    # 字符串输入
    string_result = string_node.process_text("3.14159")
    print(f"字符串输出: {string_result[0]}")
    
    # 将字符串转换为浮点数
    float_result = float_node.process_float(string_result[0], 3)
    print(f"浮点数输出: {float_result[0]}, 格式化: {float_result[1]}")
    
    assert abs(float_result[0] - 3.14159) < 0.00001
    assert float_result[1] == "3.142"
    
    print("✓ 集成测试通过")

def main():
    """主测试函数"""
    print("开始测试新增的输入节点...")
    
    try:
        test_string_input_node()
        test_float_input_node()
        test_integer_input_node()
        test_boolean_input_node()
        test_node_mappings()
        test_integration()
        
        print("\n🎉 所有测试通过！")
        print("\n=== 测试总结 ===")
        print("✓ StringInputNode - 字符串文字输入节点正常工作")
        print("✓ FloatInputNode - 浮点数输入节点正常工作")
        print("✓ IntegerInputNode - 整数输入节点正常工作")
        print("✓ BooleanInputNode - 布尔值输入节点正常工作")
        print("✓ 节点映射配置正确")
        print("✓ 节点间集成测试通过")
        print("\n新增的输入节点已准备就绪，可以在ComfyUI中使用！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)