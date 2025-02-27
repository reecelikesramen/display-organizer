import cv2
import numpy as np

def rectify_and_scale_with_visuals(image, monitor1_ids, monitor2_ids):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aru_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aru_params)
    corners, ids, rejected = detector.detectMarkers(gray)

    monitor_corners = {}
    if ids is not None:
        for i, marker_id in enumerate(ids):
            monitor_corners[marker_id[0]] = corners[i][0]

        def get_monitor_corners(monitor_ids, monitor_corners):
            monitor_pts = []
            for id_val in monitor_ids:
                monitor_pts.append(monitor_corners[id_val])
            # return np.array(monitor_pts, dtype="float32")
            return np.array([point[idx] for idx, point in enumerate(monitor_pts)], dtype="float32") #Corrected return.

        # Draw detected markers on original image
        img_with_markers = image.copy()
        cv2.aruco.drawDetectedMarkers(img_with_markers, corners, ids)
        # cv2.imshow("1. Original Image with Markers", img_with_markers)
        # cv2.waitKey(0)

        def rectify_monitor(monitor_ids, monitor_corners, image):

            top_left_marker_id = monitor_ids[0]
            monitor_pts = get_monitor_corners(monitor_ids, monitor_corners)

            # Calculate bounding box of monitor points
            x_coords = monitor_pts[:, 0]
            y_coords = monitor_pts[:, 1]
            min_x, max_x = int(min(x_coords)), int(max(x_coords))
            min_y, max_y = int(min(y_coords)), int(max(y_coords))
            width = max_x - min_x
            height = max_y - min_y

            # Calculate padding (1/10 of marker size)
            print(monitor_corners)
            marker_size = np.linalg.norm(monitor_corners[top_left_marker_id][0] - monitor_corners[top_left_marker_id][1])  # Approximate marker size
            print(f"Marker size: {marker_size}")
            padding = int(marker_size / 10)

           # Adjust monitor_pts for padding
            monitor_pts[0, 0] -= padding  # Top-left x
            monitor_pts[0, 1] -= padding  # Top-left y
            monitor_pts[1, 0] += padding  # Top-right x
            monitor_pts[1, 1] -= padding  # Top-right y
            monitor_pts[2, 0] += padding  # Bottom-right x
            monitor_pts[2, 1] += padding  # Bottom-right y
            monitor_pts[3, 0] -= padding  # Bottom-left x
            monitor_pts[3, 1] += padding  # Bottom-left y

            rect_pts = np.array([[0, 0], [width + 2*padding, 0], [width + 2*padding, height + 2*padding], [0, height + 2*padding]], dtype="float32")
            M = cv2.getPerspectiveTransform(monitor_pts, rect_pts)
            rectified_monitor = cv2.warpPerspective(image, M, (width + 2*padding, height + 2*padding))
            return rectified_monitor

        rectified_monitor1 = rectify_monitor(monitor1_ids, monitor_corners, image.copy())
        rectified_monitor2 = rectify_monitor(monitor2_ids, monitor_corners, image.copy())

        # Show rectified monitors
        # cv2.imshow("2. Rectified Monitor 1", rectified_monitor1)
        # cv2.waitKey(0)
        # cv2.imshow("3. Rectified Monitor 2", rectified_monitor2)
        # cv2.waitKey(0)

        def calculate_diagonal_distance(corners):
            dist1 = np.linalg.norm(corners[0] - corners[2])
            dist2 = np.linalg.norm(corners[1] - corners[3])
            return (dist1 + dist2) / 2.0

        gray1 = cv2.cvtColor(rectified_monitor1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(rectified_monitor2, cv2.COLOR_BGR2GRAY)
        corners1, ids1, rejected1 = detector.detectMarkers(gray1)
        corners2, ids2, rejected2 = detector.detectMarkers(gray2)

        monitor1_with_markers = rectified_monitor1.copy()
        cv2.aruco.drawDetectedMarkers(monitor1_with_markers, corners1, ids1)
        cv2.imshow("4. Rectified Monitor 1 with Markers", monitor1_with_markers)
        cv2.waitKey(0)

        monitor2_with_markers = rectified_monitor2.copy()
        cv2.aruco.drawDetectedMarkers(monitor2_with_markers, corners2, ids2)
        cv2.imshow("5. Rectified Monitor 2 with Markers", monitor2_with_markers)
        cv2.waitKey(0)

        if ids1 is not None and ids2 is not None:
            monitor1_corners_rect = corners1[0][0]
            monitor2_corners_rect = corners2[0][0]

            monitor1_diagonal = calculate_diagonal_distance(monitor1_corners_rect)
            monitor2_diagonal = calculate_diagonal_distance(monitor2_corners_rect)

            scaling_factor = monitor2_diagonal / monitor1_diagonal
            return scaling_factor
        else:
          return None
    else:
        return None
    cv2.destroyAllWindows()

# Example usage:
image = cv2.imread("test_correct_scale.jpg")
monitor1_ids = [0, 1, 2, 3]
monitor2_ids = [4, 5, 6, 7]

scaling_factor = rectify_and_scale_with_visuals(image, monitor1_ids, monitor2_ids)

if scaling_factor:
    print(f"Scaling factor: {scaling_factor}")
else:
    print("Markers not detected")
