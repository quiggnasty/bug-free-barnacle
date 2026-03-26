import os
import requests
import json
from flask import Flask, render_template, request, flash
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

GRANT_KEY = os.getenv("JOBTREAD_GRANT_KEY")
ORG_ID = os.getenv("JOBTREAD_ORG_ID")
URL = "https://api.jobtread.com/pave"

def debug_api_response(response, context):
    """Prints detailed API errors to the console for debugging"""
    if response.status_code != 200:
        print(f"\n--- API ERROR IN: {context} ---")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        print("------------------------------\n")
    return response

def fetch_daily_logs(user_id, log_date):
    """Fetches logs for the specific worker in the row"""
    if not user_id or not log_date:
        return [], "N/A"
    
    payload = {
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "dailyLogs": {
                    "$": {
                        "where": {
                            "and": [
                                [["date"], "=", log_date],
                                [["user", "id"], "=", user_id]
                            ]
                        },
                        "size": 100 # Set to max allowed
                    },
                    "nodes": {
                        "id": True,
                        "notes": True,
                        "date": True,
                        "job": { "name": True }
                    }
                }
            }
        }
    }
    try:
        res = requests.post(URL, json=payload)
        if res.status_code != 200:
            debug_api_response(res, f"fetch_daily_logs ({user_id} on {log_date})")
        
        if res.status_code == 200:
            logs = res.json().get("organization", {}).get("dailyLogs", {}).get("nodes", [])
            processed_logs = [{"id": l.get("id"), "notes": l.get("notes", ""), "job_name": l.get("job", {}).get("name", "No Job")} for l in logs]
            return processed_logs, logs[0].get("date", "") if logs else "N/A"
    except Exception as e:
        print(f"Connection Exception in fetch_daily_logs: {e}")
    return [], "N/A"

def fetch_all_day_logs(log_date):
    """Fetches EVERY daily log for the day across the whole company (Max 100)"""
    if not log_date:
        return []
    
    payload = {
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "dailyLogs": {
                    "$": {
                        "where": [["date"], "=", log_date],
                        "size": 100 # FIXED: Changed from 200 to 100
                    },
                    "nodes": {
                        "id": True,
                        "notes": True,
                        "job": { "name": True },
                        "user": { "name": True }
                    }
                }
            }
        }
    }
    try:
        res = requests.post(URL, json=payload)
        if res.status_code != 200:
            debug_api_response(res, f"fetch_all_day_logs ({log_date})")
        
        if res.status_code == 200:
            return res.json().get("organization", {}).get("dailyLogs", {}).get("nodes", [])
    except Exception as e:
        print(f"Connection Exception in fetch_all_day_logs: {e}")
    return []

def fetch_all_day_entries(user_id, date_str):
    """Fetches worker's timeline for the day"""
    if not user_id or not date_str:
        return []

    payload = {
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "timeEntries": {
                    "$": {
                        "where": {
                            "and": [
                                [["user", "id"], "=", user_id],
                                [["startedAt"], ">=", f"{date_str}T00:00:00Z"],
                                [["startedAt"], "<", f"{date_str}T23:59:59Z"]
                            ]
                        },
                        "size": 100 # Max 100
                    },
                    "nodes": {
                        "id": True,
                        "startedAt": True,
                        "minutes": True,
                        "job": {"name": True},
                        "costItem": {"name": True}
                    }
                }
            }
        }
    }
    try:
        res = requests.post(URL, json=payload)
        if res.status_code != 200:
            debug_api_response(res, f"fetch_all_day_entries ({user_id})")
        
        if res.status_code == 200:
            nodes = res.json().get("organization", {}).get("timeEntries", {}).get("nodes", [])
            return [{"id": n.get("id"), "startedAt": n.get("startedAt"), "hours": round(n.get("minutes", 0) / 60, 1), "job_name": n.get("job", {}).get("name", "N/A"), "costItem_name": n.get("costItem", {}).get("name", "N/A")} for n in nodes]
    except Exception as e:
        print(f"Connection Exception in fetch_all_day_entries: {e}")
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    report_data = []
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=7)
    day_logs_cache = {}

    if request.method == "POST":
        start_str = request.form.get("start_date")
        end_str = request.form.get("end_date")
        
        time_payload = {
            "query": {
                "$": {"grantKey": GRANT_KEY},
                "organization": {
                    "$": {"id": ORG_ID},
                    "timeEntries": {
                        "$": {
                            "where": {
                                "and": [
                                    [["costItem", "name"], "=", "Uncategorized Time"],
                                    [["startedAt"], ">=", f"{start_str}T00:00:00Z"],
                                    [["startedAt"], "<", f"{end_str}T23:59:59Z"]
                                ]
                            },
                            "size": 100 # FIXED: Changed from 150 to 100
                        },
                        "nodes": {
                            "id": True,
                            "startedAt": True,
                            "minutes": True,
                            "job": {"name": True},
                            "costItem": {"name": True},
                            "user": {"id": True, "name": True}
                        }
                    }
                }
            }
        }

        try:
            response = requests.post(URL, json=time_payload)
            if response.status_code == 200:
                entries = response.json().get("organization", {}).get("timeEntries", {}).get("nodes", [])
                for entry in entries:
                    user_id = entry.get('user', {}).get('id')
                    user_full_name = entry.get('user', {}).get('name', 'Unknown')
                    date_key = entry.get('startedAt', '')[:10]
                    
                    if not user_id or not date_key:
                        continue

                    first_name = user_full_name.split()[0]
                    logs, log_date = fetch_daily_logs(user_id, date_key)
                    day_timeline = fetch_all_day_entries(user_id, date_key)
                    
                    if date_key not in day_logs_cache:
                        day_logs_cache[date_key] = fetch_all_day_logs(date_key)
                    
                    all_company_logs = day_logs_cache[date_key]
                    mentions = []
                    for cl in all_company_logs:
                        note_text = cl.get("notes") or ""
                        cl_user = cl.get("user", {}).get("name")
                        # Mention search logic
                        if first_name.lower() in note_text.lower() and cl_user != user_full_name:
                            mentions.append({
                                "id": cl.get("id"),
                                "author": cl_user,
                                "job_name": cl.get("job", {}).get("name", "No Job"),
                                "notes": note_text
                            })

                    report_data.append({
                        "id": entry.get("id"),
                        "user_name": user_full_name,
                        "startedAt": entry.get("startedAt"),
                        "hours": round(entry.get("minutes", 0) / 60, 1),
                        "job_name": entry.get("job", {}).get("name", "N/A"),
                        "costItem_name": entry.get("costItem", {}).get("name", "N/A"),
                        "logs": logs,
                        "log_date": log_date,
                        "day_timeline": day_timeline,
                        "other_mentions": mentions
                    })
            else:
                debug_api_response(response, "Main Report Query")
                flash(f"API Error: {response.status_code}. Check terminal.")
        except Exception as e:
            flash(f"Connection Error: {str(e)}")

    return render_template("index.html", report_data=report_data, start=start_dt.date(), end=end_dt.date())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
