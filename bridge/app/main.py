import zipfile
# ENDPOINTS:
    # POST /create_connection => connection UUID | failure
    # - creates a new connection and returns its UUID
    # POST /join_connection(UUID) => success | failure
    # - joins an existing connection with the given UUID, ran from the mobile app
    # GET /is_mobile_connected(UUID) => success | failure
    # POST /send_image(UUID, image) => success more | success done | failure
    # - sends an image to the given connection UUID, ran from the desktop app
    # POST /empty_image_queue(UUID) => [images] | failure
    # - empties the image queue for the given connection UUID, ran from the desktop app
    # POST /change_state(UUID, state) => success | failure
    # - changes the state of the given connection UUID, ran from the desktop app
    # - state: new | calibrating | organizing | done
    # POST /end_connection(UUID) => success | failure
    # - ends the connection with the given UUID, ran from the mobile app

from io import BytesIO
from fastapi import FastAPI, HTTPException, Depends, Path, File, UploadFile, status
from fastapi.responses import StreamingResponse
from google.cloud import storage, firestore
import uuid
from typing import Annotated, Iterator

storage_client = storage.Client()
db = firestore.Client(database="display-organizer")
bucket = storage_client.bucket("display-organizer")

app = FastAPI()

# Dependency to check if connection exists and return the document
async def get_connection(connection_id: str):
    doc_ref = db.collection("connections").document(connection_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Connection ID {connection_id} not found")
    return doc_ref, doc

@app.post("/create_connection")
async def create_connection():
    connection_id = str(uuid.uuid4())
    db.collection("connections").document(connection_id).set({
        "state": "new",
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return {"connection_id": connection_id}

@app.post("/join_connection/{connection_id}", status_code=204)
async def join_connection(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    doc_ref, _ = connection_info
    doc_ref.update({"state": "connected"})

@app.get("/is_mobile_connected/{connection_id}")
async def is_mobile_connected(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    _, doc = connection_info
    return {"connected": doc.to_dict().get("state") == "connected"}

@app.post("/end_connection/{connection_id}", status_code=204)
async def end_connection(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    doc_ref, doc = connection_info

    # if the connection is not in the done or new state, update the state to done
    # if the other edge has acknowledged the connection as done, delete it
    if doc.to_dict().get("state") == "connected":
        doc_ref.update({"state": "done"})
    else:
        doc_ref.delete()

@app.post("/send_image/{connection_id}", status_code=204)
async def send_image(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
    image: UploadFile = File(media_type="image/jpeg", description="The JPEG image to send from the mobile app.")
):
    _, doc = connection_info
    doc = doc.to_dict()

    if doc.get("state") == "new":
        raise HTTPException(status_code=400, detail="Connection not established")
    elif doc.get("state") == "done":
        raise HTTPException(status_code=400, detail="Connection already ended")

    if not image:
        raise HTTPException(status_code=400, detail="No image provided")

    image_bytes = await image.read()
    image_uuid = uuid.uuid4()

    blob = bucket.blob(f"{connection_id}/{image_uuid}")
    blob.upload_from_string(image_bytes, content_type="image/jpeg")

@app.post("/receive_images/{connection_id}")
async def receive_images(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
):
    _, doc = connection_info
    doc = doc.to_dict()

    if doc.get("state") == "new":
        raise HTTPException(status_code=400, detail="Connection not established")
    elif doc.get("state") == "done":
        raise HTTPException(status_code=400, detail="Connection already ended")

    images_exist = False
    for blob in bucket.list_blobs(prefix=connection_id):
        images_exist = True
        break

    if not images_exist:
        return status.HTTP_204_NO_CONTENT

    response_headers = {
        "Content-Disposition": f"attachment; filename=images_{connection_id}.zip",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return StreamingResponse(pack_images_zip(connection_id), media_type="application/zip", headers=response_headers)

def pack_images_zip(connection_id: str) -> Iterator[bytes]:
    with BytesIO() as zip_buffer:
        with zipfile.ZipFile(zip_buffer, mode="w") as zip_file:
            for blob in sorted(bucket.list_blobs(prefix=connection_id), key=lambda b: b.time_created):
                name = blob.name.split("/")[-1]
                data = blob.download_as_bytes()
                zip_file.writestr(name, data)
                blob.delete()

        zip_buffer.seek(0)
        yield from zip_buffer
