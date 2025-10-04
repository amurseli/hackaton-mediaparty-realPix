from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    filename = file.filename
    content_type = file.content_type    
    with open(f"uploads/{filename}", "wb") as f:
        f.write(await file.read())

    return JSONResponse(content={
        "filename": filename,
        "content_type": content_type,
        "message": "éxito"
    })
