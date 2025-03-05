import { useEffect, useMemo, useState } from "react";
import { AppState } from "react-native";

export function useAppVisible() {
  const [appState, setAppState] = useState(AppState.currentState);
  const isAppVisible = useMemo(() => appState === "active", [appState]);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextAppState) => {
      setAppState(nextAppState);
    });

    return () => {
      subscription.remove();
    };
  }, []);

  return isAppVisible;
}
