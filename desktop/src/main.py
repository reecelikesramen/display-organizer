import sys
import time
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
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
        self.app.setQuitOnLastWindowClosed(False)
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
        self.main_thread.started.connect(self.worker.start)
        self.main_thread.start()

    def open_qrcode_screen(self, connection_id: str) -> None:
        qrcode_screen = QRCodeScreen(self.app, connection_id)
        qrcode_screen.screen_close_requested.connect(lambda: self.worker.qrcode_screen_closed.emit()) # check if can just put in slot
        qrcode_screen.show()
        self.qrcode_screen = qrcode_screen

    def close_qrcode_screen(self) -> None:
        if self.qrcode_screen:
            pass
            self.qrcode_screen.close()
        else:
            print("QRCodeScreen is not open")

    def open_calibration_screen(self) -> None:
        calibration_screen = CalibrationScreen(self.app)
        calibration_screen.screen_close_requested.connect(lambda: self.worker.calibration_screen_closed.emit())
        calibration_screen.showFullScreen()
        self.calibration_screen = calibration_screen

    def close_calibration_screen(self) -> None:
        if self.calibration_screen:
            self.calibration_screen.close()
        else:
            print("CalibrationScreen is not open")

    def open_organization_screen(self) -> None:
        organization_screen = OrganizationScreen(self.app)
        organization_screen.screen_close_requested.connect(lambda: self.worker.organization_screen_closed.emit())
        organization_screen.show()
        self.organization_screen = organization_screen

    def close_organization_screen(self) -> None:
        if self.organization_screen:
            self.organization_screen.close()
        else:
            print("OrganizationScreen is not open")

    def start(self):
        self.app.exec()

    def exit(self):
        self.app.quit()


class MainWorker(QObject):
    open_qrcode_screen = pyqtSignal(str)
    close_qrcode_screen = pyqtSignal()
    qrcode_screen_closed = pyqtSignal()
    open_calibration_screen = pyqtSignal()
    close_calibration_screen = pyqtSignal()
    calibration_screen_closed = pyqtSignal()
    open_organization_screen = pyqtSignal()
    close_organization_screen = pyqtSignal()
    organization_screen_closed = pyqtSignal()
    exit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.connection_id = None
        self.timer = QTimer(self)
        self.calibration_images_received = 0

    def handle_close(self):
        print("Exiting app")
        api.end_connection(self.connection_id)
        self.exit_app.emit()

    def start(self):
        self.connection_id = api.create_connection()
        self.open_qrcode_screen.emit(self.connection_id)

        self.qrcode_screen_closed.connect(self.handle_close)
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(500)

    def check_connection(self):
        status = api.get_connected_mobile_device_id(self.connection_id)
        if not status.connected:
            return

        print(f"Connected to device ID: {status.device_id}")
        self.close_qrcode_screen.emit()
        self.timer.disconnect()
        self.timer.stop()
        QTimer.singleShot(0, self.start_calibration)

    def start_calibration(self):
        self.open_calibration_screen.emit()
        api.set_connection_state(self.connection_id, "calibrating")

        self.calibration_screen_closed.connect(self.handle_close)
        self.timer.timeout.connect(self.calibrate_camera)
        self.timer.start(500)

    def calibrate_camera(self):
        images = api.get_images(self.connection_id, "calibrating")
        for img in images:
            cv2.imwrite(f"calibration/{str(uuid.uuid4())}.jpg", img)
            self.calibration_images_received += 1

        print(f"Considered {self.calibration_images_received} images")

        if self.calibration_images_received < 3:
            return

        self.close_calibration_screen.emit()
        self.timer.disconnect()
        self.timer.stop()
        QTimer.singleShot(0, self.start_organization)

    def start_organization(self):
        self.open_organization_screen.emit()
        api.set_connection_state(self.connection_id, "organizing")
        QTimer.singleShot(5000, self.handle_close)

if __name__ == "__main__":
    app = App()
    app.start()
