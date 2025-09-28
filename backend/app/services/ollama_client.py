import requests
import os
from typing import Dict, Optional, Any
import asyncio
import aiohttp

class OllamaLLM:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = 30
        
    async def query(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Query Ollama API with local Llama model"""
        
        # Check if Ollama is running
        if not await self._check_ollama_status():
            return {
                "status": "error",
                "text": "Ollama service is not running. Please start Ollama first.",
                "meta": {"fallback": True, "ollama_offline": True}
            }
        
        # Prepare the system message for Azimuth Core
        system_prompt = """You are a helpful AI assistant for a personal finance app called Azimuth Core. 
This is a completely local, privacy-focused financial management tool. 
Be concise, helpful, and encouraging. Keep responses under 100 words. 
Focus on local financial management, CSV imports, and transaction categorization.
If a feature isn't implemented yet, guide users to what they can do now."""
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        try:
            print(f"🤖 Querying Ollama: {self.model}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    
                    print(f"Ollama API Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if "response" in result:
                            generated_text = result["response"].strip()
                            
                            print(f"✅ Ollama Response: {generated_text[:100]}...")
                            return {
                                "status": "success",
                                "text": generated_text,
                                "meta": {
                                    "model": self.model,
                                    "length": len(generated_text),
                                    "local": True,
                                    "eval_count": result.get("eval_count", 0),
                                    "eval_duration": result.get("eval_duration", 0)
                                }
                            }
                        else:
                            print(f"Unexpected Ollama response format: {result}")
                            return self._fallback_response("Unexpected response format from local AI")
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Ollama API Error {response.status}: {error_text}")
                        return self._fallback_response(f"Local AI service error ({response.status})")
            
        except asyncio.TimeoutError:
            print("⏰ Ollama request timeout")
            return self._fallback_response("Local AI response took too long")
        except aiohttp.ClientConnectorError:
            print("🔌 Cannot connect to Ollama")
            return self._fallback_response("Cannot connect to local AI service")
        except Exception as e:
            print(f"❌ Ollama Exception: {e}")
            return self._fallback_response("Local AI service temporarily unavailable")
    
    async def _check_ollama_status(self) -> bool:
        """Check if Ollama is running and responsive"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False
    
    def _fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Generate a fallback response when Ollama fails"""
        return {
            "status": "error",
            "text": f"{error_msg}. Using smart fallback response instead.",
            "meta": {"fallback": True, "local": True}
        }
    
    async def check_model_availability(self) -> Dict[str, Any]:
        """Check if the configured model is available"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        model_names = [model.get("name", "") for model in models]
                        
                        return {
                            "ollama_running": True,
                            "model_available": self.model in model_names,
                            "available_models": model_names,
                            "configured_model": self.model
                        }
                    else:
                        return {
                            "ollama_running": False,
                            "model_available": False,
                            "error": f"Ollama API returned {response.status}"
                        }
        except Exception as e:
            return {
                "ollama_running": False,
                "model_available": False,
                "error": str(e)
            }
    
    async def pull_model(self) -> Dict[str, Any]:
        """Pull/download the configured model"""
        payload = {
            "name": self.model
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": f"Model {self.model} pulled successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to pull model: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to pull model: {str(e)}"
            }

# Initialize singleton
llm_client = OllamaLLM()