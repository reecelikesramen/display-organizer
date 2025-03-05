const QR_CODE_PREFIX = "DISPLAY_ORGANIZER"; // TODO: this will change, need to keep in sync with desktop. will encode version or build SHA
export default RegExp(
  `^${QR_CODE_PREFIX}([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$`,
);
