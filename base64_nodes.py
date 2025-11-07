import numpy as np
import torch
import base64
import re
from io import BytesIO
from PIL import Image

class Base64ImageLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_string": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_image"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Base64 Image"

    def load_image(self, base64_string):
        # Remove data URL prefix if present (e.g. "data:image/png;base64,")
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        # Remove any whitespace that may have been introduced in formatting
        base64_string = re.sub(r'\s+', '', base64_string)
        
        # Decode the base64 string
        try:
            image_data = base64.b64decode(base64_string)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            
            # Convert to tensor format expected by ComfyUI
            img_tensor = torch.from_numpy(np.array(image).astype(np.float32) / 255.0)
            img_tensor = img_tensor.unsqueeze(0) # Add batch dimension
            
            return (img_tensor,)
        except Exception as e:
            print(f"Error loading base64 image: {e}")
            # Return a small placeholder red image in case of error
            placeholder = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            placeholder[..., 0] = 1.0  # Red color for error
            return (placeholder,)

class Base64MaskLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_string": ("STRING", {"multiline": True, "default": ""}),
                "invert": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("MASK",)
    FUNCTION = "load_mask"
    CATEGORY = "ETN"
    DISPLAY_NAME = "Base64 Mask"

    def load_mask(self, base64_string, invert):
        # Remove data URL prefix if present
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        # Remove whitespace
        base64_string = re.sub(r'\s+', '', base64_string)
        
        try:
            image_data = base64.b64decode(base64_string)
            mask_image = Image.open(BytesIO(image_data)).convert("L")  # Convert to grayscale
            
            # Convert to tensor format expected for masks
            mask_np = np.array(mask_image).astype(np.float32) / 255.0
            
            if invert:
                mask_np = 1.0 - mask_np
                
            mask_tensor = torch.from_numpy(mask_np)
            
            return (mask_tensor,)
        except Exception as e:
            print(f"Error loading base64 mask: {e}")
            # Return a placeholder mask in case of error
            placeholder = torch.zeros((64, 64), dtype=torch.float32)
            return (placeholder,)

# Register the nodes
NODE_CLASS_MAPPINGS = {
    "Base64ImageLoader": Base64ImageLoader,
    "Base64MaskLoader": Base64MaskLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Base64ImageLoader": "Base64 Image",
    "Base64MaskLoader": "Base64 Mask",
}