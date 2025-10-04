from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from ingredients_service import fetch_manifest, build_manifest_tree, build_thumbnail_tree

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/verify/tree")
async def verify_tree(image: UploadFile = File(...), thumbnails: bool = Query(False)):
    contents = await image.read()
    try:
        manifest_data = await fetch_manifest(contents, image.filename, image.content_type)
        tree = build_manifest_tree(manifest_data, include_thumbnails=thumbnails)
        return tree
    except Exception as e:
        return {"error": str(e)}

@app.post("/verify/raw")
async def verify_raw(image: UploadFile = File(...)):
    contents = await image.read()
    try:
        manifest_data = await fetch_manifest(contents, image.filename, image.content_type)
        return manifest_data
    except Exception as e:
        return {"error": str(e)}

@app.post("/verify/thumbnails")
async def verify_thumbnails(image: UploadFile = File(...)):
    contents = await image.read()
    try:
        manifest_data = await fetch_manifest(contents, image.filename, image.content_type)
        tree = build_thumbnail_tree(manifest_data)
        return tree
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
