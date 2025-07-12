# models/llm_handler.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Optional


class LLMHandler:
    """Handle LLM interactions with memory optimization for T4 GPU"""

    def __init__(self, config: Dict):
        self.config = config
        self.model_name = config.get(
            "model_name", "deepseek-ai/DeepSeek-Coder-V2-Lite-Base"
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load model with memory optimization
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,  # Use half precision for memory efficiency
            device_map="auto",
            trust_remote_code=True,
        )

    def generate(self, prompt: str, params: Optional[Dict] = None) -> str:
        """Generate response from prompt"""
        if params is None:
            params = {}

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate with memory-efficient settings
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=params.get("max_tokens", 2048),
                temperature=params.get("temperature", 0.7),
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt) :].strip()
