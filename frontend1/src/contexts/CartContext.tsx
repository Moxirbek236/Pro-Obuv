import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { cartApi } from '@/api/cart';
import { CartItem } from '@/types/cart.types';
import { useAuth } from '../hooks/useAuth'; // Fix import path
import toast from 'react-hot-toast';

interface CartContextType {
    items: CartItem[];
    itemCount: number;
    total: number;
    isLoading: boolean;
    addToCart: (productId: number, quantity?: number) => Promise<void>;
    removeFromCart: (cartItemId: number) => Promise<void>;
    updateQuantity: (cartItemId: number, quantity: number) => Promise<void>;
    clearCart: () => Promise<void>;
}

export const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuth();
    const [items, setItems] = useState<CartItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch cart when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            fetchCart();
        } else {
            setItems([]);
        }
    }, [isAuthenticated]);

    const fetchCart = async () => {
        try {
            setIsLoading(true);
            const response = await cartApi.getCart();
            if (response.success && response.data) {
                setItems(response.data);
            }
        } catch (error) {
            console.error('Failed to fetch cart:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const addToCart = async (productId: number, quantity: number = 1) => {
        if (!isAuthenticated) {
            toast.error('Iltimos, avval tizimga kiring');
            return;
        }

        try {
            const response = await cartApi.addToCart(productId, quantity);
            if (response.success) {
                toast.success("Savatchaga qo'shildi");
                fetchCart();
            }
        } catch (error) {
            console.error('Failed to add to cart:', error);
            toast.error("Xatolik yuz berdi");
        }
    };

    const removeFromCart = async (cartItemId: number) => {
        try {
            const response = await cartApi.removeFromCart(cartItemId);
            if (response.success) {
                toast.success("O'chirildi");
                setItems(prev => prev.filter(item => item.id !== cartItemId));
                fetchCart();
            }
        } catch (error) {
            console.error('Failed to remove from cart:', error);
            toast.error("Xatolik yuz berdi");
        }
    };

    const updateQuantity = async (cartItemId: number, quantity: number) => {
        if (quantity < 1) return;
        try {
            const response = await cartApi.updateCartItem(cartItemId, quantity);
            if (response.success) {
                fetchCart();
            }
        } catch (error) {
            console.error('Failed to update quantity:', error);
        }
    };

    const clearCart = async () => {
        try {
            const response = await cartApi.clearCart();
            if (response.success) {
                setItems([]);
                toast.success('Savatcha tozalandi');
            }
        } catch (error) {
            console.error('Failed to clear cart:', error);
        }
    };

    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    const total = 0; // Mock total for now

    const value = {
        items,
        itemCount,
        total,
        isLoading,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart
    };

    return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
