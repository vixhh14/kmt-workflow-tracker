import React, { useEffect, useState } from "react";
import client from "../api/api"; // Keeping original import for existing logic
import UserApplications from "../components/UserApplications";
import { LayoutDashboard, Users, ClipboardList } from "lucide-react";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("applications");
  const [users, setUsers] = useState([]);
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetchUsers();
    fetchTasks();
  }, []);

  async function fetchUsers() {
    try {
      const res = await client.get("/users/");
      setUsers(res.data);
    } catch (e) {
      setUsers([]);
    }
  }

  async function fetchTasks() {
    try {
      const res = await client.get("/tasks/");
      setTasks(res.data);
    } catch (e) {
      setTasks([]);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("applications")}
            className={`pb-3 px-4 font-medium flex items-center ${activeTab === "applications"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
              }`}
          >
            <Users className="mr-2" size={18} /> User Applications
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 px-4 font-medium flex items-center ${activeTab === "overview"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
              }`}
          >
            <LayoutDashboard className="mr-2" size={18} /> System Overview
          </button>
        </div>

        {/* Content */}
        {activeTab === "applications" && (
          <UserApplications />
        )}

        {activeTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 flex items-center">
                <Users className="mr-2" /> All Users ({users.length})
              </h3>
              <div className="overflow-auto max-h-96">
                <pre className="text-xs">{JSON.stringify(users, null, 2)}</pre>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 flex items-center">
                <ClipboardList className="mr-2" /> All Tasks ({tasks.length})
              </h3>
              <div className="overflow-auto max-h-96">
                <pre className="text-xs">{JSON.stringify(tasks, null, 2)}</pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
