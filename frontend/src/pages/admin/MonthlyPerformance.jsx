import React, { useState, useEffect } from 'react';
import { getOperatorPerformance, getUsers } from '../../api/services';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Calendar, Clock, CheckCircle, AlertCircle, RotateCcw, TrendingUp, Filter } from 'lucide-react';

const MonthlyPerformance = () => {
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState(null);
    const [graphData, setGraphData] = useState([]);
    const [operators, setOperators] = useState([]);

    // Filters
    const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [selectedOperator, setSelectedOperator] = useState('');

    useEffect(() => {
        fetchInitialData();
    }, []);

    useEffect(() => {
        fetchPerformanceData();
    }, [selectedMonth, selectedYear, selectedOperator]);

    const fetchInitialData = async () => {
        try {
            const usersRes = await getUsers();
            const ops = usersRes.data.filter(u => u.role === 'operator');
            setOperators(ops);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    };

    const fetchPerformanceData = async () => {
        try {
            setLoading(true);
            const res = await getOperatorPerformance(selectedMonth, selectedYear, selectedOperator || null);
            setMetrics(res.data.metrics);
            setGraphData(res.data.graph_data);
        } catch (error) {
            console.error('Failed to fetch performance data:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds) return '0h 0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    };

    const months = [
        { value: 1, label: 'January' },
        { value: 2, label: 'February' },
        { value: 3, label: 'March' },
        { value: 4, label: 'April' },
        { value: 5, label: 'May' },
        { value: 6, label: 'June' },
        { value: 7, label: 'July' },
        { value: 8, label: 'August' },
        { value: 9, label: 'September' },
        { value: 10, label: 'October' },
        { value: 11, label: 'November' },
        { value: 12, label: 'December' }
    ];

    const years = [2024, 2025, 2026];

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Monthly Operator Performance</h1>
                    <p className="text-gray-600">Track operator efficiency and task completion metrics</p>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-3">
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    >
                        {months.map(m => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>

                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    >
                        {years.map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>

                    <select
                        value={selectedOperator}
                        onChange={(e) => setSelectedOperator(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 min-w-[150px]"
                    >
                        <option value="">All Operators</option>
                        {operators.map(op => (
                            <option key={op.user_id} value={op.user_id}>{op.username}</option>
                        ))}
                    </select>
                </div>
            </div>

            {loading ? (
                <div className="text-center py-12">Loading performance data...</div>
            ) : (
                <>
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">Tasks Completed</p>
                                <CheckCircle size={18} className="text-blue-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{metrics?.completed_tasks || 0}</p>
                            <p className="text-xs text-gray-500">of {metrics?.total_tasks || 0} total tasks</p>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">Avg Time / Task</p>
                                <Clock size={18} className="text-green-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{formatDuration(metrics?.avg_time_per_task_seconds)}</p>
                            <p className="text-xs text-gray-500">per completed task</p>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">Total Duration</p>
                                <Clock size={18} className="text-purple-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{formatDuration(metrics?.total_working_duration_seconds)}</p>
                            <p className="text-xs text-gray-500">total working time</p>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">On Hold</p>
                                <AlertCircle size={18} className="text-yellow-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{metrics?.on_hold_tasks || 0}</p>
                            <p className="text-xs text-gray-500">currently paused</p>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-orange-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">Rescheduled</p>
                                <RotateCcw size={18} className="text-orange-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{metrics?.rescheduled_tasks || 0}</p>
                            <p className="text-xs text-gray-500">due date changes</p>
                        </div>

                        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-indigo-500">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-gray-600">Completion %</p>
                                <TrendingUp size={18} className="text-indigo-500" />
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{metrics?.completion_percentage}%</p>
                            <p className="text-xs text-gray-500">adjusted (-2% rule)</p>
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-lg font-semibold mb-6">Daily Work Duration</h3>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={graphData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="date" />
                                    <YAxis
                                        label={{ value: 'Hours', angle: -90, position: 'insideLeft' }}
                                        tickFormatter={(seconds) => (seconds / 3600).toFixed(1)}
                                    />
                                    <Tooltip
                                        formatter={(value) => [formatDuration(value), 'Duration']}
                                        labelFormatter={(label) => `Date: ${label}`}
                                    />
                                    <Legend />
                                    <Line
                                        type="monotone"
                                        dataKey="duration"
                                        name="Work Duration"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        activeDot={{ r: 8 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default MonthlyPerformance;
