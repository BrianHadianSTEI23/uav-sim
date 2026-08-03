#!/usr/bin/env python3
"""
Module 2.4 (Fallback): Standard ONNX Runtime Quantizer (INT8)
Does NOT require AMD Vitis AI or Docker. Runs on pure PyPI ONNXRuntime.
"""

import os
import numpy as np
import onnxruntime
from onnxruntime.quantization import (
    quantize_static,
    CalibrationDataReader,
    QuantType,
    QuantFormat
)

class PerceptionDataReader(CalibrationDataReader):
    def __init__(self, data_path: str, input_name: str, num_samples: int = 50):
        self.input_name = input_name
        self.num_samples = num_samples
        self.current_idx = 0
        
        if os.path.exists(data_path):
            self.data = np.load(data_path)
        else:
            self.data = np.random.uniform(low=-1.0, high=1.0, size=(num_samples, 3, 64, 64)).astype(np.float32)
            os.makedirs(os.path.dirname(data_path), exist_ok=True)
            np.save(data_path, self.data)

    def get_next(self):
        if self.current_idx >= self.num_samples:
            return None
        batch = self.data[self.current_idx : self.current_idx + 1]
        self.current_idx += 1
        return {self.input_name: batch}

def quantize_perception_model(fp32_path, int8_path, calib_data_path):
    print("=======================================================")
    print("   Standard ONNXRuntime Static INT8 Quantization       ")
    print("=======================================================")

    dr = PerceptionDataReader(data_path=calib_data_path, input_name="input")

    # Standard Static Quantization (Cross-platform replacement for vai_q_onnx)
    quantize_static(
        model_input=fp32_path,
        model_output=int8_path,
        calibration_data_reader=dr,
        quant_format=QuantFormat.QOperator,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8
    )

    print(f"[SUCCESS] Quantized INT8 model generated at: {int8_path}")

def verify_quantized_model(fp32_path, int8_path):
    dummy_input = np.random.uniform(low=-1.0, high=1.0, size=(1, 3, 64, 64)).astype(np.float32)

    s_fp32 = onnxruntime.InferenceSession(fp32_path)
    s_int8 = onnxruntime.InferenceSession(int8_path)

    out_fp32 = s_fp32.run(None, {"input": dummy_input})[0]
    out_int8 = s_int8.run(None, {"input": dummy_input})[0]

    mse = np.mean((out_fp32 - out_int8) ** 2)
    print(f"[VERIFICATION] Mean Squared Error (FP32 vs INT8): {mse:.6f}")

if __name__ == "__main__":
    fp32_model = "models/obstacle_detector_fp32.onnx"
    int8_model = "models/obstacle_detector_int8.onnx"
    calib_data = "data/calibration_data.npy"

    quantize_perception_model(fp32_model, int8_model, calib_data)
    verify_quantized_model(fp32_model, int8_model)