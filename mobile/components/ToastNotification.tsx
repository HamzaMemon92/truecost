import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, Animated, StyleSheet, TouchableOpacity
} from 'react-native';

type ToastType = 'success' | 'error' | 'info';

interface ToastMessage {
  id: number;
  message: string;
  type: ToastType;
}

// Singleton event emitter pattern — no context provider needed
type ToastListener = (msg: ToastMessage) => void;
const listeners: ToastListener[] = [];

export const showToast = (message: string, type: ToastType = 'success') => {
  const msg = { id: Date.now(), message, type };
  listeners.forEach(l => l(msg));
};

const COLORS: Record<ToastType, { bg: string; border: string; text: string }> = {
  success: { bg: '#ECFDF5', border: '#10B981', text: '#065F46' },
  error:   { bg: '#FEF2F2', border: '#EF4444', text: '#991B1B' },
  info:    { bg: '#EFF6FF', border: '#3B82F6', text: '#1E40AF' },
};

const ICONS: Record<ToastType, string> = {
  success: '✅',
  error: '❌',
  info: 'ℹ️',
};

function ToastItem({ toast, onHide }: { toast: ToastMessage; onHide: () => void }) {
  const opacity = useState(new Animated.Value(0))[0];
  const translateY = useState(new Animated.Value(-20))[0];

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 250, useNativeDriver: true }),
      Animated.timing(translateY, { toValue: 0, duration: 250, useNativeDriver: true }),
    ]).start();

    const timer = setTimeout(() => {
      Animated.parallel([
        Animated.timing(opacity, { toValue: 0, duration: 300, useNativeDriver: true }),
        Animated.timing(translateY, { toValue: -20, duration: 300, useNativeDriver: true }),
      ]).start(onHide);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  const c = COLORS[toast.type];

  return (
    <Animated.View style={[styles.toast, { opacity, transform: [{ translateY }], backgroundColor: c.bg, borderLeftColor: c.border }]}>
      <Text style={styles.icon}>{ICONS[toast.type]}</Text>
      <Text style={[styles.message, { color: c.text }]}>{toast.message}</Text>
    </Animated.View>
  );
}

export default function ToastNotification() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const listener: ToastListener = (msg) => {
      setToasts(prev => [...prev, msg]);
    };
    listeners.push(listener);
    return () => {
      const idx = listeners.indexOf(listener);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);

  const remove = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <View style={styles.container} pointerEvents="none">
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onHide={() => remove(t.id)} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 60,
    left: 16,
    right: 16,
    zIndex: 9999,
    gap: 8,
  },
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 6,
    gap: 10,
  },
  icon: { fontSize: 16 },
  message: { flex: 1, fontSize: 14, fontWeight: '600', lineHeight: 20 },
});
