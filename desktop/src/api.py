from io import BytesIO
from typing import Optional
import zipfile
import cv2
import numpy as np
import requests
import os
from pydantic import BaseModel

BASE_URL = os.getenv("API_BASE_URL")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
HEADERS = {"Accept": "application/json", "Authorization": f"bearer {AUTH_TOKEN}"}


def create_connection() -> str:
    response = requests.request(
        "POST", f"{BASE_URL}/create_connection", headers=HEADERS
    )
    response.raise_for_status()
    print(response.text)
    return response.json().get("connection_id")


class ConnectedMobileDevice(BaseModel):
    connected: bool
    device_id: Optional[str]


def get_connected_mobile_device_id(connection_id: str) -> ConnectedMobileDevice:
    response = requests.request(
        "GET", f"{BASE_URL}/connected_mobile_device_id/{connection_id}", headers=HEADERS
    )
    response.raise_for_status()
    print(response.text)
    return ConnectedMobileDevice.model_validate_json(response.text)


def set_connection_state(connection_id: str, state: str):
    response = requests.request(
        "POST",
        f"{BASE_URL}/connection_state/{connection_id}?state={state}",
        headers=HEADERS,
    )
    response.raise_for_status()
    print(response.status_code)


def end_connection(connection_id: str):
    response = requests.request(
        "POST",
        f"{BASE_URL}/end_connection/{connection_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    print(response.status_code)


def get_images(connection_id: str, state: str) -> list[np.ndarray]:
    headers = HEADERS.copy()
    headers.update(
        {"Accept-Encoding": "gzip, deflate, br", "Accept": "application/zip"}
    )
    response = requests.request(
        "GET",
        f"{BASE_URL}/image_queue/{connection_id}?state={state}",
        headers=headers,
        stream=True,
    )
    response.raise_for_status()

    if response.status_code == 204:
        return []

    images = []
    with zipfile.ZipFile(BytesIO(response.content)) as zip:
        for fname in zip.namelist():
            with zip.open(fname) as img_file:
                img_bytes = img_file.read()
                img_np = np.frombuffer(img_bytes, dtype=np.uint8)
                img_cv2 = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                if img_cv2 is None:
                    raise Exception(f"Could not decode {fname} into a OpenCV image")

                images.append(img_cv2)

    return images
