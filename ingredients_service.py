import httpx
import base64

C2PA_API_URL = "https://api.realpix.org/c2pa/upload"

async def fetch_manifest(image_bytes: bytes, filename: str, content_type: str):
    async with httpx.AsyncClient() as client:
        files = {'file': (filename, image_bytes, content_type)}
        response = await client.post(C2PA_API_URL, files=files)
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}, {response.text}")
        return response.json()


def parse_manifest_node(manifest_id: str, manifests: dict, visited=None, include_thumbnails=False):
    if visited is None:
        visited = set()
    if manifest_id in visited:
        return {"title": manifest_id, "ingredients": [], "actions": []}
    visited.add(manifest_id)

    manifest = manifests.get(manifest_id, {})
    signature = manifest.get("signature_info", {})

    node = {
        "title": manifest.get("title", manifest_id),
        "issuer": signature.get("issuer", "Unknown"),
        "date": signature.get("time"),
        "ingredients": [],
        "actions": []
    }

    if include_thumbnails and "thumbnail" in manifest:
        thumb = manifest.get("thumbnail", {})
        data = thumb.get("data", {}).get("data", [])
        if data:
            b64 = base64.b64encode(bytearray(data)).decode("utf-8")
            node["thumbnail"] = f"data:image/{thumb.get('format', 'jpeg')};base64,{b64}"

    for assertion in manifest.get("assertions", []):
        if assertion.get("label") == "c2pa.actions":
            for action in assertion.get("data", {}).get("actions", []):
                node["actions"].append(action.get("action", "unknown").replace("c2pa.", ""))
                ingredient = action.get("parameters", {}).get("ingredient")
                if ingredient and "url" in ingredient:
                    ingredient_id = ingredient["url"].split("/")[-1]
                    if ingredient_id in manifests:
                        child_node = parse_manifest_node(ingredient_id, manifests, visited, include_thumbnails)
                        node["ingredients"].append(child_node)

    for ing in manifest.get("ingredients", []):
        ing_id = ing.get("document_id")
        if ing_id and ing_id in manifests:
            child_node = parse_manifest_node(ing_id, manifests, visited, include_thumbnails)
            node["ingredients"].append(child_node)
        else:
            child_node = {
                "title": ing.get("title", ing.get("document_id", "Unknown")),
                "issuer": ing.get("issuer", "Unknown"),
                "date": ing.get("date"),
                "ingredients": [],
                "actions": []
            }
            if include_thumbnails and "thumbnail" in ing:
                thumb = ing.get("thumbnail", {})
                data = thumb.get("data", {}).get("data", [])
                if data:
                    b64 = base64.b64encode(bytearray(data)).decode("utf-8")
                    child_node["thumbnail"] = f"data:image/{thumb.get('format', 'jpeg')};base64,{b64}"
            node["ingredients"].append(child_node)

    return node


def build_manifest_tree(manifest_data: dict, include_thumbnails=False):
    active_id = manifest_data.get("activeManifest")
    if not active_id:
        return {}
    manifests = manifest_data.get("manifests", {})
    return parse_manifest_node(active_id, manifests, include_thumbnails=include_thumbnails)


def build_thumbnail_tree(manifest_data: dict):
    return build_manifest_tree(manifest_data, include_thumbnails=True)
