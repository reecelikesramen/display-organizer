import cv2

ARUCO_TAG_DICTIONARY = cv2.aruco.DICT_4X4_50
ARUCO_MARKER_PADDING = 5  # mm
ARUCO_MARKER_SIZE = 50  # mm
QR_CODE_SIZE = 100  # mm
CHESSBOARD = (6, 9)  # number of row, col intersection points
CHESSBOARD_SIZE = 150  # mm
QR_CODE_PREFIX = "DISPLAY_ORGANIZER"  # prefix put in front of connection UUID for later versioning compat and so dont scan any old UUID
