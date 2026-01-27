import React, { useState, useEffect } from 'react';
import api from '../../api/axios';
import { getPlanningDashboardSummary } from '../../api/planning';

import { Folder, TrendingUp, Settings, Clock, CheckCircle, Users, Activity, RefreshCw, Pause, UserPlus } from 'lucide-react';
import QuickAssign from '../../components/QuickAssign';
import OperationalTaskSection from '../../components/OperationalTaskSection.jsx';

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-600 mb-1 truncate">{title}</p>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
                {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
            </div>
            <div className={`p-2 sm:p-3 rounded-full ${color} flex-shrink-0 ml-2`}>
                <Icon className="text-white" size={20} />
            </div>
        </div>
    </div>
);

const PlanningDashboard = () => {
    const [summary, setSummary] = useState({
        total_projects: 0,
        total_tasks: 0,
        total_tasks_running: 0,
        machines_active: 0,
        pending_tasks: 0,
        completed_tasks: 0,
        on_hold_tasks: 0,
        project_summary: [],
        operator_status: []
    });
    const [projects, setProjects] = useState([]);
    const [operators, setOperators] = useState([]);
    const [selectedProject, setSelectedProject] = useState('all');
    const [selectedOperator, setSelectedOperator] = useState('all');

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadInitial = async () => {
            try {
                const [projRes, userRes] = await Promise.all([
                    api.get('/dropdowns/projects'),
                    api.get('/dropdowns/users/assignable')
                ]);
                setProjects(Array.isArray(projRes?.data) ? projRes.data : []);
                setOperators(Array.isArray(userRes?.data) ? userRes.data : []);
            } catch (e) {
                console.error("Dropdown load failed", e);
            }
        };
        loadInitial();
    }, []);

    useEffect(() => {
        fetchDashboard();
    }, [selectedProject, selectedOperator]);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching planning dashboard...', { project: selectedProject, operator: selectedOperator });
            const response = await getPlanningDashboardSummary(selectedProject, selectedOperator);
            console.log('✅ Planning dashboard loaded');

            const data = response.data;

            setSummary({
                total_projects: data.total_projects || 0,
                total_tasks: data.total_tasks || 0,
                total_tasks_running: data.total_tasks_running || 0,
                machines_active: data.machines_active || 0,
                pending_tasks: data.pending_tasks || 0,
                completed_tasks: data.completed_tasks || 0,
                on_hold_tasks: data.on_hold_tasks || 0,
                project_summary: data.project_summary || [],
                operator_status: data.operator_status || []
            });
        } catch (err) {
            console.error('❌ Failed to fetch planning dashboard:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'Completed': return 'bg-green-100 text-green-800';
            case 'In Progress': return 'bg-blue-100 text-blue-800';
            case 'Pending': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                    <h3 className="text-lg font-semibold text-red-900 mb-2">Error Loading Dashboard</h3>
                    <p className="text-red-700 mb-4">{error}</p>
                    <button
                        onClick={fetchDashboard}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Planning Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Overview of projects and resources</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="p-2 border rounded text-sm bg-white shadow-sm focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Projects</option>
                        {projects.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                    </select>
                    <select
                        value={selectedOperator}
                        onChange={(e) => setSelectedOperator(e.target.value)}
                        className="p-2 border rounded text-sm bg-white shadow-sm focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Operators</option>
                        {operators.map(o => (
                            <option key={o.user_id} value={o.user_id}>{o.full_name || o.username}</option>
                        ))}
                    </select>
                    <button
                        onClick={fetchDashboard}
                        className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto shadow-sm"
                        disabled={loading}
                    >
                        <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 sm:gap-4">
                <StatCard
                    title="Total Projects"
                    value={summary.total_projects}
                    icon={Folder}
                    color="bg-purple-500"
                />
                <StatCard
                    title="Total Tasks"
                    value={summary.total_tasks}
                    icon={TrendingUp}
                    color="bg-indigo-500"
                />
                <StatCard
                    title="Pending"
                    value={summary.pending_tasks}
                    icon={Clock}
                    color="bg-gray-500"
                />
                <StatCard
                    title="In Progress"
                    value={summary.total_tasks_running}
                    icon={TrendingUp}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Completed"
                    value={summary.completed_tasks}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
                <StatCard
                    title="On Hold"
                    value={summary.on_hold_tasks}
                    icon={Pause}
                    color="bg-yellow-500"
                />
            </div>

            <QuickAssign onAssignSuccess={fetchDashboard} />

            {/* Project Summary */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Progress</h2>
                {summary.project_summary.length > 0 ? (
                    <div className="space-y-4">
                        {summary.project_summary.map((project, index) => (
                            <div key={index} className="border-b pb-4 last:border-b-0 last:pb-0">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex-1">
                                        <h3 className="font-medium text-gray-900">{project.project}</h3>
                                        <p className="text-sm text-gray-600">
                                            {project.completed_tasks} / {project.total_tasks} tasks completed
                                        </p>
                                    </div>
                                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                                        {project.status}
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2.5">
                                    <div
                                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                                        style={{ width: `${project.progress}%` }}
                                    ></div>
                                </div>
                                <p className="text-xs text-gray-600 mt-1">{project.progress.toFixed(1)}% Complete</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <Folder className="mx-auto mb-4" size={48} />
                        <p>No projects found</p>
                    </div>
                )}
            </div>

            {/* Operator Status */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center mb-4">
                    <Users className="text-blue-600 mr-2" size={24} />
                    <h2 className="text-lg font-semibold text-gray-900">Operator Status</h2>
                </div>
                {summary.operator_status.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {summary.operator_status.map((operator, index) => (
                            <div
                                key={index}
                                className={`p-4 rounded-lg border-2 ${operator.status === 'Active'
                                    ? 'bg-green-50 border-green-300'
                                    : 'bg-gray-50 border-gray-300'
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-medium text-gray-900">{operator.name}</h3>
                                    <span
                                        className={`flex h-3 w-3 rounded-full ${operator.status === 'Active' ? 'bg-green-500' : 'bg-gray-400'
                                            }`}
                                    ></span>
                                </div>
                                <p className="text-sm text-gray-600">
                                    {operator.current_task ? (
                                        <span className="flex items-center">
                                            <Activity size={14} className="mr-1" />
                                            {operator.current_task}
                                        </span>
                                    ) : (
                                        <span className="text-gray-400">No active task</span>
                                    )}
                                </p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <Users className="mx-auto mb-4" size={48} />
                        <p>No operators found</p>
                    </div>
                )}
            </div>

            {/* Filing & Fabrication Monitoring */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                        <span className="w-3 h-3 bg-blue-600 rounded-full mr-2"></span>
                        Filing Monitoring
                    </h2>
                    <OperationalTaskSection type="filing" />
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                        <span className="w-3 h-3 bg-orange-600 rounded-full mr-2"></span>
                        Fabrication Monitoring
                    </h2>
                    <OperationalTaskSection type="fabrication" />
                </div>
            </div>
        </div>
    );
};

export default PlanningDashboard;
