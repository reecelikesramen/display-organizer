import cv2
import numpy as np

def aabb_collision(min_a, max_a, min_b, max_b):
    return (min_a[0] <= max_b[0] and max_a[0] >= min_b[0] and
            min_a[1] <= max_b[1] and max_a[1] >= min_b[1])

def aabb_mvt(min_a, max_a, min_b, max_b):
    if aabb_collision(min_a, max_a, min_b, max_b):
        return (0, 0)  # Already colliding

    overlap_x = min(max_a[0], max_b[0]) - max(min_a[0], min_b[0])
    overlap_y = min(max_a[1], max_b[1]) - max(min_a[1], min_b[1])

    if overlap_x < 0:
        overlap_x = 0;
    if overlap_y < 0:
        overlap_y = 0;

    if abs(max_a[0] - min_b[0]) <  abs(max_b[0] - min_a[0]) :
        x_movement = max(0, min_b[0] - max_a[0])
    else:
        x_movement = max(0, min_a[0] - max_b[0])

    if abs(max_a[1] - min_b[1]) < abs(max_b[1] - min_a[1]):
        y_movement = max(0, min_b[1] - max_a[1])
    else:
        y_movement = max(0, min_a[1] - max_b[1])

    if (x_movement == 0 and y_movement == 0):
        if abs(overlap_x) < abs(overlap_y):
            if min_a[0] < min_b[0]:
                x_movement = min_b[0] - max_a[0]
            else:
                x_movement = max_b[0] - min_a[0]
        else:
            if min_a[1] < min_b[1]:
                y_movement = min_b[1] - max_a[1]
            else:
                y_movement = max_b[1] - min_a[1]

    return (x_movement, y_movement)

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

            x_coords = monitor_pts[:, 0]
            y_coords = monitor_pts[:, 1]
            min_x, max_x = int(min(x_coords)), int(max(x_coords))
            min_y, max_y = int(min(y_coords)), int(max(y_coords))
            width = max_x - min_x
            height = max_y - min_y

            # print(monitor_pts)

            marker_size = np.linalg.norm(monitor_corners[top_left_marker_id][0] - monitor_corners[top_left_marker_id][1])
            padding = int(marker_size / 10)

            monitor_pts[0, 0] -= padding
            monitor_pts[0, 1] -= padding
            monitor_pts[1, 0] += padding
            monitor_pts[1, 1] -= padding
            monitor_pts[2, 0] += padding
            monitor_pts[2, 1] += padding
            monitor_pts[3, 0] -= padding
            monitor_pts[3, 1] += padding

            rect_pts = np.array([[0, 0], [width + 2*padding, 0], [width + 2*padding, height + 2*padding], [0, height + 2*padding]], dtype="float32")
            M = cv2.getPerspectiveTransform(monitor_pts, rect_pts)
            rectified_monitor = cv2.warpPerspective(image, M, (width + 2*padding, height + 2*padding))
            return rectified_monitor, min_x - padding, min_y - padding # Return rectified image and offset

        rectified_monitor1, offset1_x, offset1_y = rectify_monitor(monitor1_ids, monitor_corners, image.copy())
        rectified_monitor2, offset2_x, offset2_y = rectify_monitor(monitor2_ids, monitor_corners, image.copy())

        # TODO: use offsets to test AABB minimum translation vector to align monitors since they must touch
        print(rectified_monitor1.shape)
        print(rectified_monitor2.shape)

        # Get rid of space between monitors
        monitor1_min = np.array([offset1_x, offset1_y])
        monitor1_max = np.array([offset1_x + rectified_monitor1.shape[1], offset1_y + rectified_monitor1.shape[0]])
        monitor2_min = np.array([offset2_x, offset2_y])
        monitor2_max = np.array([offset2_x + rectified_monitor2.shape[1], offset2_y + rectified_monitor2.shape[0]])

        # Minimum translation vector: monitors must be touching along an axis
        # Must do this to get the correct offset in monitor pixels later
        mvt = aabb_mvt(monitor1_min, monitor1_max, monitor2_min, monitor2_max)
        offset2_x += mvt[0]
        offset2_y += mvt[1]

        # Create a large canvas (original image size)
        canvas = image.copy()

        # Place the rectified monitors on the canvas with offsets
        canvas[offset1_y:offset1_y+rectified_monitor1.shape[0], offset1_x:offset1_x+rectified_monitor1.shape[1]] = rectified_monitor1
        canvas[offset2_y:offset2_y+rectified_monitor2.shape[0], offset2_x:offset2_x+rectified_monitor2.shape[1]] = rectified_monitor2

        # Detect markers on the canvas
        gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        canvas_corners, canvas_ids, _ = detector.detectMarkers(gray_canvas)

        # Draw detected markers on the canvas
        cv2.aruco.drawDetectedMarkers(canvas, canvas_corners, canvas_ids)
        cv2.imshow("6. Combined Rectified Monitors (Original Positions)", canvas)
        cv2.waitKey(0)

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
        # cv2.imshow("4. Rectified Monitor 1 with Markers", monitor1_with_markers)
        # cv2.waitKey(0)

        monitor2_with_markers = rectified_monitor2.copy()
        cv2.aruco.drawDetectedMarkers(monitor2_with_markers, corners2, ids2)
        # cv2.imshow("5. Rectified Monitor 2 with Markers", monitor2_with_markers)
        # cv2.waitKey(0)

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
