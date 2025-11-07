# PR 提交材料：收录 comfy-base64 到 ComfyUI-Manager

标题（建议）：Add comfy-base64 to custom-node-list.json

摘要：
- 将 `comfy-base64` 收录到 Manager 的自定义节点列表，支持 Base64 图像/蒙版加载、输入节点、WebSocket 输出、Leafer 交互与工作流保存。

仓库信息：
- repo: https://github.com/HEFAN1577/comfy-base64
- branch: main

条目（扩展格式）示例：
```json
{
  "author": "HEFAN1577",
  "title": "ComfyUI Base64 Nodes",
  "id": "comfy-base64",
  "reference": "https://github.com/HEFAN1577/comfy-base64",
  "files": [
    "https://github.com/HEFAN1577/comfy-base64"
  ],
  "install_type": "git-clone",
  "description": "Custom nodes for Base64 image/mask loading, input nodes, WebSocket output, Leafer integration, and workflow saver."
}
```

实现与注册：
- `__init__.py` 合并 `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS`，并设置 `WEB_DIRECTORY = "web"`，安装后可自动加载。
- 节点文件包含：`base64_nodes.py`、`input_nodes.py`、`image_websocket_node.py`、`leafer_receiver_node.py`、`workflow_saver_node.py` 等。
- 依赖：`requirements.txt` 已提供。

本地自测（可选）：
1. 在 Manager 中启用 "Use local DB"，将上述条目加入本地 `custom-node-list.json`。
2. 运行 `python cm-cli.py simple-show all --mode local`，确认能看到 `comfy-base64`。
3. 运行 `python cm-cli.py install comfy-base64 --mode local` 验证安装与节点加载。

English Summary:
- Adds `comfy-base64` to the Manager list. Provides Base64 loaders (image/mask), input nodes, WebSocket output to React Flow, Leafer integration, and workflow saver tools.
- Entry fields: `author`, `title`, `id`, `reference`, `files`, `install_type`, `description`.
- Node registration via `__init__.py` with `WEB_DIRECTORY`.