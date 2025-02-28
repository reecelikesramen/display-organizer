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
import { useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, View, Text, Modal } from "react-native";
import tinycolor from "tinycolor2";
import uuidV4Regex from "@/constants/UUID4Regex";

export default function Index() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [facing, setFacing] = useState<CameraType>("back");
  const [hasRequested, setHasRequested] = useState(false); //track if permissions have been requested
  const networkState = useNetworkState();
  const scanningQR = useRef(true);
  const [uuid, setUuid] = useState<string | null>(null);

  useEffect(() => {
    if (permission && !permission.granted && !hasRequested) {
      requestPermission();
      setHasRequested(true);
    }
  }, [permission, requestPermission, hasRequested]);

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

  const handleQRCodeScanned = (result: BarcodeScanningResult) => {
    if (!scanningQR.current || result.type !== "qr" || !result.data) {
      return;
    }

    if (uuidV4Regex.test(result.data)) {
      setUuid(result.data);
      scanningQR.current = false;
      console.log("UUID scanned:", result.data);
    }
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
