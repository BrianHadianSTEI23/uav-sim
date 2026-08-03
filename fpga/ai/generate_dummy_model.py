#!/usr/bin/env python3
"""
Generate a dummy FP32 ONNX model representing an edge perception network (CNN).
Input shape: [1, 3, 64, 64] -> Output shape: [1, 10] (Obstacle classification/bounding probabilities)
"""
import torch
import torch.nn as nn
import os

class SimplePerceptionNet(nn.Module):
    def __init__(self):
        super(SimplePerceptionNet, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 10)
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

def generate_model():
    os.makedirs("models", exist_ok=True)
    model_path = "models/obstacle_detector_fp32.onnx"
    
    model = SimplePerceptionNet().eval()
    dummy_input = torch.randn(1, 3, 64, 64)
    
    torch.onnx.export(
        model,
        dummy_input,
        model_path,
        export_params=True,
        opset_version=13,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"[INFO] Exported baseline FP32 model to: {model_path}")

if __name__ == "__main__":
    generate_model()