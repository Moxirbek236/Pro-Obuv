import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

// Layouts
import MainLayout from '@/layouts/MainLayout';

// Public Pages
import HomePage from '@/pages/public/HomePage';
import MenuPage from '@/pages/public/MenuPage';
import ProductDetailPage from '@/pages/public/ProductDetailPage';
import LoginPage from '@/pages/public/LoginPage';
import RegisterPage from '@/pages/public/RegisterPage';
import AboutPage from '@/pages/public/AboutPage';
import ContactPage from '@/pages/public/ContactPage';

// User Pages
import ProfilePage from '@/pages/user/ProfilePage';
import CartPage from '@/pages/user/CartPage';
import FavoritesPage from '@/pages/user/FavoritesPage';
import OrdersPage from '@/pages/user/OrdersPage';
import SettingsPage from '@/pages/user/SettingsPage';

// Staff Pages
import StaffLoginPage from '@/pages/staff/StaffLoginPage';
import StaffDashboardPage from '@/pages/staff/StaffDashboardPage';

// Superadmin Pages
import SuperadminLoginPage from '@/pages/superadmin/SuperadminLoginPage';
import SuperadminDashboardPage from '@/pages/superadmin/SuperadminDashboardPage';

// Protected Route Component
interface ProtectedRouteProps {
    children: React.ReactNode;
    allowedRoles: ('user' | 'staff' | 'superadmin')[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
    const { isAuthenticated, role, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (!allowedRoles.includes(role as any)) {
        return <Navigate to="/unauthorized" replace />;
    }

    return <>{children}</>;
};

const AppRoutes: React.FC = () => {
    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/" element={<MainLayout />}>
                <Route index element={<HomePage />} />
                <Route path="menu" element={<MenuPage />} />
                <Route path="product/:id" element={<ProductDetailPage />} />
                <Route path="about" element={<AboutPage />} />
                <Route path="contact" element={<ContactPage />} />
                <Route path="login" element={<LoginPage />} />
                <Route path="register" element={<RegisterPage />} />

                {/* User Routes */}
                <Route
                    path="profile"
                    element={
                        <ProtectedRoute allowedRoles={['user']}>
                            <ProfilePage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="cart"
                    element={
                        <ProtectedRoute allowedRoles={['user']}>
                            <CartPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="favorites"
                    element={
                        <ProtectedRoute allowedRoles={['user']}>
                            <FavoritesPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="user"
                    element={
                        <ProtectedRoute allowedRoles={['user']}>
                            <OrdersPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="settings"
                    element={
                        <ProtectedRoute allowedRoles={['user']}>
                            <SettingsPage />
                        </ProtectedRoute>
                    }
                />
            </Route>

            {/* Staff Routes */}
            <Route path="/staff-secure-login-w7m2k" element={<StaffLoginPage />} />
            <Route
                path="/staff/dashboard"
                element={
                    <ProtectedRoute allowedRoles={['staff', 'superadmin']}>
                        <StaffDashboardPage />
                    </ProtectedRoute>
                }
            />

            {/* Superadmin Routes */}
            <Route path="/super-admin-master-login-z9x4m" element={<SuperadminLoginPage />} />
            <Route
                path="/super-admin-control-panel-master-z8x9k"
                element={
                    <ProtectedRoute allowedRoles={['superadmin']}>
                        <SuperadminDashboardPage />
                    </ProtectedRoute>
                }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

export default AppRoutes;
