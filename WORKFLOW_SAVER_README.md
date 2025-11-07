# ComfyUI 工作流保存器

这是一个为 ComfyUI 设计的工作流保存扩展，提供了全局悬浮按钮来快速保存当前工作流，并支持通过 WebSocket 发送到 Leafer 应用。

## 功能特性

- **一键保存**: 通过悬浮按钮快速保存当前工作流
- **手动命名**: 支持用户手动输入工作流文件名
- **文件替换**: 同名文件保存时自动替换之前的文件
- **标准HTTP API格式**: 保存标准ComfyUI HTTP API格式的工作流（直接的prompt对象）
- **动态路径获取**: 通过WebSocket动态获取Leafer应用的工作流保存路径
- **WebSocket集成**: 自动将工作流发送到Leafer应用 (ws://localhost:3078)
- **本地存储**: 工作流保存到动态获取的目录或默认目录
- **实时通知**: 保存状态的实时反馈
- **错误处理**: 完善的错误提示和日志记录
- **格式纯净**: 直接保存prompt对象，无额外包装数据

## 安装方法

1. 将整个 `Base64Nodes` 文件夹复制到 ComfyUI 的 `custom_nodes` 目录下
2. 安装依赖包:
   ```bash
   pip install -r requirements.txt
   ```
3. 重启 ComfyUI
4. 扩展会自动加载并显示悬浮按钮

## 依赖要求

- `websockets>=11.0.0` - WebSocket 客户端支持
- `aiohttp>=3.8.0` - 异步 HTTP 支持

## 使用方法

### 全局悬浮按钮

启动 ComfyUI 后，你会在界面左上角看到一个紫色的悬浮按钮 "💾 保存工作流"。

- **保存按钮**: 点击后在弹出的对话框中输入工作流文件名，保存到指定目录并发送到 Leafer 应用
- **文件替换**: 如果使用相同文件名保存，将自动替换之前的文件

### 保存位置

系统会通过 WebSocket 动态获取 Leafer 应用的工作流保存路径，如果获取失败则使用默认目录: `c:\Users\Administrator\Documents\GitHub\MMX\workflow\files`

### WebSocket 集成

工作流会自动通过 WebSocket 连接 `ws://localhost:3078` 发送到 Leafer 应用。系统首先会请求获取动态保存路径，然后发送标准的ComfyUI HTTP API格式（直接的prompt对象，节点ID到节点数据的映射），发送的数据格式为:

**路径查询请求:**
```json
{
  "type": "get_workflow_path"
}
```

**工作流保存数据:**
```json
{
  "type": "workflow_save",
  "filename": "workflow_20231201_143022.json",
  "workflow_data": {
    "1": {
      "inputs": {
        "text": "hello world",
        "clip": ["4", 1]
      },
      "class_type": "CLIPTextEncode"
    },
    "2": {
      "inputs": {
        "samples": ["3", 0],
        "vae": ["4", 2]
      },
      "class_type": "VAEDecode"
    }
  },
  "save_path": "动态获取的保存路径"
}
```

### 文件命名

保存的文件会自动添加时间戳，格式为: `workflow_YYYYMMDD_HHMMSS.json`

## API 配置

系统使用固定的 API 路径 `/Base64Nodes/save_workflow`，无需手动配置。

## 技术实现

- **前端**: JavaScript 扩展，集成到 ComfyUI 的扩展系统
- **后端**: Python API 端点，处理工作流保存请求
- **WebSocket**: 异步发送工作流数据到 Leafer 应用
- **存储**: JSON 格式保存工作流数据

## 文件结构

```
Base64Nodes/
├── __init__.py                 # 扩展初始化
├── workflow_saver_node.py      # 后端 API 处理和 WebSocket 发送
├── requirements.txt            # 依赖包列表
├── web/
│   └── workflow_saver.js       # 前端悬浮按钮实现
└── WORKFLOW_SAVER_README.md    # 说明文档
```

## 故障排除

### 按钮不显示

1. 确认扩展已正确安装到 `custom_nodes` 目录
2. 检查 ComfyUI 控制台是否有错误信息
3. 重启 ComfyUI

### 保存失败

1. 检查保存目录是否存在写入权限
2. 查看 ComfyUI 控制台的错误信息
3. 确认 API 路径配置正确

### WebSocket 连接失败

1. 确认 Leafer 应用的 WebSocket 服务器在端口 3078 上运行
2. 检查防火墙是否阻止了 WebSocket 连接
3. 查看 ComfyUI 控制台的 WebSocket 错误信息
4. 确认 `websockets` 包已正确安装

### 网络错误

1. 检查 ComfyUI 服务器是否正常运行
2. 确认防火墙没有阻止连接
3. 验证 API 端点是否可访问

## 版本历史

### v2.5.0 (当前版本)
- 完全修复工作流格式问题，现在保存的是标准ComfyUI HTTP API格式
- 后端直接保存prompt对象（节点ID到节点数据的映射），符合ComfyUI `/prompt` API要求
- 移除了额外的包装数据（timestamp、version等），确保格式纯净
- 前端和后端都使用标准的ComfyUI HTTP API格式

### v2.4.0
- **修复工作流格式**: 现在导出符合ComfyUI HTTP API标准的工作流格式
- 使用 `app.graphToPrompt().output` 获取正确的API格式数据
- 更新文档说明，明确HTTP API格式的使用

### v2.3.0
- 导出纯工作流JSON，移除额外元数据
- 实现动态路径获取功能
- 通过WebSocket动态获取Leafer应用的保存路径
- 优化WebSocket通信协议
- 改进数据传输格式

### v2.2.0
- 添加手动文件名输入功能
- 支持同名文件自动替换
- 更新保存路径为 workflow\files 目录
- 改进用户交互体验
- 优化文件命名逻辑

### v2.1.0
- 简化用户界面，移除设置按钮
- 使用固定 API 路径，提高稳定性
- 改进 CORS 支持和错误处理
- 优化连接测试机制

### v2.0.0
- 新增 WebSocket 集成功能
- 支持发送工作流到 Leafer 应用
- 更新保存目录到 MMX/workflow
- 添加 WebSocket 状态通知
- 新增依赖管理 (requirements.txt)

### v1.0.0
- 初始版本发布
- 支持全局悬浮按钮
- 支持自动文件命名
- 支持 API 路径配置
- 支持实时通知反馈