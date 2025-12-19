import React, { useState, useEffect } from 'react';
import {
    getMachineDailyReport,
    getUserDailyReport,
    getMonthlyPerformance,
    downloadMachineReport,
    downloadUserReport,
    downloadMonthlyPerformance
} from '../../api/admin';
import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { Download, Calendar, Monitor, Users, BarChart2 } from 'lucide-react';

const ReportsSection = () => {
    // State
    const [year, setYear] = useState(new Date().getFullYear());
    const [machineDate, setMachineDate] = useState(new Date().toISOString().split('T')[0]);
    const [userDate, setUserDate] = useState(new Date().toISOString().split('T')[0]);

    const [monthlyData, setMonthlyData] = useState([]);
    const [machineData, setMachineData] = useState([]);
    const [userData, setUserData] = useState([]);

    const [loadingMonthly, setLoadingMonthly] = useState(false);
    const [loadingMachine, setLoadingMachine] = useState(false);
    const [loadingUser, setLoadingUser] = useState(false);

    // Initial Load
    useEffect(() => {
        fetchMonthlyPerformance();
    }, [year]);

    useEffect(() => {
        fetchMachineReport();
    }, [machineDate]);

    useEffect(() => {
        fetchUserReport();
    }, [userDate]);

    // Fetch Functions
    const fetchMonthlyPerformance = async () => {
        try {
            setLoadingMonthly(true);
            const res = await getMonthlyPerformance(year);
            setMonthlyData(res.data.chart_data || []);
        } catch (error) {
            console.error("Failed to fetch monthly performance", error);
        } finally {
            setLoadingMonthly(false);
        }
    };

    const fetchMachineReport = async () => {
        try {
            setLoadingMachine(true);
            const res = await getMachineDailyReport(machineDate);
            setMachineData(res.data.report || []);
        } catch (error) {
            console.error("Failed to fetch machine report", error);
        } finally {
            setLoadingMachine(false);
        }
    };

    const fetchUserReport = async () => {
        try {
            setLoadingUser(true);
            const res = await getUserDailyReport(userDate);
            setUserData(res.data.report || []);
        } catch (error) {
            console.error("Failed to fetch user report", error);
        } finally {
            setLoadingUser(false);
        }
    };

    // Download Handlers
    const handleDownloadMachine = async () => {
        try {
            const response = await downloadMachineReport(machineDate);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `machine_summary_daily_${machineDate}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Failed to download machine report", error);
        }
    };

    const handleDownloadUser = async () => {
        try {
            const response = await downloadUserReport(userDate);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `user_activity_daily_${userDate}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Failed to download user report", error);
        }
    };

    const handleDownloadMonthly = async () => {
        try {
            const response = await downloadMonthlyPerformance(year);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `monthly_performance_${year}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Failed to download monthly performance", error);
        }
    };

    // Helper: Find current year + range
    const currentYear = new Date().getFullYear();
    const years = [currentYear, currentYear - 1, currentYear - 2];

    const formatDuration = (seconds) => {
        if (!seconds) return '0h 0m';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return `${h}h ${m}m`;
    };

    return (
        <div className="space-y-6 mt-6">
            <h2 className="text-xl font-bold text-gray-900 border-b pb-2">Detailed Reports & Analytics</h2>

            {/* 1. Monthly Performance Chart */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                    <div className="flex items-center">
                        <BarChart2 className="text-blue-600 mr-2" size={24} />
                        <h3 className="text-lg font-semibold text-gray-900">Monthly Performance</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                        <select
                            value={year}
                            onChange={(e) => setYear(parseInt(e.target.value))}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                        <button
                            onClick={handleDownloadMonthly}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                            title="Export CSV"
                        >
                            <Download size={20} />
                        </button>
                    </div>
                </div>

                <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={monthlyData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid stroke="#f5f5f5" />
                            <XAxis dataKey="month" scale="point" padding={{ left: 10, right: 10 }} />
                            <YAxis yAxisId="left" orientation="left" stroke="#8884d8" label={{ value: 'Tasks Completed', angle: -90, position: 'insideLeft' }} />
                            <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" label={{ value: 'AHT (mins)', angle: 90, position: 'insideRight' }} />
                            <Tooltip />
                            <Legend />
                            <Bar yAxisId="left" dataKey="tasks_completed" barSize={20} fill="#8884d8" name="Tasks Completed" />
                            <Line yAxisId="right" type="monotone" dataKey="aht" stroke="#82ca9d" name="Avg Handle Time (min)" />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 2. Machine Report */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
                        <div className="flex items-center">
                            <Monitor className="text-purple-600 mr-2" size={24} />
                            <h3 className="text-lg font-semibold text-gray-900">Machine Daily Report</h3>
                        </div>
                        <div className="flex items-center space-x-2">
                            <input
                                type="date"
                                value={machineDate}
                                onChange={(e) => setMachineDate(e.target.value)}
                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                            />
                            <button
                                onClick={handleDownloadMachine}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                title="Export CSV"
                            >
                                <Download size={20} />
                            </button>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Runtime</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasks</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {loadingMachine ? (
                                    <tr><td colSpan="4" className="text-center py-4">Loading...</td></tr>
                                ) : machineData.length === 0 ? (
                                    <tr><td colSpan="4" className="text-center py-4 text-gray-500">No data available</td></tr>
                                ) : (
                                    machineData.map((row) => (
                                        <tr key={row.machine_id}>
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">{row.machine_name}</td>
                                            <td className="px-4 py-3 text-sm text-gray-600">{formatDuration(row.runtime_seconds)}</td>
                                            <td className="px-4 py-3 text-sm text-gray-600">{row.tasks_run_count}</td>
                                            <td className="px-4 py-3 text-sm">
                                                <span className={`px-2 py-1 text-xs rounded-full ${row.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                                    }`}>
                                                    {row.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 3. User Activity Report */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
                        <div className="flex items-center">
                            <Users className="text-orange-600 mr-2" size={24} />
                            <h3 className="text-lg font-semibold text-gray-900">User Activity Report</h3>
                        </div>
                        <div className="flex items-center space-x-2">
                            <input
                                type="date"
                                value={userDate}
                                onChange={(e) => setUserDate(e.target.value)}
                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                            />
                            <button
                                onClick={handleDownloadUser}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition"
                                title="Export CSV"
                            >
                                <Download size={20} />
                            </button>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Work Time</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasks</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {loadingUser ? (
                                    <tr><td colSpan="4" className="text-center py-4">Loading...</td></tr>
                                ) : userData.length === 0 ? (
                                    <tr><td colSpan="4" className="text-center py-4 text-gray-500">No data available</td></tr>
                                ) : (
                                    userData.map((row) => (
                                        <tr key={row.user_id}>
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900">{row.full_name || row.username}</td>
                                            <td className="px-4 py-3 text-sm text-gray-600">{formatDuration(row.total_work_seconds)}</td>
                                            <td className="px-4 py-3 text-sm text-gray-600">{row.tasks_worked_count}</td>
                                            <td className="px-4 py-3 text-sm">
                                                <span className={`px-2 py-1 text-xs rounded-full ${row.status === 'Present' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }`}>
                                                    {row.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ReportsSection;
