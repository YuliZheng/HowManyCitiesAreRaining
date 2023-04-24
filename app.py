import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess

app = Flask(__name__)


def run_bulk_query_script():
    print("updating data")
    script_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'get_rain_weather_api_bulk_query.py')
    subprocess.run(['python', script_path])


def schedule_bulk_query():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_bulk_query_script, 'cron',
                      minute='55')  # 在每个小时的第55分钟运行
    # scheduler.add_job(run_bulk_query_script, 'interval', seconds=60)

    scheduler.start()


schedule_bulk_query()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/weather-data')
def weather_data():

    def latest_file_in_folder(folder):
        files = [f for f in os.listdir(
            folder) if os.path.isfile(os.path.join(folder, f))]
        files.sort(key=lambda x: os.path.getmtime(
            os.path.join(folder, x)), reverse=True)
        return os.path.join(folder, files[0]) if files else None
    data_folder = 'data'
    latest_file = latest_file_in_folder(data_folder)

    file_timestamp = datetime.strptime(os.path.splitext(
        os.path.basename(latest_file))[0], '%Y%m%d%H%M%S')
    time_difference = datetime.now() - file_timestamp
    print(
        f"Time difference between now and file timestamp: {time_difference}")
    with open(latest_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return jsonify({"data": data, "timestamp": file_timestamp.timestamp()})


if __name__ == '__main__':
    app.run(debug=True)
