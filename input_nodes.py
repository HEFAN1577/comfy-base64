#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI 输入节点
包含字符串文字输入节点和浮点数输入节点
"""

class StringInputNode:
    """字符串文字输入节点"""
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "请输入文字内容..."
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "process_text"
    CATEGORY = "ETN"
    DISPLAY_NAME = "String Input"
    
    def process_text(self, text):
        """处理文字输入"""
        # 基本的文字处理
        if text is None:
            text = ""
        elif not isinstance(text, str):
            text = str(text)
        
        # 记录输入信息
        print(f"[StringInput] 接收到文字: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"[StringInput] 文字长度: {len(text)}")
        
        return (text,)


class FloatInputNode:
    """浮点数输入节点"""
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {
                    "default": 0.0,
                    "min": -999999.0,
                    "max": 999999.0,
                    "step": 0.01,
                    "display": "number"
                }),
            },
            "optional": {
                "precision": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "display": "number"
                }),
            }
        }
    
    RETURN_TYPES = ("FLOAT", "STRING")
    RETURN_NAMES = ("float_output", "formatted_string")
    FUNCTION = "process_float"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Float Input"
    
    def process_float(self, value, precision=2):
        """处理浮点数输入"""
        # 输入验证和转换
        if value is None:
            value = 0.0
        elif not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                print(f"[FloatInput] 无法转换为浮点数: {value}，使用默认值 0.0")
                value = 0.0
        
        # 精度验证
        if precision is None or not isinstance(precision, int) or precision < 0:
            precision = 2
        precision = max(0, min(10, precision))
        
        # 格式化字符串
        formatted_string = f"{value:.{precision}f}"
        
        # 记录输入信息
        print(f"[FloatInput] 接收到数值: {value}")
        print(f"[FloatInput] 精度设置: {precision}")
        print(f"[FloatInput] 格式化结果: {formatted_string}")
        
        return (float(value), formatted_string)


class IntegerInputNode:
    """整数输入节点（额外添加）"""
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {
                    "default": 0,
                    "min": -999999,
                    "max": 999999,
                    "step": 1,
                    "display": "number"
                }),
            }
        }
    
    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("int_output", "string_output")
    FUNCTION = "process_int"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Integer Input"
    
    def process_int(self, value):
        """处理整数输入"""
        # 输入验证和转换
        if value is None:
            value = 0
        elif not isinstance(value, int):
            try:
                if isinstance(value, float):
                    value = int(value)
                else:
                    value = int(float(value))
            except (ValueError, TypeError):
                print(f"[IntegerInput] 无法转换为整数: {value}，使用默认值 0")
                value = 0
        
        # 记录输入信息
        print(f"[IntegerInput] 接收到整数: {value}")
        
        return (int(value), str(value))


class BooleanInputNode:
    """布尔值输入节点（额外添加）"""
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("BOOLEAN", "STRING", "INT")
    RETURN_NAMES = ("bool_output", "string_output", "int_output")
    FUNCTION = "process_bool"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Boolean Input"
    
    def process_bool(self, value):
        """处理布尔值输入"""
        # 输入验证和转换
        if value is None:
            value = False
        elif not isinstance(value, bool):
            # 转换各种类型为布尔值
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on', 'enabled')
            elif isinstance(value, (int, float)):
                value = bool(value)
            else:
                value = bool(value)
        
        # 转换为不同格式
        string_output = "true" if value else "false"
        int_output = 1 if value else 0
        
        # 记录输入信息
        print(f"[BooleanInput] 接收到布尔值: {value}")
        print(f"[BooleanInput] 字符串输出: {string_output}")
        print(f"[BooleanInput] 整数输出: {int_output}")
        
        return (value, string_output, int_output)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "StringInputNode": StringInputNode,
    "FloatInputNode": FloatInputNode,
    "IntegerInputNode": IntegerInputNode,
    "BooleanInputNode": BooleanInputNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringInputNode": "String Input",
    "FloatInputNode": "Float Input", 
    "IntegerInputNode": "Integer Input",
    "BooleanInputNode": "Boolean Input",
}