import { z } from "zod";

export const connectionState = z.enum([
  "new",
  "connected",
  "calibrating",
  "organizing",
  "done",
]);
export type ConnectionState = z.infer<typeof connectionState>;

export const getConnectionStateResponse = z.object({
  state: connectionState,
});

export const sendImageDirective = z.enum(["more_images", "next_state"]);
export type SendImageDirective = z.infer<typeof sendImageDirective>;

export const sendImageResponse = z.object({
  directive: sendImageDirective,
});

export const base64Image = z.string().regex(/^data:image\/(jpeg|jpg);base64,/);
export type Base64Image = z.infer<typeof base64Image>;
