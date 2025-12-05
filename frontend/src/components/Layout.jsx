import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users as UsersIcon, Monitor, CheckSquare, Briefcase, Menu, LogOut, X, UserCheck, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Check if we're on a role-specific dashboard
    const isRoleDashboard = location.pathname.startsWith('/dashboard/');

    // Navigation items - Users only visible to admin, Outsource only to admin and planning
    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/machines', label: 'Machines', icon: Monitor },
        { path: '/tasks', label: 'Tasks', icon: CheckSquare },
        // Outsource - accessible by admin and planning
        ...(user?.role === 'admin' || user?.role === 'planning'
            ? [{ path: '/outsource', label: 'Outsource', icon: Briefcase }]
            : []),
        // Users - accessible by admin and planning
        ...(user?.role === 'admin' || user?.role === 'planning'
            ? [{ path: '/workflow-tracker', label: 'Users', icon: UsersIcon }]
            : []),
        // User Approvals - accessible by admin and planning
        ...(user?.role === 'admin' || user?.role === 'planning'
            ? [{ path: '/admin/approvals', label: 'User Approvals', icon: UserCheck }]
            : []),
        // Change Password - accessible by all users
        { path: '/admin/change-password', label: 'Change Password', icon: Lock },
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false);
    };

    return (
        <div className="flex h-screen bg-gray-100 overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            {isMobileMenuOpen && !isRoleDashboard && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
                    onClick={closeMobileMenu}
                ></div>
            )}

            {/* Sidebar */}
            {!isRoleDashboard && (
                <aside
                    className={`
                        fixed lg:static inset-y-0 left-0 z-30 w-64 bg-white shadow-md transform transition-transform duration-300 ease-in-out
                        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                    `}
                >
                    <div className="p-4 border-b flex justify-between items-center">
                        <div>
                            <h1 className="text-xl font-bold text-blue-600">Workflow Tracker</h1>
                            <p className="text-xs text-gray-500 mt-1">{user?.role || 'User'}</p>
                        </div>
                        <button onClick={closeMobileMenu} className="lg:hidden text-gray-500 hover:text-gray-700">
                            <X size={24} />
                        </button>
                    </div>
                    <nav className="p-4 space-y-2 overflow-y-auto h-[calc(100vh-80px)]">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.path;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={closeMobileMenu}
                                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive
                                        ? 'bg-blue-50 text-blue-600'
                                        : 'text-gray-600 hover:bg-gray-50'
                                        }`}
                                >
                                    <Icon size={20} />
                                    <span className="font-medium">{item.label}</span>
                                </Link>
                            );
                        })}
                    </nav>
                </aside>
            )}

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden w-full">
                <header className="bg-white shadow-sm p-4 flex items-center justify-between z-10">
                    <div className="flex items-center">
                        {!isRoleDashboard && (
                            <button
                                onClick={toggleMobileMenu}
                                className="mr-4 text-gray-600 hover:text-gray-900 lg:hidden focus:outline-none"
                            >
                                <Menu size={24} />
                            </button>
                        )}
                        <h2 className="text-lg font-semibold text-gray-800 truncate max-w-[150px] sm:max-w-none">
                            {navItems.find(i => i.path === location.pathname)?.label || 'Dashboard'}
                        </h2>
                    </div>

                    <div className="flex items-center space-x-2 sm:space-x-4">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-gray-900">{user?.username || 'User'}</p>
                            <p className="text-xs text-gray-500">{user?.email || ''}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="flex items-center space-x-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                            title="Logout"
                        >
                            <LogOut size={20} />
                            <span className="hidden sm:inline text-sm">Logout</span>
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-4 sm:p-6">
                    {children || <Outlet />}
                </main>
            </div>
        </div>
    );
};

export default Layout;
