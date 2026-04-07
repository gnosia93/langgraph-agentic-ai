# qwen_quantize.py
# Qwen3.5-27B 양자화 (Quantization) 예제
# BF16 (54GB) → INT4 (13.5GB) 로 모델 크기 축소

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from awq import AutoAWQForCausalLM

# ============================================================
# 방법 1: AWQ (Activation-aware Weight Quantization) - 추천
# pip install autoawq
# ============================================================
model_name = "Qwen/Qwen3.5-27B"

# AWQ 양자화
model = AutoAWQForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,              # INT4 양자화
}

# calibration 데이터로 양자화 (품질 유지를 위해 대표 데이터 사용)
model.quantize(
    tokenizer,
    quant_config=quant_config,
    calib_data="wikitext",    # calibration 데이터셋
    n_samples=128,
)

# 저장 (원본 54GB → 약 15GB)
model.save_quantized("./qwen-27b-awq-int4")
tokenizer.save_pretrained("./qwen-27b-awq-int4")
print("AWQ quantization done!")


# ============================================================
# 방법 2: GPTQ (더 느리지만 품질 약간 더 좋음)
# pip install auto-gptq
# ============================================================
# from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
#
# quantize_config = BaseQuantizeConfig(
#     bits=4,
#     group_size=128,
#     desc_act=True,
# )
#
# model = AutoGPTQForCausalLM.from_pretrained(
#     model_name, quantize_config=quantize_config
# )
# model.quantize(examples)  # calibration 데이터 필요
# model.save_quantized("./qwen-27b-gptq-int4")


# ============================================================
# 양자화된 모델 로드 및 추론 테스트
# ============================================================
from awq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_quantized("./qwen-27b-awq-int4")
tokenizer = AutoTokenizer.from_pretrained("./qwen-27b-awq-int4")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "GPU OOM이 발생했을 때 해결 방법을 알려줘"},
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to("cuda")

output = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
