import React, { useEffect, useState } from "react";
import client from "../api/api";

export default function AdminDashboard() {
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
    <div className="container">
      <h2>Admin Dashboard</h2>
      <h3>Users</h3>
      <pre style={{ maxHeight: 300, overflow: "auto" }}>{JSON.stringify(users, null, 2)}</pre>
      <h3>Tasks</h3>
      <pre style={{ maxHeight: 300, overflow: "auto" }}>{JSON.stringify(tasks, null, 2)}</pre>
    </div>
  );
}
