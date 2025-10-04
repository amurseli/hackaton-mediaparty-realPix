# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime

app = FastAPI()

# CORS para que el front pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL de la API real
C2PA_API_URL = "https://api.realpix.org/c2pa/upload"

@app.post("/verify/basic")
async def verify_basic(image: UploadFile = File(...)):
    """Devuelve issuer, fecha, autor, acciones y coordenadas"""
    
    # Leer imagen
    contents = await image.read()
    
    # Llamar a la API real
    async with httpx.AsyncClient() as client:
        # IMPORTANTE: el campo debe llamarse "file" no "image"
        files = {'file': (image.filename, contents, image.content_type)}
        response = await client.post(C2PA_API_URL, files=files)
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
            
        manifest_data = response.json()
    
    # Parsear lo que necesitas
    active_id = manifest_data.get("activeManifest")
    if not active_id:
        return {"error": "No active manifest found"}
        
    manifest = manifest_data.get("manifests", {}).get(active_id, {})
    signature = manifest.get("signature_info", {})
    
    # Buscar autor y acciones en assertions
    author_name = "Unknown"
    actions = []
    latitude = None
    longitude = None
    
    for assertion in manifest.get("assertions", []):
        if assertion.get("label") == "stds.schema-org.CreativeWork":
            authors = assertion.get("data", {}).get("author", [])
            if authors:
                author_name = authors[0].get("name", "Unknown")
        elif assertion.get("label") == "c2pa.actions":
            for action in assertion.get("data", {}).get("actions", []):
                action_name = action.get("action", "").replace("c2pa.", "")
                actions.append(action_name)
        # Buscar GPS (pueden estar en exif:GPSData o en otras assertions)
        elif "GPS" in assertion.get("label", ""):
            gps_data = assertion.get("data", {})
            if "latitude" in gps_data:
                latitude = gps_data.get("latitude")
            if "longitude" in gps_data:
                longitude = gps_data.get("longitude")
    
    return {
        "issuer": signature.get("issuer", "Unknown"),
        "date": signature.get("time"),
        "author": author_name,
        "actions": actions,
        "latitude": latitude,
        "longitude": longitude,
        "verified": bool(signature.get("issuer"))
    }

@app.post("/verify/location")
async def verify_location(image: UploadFile = File(...)):
    """Solo devuelve coordenadas si existen"""
    
    contents = await image.read()
    
    # Llamar a la API real
    async with httpx.AsyncClient() as client:
        files = {'file': (image.filename, contents, image.content_type)}
        response = await client.post(C2PA_API_URL, files=files)
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
            
        manifest_data = response.json()
    
    # TODO: Buscar coordenadas reales en el manifest
    # Por ahora devuelve mock, pero tienes el manifest_data real para parsear
    return {
        "latitude": -34.603722,
        "longitude": -58.381592
    }

@app.post("/verify/debug")
async def verify_debug(image: UploadFile = File(...)):
    """Devuelve el manifest completo para debug"""
    contents = await image.read()
    
    async with httpx.AsyncClient() as client:
        files = {'file': (image.filename, contents, image.content_type)}
        response = await client.post(C2PA_API_URL, files=files)
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}", "detail": response.text}
            
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)