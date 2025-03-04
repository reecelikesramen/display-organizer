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

# STATES: new | connected | calibrating | organizing | done

from io import BytesIO
import logging
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Path,
    File,
    Query,
    UploadFile,
    Response,
    status,
)
from fastapi.responses import StreamingResponse
from google.cloud import storage, firestore
import uuid
from typing import Annotated, Iterator
import zipfile

storage_client = storage.Client()
db = firestore.Client(database="display-organizer")
bucket = storage_client.bucket("display-organizer")

app = FastAPI()


# Dependency to check if connection exists and return the document
async def get_connection(connection_id: str):
    doc_ref = db.collection("connections").document(connection_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=404, detail=f"Connection ID {connection_id} not found"
        )
    return doc_ref, doc


@app.post("/create_connection")
async def create_connection():
    connection_id = str(uuid.uuid4())
    db.collection("connections").document(connection_id).set(
        {
            "state": "new",
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return {"connection_id": connection_id}


@app.post("/join_connection/{connection_id}", status_code=204)
async def join_connection(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
):
    doc_ref, doc = connection_info

    if doc.to_dict().get("state") != "new":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot join Connection ID {connection_id}, mobile device has already paired or connection has ended",
        )

    doc_ref.update({"state": "connected"})


@app.get("/connected_mobile_device_id/{connection_id}")
async def connected_mobile_device_id(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
):
    _, doc = connection_info
    return {
        "connected": doc.to_dict().get("state") not in ("new", "done"),
        "device_id": "placeholder",
    }


@app.get("/connection_state/{connection_id}")
async def get_connection_state(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
):
    _, doc = connection_info
    return {"state": doc.to_dict().get("state")}


@app.post("/connection_state/{connection_id}", status_code=204)
async def set_connection_state(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
    state: Annotated[
        str, Query(description="The state to associate this image upload with.")
    ],
):
    doc_ref, doc = connection_info

    state_from_to = (doc.to_dict().get("state"), state)
    if state_from_to not in [
        ("connected", "calibrating"),
        ("connected", "organizing"),
        ("calibrating", "organizing"),
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"Could not change connection state from {state_from_to[0]} to {state_from_to[1]} for Connection ID {connection_id}",
        )

    doc_ref.update({"state": state})


@app.post("/end_connection/{connection_id}", status_code=204)
async def end_connection(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
):
    doc_ref, doc = connection_info

    # if the connection is not in the done or new state, update the state to done
    # if the other edge has acknowledged the connection as done, delete it
    if doc.to_dict().get("state") not in ("new", "connected", "done"):
        doc_ref.update({"state": "done"})
    else:
        # XXX: Keep 100% of previous data for analysis and improvement right now
        dest = db.collection("data_collection").document(doc_ref.id)
        dest.set(doc.to_dict())
        for blob in bucket.list_blobs(prefix=connection_id):
            bucket.rename_blob(blob, "data_collection/" + blob.name)
        doc_ref.delete()

        # TODO: delete 80-90% of previous data after we go live, for now keep all records as extra data
        # delete the connection document and all associated blobs
        # doc_ref.delete()
        # for blob in bucket.list_blobs(prefix=connection_id):
        #     blob.delete()


@app.post("/image_queue/{connection_id}")
async def enqueue_image(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
    state: Annotated[
        str, Query(description="The state to associate this image upload with.")
    ],
    image: UploadFile = File(
        media_type="image/jpeg",
        description="The JPEG image to send from the mobile app.",
    ),
):
    _, doc = connection_info
    current_state = doc.to_dict().get("state")

    if current_state == "new":
        raise HTTPException(status_code=400, detail="Connection not established")
    elif current_state == "connected":
        raise HTTPException(
            status_code=400, detail="Connection not in state to receive images"
        )
    elif current_state == "done":
        raise HTTPException(status_code=400, detail="Connection already ended")

    if state not in ("calibrating", "organizing"):
        raise HTTPException(
            status_code=400,
            detail="Can only enqueue images in calibrating or organizing state",
        )

    # XXX: maybe make this a bit more selective
    if current_state != state:
        return {"directive": "next_state"}

    if not image or image.size == 0:
        raise HTTPException(status_code=400, detail="No image provided")

    image_bytes = await image.read()
    image_uuid = uuid.uuid4()

    blob = bucket.blob(f"{connection_id}/{state}/{image_uuid}.jpg")
    blob.upload_from_string(image_bytes, content_type="image/jpeg")

    return {"directive": "more_images"}


@app.get("/image_queue/{connection_id}")
async def dequeue_images(
    connection_id: Annotated[str, Path()],
    connection_info: Annotated[tuple, Depends(get_connection)],
    state: Annotated[
        str, Query(description="Only receive images associated with this state.")
    ],
):
    _, doc = connection_info
    doc = doc.to_dict()

    def pack_images_zip() -> Iterator[bytes]:
        logging.info(f"Starting pack_images_zip for {connection_id}/{state}")
        blob_count = 0
        with BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, mode="w") as zip_file:
                for blob in sorted(
                    bucket.list_blobs(prefix=f"{connection_id}/{state}"),
                    key=lambda b: b.time_created,
                ):
                    blob_count += 1
                    name = blob.name.split("/")[-1]
                    try:
                        data = blob.download_as_bytes()
                        logging.info(f"Downloaded blob: {name}, size: {len(data)}")
                        zip_file.writestr(name, data)
                        # XXX: Keeping 100% of previous data for analysis and improvement right now
                        bucket.rename_blob(blob, "data_collection/" + blob.name)
                        # TODO: delete 80-90% of previous data after we go live
                        # blob.delete()
                    except Exception as e:
                        logging.error(f"Error processing blob {name}: {e}")

                logging.info(f"Processed {blob_count} blobs.")

        zip_buffer.seek(0)

        logging.info(f"Finished pack_images_zip for {connection_id}/{state}")
        yield from zip_buffer

    if doc.get("state") == "new":
        raise HTTPException(status_code=400, detail="Connection not established")
    if doc.get("state") == "done":
        raise HTTPException(status_code=400, detail="Connection already ended")
    if state not in ("calibrating", "organizing"):
        raise HTTPException(
            status_code=400,
            detail="Image queue is only available for calibrating or organizing state",
        )

    images_exist = False
    if next(bucket.list_blobs(prefix=f"{connection_id}/{state}")):
        images_exist = True

    if not images_exist:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    response_headers = {
        "Content-Disposition": f"attachment; filename=images_{connection_id}.zip",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    return StreamingResponse(
        pack_images_zip(), media_type="application/zip", headers=response_headers
    )
