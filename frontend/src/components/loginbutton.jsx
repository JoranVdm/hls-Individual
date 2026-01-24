// src/components/LoginButton.tsx
import React from "react";

const KEYCLOAK_URL = "http://localhost:8080";
const REALM = "dverse";
const CLIENT_ID = "gateway";
const REDIRECT_URI = "http://localhost:5173"; // your frontend

export const LoginButton = () => {
  const handleLogin = () => {
    const authUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth` +
      `?client_id=${CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
      `&response_type=token`; // implicit flow for simplicity
    window.location.href = authUrl;
  };

  return <button onClick={handleLogin}>Login / Register</button>;
};
