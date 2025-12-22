import React, { useState, useEffect } from 'react';
import {
    getMachineDailyReport,
    getUserDailyReport,
    getMachineDetailedReport,
    getUserDetailedReport,
    getActiveWorkMonitoring,
    downloadMachineReport,
    downloadUserReport
} from '../../api/admin';
import { getMachines, getUsers } from '../../api/services';
import {
    Monitor,
    Users,
    Activity,
    Calendar,
    Download,
    Search,
    Clock,
    Play,
    Pause,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { resolveMachineName } from '../../utils/machineUtils';

const Reports = () => {
    const [activeTab, setActiveTab] = useState('machine-summary');
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(false);

    // Data states
    const [machines, setMachines] = useState([]);
    const [users, setUsers] = useState([]);
    const [reportData, setReportData] = useState([]);
    const [selectedId, setSelectedId] = useState('');

    // Load initial metadata
    useEffect(() => {
        const loadMetadata = async () => {
            try {
                const [machinesRes, usersRes] = await Promise.all([
                    getMachines(),
                    getUsers()
                ]);
                setMachines(machinesRes.data || []);
                setUsers(usersRes.data || []);
            } catch (err) {
                console.error("Failed to load metadata", err);
            }
        };
        loadMetadata();
    }, []);

    // Fetch report data when inputs change
    useEffect(() => {
        fetchData();
    }, [activeTab, date, selectedId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            let res;
            if (activeTab === 'machine-summary') {
                res = await getMachineDailyReport(date);
                setReportData(res.data.report || []);
            } else if (activeTab === 'user-summary') {
                res = await getUserDailyReport(date);
                setReportData(res.data.report || []);
            } else if (activeTab === 'machine-detailed' && selectedId) {
                res = await getMachineDetailedReport(selectedId, date);
                setReportData(res.data || []);
            } else if (activeTab === 'user-detailed' && selectedId) {
                res = await getUserDetailedReport(selectedId, date);
                setReportData(res.data || []);
            } else if (activeTab === 'active-monitoring') {
                res = await getActiveWorkMonitoring();
                setReportData(res.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch report data", err);
            setReportData([]);
        } finally {
            setLoading(false);
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds || isNaN(seconds)) return '0s';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m ${s}s`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    };

    const formatTime = (isoString) => {
        if (!isoString) return '--';
        return new Date(isoString).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    };

    const formatMinutesToHHMM = (minutes) => {
        if (!minutes || isNaN(minutes)) return '00:00';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    };

    const handleDownload = async () => {
        try {
            let response;
            let filename;
            if (activeTab === 'machine-summary') {
                response = await downloadMachineReport(date);
                filename = `machine_summary_${date}.csv`;
            } else if (activeTab === 'user-summary') {
                response = await downloadUserReport(date);
                filename = `user_summary_${date}.csv`;
            } else {
                alert("CSV Export is currently available for Summary reports only.");
                return;
            }

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Download failed", err);
        }
    };

    const tabs = [
        { id: 'machine-summary', label: 'Machine Summary', icon: Monitor },
        { id: 'machine-detailed', label: 'Machine Detailed', icon: Search },
        { id: 'user-summary', label: 'User Summary', icon: Users },
        { id: 'user-detailed', label: 'User Detailed', icon: Search },
        { id: 'active-monitoring', label: 'Active Monitoring', icon: Activity },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <h1 className="text-2xl font-bold text-gray-900">Reports Center</h1>
                <div className="flex gap-2">
                    {['machine-summary', 'user-summary'].includes(activeTab) && (
                        <button
                            onClick={handleDownload}
                            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                        >
                            <Download size={18} />
                            <span>Export CSV</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="flex flex-wrap border-b border-gray-200">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => {
                            setActiveTab(tab.id);
                            setSelectedId('');
                            setReportData([]);
                        }}
                        className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
                            ? 'border-blue-600 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        <tab.icon size={16} />
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-white p-4 rounded-lg shadow-sm">
                {activeTab !== 'active-monitoring' && (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</label>
                        <div className="relative">
                            <Calendar className="absolute left-3 top-2.5 text-gray-400" size={18} />
                            <input
                                type="date"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                )}

                {activeTab === 'machine-detailed' && (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Select Machine</label>
                        <select
                            value={selectedId}
                            onChange={(e) => setSelectedId(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">-- Choose Machine --</option>
                            {machines.map(m => (
                                <option key={m.id} value={m.id}>{resolveMachineName(m)}</option>
                            ))}
                        </select>
                    </div>
                )}

                {activeTab === 'user-detailed' && (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Select User</label>
                        <select
                            value={selectedId}
                            onChange={(e) => setSelectedId(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">-- Choose User --</option>
                            {users.map(u => <option key={u.user_id} value={u.user_id}>{u.full_name || u.username}</option>)}
                        </select>
                    </div>
                )}

                <div className="flex items-end">
                    <button
                        onClick={fetchData}
                        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition font-medium w-full sm:w-auto"
                    >
                        Refresh Data
                    </button>
                </div>
            </div>

            {/* Content Container */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-12 text-center text-gray-500">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p>Loading report data...</p>
                    </div>
                ) : reportData.length === 0 ? (
                    <div className="p-12 text-center text-gray-500 italic">
                        No records found for the selected criteria.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-gray-50">
                                {activeTab === 'machine-summary' && (
                                    <tr>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Machine Name</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Category</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Runtime (Active)</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Tasks Run</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Status</th>
                                    </tr>
                                )}
                                {activeTab === 'user-summary' && (
                                    <tr>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">User Name</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Role</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Work Time</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Tasks Worked</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Status</th>
                                    </tr>
                                )}
                                {activeTab === 'machine-detailed' && (
                                    <tr>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Task Title</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Operator</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Start Time</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">End Time</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Expected</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Actual</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Status</th>
                                    </tr>
                                )}
                                {activeTab === 'user-detailed' && (
                                    <tr>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Task Title</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Machine</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Start Time</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">End Time</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Expected</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Actual</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Holds</th>
                                    </tr>
                                )}
                                {activeTab === 'active-monitoring' && (
                                    <tr>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Operator</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Machine</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Task</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Status</th>
                                        <th className="px-6 py-4 text-left font-semibold text-gray-700">Live Runtime</th>
                                    </tr>
                                )}
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {reportData.map((row, idx) => (
                                    <React.Fragment key={idx}>
                                        {activeTab === 'machine-summary' && (
                                            <tr className="hover:bg-gray-50">
                                                <td className="px-6 py-4 font-medium text-gray-900">{row.machine_name}</td>
                                                <td className="px-6 py-4 text-gray-600">{row.category}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono">{formatDuration(row.runtime_seconds)}</td>
                                                <td className="px-6 py-4 text-gray-600">{row.tasks_run_count}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${row.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                        {row.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        )}
                                        {activeTab === 'user-summary' && (
                                            <tr className="hover:bg-gray-50">
                                                <td className="px-6 py-4 font-medium text-gray-900">{row.full_name || row.username}</td>
                                                <td className="px-6 py-4 text-gray-600 capitalize">{row.role}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono">{formatDuration(row.total_work_seconds)}</td>
                                                <td className="px-6 py-4 text-gray-600">{row.tasks_worked_count}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${row.status === 'Present' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                        {row.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        )}
                                        {activeTab === 'machine-detailed' && (
                                            <tr className="hover:bg-gray-50">
                                                <td className="px-6 py-4 font-medium text-gray-900">{row.task_title}</td>
                                                <td className="px-6 py-4 text-gray-600">{row.operator}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono text-xs">{formatTime(row.start_time)}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono text-xs">{formatTime(row.end_time)}</td>
                                                <td className="px-6 py-4 text-gray-500 font-mono">{formatMinutesToHHMM(row.expected_duration_minutes)}</td>
                                                <td className={`px-6 py-4 font-mono font-bold ${row.expected_duration_minutes && (row.runtime_seconds / 60) > row.expected_duration_minutes ? 'text-red-600' : 'text-green-600'}`}>
                                                    {formatDuration(row.runtime_seconds)}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${row.status === 'Running' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                                                        {row.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        )}
                                        {activeTab === 'user-detailed' && (
                                            <tr className="hover:bg-gray-50">
                                                <td className="px-6 py-4 font-medium text-gray-900">{row.task_title}</td>
                                                <td className="px-6 py-4 text-gray-600">{row.machine_name}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono text-xs">{formatTime(row.start_time)}</td>
                                                <td className="px-6 py-4 text-gray-600 font-mono text-xs">{formatTime(row.end_time)}</td>
                                                <td className="px-6 py-4 text-gray-500 font-mono">{formatMinutesToHHMM(row.expected_duration_minutes)}</td>
                                                <td className={`px-6 py-4 font-mono font-bold ${row.expected_duration_minutes && (row.duration_seconds / 60) > row.expected_duration_minutes ? 'text-red-600' : 'text-green-600'}`}>
                                                    {formatDuration(row.duration_seconds)}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <span className="text-xs text-gray-500">{row.holds?.length || 0} holds</span>
                                                        {row.holds?.length > 0 && (
                                                            <div className="text-[10px] text-orange-600 bg-orange-50 p-1 rounded">
                                                                Last: {row.holds[row.holds.length - 1].reason}
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                        {activeTab === 'active-monitoring' && (
                                            <tr className="hover:bg-gray-50">
                                                <td className="px-6 py-4 text-gray-700 font-bold tracking-tight">👤 {row.operator_name || 'Unassigned'}</td>
                                                <td className="px-6 py-4 text-gray-600 font-medium">⚙️ {row.machine_name || 'Handwork'}</td>
                                                <td className="px-6 py-4 font-medium text-gray-900 border-l-4 border-blue-500 pl-4">
                                                    <div className="flex flex-col">
                                                        <span>{row.title}</span>
                                                        <span className="text-[10px] text-gray-400 font-normal">📁 {row.project}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center">
                                                        <div className={`h-2 w-2 rounded-full mr-2 animate-pulse ${row.status === 'in_progress' ? 'bg-green-500' : 'bg-amber-500'}`}></div>
                                                        <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-widest ${row.status === 'in_progress' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
                                                            }`}>
                                                            {row.status === 'in_progress' ? 'RUNNING' : 'ON HOLD'}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col">
                                                        <span className="text-lg font-bold font-mono text-gray-800">{formatDuration(row.duration_seconds)}</span>
                                                        <span className="text-[9px] text-gray-400 italic">Started: {formatTime(row.started_at)}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <div className="text-xs text-gray-400 italic text-right">
                All times are in IST. Reports are generated based on actual task activity logs.
            </div>
        </div>
    );
};

export default Reports;
