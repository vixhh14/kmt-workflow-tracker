import sqlite3
import pandas as pd
# Connect to database
conn = sqlite3.connect('workflow.db')
# View all tasks
tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
print(tasks)
# View all users
users = pd.read_sql_query("SELECT * FROM users", conn)
print(users)
# View task time logs
logs = pd.read_sql_query("SELECT * FROM task_time_logs", conn)
print(logs)
conn.close()