import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";
import { Colors } from "@/constants/Colors";
import { FontAwesome6 } from "@expo/vector-icons";
import {
  BarcodeScanningResult,
  CameraType,
  CameraView,
  useCameraPermissions,
} from "expo-camera";
import { useNetworkState } from "expo-network";
import { useCallback, useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, View, Text, Modal } from "react-native";
import tinycolor from "tinycolor2";
import connectionIDRegex from "@/constants/ConnectionIDRegex";
import * as api from "@/api";
import { ConnectionState } from "@/api/model";

export default function Index() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [facing, setFacing] = useState<CameraType>("back");
  const [hasRequested, setHasRequested] = useState(false); //track if permissions have been requested
  const networkState = useNetworkState();
  const [scanningQR, setScanningQR] = useState(true);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [appState, setAppState] = useState<ConnectionState>("new");

  useEffect(() => {
    if (permission && !permission.granted && !hasRequested) {
      requestPermission();
      setHasRequested(true);
    }
  }, [permission, requestPermission, hasRequested]);

  useEffect(() => {
    if (connectionId) {
      console.log("Connection ID:", connectionId);
      api.joinConnection(connectionId);
      setAppState("connected");
    }
  }, [connectionId]);

  useEffect(() => {
    if (appState === "connected") {
      console.log("Connected");
      const interval = setInterval(async () => {
        const state = await api.getConnectionState(connectionId!);
        if (state === "calibrating") {
          setAppState("calibrating");
          clearInterval(interval);
        }
      }, 500);
    } else if (appState === "calibrating") {
      console.log("Calibrating");
      const interval = setInterval(async () => {
        const picture = await cameraRef.current?.takePictureAsync({
          base64: true,
          fastMode: true,
          quality: 0.2,
          skipProcessing: false, // TODO look into
          shutterSound: false,
          imageType: "jpg",
          exif: true,
        });
        if (!picture) {
          console.error("Failed to take picture");
        }

        // api.sendImage(connectionId!, "calibrating", picture!.base64!);
        // if (state === "calibrating") {
        //   setAppState("calibrating");
        //   clearInterval(interval);
        // }
      }, 1000);
    }
  }, [appState]);

  const handleQRCodeScanned = useCallback(
    (result: BarcodeScanningResult) => {
      if (!scanningQR || result.type !== "qr" || !result.data) {
        return;
      }

      const match = result.data.match(connectionIDRegex);
      if (match) {
        setConnectionId(match[1]);
        setScanningQR(false);
      }
    },
    [scanningQR],
  );

  if (!permission) {
    return null;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text>Permission denied</Text>
      </View>
    );
  }

  const toggleFacing = () => {
    setFacing((prev) => (prev === "back" ? "front" : "back"));
  };

  return (
    <CameraView
      style={styles.camera}
      ref={cameraRef}
      mode={"picture"}
      facing={facing}
      onBarcodeScanned={handleQRCodeScanned}
    >
      <Modal
        animationType="fade"
        transparent={true}
        visible={!networkState.isInternetReachable}
      >
        <ThemedView style={styles.modalView}>
          <ThemedText type="subtitle">
            Please connect to the internet
          </ThemedText>
        </ThemedView>
      </Modal>
      <View style={styles.shutterContainer}>
        <Pressable onPress={toggleFacing}>
          <FontAwesome6 name="rotate-left" size={32} color="white" />
        </Pressable>
      </View>
    </CameraView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
  },
  camera: {
    flex: 1,
    width: "100%",
  },
  shutterContainer: {
    position: "absolute",
    bottom: 44,
    left: 0,
    width: "100%",
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 30,
  },
  shutterBtn: {
    backgroundColor: "transparent",
    borderWidth: 5,
    borderColor: "white",
    width: 85,
    height: 85,
    borderRadius: 45,
    alignItems: "center",
    justifyContent: "center",
  },
  shutterBtnInner: {
    width: 70,
    height: 70,
    borderRadius: 50,
  },
  centeredView: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.5)", // Semi-transparent background
  },
  modalView: {
    width: "100%", // Take up full width
    height: "100%", // Take up full height
    backgroundColor: tinycolor(Colors.dark.background)
      .setAlpha(0.75)
      .toRgbString(),
    alignItems: "center",
    justifyContent: "center", // center content
  },
});
