import httpx
import base64
from ai_detector import is_ai_generated

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
        "claim_generator": manifest.get("claim_generator"),
        "format": manifest.get("format"),
        "instance_id": manifest.get("instance_id"),
        "actions": [],
        "ingredients": [],
        "ai_generated": False,
    }

    action_tools = [
        action.get("parameters", {}).get("com.adobe.tool", "")
        for assertion in manifest.get("assertions", [])
        if assertion.get("label") == "c2pa.actions"
        for action in assertion.get("data", {}).get("actions", [])
    ]

    node["ai_generated"] = is_ai_generated(
        manifest.get("claim_generator"),
        signature.get("issuer"),
        manifest.get("title"),
        action_tools=action_tools
    )


    if include_thumbnails and "thumbnail" in manifest:
        thumb_data = manifest["thumbnail"].get("data", {})
        if thumb_data.get("type") == "Buffer":
            import base64
            b64_thumb = base64.b64encode(bytes(thumb_data.get("data", []))).decode("utf-8")
            node["thumbnail"] = f"data:{manifest['thumbnail'].get('format')};base64,{b64_thumb}"

    for assertion in manifest.get("assertions", []):
        if assertion.get("label") == "c2pa.actions":
            actions_data = assertion.get("data", {})
            for action in actions_data.get("actions", []):
                node["actions"].append({
                    "name": action.get("action"),
                    "parameters": action.get("parameters", {}),
                })
            if "metadata" in actions_data:
                node["actions_metadata"] = actions_data["metadata"]

    for ing in manifest.get("ingredients", []):
        ing_id = ing.get("document_id")
        if ing_id and ing_id in manifests:
            child_node = parse_manifest_node(ing_id, manifests, visited, include_thumbnails)
            node["ingredients"].append(child_node)
        else:
            node["ingredients"].append({
                "title": ing.get("title", ing.get("document_id", "Unknown")),
                "issuer": ing.get("issuer", "Unknown"),
                "date": ing.get("metadata", {}).get("dateTime") or ing.get("date"),
                "format": ing.get("format"),
                "instance_id": ing.get("instance_id"),
                "actions": [],
                "ingredients": []
            })

    return node



def build_manifest_tree(manifest_data: dict, include_thumbnails=False):
    active_id = manifest_data.get("activeManifest")
    if not active_id:
        return {}
    manifests = manifest_data.get("manifests", {})
    return parse_manifest_node(active_id, manifests, include_thumbnails=include_thumbnails)


def build_thumbnail_tree(manifest_data: dict):
    return build_manifest_tree(manifest_data, include_thumbnails=True)
