"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type GeoErrorType =
  | "unsupported"
  | "insecure_context"
  | "permission_denied"
  | "position_unavailable"
  | "timeout"
  | "unknown";

export type DevicePosition = {
  lat: number;
  lng: number;
  accuracy: number;
  /** ISO 8601, tomado de GeolocationPosition.timestamp (reloj del dispositivo). */
  capturedAt: string;
};

export type GeolocationStatus = "idle" | "locating" | "watching" | "success" | "error";

export const LOW_ACCURACY_THRESHOLD_METERS = 50;

const GEOLOCATION_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 15000,
  maximumAge: 0,
};

function mapGeolocationError(error: GeolocationPositionError): GeoErrorType {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return "permission_denied";
    case error.POSITION_UNAVAILABLE:
      return "position_unavailable";
    case error.TIMEOUT:
      return "timeout";
    default:
      return "unknown";
  }
}

/**
 * Envuelve navigator.geolocation (getCurrentPosition / watchPosition / clearWatch).
 * No inicia seguimiento automáticamente; el consumidor decide cuándo.
 */
export function useDeviceGeolocation() {
  const [status, setStatus] = useState<GeolocationStatus>("idle");
  const [position, setPosition] = useState<DevicePosition | null>(null);
  const [errorType, setErrorType] = useState<GeoErrorType | null>(null);
  const watchIdRef = useRef<number | null>(null);

  const isSupported = typeof navigator !== "undefined" && "geolocation" in navigator;
  const isSecureContext = typeof window !== "undefined" && window.isSecureContext;

  const handleSuccess = useCallback((pos: GeolocationPosition) => {
    setPosition({
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
      capturedAt: new Date(pos.timestamp).toISOString(),
    });
    setErrorType(null);
    setStatus((current) => (current === "watching" ? "watching" : "success"));
  }, []);

  const handleError = useCallback((error: GeolocationPositionError) => {
    setErrorType(mapGeolocationError(error));
    setStatus("error");
  }, []);

  const getCurrentPosition = useCallback(() => {
    if (!isSupported) {
      setErrorType("unsupported");
      setStatus("error");
      return;
    }
    if (!isSecureContext) {
      setErrorType("insecure_context");
      setStatus("error");
      return;
    }
    setStatus("locating");
    setErrorType(null);
    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, GEOLOCATION_OPTIONS);
  }, [isSupported, isSecureContext, handleSuccess, handleError]);

  const startWatching = useCallback(() => {
    if (!isSupported) {
      setErrorType("unsupported");
      setStatus("error");
      return;
    }
    if (!isSecureContext) {
      setErrorType("insecure_context");
      setStatus("error");
      return;
    }
    if (watchIdRef.current != null) return;
    setErrorType(null);
    setStatus("watching");
    watchIdRef.current = navigator.geolocation.watchPosition(handleSuccess, handleError, GEOLOCATION_OPTIONS);
  }, [isSupported, isSecureContext, handleSuccess, handleError]);

  const stopWatching = useCallback(() => {
    if (watchIdRef.current != null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
      setStatus((current) => (current === "watching" ? "idle" : current));
    }
  }, []);

  // Detener el seguimiento también al desmontar el componente.
  useEffect(() => {
    return () => {
      if (watchIdRef.current != null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, []);

  const isWatching = status === "watching";
  const isLowAccuracy = position != null && position.accuracy > LOW_ACCURACY_THRESHOLD_METERS;

  return {
    status,
    position,
    errorType,
    isWatching,
    isLowAccuracy,
    isSupported,
    isSecureContext,
    getCurrentPosition,
    startWatching,
    stopWatching,
  };
}
