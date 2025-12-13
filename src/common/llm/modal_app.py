# src/common/llm/modal_app.py
"""
Modal deployment for N-ATLaS LLM with vLLM inference.

Deploy with:
    modal deploy src/common/llm/modal_app.py

The model will be downloaded during container build (not on your PC).
"""

import modal

# Modal app configuration
app = modal.App("natlas-inference")

# Model configuration
MODEL_ID = "NCAIR1/N-ATLaS"
MODEL_REVISION = "main"

# Create a volume to cache the model weights
model_volume = modal.Volume.from_name("natlas-model-cache", create_if_missing=True)
MODEL_DIR = "/models"


def download_model():
    """Download model during image build."""
    import os
    from huggingface_hub import snapshot_download
    
    # Get HF token from environment (set via Modal secret)
    hf_token = os.environ.get("HF_TOKEN")
    
    snapshot_download(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=f"{MODEL_DIR}/{MODEL_ID}",
        ignore_patterns=["*.pt", "*.bin"],  # Prefer safetensors
        token=hf_token,
    )


# Build the container image with all dependencies
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.4.post1",
        "huggingface_hub",
        "hf_transfer",
        "fastapi",  # Required for web endpoints
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model, 
        volumes={MODEL_DIR: model_volume},
        secrets=[modal.Secret.from_name("huggingface")],
    )
)


@app.cls(
    gpu="A10G",  # A10G with 24GB - good balance of cost and performance
    image=vllm_image,
    volumes={MODEL_DIR: model_volume},
    scaledown_window=300,  # Keep warm for 5 minutes
    timeout=600,  # 10 minute max per request
)
@modal.concurrent(max_inputs=10)  # Handle multiple requests
class NATLaSModel:
    """N-ATLaS LLM inference class using vLLM."""
    
    @modal.enter()
    def load_model(self):
        """Load the model when container starts."""
        from vllm import LLM, SamplingParams
        
        self.llm = LLM(
            model=f"{MODEL_DIR}/{MODEL_ID}",
            tensor_parallel_size=1,
            dtype="half",  # FP16 for memory efficiency
            gpu_memory_utilization=0.90,
            max_model_len=8092,  # Model's context length
            trust_remote_code=True,
        )
        
        # Default sampling parameters
        self.default_params = SamplingParams(
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            repetition_penalty=1.12,
        )
    
    @modal.method()
    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.12,
    ) -> dict:
        """
        Generate a response from the model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            repetition_penalty: Penalty for repeated tokens
            
        Returns:
            Dict with 'response' text and 'usage' stats
        """
        from vllm import SamplingParams
        from datetime import datetime
        
        # Format messages using the chat template
        # N-ATLaS uses Llama-3 format
        formatted_prompt = self._format_chat(messages)
        
        # Create sampling parameters
        params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repetition_penalty=repetition_penalty,
            stop=["<|eot_id|>", "<|end_of_text|>"],
        )
        
        # Generate
        outputs = self.llm.generate([formatted_prompt], params)
        
        response_text = outputs[0].outputs[0].text.strip()
        
        return {
            "response": response_text,
            "usage": {
                "prompt_tokens": len(outputs[0].prompt_token_ids),
                "completion_tokens": len(outputs[0].outputs[0].token_ids),
                "total_tokens": len(outputs[0].prompt_token_ids) + len(outputs[0].outputs[0].token_ids),
            },
            "model": MODEL_ID,
        }
    
    def _format_chat(self, messages: list[dict]) -> str:
        """Format messages into Llama-3 chat template."""
        from datetime import datetime
        
        current_date = datetime.now().strftime('%d %b %Y')
        
        formatted = "<|begin_of_text|>"
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted += f"<|start_header_id|>system<|end_header_id|>\n\n"
                formatted += f"Cutting Knowledge Date: December 2023\n"
                formatted += f"Today Date: {current_date}\n\n"
                formatted += f"{content}<|eot_id|>"
            elif role == "user":
                formatted += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                formatted += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
        
        # Add generation prompt
        formatted += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        
        return formatted
    
    @modal.method()
    def health_check(self) -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "model": MODEL_ID,
            "gpu": "A10G-24GB",
        }


# Web endpoint for HTTP access
@app.function(
    image=modal.Image.debian_slim().pip_install("fastapi", "pydantic"),
    timeout=600,
)
@modal.fastapi_endpoint(method="POST", docs=True)
def generate_endpoint(request: dict) -> dict:
    """
    HTTP endpoint for text generation.
    
    Request body:
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    """
    model = NATLaSModel()
    
    messages = request.get("messages", [])
    max_tokens = request.get("max_tokens", 1024)
    temperature = request.get("temperature", 0.7)
    top_p = request.get("top_p", 0.9)
    repetition_penalty = request.get("repetition_penalty", 1.12)
    
    if not messages:
        return {"error": "No messages provided"}
    
    return model.generate.remote(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
    )


# Health check endpoint
@app.function(image=modal.Image.debian_slim().pip_install("fastapi"))
@modal.fastapi_endpoint(method="GET")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "model": MODEL_ID}


# Local entrypoint for testing
@app.local_entrypoint()
def main():
    """Test the model locally."""
    model = NATLaSModel()
    
    # Test with a simple prompt
    messages = [
        {
            "role": "system",
            "content": "You are Kliniq AI, a helpful multilingual healthcare assistant. You speak English, Hausa, Igbo, and Yoruba fluently. You help patients with health questions, appointment scheduling, and medical information. Always be empathetic and professional."
        },
        {
            "role": "user", 
            "content": "Hello! Can you explain what malaria is?"
        }
    ]
    
    print("Testing N-ATLaS model...")
    result = model.generate.remote(messages=messages)
    print(f"\nResponse:\n{result['response']}")
    print(f"\nUsage: {result['usage']}")
