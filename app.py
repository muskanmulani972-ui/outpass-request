#!/usr/bin/env python
# coding: utf-8

# In[4]:


from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
DB = "outpass.db"

# =====================================================
# DATABASE INITIALIZATION
# =====================================================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # student requests
    c.execute("""
    CREATE TABLE IF NOT EXISTS outpass_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        student_name TEXT,
        reason TEXT,
        request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        approve_date DATETIME,
        reject_date DATETIME,
        remarks TEXT
    );
    """)

    # warden actions day-wise
    c.execute("""
    CREATE TABLE IF NOT EXISTS warden_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        student_id TEXT,
        student_name TEXT,
        action TEXT,
        action_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        remarks TEXT
    );
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# HOME ROUTE
# =====================================================
@app.route("/")
def home():
    return redirect("/request")


# =====================================================
# STUDENT REQUEST FORM
# =====================================================
@app.route("/request", methods=["GET","POST"])
def request_outpass():
    if request.method == "POST":
        student_id = request.form["student_id"]
        student_name = request.form["student_name"]
        reason = request.form["reason"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO outpass_requests (student_id, student_name, reason)
            VALUES (?, ?, ?)
        """, (student_id, student_name, reason))
        conn.commit()
        conn.close()
        return "<h3>Request Submitted Successfully ✔</h3><a href='/request'>Back</a>"

    return render_template_string(STUDENT_PAGE)


# =====================================================
# WARDEN DASHBOARD
# =====================================================
@app.route("/warden")
def warden_dashboard():
    today = date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM outpass_requests WHERE DATE(request_date)=?", (today,))
    rows = c.fetchall()
    conn.close()
    return render_template_string(WARDEN_DASHBOARD, rows=rows, today=today)


# =====================================================
# APPROVE ACTION
# =====================================================
@app.route("/approve/<int:req_id>", methods=["POST"])
def approve(req_id):
    remarks = request.form["remarks"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        UPDATE outpass_requests
        SET status='approved', approve_date=?, remarks=?
        WHERE request_id=?
    """, (now, remarks, req_id))

    c.execute("SELECT student_id, student_name FROM outpass_requests WHERE request_id=?", (req_id,))
    stu = c.fetchone()

    c.execute("""
        INSERT INTO warden_logs (request_id, student_id, student_name, action, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (req_id, stu[0], stu[1], "approved", remarks))

    conn.commit()
    conn.close()
    return redirect("/warden")


# =====================================================
# REJECT ACTION
# =====================================================
@app.route("/reject/<int:req_id>", methods=["POST"])
def reject(req_id):
    remarks = request.form["remarks"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        UPDATE outpass_requests
        SET status='rejected', reject_date=?, remarks=?
        WHERE request_id=?
    """, (now, remarks, req_id))

    c.execute("SELECT student_id, student_name FROM outpass_requests WHERE request_id=?", (req_id,))
    stu = c.fetchone()

    c.execute("""
        INSERT INTO warden_logs (request_id, student_id, student_name, action, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (req_id, stu[0], stu[1], "rejected", remarks))

    conn.commit()
    conn.close()
    return redirect("/warden")


# =====================================================
# DAILY LOG VIEW
# =====================================================
@app.route("/logs")
def logs():
    today = request.args.get("date", date.today().strftime("%Y-%m-%d"))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT request_id, student_id, student_name, action, action_time, remarks
        FROM warden_logs
        WHERE DATE(action_time)=?
        ORDER BY action_time
    """, (today,))
    rows = c.fetchall()
    conn.close()
    return render_template_string(LOGS_PAGE, rows=rows, today=today)


# =====================================================
# RESPONSIVE HTML UI WITH BOOTSTRAP
# =====================================================
STUDENT_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Outpass Request</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-3">
<div class="container">
<h2 class="mb-4">Student Outpass Request</h2>
<form method="POST" class="mb-3">
<div class="mb-3">
<label>ID</label>
<input name="student_id" class="form-control" required>
</div>
<div class="mb-3">
<label>Name</label>
<input name="student_name" class="form-control" required>
</div>
<div class="mb-3">
<label>Reason</label>
<textarea name="reason" class="form-control" required></textarea>
</div>
<button type="submit" class="btn btn-primary">Submit</button>
</form>
<a href='/warden' class="btn btn-secondary">Warden Dashboard</a>
</div>
</body>
</html>
"""

WARDEN_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
<title>Warden Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-3">
<div class="container">
<h2>Warden Dashboard ({{today}})</h2>
<table class="table table-bordered table-striped">
<thead class="table-dark">
<tr>
<th>ID</th><th>Name</th><th>Reason</th><th>Status</th>
<th>Approve Time</th><th>Reject Time</th><th>Remarks</th><th>Action</th>
</tr>
</thead>
<tbody>
{% for r in rows %}
<tr>
<td>{{r[1]}}</td><td>{{r[2]}}</td><td>{{r[3]}}</td><td>{{r[5]}}</td>
<td>{{r[6]}}</td><td>{{r[7]}}</td><td>{{r[8]}}</td>
<td>
<form method="POST" action="/approve/{{r[0]}}" style="display:inline;">
<input name="remarks" placeholder="remarks" class="form-control form-control-sm mb-1">
<button type="submit" class="btn btn-success btn-sm">Approve</button>
</form>
<form method="POST" action="/reject/{{r[0]}}" style="display:inline;">
<input name="remarks" placeholder="remarks" class="form-control form-control-sm mb-1">
<button type="submit" class="btn btn-danger btn-sm">Reject</button>
</form>
</td>
</tr>
{% endfor %}
</tbody>
</table>
<a href="/logs" class="btn btn-info">View Daily Logs</a>
<a href="/request" class="btn btn-secondary">New Request</a>
</div>
</body>
</html>
"""

LOGS_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Warden Logs</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-3">
<div class="container">
<h2>Warden Logs - {{today}}</h2>
<form method="GET" action="/logs" class="mb-3">
<input type="date" name="date" value="{{today}}" class="form-control mb-2">
<button type="submit" class="btn btn-primary mb-3">Show</button>
</form>
<table class="table table-bordered table-striped">
<thead class="table-dark">
<tr>
<th>Action Time</th><th>Student ID</th><th>Name</th><th>Action</th><th>Remarks</th>
</tr>
</thead>
<tbody>
{% for r in rows %}
<tr>
<td>{{r[4]}}</td><td>{{r[1]}}</td><td>{{r[2]}}</td><td>{{r[3]}}</td><td>{{r[5]}}</td>
</tr>
{% endfor %}
</tbody>
</table>
<a href="/warden" class="btn btn-secondary">Back</a>
</div>
</body>
</html>
"""

# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)


# In[ ]:





# In[ ]:




