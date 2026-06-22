# Local LLM và quantization

Gợi ý model cho laptop:

- qwen3:0.6b: máy yếu, test pipeline.
- qwen3:1.7b: mặc định cho lớp.
- qwen3:4b: máy mạnh hơn.
- gemma3:1b: nhẹ.
- gemma3:4b: có text-image trên Ollama.
- gemma3:1b-it-qat hoặc 4b-it-qat: trải nghiệm quantization-aware trained model.

Tìm GGUF: dùng từ khóa `Qwen3 1.7B GGUF Q4_K_M`, `Gemma 3 1B GGUF Q5_K_M`.
