import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import Layout from './components/Layout.jsx';
import PlanningLayout from './components/PlanningLayout.jsx';
import Login from './pages/login.jsx';

// Dashboards
import AdminDashboard from './pages/dashboards/AdminDashboard.jsx';
import OperatorDashboard from './pages/dashboards/OperatorDashboard.jsx';
import SupervisorDashboard from './pages/dashboards/SupervisorDashboard.jsx';
import PlanningDashboard from './pages/dashboards/PlanningDashboard.jsx';
import FileMasterDashboard from './pages/dashboards/FileMasterDashboard.jsx';
import FabMasterDashboard from './pages/dashboards/FabMasterDashboard.jsx';

// Pages
import Dashboard from './pages/Dashboard.jsx';
import Users from './pages/Users.jsx';
import Projects from './pages/Projects.jsx';
import Machines from './pages/Machines.jsx';
import Tasks from './pages/Tasks.jsx';
import Outsource from './pages/Outsource.jsx';
import Signup from './pages/Signup.jsx';
import SignupSkills from './pages/SignupSkills.jsx';
import UserApprovals from './pages/admin/UserApprovals.jsx';
import UserPerformance from './pages/admin/UserPerformance.jsx';
import MonthlyPerformance from './pages/admin/MonthlyPerformance.jsx';
import ChangePassword from './pages/admin/ChangePassword.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import WorkflowTracker from './pages/WorkflowTracker.jsx';
import Profile from './pages/Profile.jsx';
import Reports from './pages/admin/Reports.jsx';

function App() {
    return (
        <ErrorBoundary>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/signup/skills" element={<SignupSkills />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />

                    <Route path="/dashboard/admin" element={
                        <ProtectedRoute allowedRoles={['admin']}>
                            <Layout><AdminDashboard /></Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/dashboard/operator" element={
                        <ProtectedRoute allowedRoles={['operator']}>
                            <Layout><OperatorDashboard /></Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/dashboard/supervisor" element={
                        <ProtectedRoute allowedRoles={['supervisor']}>
                            <Layout><SupervisorDashboard /></Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/dashboard/planning" element={
                        <ProtectedRoute allowedRoles={['planning']}>
                            <PlanningLayout><PlanningDashboard /></PlanningLayout>
                        </ProtectedRoute>
                    } />
                    <Route path="/dashboard/file-master" element={
                        <ProtectedRoute allowedRoles={['FILE_MASTER', 'file_master']}>
                            <Layout><FileMasterDashboard /></Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/dashboard/fab-master" element={
                        <ProtectedRoute allowedRoles={['FAB_MASTER', 'fab_master']}>
                            <Layout><FabMasterDashboard /></Layout>
                        </ProtectedRoute>
                    } />

                    <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                        <Route index element={<Dashboard />} />
                        <Route path="users" element={<ProtectedRoute allowedRoles={['admin']}><Users /></ProtectedRoute>} />
                        <Route path="projects" element={<ProtectedRoute allowedRoles={['admin']}><Projects /></ProtectedRoute>} />
                        <Route path="machines" element={<Machines />} />
                        <Route path="tasks" element={<Tasks />} />
                        <Route path="outsource" element={<ProtectedRoute allowedRoles={['admin', 'planning']}><Outsource /></ProtectedRoute>} />
                        <Route path="workflow-tracker" element={<ProtectedRoute allowedRoles={['admin', 'planning']}><WorkflowTracker /></ProtectedRoute>} />
                        <Route path="admin/approvals" element={<ProtectedRoute allowedRoles={['admin']}><UserApprovals /></ProtectedRoute>} />
                        <Route path="admin/performance" element={<ProtectedRoute allowedRoles={['admin']}><UserPerformance /></ProtectedRoute>} />
                        <Route path="admin/monthly-performance" element={<ProtectedRoute allowedRoles={['admin']}><MonthlyPerformance /></ProtectedRoute>} />
                        <Route path="admin/reports" element={<ProtectedRoute allowedRoles={['admin']}><Reports /></ProtectedRoute>} />
                        <Route path="admin/change-password" element={<ChangePassword />} />
                        <Route path="profile" element={<Profile />} />
                    </Route>

                    <Route path="/unauthorized" element={
                        <div className="flex items-center justify-center h-screen">
                            <div className="text-center">
                                <h1 className="text-2xl font-bold text-red-600">Unauthorized</h1>
                                <p className="text-gray-600 mt-2">You don't have permission to access this page.</p>
                            </div>
                        </div>
                    } />

                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            </AuthProvider>
        </ErrorBoundary>
    );
}

export default App;
