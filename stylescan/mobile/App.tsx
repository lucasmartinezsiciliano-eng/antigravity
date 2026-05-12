import React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { COLORS } from "./constants/theme";

import HomeScreen from "./screens/HomeScreen";
import QuizScreen from "./screens/QuizScreen";
import ConsentScreen from "./screens/ConsentScreen";
import PaymentPendingScreen from "./screens/PaymentPendingScreen";
import CaptureScreen from "./screens/CaptureScreen";
import ResultScreen from "./screens/ResultScreen";
import UpsellScreen from "./screens/UpsellScreen";
import VisualsScreen from "./screens/VisualsScreen";

export type RootStackParams = {
  Home: undefined;
  Quiz: { barberCode?: string };
  Consent: { quizAnswers: object; barberCode?: string };
  PaymentPending: { analysis_id: string };
  Capture: { analysisId: string };
  Upload: { analysisId: string; photoUris: string[] };
  Result: { analysisId: string };
  Upsell: { analysisId: string; type: "colorimetry" | "products" };
  Visuals: { analysisId: string; cuts: { nombre: string; nombre_tecnico: string }[] };
};

const Stack = createNativeStackNavigator<RootStackParams>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: COLORS.bg },
          headerTintColor: COLORS.text,
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: COLORS.bg },
          headerShadowVisible: false,
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Quiz"
          component={QuizScreen}
          options={{ title: "Tus preferencias", headerBackTitle: "" }}
        />
        <Stack.Screen
          name="Consent"
          component={ConsentScreen}
          options={{ title: "Consentimiento de datos", headerBackTitle: "" }}
        />
        <Stack.Screen
          name="PaymentPending"
          component={PaymentPendingScreen}
          options={{ title: "Esperando pago", headerBackTitle: "", gestureEnabled: false }}
        />
        <Stack.Screen
          name="Capture"
          component={CaptureScreen}
          options={{ headerShown: false, gestureEnabled: false }}
        />
        <Stack.Screen
          name="Result"
          component={ResultScreen}
          options={{ title: "Tu análisis", headerBackTitle: "" }}
        />
        <Stack.Screen
          name="Upsell"
          component={UpsellScreen}
          options={{ title: "Añadir análisis", headerBackTitle: "" }}
        />
        <Stack.Screen
          name="Visuals"
          component={VisualsScreen}
          options={{ title: "Prueba virtual", headerBackTitle: "" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
