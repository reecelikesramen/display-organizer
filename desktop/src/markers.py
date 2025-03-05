from itertools import product
import cv2
import numpy as np
import qrcode
from constants import ARUCO_TAG_DICTIONARY, CHESSBOARD


def make_qr_code_img(connection_id: str, qr_size_px: int) -> np.ndarray:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4
    )

    qr.add_data(f"DISPLAY_ORGANIZER{connection_id}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((qr_size_px, qr_size_px))
    qr_img_rgb = np.array(qr_img.convert("RGB"))
    return qr_img_rgb


def make_chessboard_img(chessboard_width_px: int) -> np.ndarray:
    rows = CHESSBOARD[0] + 1
    cols = CHESSBOARD[1] + 1

    SQUARE_SIZE_PX = chessboard_width_px / cols

    chessboard_height_px = int(rows * SQUARE_SIZE_PX)
    board_img = np.zeros((chessboard_height_px, chessboard_width_px, 3), dtype=np.uint8)

    for i, j in product(range(rows), range(cols)):
        x = int(j * SQUARE_SIZE_PX)
        y = int(i * SQUARE_SIZE_PX)

        # black or white square
        color = (0, 0, 0) if (i + j) % 2 == 0 else (255, 255, 255)

        # draw square in image
        cv2.rectangle(
            board_img,
            (x, y),
            (x + int(SQUARE_SIZE_PX), y + int(SQUARE_SIZE_PX)),
            color,
            -1,
        )

    return board_img


def make_aruco_marker_img(marker_id: int, marker_size_px: int) -> np.ndarray:
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_TAG_DICTIONARY)
    marker_image = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_size_px)
    marker_image_rgb = cv2.cvtColor(marker_image, cv2.COLOR_GRAY2RGB)
    return marker_image_rgb
