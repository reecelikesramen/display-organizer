import sys
import time
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from screens import CalibrationScreen, OrganizationScreen, QRCodeScreen


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
        self.thread = QThread()
        self.worker = MainWorker()

        self.worker.open_qrcode_screen.connect(self.open_qrcode_screen)
        self.worker.close_qrcode_screen.connect(self.close_qrcode_screen)
        self.worker.open_calibration_screen.connect(self.open_calibration_screen)
        self.worker.close_calibration_screen.connect(self.close_calibration_screen)
        self.worker.open_organization_screen.connect(self.open_organization_screen)
        self.worker.close_organization_screen.connect(self.close_organization_screen)
        self.worker.exit_app.connect(self.exit)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def open_qrcode_screen(self, connection_id: str) -> None:
        qrcode_screen = QRCodeScreen(self.app, connection_id)
        qrcode_screen.show()
        self.qrcode_screen = qrcode_screen

    def close_qrcode_screen(self) -> None:
        self.qrcode_screen.close()

    def open_calibration_screen(self) -> None:
        calibration_screen = CalibrationScreen(self.app)
        calibration_screen.showFullScreen()
        self.calibration_screen = calibration_screen

    def close_calibration_screen(self) -> None:
        self.calibration_screen.close()

    def open_organization_screen(self) -> None:
        organization_screen = OrganizationScreen(self.app)
        organization_screen.show()
        self.organization_screen = organization_screen

    def close_organization_screen(self) -> None:
        self.organization_screen.close_windows()

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
        print("hello")

    def run(self):
        print("in the thread!")
        self.open_qrcode_screen.emit("test_qr_code")
        time.sleep(2)
        self.close_qrcode_screen.emit()
        self.exit_app.emit()


if __name__ == "__main__":
    app = App()
    app.start()
