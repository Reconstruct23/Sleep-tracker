from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Helper function to dynamically get Notion credentials
def get_notion_context(context="sleep_tracker"):
    """
    Dynamically retrieve the appropriate Notion token and database ID.
    
    :param context: The context for which the credentials are required.
                    Options: "sleep_tracker" or "lifeos_config".
    :return: A tuple (NOTION_TOKEN, DATABASE_ID).
    """
    if context == "sleep_tracker":
        return os.getenv("NOTION_TOKEN"), os.getenv("DATABASE_ID")
    elif context == "lifeos_config":
        return os.getenv("LIFEOS_NOTION_TOKEN"), os.getenv("LIFEOS_DATABASE_ID")
    else:
        raise ValueError("Invalid context provided. Use 'sleep_tracker' or 'lifeos_config'.")

# Notion API URL
NOTION_URL = f"https://api.notion.com/v1/pages"

# Helper function to send data to Notion
def send_to_notion(data, context="sleep_tracker"):
    NOTION_TOKEN, _ = get_notion_context(context)
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    app.logger.info(f"Sending the following data to Notion:\n{data}")
    response = requests.post(NOTION_URL, headers=headers, json=data)
    app.logger.info(f"Response status code: {response.status_code}")
    app.logger.info(f"Response text: {response.text}")
    return response.status_code, response.text

# Helper function to update existing data in Notion
def update_notion_page(page_id, data, context="sleep_tracker"):
    NOTION_TOKEN, _ = get_notion_context(context)
    update_url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    app.logger.info(f"Updating the following data in Notion:\n{data}")
    response = requests.patch(update_url, headers=headers, json=data)
    app.logger.info(f"Response status code: {response.status_code}")
    app.logger.info(f"Response text: {response.text}")
    return response.status_code, response.text

@app.route("/log_sleep", methods=["POST"])
def log_sleep():
    now = datetime.now(timezone.utc)  # Ensure UTC timezone awareness
    _, DATABASE_ID = get_notion_context("sleep_tracker")
    sleep_data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Default Title Column": {"title": [{"text": {"content": "Sleep Entry"}}]},
            "Sleep Time": {"date": {"start": now.isoformat()}},
            "Date": {"date": {"start": now.date().isoformat()}},
        },
    }
    status, response = send_to_notion(sleep_data, "sleep_tracker")
    if status == 200:
        return jsonify({"message": "Sleep time logged successfully!"}), 200
    else:
        return jsonify({"error": response}), 400

@app.route("/log_wake", methods=["POST"])
def log_wake():
    now = datetime.now(timezone.utc)  # Ensure UTC timezone awareness
    NOTION_TOKEN, DATABASE_ID = get_notion_context("sleep_tracker")
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Fetch the latest sleep time from Notion
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(query_url, headers=headers)
    data = response.json()

    # Find the most recent sleep entry
    sleep_entry = None
    for result in data.get("results", []):
        if "Sleep Time" in result["properties"] and result["properties"]["Sleep Time"]["date"] and not result["properties"].get("Wake Time", {}).get("date"):
            sleep_entry = result
            break  # Assuming the query returns the latest entry first

    if not sleep_entry:
        return jsonify({"error": "No recent sleep entry found to update with wake time."}), 400

    page_id = sleep_entry["id"]
    sleep_time_str = sleep_entry["properties"]["Sleep Time"]["date"]["start"]
    sleep_time_obj = datetime.fromisoformat(sleep_time_str)

    # Ensure both datetime objects are timezone-aware before subtraction
    if sleep_time_obj.tzinfo is None:
        sleep_time_obj = sleep_time_obj.replace(tzinfo=timezone.utc)

    wake_time_obj = now

    # Calculate hours slept
    hours_slept = round((wake_time_obj - sleep_time_obj).total_seconds() / 3600, 2)

    # Update the existing row in Notion
    wake_data = {
        "properties": {
            "Wake Time": {"date": {"start": now.isoformat()}},
            "Hours Slept": {"number": hours_slept},
        },
    }
    status, response = update_notion_page(page_id, wake_data, "sleep_tracker")
    if status == 200:
        return jsonify({"message": f"Wake time logged successfully! You slept {hours_slept} hours."}), 200
    else:
        return jsonify({"error": response}), 400

@app.route("/", methods=["GET"])
def home():
    return {"message": "Server is running. Try /log_sleep or /log_wake for logging."}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
