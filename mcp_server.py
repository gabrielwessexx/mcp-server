from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
import os
from dotenv import load_dotenv
import openai
from product_scraper import ProductScraper

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(title="MCP Server - Model Control Protocol")

# Configuração do cliente OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class ModelRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7

class ModelResponse(BaseModel):
    response: str
    model: str
    tokens_used: int

class ProductInfo(BaseModel):
    nome: str
    preco: str
    estoque: str

# Armazenamento de conexões ativas
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Processa a requisição do modelo
            response = await process_model_request(request_data)
            
            # Envia a resposta de volta ao cliente
            await websocket.send_json(response.dict())
    except Exception as e:
        print(f"Erro na conexão WebSocket: {str(e)}")
    finally:
        if client_id in active_connections:
            del active_connections[client_id]

async def process_model_request(request_data: dict) -> ModelResponse:
    try:
        # Validação do modelo solicitado
        if request_data["model"] not in ["gpt-3.5-turbo", "gpt-4"]:
            raise HTTPException(status_code=400, detail="Modelo não suportado")

        # Chamada para a API do OpenAI
        response = await openai.ChatCompletion.acreate(
            model=request_data["model"],
            messages=[{"role": "user", "content": request_data["prompt"]}],
            max_tokens=request_data.get("max_tokens", 100),
            temperature=request_data.get("temperature", 0.7)
        )

        return ModelResponse(
            response=response.choices[0].message.content,
            model=request_data["model"],
            tokens_used=response.usage.total_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def get_products():
    """Endpoint para obter informações dos produtos"""
    try:
        scraper = ProductScraper()
        products = scraper.get_products()
        return {"status": "success", "products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/report")
async def get_products_report():
    """Endpoint para obter um relatório formatado dos produtos"""
    try:
        scraper = ProductScraper()
        products = scraper.get_products()
        report = scraper.format_report(products)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(active_connections)}

@app.get("/models")
async def list_models():
    return {
        "available_models": [
            "gpt-3.5-turbo",
            "gpt-4"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)