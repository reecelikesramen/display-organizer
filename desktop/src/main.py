import sys
import time
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from screens import CalibrationScreen, OrganizationScreen, QRCodeScreen
import cv2
import api
import uuid

def print_screen_info(app: QApplication) -> None:
    for screen in app.screens():
        # Create display information dictionary
        display_info = {
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
                "width": screen.physicalSize().width(),
                "height": screen.physicalSize().height(),
            },
            "physicalDPI": screen.physicalDotsPerInch(),
            "logicalDPI": screen.logicalDotsPerInch(),
            "refreshRate": screen.refreshRate(),
            "depth": screen.depth(),
            "devicePixelRatio": screen.devicePixelRatio(),
        }
        print(display_info)


class App(QObject):
    qrcode_screen: Optional[QRCodeScreen] = None
    calibration_screen: Optional[CalibrationScreen] = None
    organization_screen: Optional[OrganizationScreen] = None

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.main_thread = QThread()
        self.worker = MainWorker()

        self.worker.open_qrcode_screen.connect(self.open_qrcode_screen)
        self.worker.close_qrcode_screen.connect(self.close_qrcode_screen)
        self.worker.open_calibration_screen.connect(self.open_calibration_screen)
        self.worker.close_calibration_screen.connect(self.close_calibration_screen)
        self.worker.open_organization_screen.connect(self.open_organization_screen)
        self.worker.close_organization_screen.connect(self.close_organization_screen)
        self.worker.exit_app.connect(self.exit)

        self.worker.moveToThread(self.main_thread)
        self.main_thread.started.connect(self.worker.run)
        self.main_thread.start()

    def open_qrcode_screen(self, connection_id: str) -> None:
        qrcode_screen = QRCodeScreen(self.app, connection_id)
        qrcode_screen.show()
        self.qrcode_screen = qrcode_screen

    def close_qrcode_screen(self) -> None:
        if self.qrcode_screen:
            self.qrcode_screen.close()
        else:
            print("QRCodeScreen is not open")

    def open_calibration_screen(self) -> None:
        calibration_screen = CalibrationScreen(self.app)
        calibration_screen.showFullScreen()
        self.calibration_screen = calibration_screen

    def close_calibration_screen(self) -> None:
        if self.calibration_screen:
            self.calibration_screen.close()
        else:
            print("CalibrationScreen is not open")

    def open_organization_screen(self) -> None:
        organization_screen = OrganizationScreen(self.app)
        organization_screen.show()
        self.organization_screen = organization_screen

    def close_organization_screen(self) -> None:
        if self.organization_screen:
            self.organization_screen.close_windows()
        else:
            print("OrganizationScreen is not open")

    def start(self):
        self.app.exec()

    def exit(self):
        self.app.quit()


class MainWorker(QObject):
    open_qrcode_screen = pyqtSignal(str)
    close_qrcode_screen = pyqtSignal()
    open_calibration_screen = pyqtSignal()
    close_calibration_screen = pyqtSignal()
    open_organization_screen = pyqtSignal()
    close_organization_screen = pyqtSignal()
    exit_app = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        # conect to mobile devie via QR code
        connection_id = api.create_connection()
        self.open_qrcode_screen.emit(connection_id)

        # idle while not connected
        connected = False
        while not connected:
            status = api.get_connected_mobile_device_id(connection_id)
            if status.connected:
                print(f"Connected to device ID: {status.device_id}")
                connected = True
            else:
                time.sleep(0.5)
        self.close_qrcode_screen.emit()

        # open calibration screen
        self.open_calibration_screen.emit()
        api.set_connection_state(connection_id, "calibrating")

        # receive images until calibrated
        considered = 0
        while considered < 10:
            images = api.get_images(connection_id, "calibrating")
            for img in images:
                cv2.imwrite(str(uuid.uuid4()) + ".jpg", img)
                considered += 1

        self.close_calibration_screen.emit()

        self.exit_app.emit()


if __name__ == "__main__":
    app = App()
    app.start()
