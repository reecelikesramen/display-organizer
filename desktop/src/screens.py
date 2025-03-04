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
from PyQt6.QtWidgets import QApplication


# XXX: probably should provide this since i can't code sign apps right now for distribution
def qr_code_cli(connection_id: str):
    pass


def qr_code_screen(app: QApplication, connection_id: str):
    pass


def calibration_screen(app: QApplication):
    pass


def organization_screen(app: QApplication):
    pass


# XXX: probably should provide this since i can't code sign apps right now for distribution
def finish_screen_cli():
    pass


def finish_screen(app: QApplication):
    pass
