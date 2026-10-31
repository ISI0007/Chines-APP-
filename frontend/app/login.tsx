import React from "react";
import { Redirect } from "expo-router";
import { useAuth } from "../hooks/useAuth";
import LoginScreen from "../screens/LoginScreen";

export default function Login() {
  return useAuth(state => state.user) ? <Redirect href="/" /> : <LoginScreen />;
}
