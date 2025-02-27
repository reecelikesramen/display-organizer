import sys
import uuid
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication
from PyQt6.QtCore import Qt, QSize, QRect, QPointF
import cv2
import qrcode
import numpy as np

def generate_aruco_marker(marker_id, marker_size=200):
    """Generates an ArUco marker image."""
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_image = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_size)
    # Convert grayscale image to RGB
    marker_image_rgb = cv2.cvtColor(marker_image, cv2.COLOR_GRAY2RGB)
    return marker_image_rgb

def generate_qr_code(data, qr_size=300):
    """Generates a QR code image."""
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version based on data size
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((qr_size, qr_size))
    return np.array(img.convert("RGB"))

def serialize_qt_objects(obj):
    """Convert Qt objects to serializable types."""
    if isinstance(obj, QSize):
        return {"width": obj.width(), "height": obj.height()}
    elif isinstance(obj, QRect):
        return {"x": obj.x(), "y": obj.y(), "width": obj.width(), "height": obj.height()}
    elif isinstance(obj, QPointF):
        return {"x": obj.x(), "y": obj.y()}
    return str(obj)

def display_on_all_screens():
    """Displays ArUco markers and QR codes on all screens."""
    app = QApplication(sys.argv)
    screens = QGuiApplication.screens()
    desktop_id = str(uuid.uuid4())

    print(f"Desktop ID: {desktop_id}")
    print(f"Found {len(screens)} screen(s)")

    # Generate QR code with desktop ID for pairing
    desktop_info = {
        "desktopID": desktop_id,
        "screenCount": len(screens)
    }

    # Create and show windows for each screen
    windows = []
    for i, screen in enumerate(screens):
        # Gather screen information
        physical_size = screen.physicalSize()
        physical_width_mm = physical_size.width()
        physical_height_mm = physical_size.height()

        # Create display information dictionary
        display_info = {
            "desktopID": desktop_id,
            "screenIndex": i,
            "screenName": screen.name(),
            "manufacturer": screen.manufacturer(),
            "model": screen.model(),
            "serialNumber": screen.serialNumber(),
            "geometry": {
                "x": screen.geometry().x(),
                "y": screen.geometry().y(),
                "width": screen.geometry().width(),
                "height": screen.geometry().height(),
            },
            "physicalSize": {
                "width": physical_width_mm,
                "height": physical_height_mm
            },
            "physicalDPI": screen.physicalDotsPerInch(),
            "logicalDPI": screen.logicalDotsPerInch(),
            "refreshRate": screen.refreshRate(),
            "depth": screen.depth(),
            "devicePixelRatio": screen.devicePixelRatio()
        }

        # Print display info for debugging
        print(f"\nScreen {i+1} Info:")
        print(json.dumps(display_info, indent=2, default=serialize_qt_objects))

        # Create window for this screen
        window = QWidget()
        window.setWindowTitle(f"Display {i + 1}")
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        window.setGeometry(screen.geometry())

        # Get screen dimensions
        screen_width = screen.geometry().width()
        screen_height = screen.geometry().height()

        # Create a layout
        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)

        # Generate ArUco Markers (ensure unique IDs across all screens)
        aruco_size = min(screen_width, screen_height) // 10  # Adjust size based on screen
        aruco_top_left = generate_aruco_marker(i * 4, aruco_size)
        aruco_top_right = generate_aruco_marker(i * 4 + 1, aruco_size)
        aruco_bottom_left = generate_aruco_marker(i * 4 + 2, aruco_size)
        aruco_bottom_right = generate_aruco_marker(i * 4 + 3, aruco_size)

        # Convert display info to JSON string
        json_data = json.dumps(display_info, default=serialize_qt_objects)

        # Generate QR Code
        qr_size = min(screen_width, screen_height) // 3  # Adjust size based on screen
        qr_code_image = generate_qr_code(json_data, qr_size)

        # Create background image
        combined_image = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255  # White background

        # Place ArUco Markers in corners with some padding
        padding = aruco_size // 10

        # Top left
        h, w = aruco_top_left.shape[:2]
        combined_image[padding:padding+h, padding:padding+w] = aruco_top_left

        # Top right
        h, w = aruco_top_right.shape[:2]
        combined_image[padding:padding+h, screen_width-padding-w:screen_width-padding] = aruco_top_right

        # Bottom left
        h, w = aruco_bottom_left.shape[:2]
        combined_image[screen_height-padding-h:screen_height-padding, padding:padding+w] = aruco_bottom_left

        # Bottom right
        h, w = aruco_bottom_right.shape[:2]
        combined_image[screen_height-padding-h:screen_height-padding, screen_width-padding-w:screen_width-padding] = aruco_bottom_right

        # Place QR Code in center
        h, w = qr_code_image.shape[:2]
        qr_x = (screen_width - w) // 2
        qr_y = (screen_height - h) // 2
        combined_image[qr_y:qr_y+h, qr_x:qr_x+w] = qr_code_image

        # Convert to QPixmap
        height, width, channel = combined_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(combined_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        # Display Image
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Store window for showing later
        windows.append(window)

    # Show all windows
    for window in windows:
        window.showFullScreen()

    # Add keyboard shortcut to quit (Escape key)
    for window in windows:
        window.keyPressEvent = lambda event: app.quit() if event.key() == Qt.Key.Key_Escape else None

    print("\nPress ESC to exit the application")
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        display_on_all_screens()
    except Exception as e:
        print(f"Error: {e}")
