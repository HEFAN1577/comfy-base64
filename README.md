# ComfyUI Base64 Nodes

This extension adds two nodes to ComfyUI for working with base64-encoded images:

1. **Base64 Image** - Loads a base64-encoded string and converts it to a standard image format
2. **Base64 Mask** - Loads a base64-encoded string and converts it to a mask format

## Installation

Place the `Base64Nodes` folder in your `ComfyUI/custom_nodes/` directory.

## Usage

### Base64 Image

The Base64 Image node accepts a base64 string and outputs a regular image that can be used with other ComfyUI nodes.

- Input: Base64-encoded image string (with or without the data URL prefix)
- Output: Standard IMAGE format

### Base64 Mask

The Base64 Mask node converts a base64 string to a mask that can be used with other ComfyUI mask inputs.

- Input: Base64-encoded image string (with or without the data URL prefix)
- Input: Invert option (boolean) - when enabled, inverts the mask values
- Output: Standard MASK format

## Examples

Both nodes handle the following base64 formats:
- Raw base64: `iVBORw0KGgoAAAANSUhEUgAA...`
- Data URL: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...`

## Error Handling

If the base64 string is invalid or cannot be decoded, a small placeholder image will be returned. 