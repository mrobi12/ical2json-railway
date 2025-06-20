import json
import requests
import icalendar
from flask import Flask, Response, request
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
import recurring_ical_events
from zoneinfo import ZoneInfo

app = Flask(__name__)
brisbane_tz = ZoneInfo("Australia/Brisbane")

@app.route('/<path:url>')
def ical_to_json(url):
    try:
        # Decode and prepare the calendar URL
        decoded_url = unquote(url)
        if not decoded_url.startswith('http'):
            decoded_url = 'https://' + decoded_url

        # Download the .ics file
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(decoded_url, headers=headers)
        if response.status_code != 200:
            return Response(f"Failed to fetch calendar: {response.status_code}", status=500)

        # Parse the calendar
        cal = icalendar.Calendar.from_ical(response.content)

        # Determine the target date (default to today Brisbane time)
        date_str = request.args.get('date')
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = datetime.now(brisbane_tz).date()

        # Get Brisbane-local datetime range for the day
        day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=brisbane_tz)
        day_end = day_start + timedelta(days=1)

        # Expand recurring events
        events = recurring_ical_events.of(cal).between(day_start, day_end)

        output = []
        for event in events:
            item = {}
            for k, v in event.items():
                try:
                    if k in ["DTSTART", "DTEND", "DTSTAMP", "CREATED", "LAST-MODIFIED", "RECURRENCE-ID"]:
                        dt = v.dt
                        if isinstance(dt, datetime):
                            # Convert to Brisbane time
                            dt = dt.astimezone(brisbane_tz)
                            item[k] = dt.isoformat()
                        else:
                            item[k] = str(dt)
                    else:
                        item[k] = v.to_ical().decode()
                except Exception:
                    item[k] = str(v)
            output.append(item)

        return Response(json.dumps(output, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
