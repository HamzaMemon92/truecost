import { useState, useEffect, useCallback } from 'react';

export interface BasketItem {
  canonical_product_id: string;
  quantity: number;
  title: string;
  image_url?: string;
  variant?: string;
}

const STORAGE_KEY = 'tc_unified_basket';

export function useBasket() {
  // Initialize from localStorage if available
  const [items, setItems] = useState<BasketItem[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error("Failed to parse basket from localStorage", e);
    }
    return [];
  });

  const [isOpen, setIsOpen] = useState(false);

  // Sync to localStorage whenever items change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const addItem = useCallback((newItem: Omit<BasketItem, 'quantity'>, quantity: number = 1) => {
    setItems(current => {
      const existingIndex = current.findIndex(
        i => i.canonical_product_id === newItem.canonical_product_id
      );
      if (existingIndex >= 0) {
        const updated = [...current];
        const existingItem = updated[existingIndex];
        if (existingItem) {
          updated[existingIndex] = {
            ...existingItem,
            quantity: existingItem.quantity + quantity
          };
        }
        return updated;
      }
      return [...current, { ...newItem, quantity }];
    });
    setIsOpen(true); // Open basket when item is added
  }, []);

  const removeItem = useCallback((id: string) => {
    setItems(current => current.filter(i => i.canonical_product_id !== id));
  }, []);

  const updateQuantity = useCallback((id: string, quantity: number) => {
    if (quantity <= 0) {
      removeItem(id);
      return;
    }
    setItems(current => current.map(
      i => i.canonical_product_id === id ? { ...i, quantity } : i
    ));
  }, [removeItem]);

  const clearBasket = useCallback(() => {
    setItems([]);
  }, []);

  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return {
    items,
    itemCount,
    isOpen,
    setIsOpen,
    addItem,
    removeItem,
    updateQuantity,
    clearBasket,
  };
}
