import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import {
    LayoutDashboard, BarChart3, Users, Database,
    Settings, LogOut, Shield, FileText, Activity, Layers, Menu as MenuIcon, X
} from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

const SuperadminDashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const menuItems = [
        { icon: LayoutDashboard, label: 'Overview', path: '/super-admin-control-panel-master-z8x9k' },
        { icon: BarChart3, label: 'Analytics', path: '/super-admin/analytics' },
        { icon: Users, label: 'User Management', path: '/super-admin/users' },
        { icon: Shield, label: 'Staff Access', path: '/super-admin/staff' },
        { icon: Database, label: 'Inventory', path: '/super-admin/inventory' },
        { icon: FileText, label: 'Reports', path: '/super-admin/reports' },
        { icon: Activity, label: 'System Logs', path: '/super-admin/logs' },
        { icon: Settings, label: 'System Config', path: '/super-admin/settings' },
    ];

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 flex font-sans">
            {/* Sidebar */}
            <aside className={`fixed inset-y-0 left-0 z-50 w-72 bg-gray-950 border-r border-gray-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                <div className="flex items-center justify-between h-20 px-6 border-b border-gray-800">
                    <div className="flex items-center gap-2 text-red-500">
                        <Shield className="w-8 h-8" />
                        <span className="text-lg font-bold tracking-wider text-white">ADMIN<span className="text-red-500">CORE</span></span>
                    </div>
                    <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <nav className="p-4 space-y-2">
                    {menuItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-all ${isActive
                                        ? 'bg-red-900/20 text-red-500 border-l-4 border-red-500'
                                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`}
                            >
                                <item.icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="absolute bottom-0 w-full p-6 border-t border-gray-800 bg-gray-950">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span className="text-xs text-gray-500 font-mono">SYSTEM ONLINE</span>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-red-900/30 text-gray-300 hover:text-red-500 rounded-lg transition-colors border border-gray-700 hover:border-red-900/50"
                    >
                        <LogOut className="w-4 h-4" />
                        Terminate Session
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-gray-900">
                {/* Header */}
                <header className="bg-gray-950 border-b border-gray-800 h-20 flex items-center justify-between px-8">
                    <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-gray-400 hover:text-white">
                        <MenuIcon className="w-6 h-6" />
                    </button>

                    <div className="flex items-center gap-4 ml-auto">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-white">Super Administrator</p>
                            <p className="text-xs text-gray-500 font-mono">ID: ROOT_ACCESS_01</p>
                        </div>
                        <div className="w-10 h-10 bg-red-900/30 rounded-lg flex items-center justify-center border border-red-900/50 text-red-500 font-bold">
                            SA
                        </div>
                    </div>
                </header>

                {/* Dashboard Content */}
                <main className="flex-1 overflow-y-auto p-8">
                    {children}
                </main>
            </div>
        </div>
    );
};

const SuperadminDashboardPage: React.FC = () => {
    return (
        <SuperadminDashboardLayout>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {[
                    { label: 'Total Revenue', value: '128.5M', sub: '+12% from last month', icon: Database, color: 'text-green-500' },
                    { label: 'Active Users', value: '2,451', sub: '+180 new users', icon: Users, color: 'text-blue-500' },
                    { label: 'Total Orders', value: '1,240', sub: '45 pending', icon: Activity, color: 'text-yellow-500' },
                    { label: 'Server Load', value: '24%', sub: 'Optimal performance', icon: Layers, color: 'text-purple-500' },
                ].map((stat, i) => (
                    <div key={i} className="bg-gray-950 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <p className="text-gray-400 text-sm font-medium">{stat.label}</p>
                                <h3 className="text-3xl font-bold text-white mt-1 font-mono">{stat.value}</h3>
                            </div>
                            <div className={`p-2 rounded-lg bg-gray-900 ${stat.color}`}>
                                <stat.icon className="w-6 h-6" />
                            </div>
                        </div>
                        <p className="text-xs text-gray-500">{stat.sub}</p>
                    </div>
                ))}
            </div>

            {/* Chart Placeholder */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-2 bg-gray-950 border border-gray-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-white">Revenue Analytics</h3>
                        <select className="bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1">
                            <option>Last 7 days</option>
                            <option>Last 30 days</option>
                            <option>This Year</option>
                        </select>
                    </div>
                    <div className="h-64 flex items-center justify-center border-t border-gray-900 bg-gray-900/30 rounded-lg">
                        <span className="text-gray-500 font-mono text-sm">CHART_VISUALIZATION_COMPONENT_PLACEHOLDER</span>
                    </div>
                </div>

                <div className="bg-gray-950 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-6">System Health</h3>
                    <div className="space-y-6">
                        {[
                            { label: 'CPU Usage', val: 45, color: 'bg-blue-500' },
                            { label: 'Memory', val: 62, color: 'bg-purple-500' },
                            { label: 'Storage', val: 28, color: 'bg-green-500' },
                            { label: 'Network', val: 15, color: 'bg-yellow-500' },
                        ].map((item, i) => (
                            <div key={i}>
                                <div className="flex justify-between text-xs text-gray-400 mb-2">
                                    <span>{item.label}</span>
                                    <span>{item.val}%</span>
                                </div>
                                <div className="w-full bg-gray-900 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full ${item.color}`}
                                        style={{ width: `${item.val}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </SuperadminDashboardLayout>
    );
};

export default SuperadminDashboardPage;
