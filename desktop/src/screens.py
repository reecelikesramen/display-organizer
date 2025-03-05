# SCREENS:
# - QR code screen: main screen (window or fullscreen and CLI)
#   - 5 or 10cm QR code
# - Calibration screen: all screens
#   - large 6x9 fullscreen openCV chessboard with 1-2cm padding around the edges
# - Organization screen: all screens
#   - 5cm aruco tags, 9 total, 1cm edge padding
# - Success screen
#   - button to test out, apply, or cancel reorganization
#   - button to leave review with comment optional
#   - button to buy me a coffee
#   - show calculated display positions and resolutions
from itertools import product
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSizePolicy, QLabel
from PyQt6.QtGui import QPixmap, QImage, QScreen
from PyQt6.QtCore import Qt, pyqtSignal, QObject
import numpy as np
from constants import (
    ARUCO_MARKER_PADDING,
    QR_CODE_SIZE,
    CHESSBOARD,
    CHESSBOARD_SIZE,
    ARUCO_MARKER_SIZE,
)
from markers import make_qr_code_img, make_chessboard_img, make_aruco_marker_img


# XXX: probably should provide this since i can't code sign apps right now for distribution
def qr_code_cli(connection_id: str):
    pass


class QRCodeScreen(QWidget):
    screen_close_requested = pyqtSignal()

    def __init__(
        self, app: QApplication, connection_id: str, fullscreen=False
    ):
        super().__init__()
        screen = app.primaryScreen()

        if not screen:
            raise ValueError("No primary screen found")

        self.setWindowTitle("Display Organizer")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # pixels per inch => pixels per mm
        ppmm = screen.physicalDotsPerInch() / 25.4
        qr_code_size_px = int(QR_CODE_SIZE * ppmm)

        self.setFixedSize(qr_code_size_px, qr_code_size_px)

        # Get the geometry of the primary screen
        screen_geometry = screen.geometry()

        # Center the window on the primary screen
        self.move(screen_geometry.center() - self.rect().center())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # get image into Qt format
        qr_code_img = make_qr_code_img(connection_id, qr_code_size_px)
        bytes_per_line = 3 * qr_code_size_px
        pixmap = QPixmap.fromImage(
            QImage(
                qr_code_img.data,
                qr_code_size_px,
                qr_code_size_px,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )
        )

        # display image
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def keyPressEvent(self, a0):
        super().keyPressEvent(a0)
        if a0 and a0.key() == Qt.Key.Key_Escape:
            self.screen_close_requested.emit()


class CalibrationScreen(QWidget):
    screen_close_requested = pyqtSignal()

    def __init__(self, app: QApplication):
        super().__init__()
        screen = app.primaryScreen()

        if not screen:
            raise ValueError("No primary screen found")

        self.setWindowTitle("Display Organizer")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        top_inset = screen.availableGeometry().top() - screen.geometry().top()
        if top_inset < 30:
            top_inset = 0

        window_width = screen.geometry().width()
        window_height = screen.geometry().height() - top_inset
        window_geometry = screen.geometry()
        window_geometry.setTop(top_inset)
        self.setGeometry(window_geometry)

        # pixels per inch => pixels per mm
        ppmm = screen.physicalDotsPerInch() / 25.4
        chessboard_width_px = int(CHESSBOARD_SIZE * ppmm)
        chessboard_height_px = int(
            CHESSBOARD_SIZE * (CHESSBOARD[0] + 1) / (CHESSBOARD[1] + 1) * ppmm
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # background img
        img = np.ones((window_height, window_width, 3), dtype=np.uint8) * 128

        insert = (
            (window_height - chessboard_height_px) // 2,
            (window_height - chessboard_height_px) // 2 + chessboard_height_px - 1,
            (window_width - chessboard_width_px) // 2,
            (window_width - chessboard_width_px) // 2 + chessboard_width_px,
        )

        # get image into Qt format
        chessboard_img = make_chessboard_img(chessboard_width_px)
        img[insert[0] : insert[1], insert[2] : insert[3]] = chessboard_img
        bytes_per_line = 3 * window_width
        pixmap = QPixmap.fromImage(
            QImage(
                img.data,
                window_width,
                window_height,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )
        )

        # display image
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def keyPressEvent(self, a0):
        super().keyPressEvent(a0)
        if a0 and a0.key() == Qt.Key.Key_Escape:
            self.screen_close_requested.emit()


class OrganizationScreen(QObject):
    screen_close_requested = pyqtSignal()

    def __init__(
        self,
        app: QApplication,
    ):
        super().__init__()
        self._windows = [
            self._make_organization_window(i, screen)
            for i, screen in enumerate(app.screens())
        ]

    def _make_organization_window(self, screen_idx: int, screen: QScreen):
        window = QWidget()
        window.setWindowTitle("Display Organizer")
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        window.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # this checks if there is some sort of notch by measuring the height of the menu bar.
        # Qt has issues displaying in the menu bar, but screen geometry includes it so the window
        # clips beneath the bottom of the screen unless accounted for.
        top_inset = screen.availableGeometry().top() - screen.geometry().top()
        if top_inset < 30:
            top_inset = 0

        window_width = screen.geometry().width()
        window_height = screen.geometry().height() - top_inset
        window_geometry = screen.geometry()
        window_geometry.setTop(top_inset)
        window.setGeometry(window_geometry)

        # pixels per inch => pixels per mm
        ppmm = screen.physicalDotsPerInch() / 25.4
        marker_size_px = int(ARUCO_MARKER_SIZE * ppmm)
        marker_padding_px = int(ARUCO_MARKER_PADDING * ppmm)

        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)

        # background img
        img = np.ones((window_height, window_width, 3), dtype=np.uint8) * 128

        effective_width = window_width - 2 * marker_padding_px - marker_size_px
        effective_height = window_height - 2 * marker_padding_px - marker_size_px
        for i, j in product(range(3), range(3)):
            x = int(j * effective_width / 2) + marker_padding_px
            y = int(i * effective_height / 2) + marker_padding_px

            marker_id = screen_idx * 9 + i * 3 + j
            marker_img = make_aruco_marker_img(marker_id, marker_size_px)
            img[y : y + marker_size_px, x : x + marker_size_px] = marker_img

        # get image into Qt format
        bytes_per_line = 3 * window_width
        pixmap = QPixmap.fromImage(
            QImage(
                img.data,
                window_width,
                window_height,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )
        )

        # display image
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        window.keyPressEvent = lambda a0: (
            self.screen_close_requested.emit() if a0 and a0.key() == Qt.Key.Key_Escape else None
        )

        return window

    def show(self):
        for window in self._windows:
            window.showFullScreen()

    def close(self):
        for window in self._windows:
            window.close()


# XXX: probably should provide this since i can't code sign apps right now for distribution
def finish_screen_cli():
    pass


def finish_screen(app: QApplication):
    pass
