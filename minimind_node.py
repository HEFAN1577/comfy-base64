import torch
import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc

class MiniMindTextGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_path = None
        # 强制使用GPU，如果可用的话
        if torch.cuda.is_available():
            self.device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"[MiniMind] 检测到CUDA可用，使用GPU: {gpu_name}")
            print(f"[MiniMind] GPU总内存: {gpu_memory:.1f}GB")
            print(f"[MiniMind] CUDA版本: {torch.version.cuda}")
        else:
            self.device = "cpu"
            print("[MiniMind] CUDA不可用，使用CPU")
        
        self.print_device_info()
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_length": ("INT", {"default": 100, "min": 1, "max": 2048, "step": 1, "display": "number", "forceInput": False}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.1, "max": 2.0, "step": 0.1, "display": "slider", "forceInput": False}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.1, "max": 1.0, "step": 0.1, "display": "slider", "forceInput": False}),
                "do_sample": ("BOOLEAN", {"default": True}),
                "repetition_penalty": ("FLOAT", {"default": 1.1, "min": 1.0, "max": 2.0, "step": 0.1, "display": "slider", "forceInput": False}),
            },
            "optional": {
                "reload_model": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("generated_text", "full_response")
    FUNCTION = "generate"
    

    CATEGORY = "ETN"
    DISPLAY_NAME = "MiniMind Text Generator"
    
    def print_device_info(self):
        """打印设备信息"""
        if self.device == "cuda":
            current_memory = torch.cuda.memory_allocated(0) / 1024**3
            cached_memory = torch.cuda.memory_reserved(0) / 1024**3
            print(f"[MiniMind] 当前GPU内存使用: {current_memory:.2f}GB")
            print(f"[MiniMind] GPU缓存内存: {cached_memory:.2f}GB")
        else:
            print(f"[MiniMind] 当前设备: {self.device}")
    
    def load_model(self, force_reload=False):
        """加载MiniMind模型"""
        model_path = r"c:\Users\Administrator\Documents\GitHub\comfyuiJJ\Base64Nodes\MiniMind2-Small"
        
        # 检查是否需要重新加载模型
        if self.model is not None and self.model_path == model_path and not force_reload:
            return True
            
        try:
            # 清理之前的模型
            if self.model is not None:
                del self.model
                del self.tokenizer
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            print(f"[MiniMind] 正在加载模型: {model_path}")
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型路径不存在: {model_path}")
                
            config_path = os.path.join(model_path, "config.json")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            # 加载tokenizer
            print("[MiniMind] 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 设置pad_token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            print(f"[MiniMind] 加载模型到设备: {self.device}")
            if self.device == "cuda":
                # GPU优化设置
                print(f"[MiniMind] GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.bfloat16,  # 使用bfloat16节省GPU内存
                    device_map="auto",  # 自动分配GPU
                    trust_remote_code=True,
                    local_files_only=True,
                    low_cpu_mem_usage=True,  # 减少CPU内存使用
                    use_cache=True  # 启用缓存加速推理
                )
            else:
                # CPU设置
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                    local_files_only=True
                )
                self.model = self.model.to(self.device)
            
            self.model.eval()
            self.model_path = model_path
            
            print(f"[MiniMind] 模型加载成功! 设备: {self.device}")
            
            # 显示加载后的内存使用情况
            if self.device == "cuda":
                current_memory = torch.cuda.memory_allocated(0) / 1024**3
                print(f"[MiniMind] 模型加载后GPU内存使用: {current_memory:.2f}GB")
            
            return True
            
        except Exception as e:
            print(f"[MiniMind] 模型加载失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def get_system_prompt(self, role):
        """根据角色获取系统提示词"""
        role_prompts = {
            "通用助手": "You are a helpful assistant. 你是一个有用的AI助手，能够回答各种问题并提供帮助。",
            "翻译专家": "You are a professional translator. 你是一个专业的翻译专家，能够准确地在中英文之间进行翻译，保持原文的意思和语调。请直接提供翻译结果，无需额外解释。",
            "提示词扩写师": "You are a prompt expansion specialist. 你是一个提示词扩写专家，能够将简短的提示词扩展成详细、具体、富有创意的完整提示词。请保持原意的基础上，添加更多细节、风格描述和技术要求。",
            "创意写作师": "You are a creative writer. 你是一个富有创意的写作师，擅长创作各种类型的文学作品，包括小说、诗歌、剧本等。你的写作风格生动有趣，富有想象力。",
            "技术专家": "You are a technical expert. 你是一个技术专家，精通编程、软件开发、系统架构等技术领域。你能够提供准确的技术建议和解决方案，并用清晰易懂的方式解释复杂的技术概念。",
            "教学助手": "You are a teaching assistant. 你是一个教学助手，擅长用简单易懂的方式解释复杂概念，能够根据学习者的水平调整教学内容，并提供有针对性的学习建议。"
        }
        return role_prompts.get(role, role_prompts["通用助手"])
    
    def format_prompt(self, prompt, role="通用助手"):
        """格式化输入提示词"""
        # 输入验证和转换
        if prompt is None:
            prompt = "你好，请介绍一下你自己。"  # 使用默认提示词
            print(f"[MiniMind] 提示词为None，使用默认提示词")
        elif not isinstance(prompt, str):
            # 将非字符串类型转换为字符串
            try:
                if isinstance(prompt, (list, dict)):
                    prompt = str(prompt)
                else:
                    prompt = str(prompt)
                print(f"[MiniMind] 提示词类型转换: {type(prompt)} -> str")
            except Exception as e:
                print(f"[MiniMind] 提示词类型转换失败: {str(e)}，使用默认提示词")
                prompt = "你好，请介绍一下你自己。"
        
        # 确保提示词不为空
        if not prompt.strip():
            prompt = "你好，请介绍一下你自己。"
            print(f"[MiniMind] 提示词为空，使用默认提示词")
        
        # 获取角色对应的系统提示词
        system_prompt = self.get_system_prompt(role)
        
        # 使用chat模板格式化提示词
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # 尝试使用tokenizer的chat_template
            if hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template:
                formatted_prompt = self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
            else:
                # 手动格式化
                formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        except Exception as e:
            print(f"[MiniMind] 格式化提示词失败，使用原始提示词: {str(e)}")
            formatted_prompt = prompt
            
        return formatted_prompt
    
    def generate_text(self, prompt, max_length=100, temperature=0.7, top_p=0.9, 
                     do_sample=True, repetition_penalty=1.1, reload_model=False):
        """生成文本"""
        try:
            # 加载模型
            if not self.load_model(force_reload=reload_model):
                return ("模型加载失败，请检查模型路径和文件", "Error: Model loading failed")
            
            # 格式化提示词 - 使用固定角色
            role = "通用助手"
            formatted_prompt = self.format_prompt(prompt, role)
            print(f"[MiniMind] 当前角色: {role}")
            
            # 安全地打印格式化后的提示词
            try:
                if isinstance(formatted_prompt, str):
                    print(f"[MiniMind] 格式化后的提示词: {formatted_prompt[:200]}...")
                else:
                    print(f"[MiniMind] 格式化后的提示词: {str(formatted_prompt)[:200]}...")
            except Exception as e:
                print(f"[MiniMind] 无法显示格式化提示词: {str(e)}")
            
            # 编码输入
            inputs = self.tokenizer(
                formatted_prompt, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=2048
            )
            
            # 移动到正确的设备，并过滤掉不需要的键
            filtered_inputs = {}
            for k, v in inputs.items():
                if k in ['input_ids', 'attention_mask']:  # 只保留模型需要的输入
                    filtered_inputs[k] = v.to(self.device)
            inputs = filtered_inputs
            
            print(f"[MiniMind] 开始生成文本，最大长度: {max_length}")
            
            # GPU优化的生成设置
            generation_kwargs = {
                "max_new_tokens": max_length,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
                "repetition_penalty": repetition_penalty,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "use_cache": True
            }
            
            # 如果使用GPU，添加额外的优化参数
            if self.device == "cuda":
                generation_kwargs.update({
                    "num_beams": 1,  # 使用贪婪搜索以节省GPU内存
                    "early_stopping": True,  # 提前停止以节省计算
                })
                print(f"[MiniMind] 使用GPU优化设置进行推理")
            
            # 生成文本
            with torch.no_grad():
                if self.device == "cuda":
                    # GPU推理时启用自动混合精度
                    with torch.cuda.amp.autocast():
                        outputs = self.model.generate(**inputs, **generation_kwargs)
                else:
                    outputs = self.model.generate(**inputs, **generation_kwargs)
            
            # 解码输出
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
            
            # 提取生成的部分（去除输入提示词）
            input_length = len(formatted_prompt)
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            # 清理生成的文本
            generated_text = generated_text.strip()
            
            # 如果生成的文本为空，返回完整响应的一部分
            if not generated_text:
                # 尝试从完整响应中提取
                if "<|im_start|>assistant" in full_response:
                    assistant_part = full_response.split("<|im_start|>assistant")[-1]
                    if "<|im_end|>" in assistant_part:
                        generated_text = assistant_part.split("<|im_end|>")[0].strip()
                    else:
                        generated_text = assistant_part.strip()
                
                if not generated_text:
                    generated_text = "生成的文本为空，请尝试调整参数或重新加载模型。"
            
            print(f"[MiniMind] 生成完成，输出长度: {len(generated_text)}")
            
            # 显示生成后的GPU内存使用情况
            if self.device == "cuda":
                current_memory = torch.cuda.memory_allocated(0) / 1024**3
                print(f"[MiniMind] 生成完成后GPU内存使用: {current_memory:.2f}GB")
            
            return (generated_text, full_response)
            
        except Exception as e:
            error_msg = f"生成文本时出错: {str(e)}"
            print(f"[MiniMind] {error_msg}")
            import traceback
            print(traceback.format_exc())
            return (error_msg, f"Error: {str(e)}")
    
    def generate(self, prompt, max_length, temperature, top_p, do_sample, repetition_penalty, reload_model=False):
        """主要的生成方法，供ComfyUI调用"""
        try:
            # 记录原始参数
            print(f"[MiniMind] 接收到的原始参数: max_length={max_length} (type: {type(max_length)}), temperature={temperature} (type: {type(temperature)}), top_p={top_p} (type: {type(top_p)}), repetition_penalty={repetition_penalty} (type: {type(repetition_penalty)})")
            
            # 强化参数验证和修正 - 处理ComfyUI可能传递的无效值
            # 修正 max_length
            original_max_length = max_length
            if max_length is None or not isinstance(max_length, (int, float)) or max_length <= 0:
                print(f"[MiniMind] max_length 无效 ({original_max_length})，已修正为: 100")
                max_length = 100
            else:
                max_length = max(1, min(2048, int(max_length)))
                
            # 修正 temperature
            original_temperature = temperature
            if temperature is None or not isinstance(temperature, (int, float)) or temperature <= 0:
                print(f"[MiniMind] temperature 无效 ({original_temperature})，已修正为: 0.7")
                temperature = 0.7
            else:
                temperature = max(0.1, min(2.0, float(temperature)))
                
            # 修正 top_p
            original_top_p = top_p
            if top_p is None or not isinstance(top_p, (int, float)) or top_p <= 0:
                print(f"[MiniMind] top_p 无效 ({original_top_p})，已修正为: 0.9")
                top_p = 0.9
            else:
                top_p = max(0.1, min(1.0, float(top_p)))
                
            # 修正 repetition_penalty
            original_repetition_penalty = repetition_penalty
            if repetition_penalty is None or not isinstance(repetition_penalty, (int, float)) or repetition_penalty < 1.0:
                print(f"[MiniMind] repetition_penalty 无效 ({original_repetition_penalty})，已修正为: 1.1")
                repetition_penalty = 1.1
            else:
                repetition_penalty = max(1.0, min(2.0, float(repetition_penalty)))
            
            print(f"[MiniMind] 参数验证后: max_length={max_length}, temperature={temperature}, top_p={top_p}, repetition_penalty={repetition_penalty}")
            
            result = self.generate_text(
                prompt=prompt,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                repetition_penalty=repetition_penalty,
                reload_model=reload_model
            )
            return result
        except Exception as e:
            error_msg = f"生成文本时发生错误: {str(e)}"
            print(f"[MiniMind] {error_msg}")
            return (error_msg, f"Error: {str(e)}")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MiniMindTextGenerator": MiniMindTextGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMindTextGenerator": "MiniMind Text Generator",
}