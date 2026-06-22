"""Optional example: PyTorch model -> ONNX export.

This file is for reading and exploration. It is not required for the main Lab 5
runtime because the main project keeps dependencies lightweight.

To run this optional example, install torch separately.
"""
from __future__ import annotations

# import torch
# import torch.nn as nn
#
# class TinyNet(nn.Module):
#     def __init__(self):
#         super().__init__()
#         self.net = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 3))
#
#     def forward(self, x):
#         return self.net(x)
#
# model = TinyNet()
# torch.save(model.state_dict(), "models/tinynet_state_dict.pth")
# dummy_input = torch.randn(1, 4)
# torch.onnx.export(
#     model,
#     dummy_input,
#     "models/tinynet.onnx",
#     input_names=["features"],
#     output_names=["logits"],
#     opset_version=12,
# )
# print("Exported models/tinynet.onnx")
