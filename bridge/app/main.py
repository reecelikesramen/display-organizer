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

from fastapi import FastAPI, HTTPException, Depends, Path
from google.cloud import storage, firestore
import uuid
from typing import Annotated

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
    doc_ref.update({"state": "calibrating"})

@app.get("/is_mobile_connected/{connection_id}")
async def is_mobile_connected(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    _, doc = connection_info
    return {"connected": doc.to_dict().get("state") == "calibrating"}

@app.post("/change_state/{connection_id}", status_code=204)
async def change_state(
    connection_id: Annotated[str, Path()],
    state: str,
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    doc_ref, doc = connection_info

    # successful state changes are from calibrating to organizing or organizing to done
    to_from = (doc.to_dict().get("state"), state)
    if to_from == ("calibrating", "organizing") or to_from == ("organizing", "done"):
        doc_ref.update({"state": state})
        return

    raise HTTPException(status_code=400, detail=f"Invalid state transition from {to_from[0]} to {to_from[1]}")

@app.post("/end_connection/{connection_id}", status_code=204)
async def end_connection(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)]
):
    doc_ref, doc = connection_info

    # if the connection is not in the done state, update the state to done
    # if the other edge has acknowledged the connection as done, delete it
    if doc.to_dict().get("state") != "done":
        doc_ref.update({"state": "done"})
    else:
        doc_ref.delete()
