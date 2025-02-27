import cv2
from cv2.typing import MatLike
import numpy as np
import json
import os

def process_image(image_path: str, screen_info: dict):
    img = cv2.imread(image_path)
    vis_img = img.copy()
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aru_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aru_params)
    corners, ids, rejected = detector.detectMarkers(img_gray)

    print(corners)

    vis_img = cv2.aruco.drawDetectedMarkers(vis_img, corners, ids)
    cv2.imwrite("detected_markers.jpg", vis_img)

    if ids is None or len(ids) == 0:
        print("No ArUco markers detected")
        return None

    screen_corners = [get_corners_for_screen(i, corners, ids) for i in range(len(screen_info))]

    return None

    # scaling_and_offsets = calculate_scaling_and_offsets(screen_corners, screen_info)



def get_corners_for_screen(screen_idx, corners, ids):
    corner_indices = [screen_idx + i for i in range(4)]
    screen_corners = []
    for idx in corner_indices:
        corner_idx = np.where(ids == idx)[0][0]
        if corner_idx is None:
            print(f"Warning: corner {idx} not found for screen {screen_idx}")
            return None

        screen_corners.append(corners[corner_idx])

    return screen_corners

def calculate_scaling_and_offsets(screen_corners, screen_info):
    """
    screen_corners: dict screen idx to corners array
    screen_info: dict screen idx to screen info dict
    returns: dict screen idx to scaling and offsets
    """

    # TODO: checks

    main_corners = screen_corners[0]
    main_info = screen_info[0]

    for screen_idx in range(len(screen_corners)):
        # skip main display
        if screen_idx == 0:
            continue




if __name__ == "__main__":
    process_image("./test_image.jpg", dict({0: {}, 1: {}}))
