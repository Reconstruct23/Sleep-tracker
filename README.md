# LifeOS: Sleep Tracker API

## Overview
LifeOS is a Flask-based API designed to track sleep and wake times, calculate hours slept, and store the data in a Notion database. It also supports insights into your sleep patterns.

## Features
- **Log Sleep**:
  - Endpoint: `/log_sleep`
  - Logs the current sleep time into the Notion database.
- **Log Wake**:
  - Endpoint: `/log_wake`
  - Logs the wake time, calculates hours slept, and updates the most recent sleep entry in the Notion database.

## Requirements
- Python 3.8+
- Notion API integration
- Flask
- `python-dotenv` for managing environment variables

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>