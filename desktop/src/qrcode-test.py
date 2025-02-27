import cv2
import re
import numpy as np

def detect_qr_codes_opencv(image_path):
    """
    Attempt to detect QR codes using OpenCV's QRCodeDetector
    with enhanced preprocessing and parameter tuning.
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return "Failed to load image"

    # Create a copy for visualization
    vis_img = img.copy()

    # img = cv2.GaussianBlur(img, (5, 5), 0)

    # Create QR code detector
    qr_detector = cv2.QRCodeDetector()

    # Preprocessing steps to improve detection
    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Apply adaptive thresholding to handle uneven lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 51, 9
    )

    # 3. Try with different preprocessing approaches
    results = []

    # Try native OpenCV detectAndDecodeMulti on original image
    retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(img)
    if retval:
        results.append({
            "source": "OpenCV (original)",
            "decoded": decoded_info,
            "points": points
        })

    # Try with gray image
    retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
    if retval:
        results.append({
            "source": "OpenCV (grayscale)",
            "decoded": decoded_info,
            "points": points
        })

    # Try with binary image
    retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(binary)
    if retval:
        results.append({
            "source": "OpenCV (binary)",
            "decoded": decoded_info,
            "points": points
        })

    # Visualize results
    for result in results:
        source = result["source"]
        decoded_info = result["decoded"]
        points = result["points"]

        # Draw polygons and decoded info
        if points is not None:
            for i, point_set in enumerate(points):
                if point_set is not None and len(point_set) > 0:
                    point_set = point_set.astype(np.int32)
                    cv2.polylines(vis_img, [point_set], True, (0, 255, 0), 3)

                    # Get text position (use the top-left point)
                    if isinstance(point_set, np.ndarray) and point_set.shape[0] >= 1:
                        text_x, text_y = point_set[0][0], point_set[0][1] - 10
                    else:
                        text_x, text_y = 10, 30 + (i * 30)

                    # Add decoded text
                    info_text = f"{source}: {decoded_info[i]}" if i < len(decoded_info) else "No info"
                    cv2.putText(vis_img, info_text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # Save visualization
    cv2.imwrite("qr_detection_results.jpg", vis_img)

    # Combine all unique decoded QR codes
    all_decoded = set()
    for result in results:
        all_decoded.update(result["decoded"])

    for data in all_decoded:
        if re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", data):
            return data

    return None

# Example usage
if __name__ == "__main__":
    image_path = "./test_image.jpg"
    results = detect_qr_codes_opencv(image_path)
    print(results)
