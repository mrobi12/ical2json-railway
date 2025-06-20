import json
import requests
import icalendar
from flask import Flask, Response, request
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
import recurring_ical_events
from zoneinfo import ZoneInfo  # Python 3.9+

app = Flask(__name__)

brisbane_tz = ZoneInfo("Australia/Brisbane")

@app.route('/<path:url>')
def ical_to_json(url):
    try:
        # Decode URL
        decoded_url = unquote(url)
        if not decoded_url.startswith('http'):
            decoded_url = 'https://' + decoded_url

        # Fetch calendar data
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(decoded_url, headers=headers)
        if response.status_code != 200:
            return Response(f"Failed to fetch calendar: {response.status_code}", status=500)

        # Parse calendar
        cal = icalendar.Calendar.from_ical(response.content)

        # Target date from query, default Brisbane "today"
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response("Invalid date format. Use YYYY-MM-DD.", status=400)
        else:
            # Use Brisbane now date, not UTC
            target_date = datetime.now(brisbane_tz).date()

        # Define day range in Brisbane TZ
        day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=brisbane_tz)
        day_end = day_start + timedelta(days=1)

        # Get expanded recurring events within that Brisbane day range
        events = recurring_ical_events.of(cal).between(day_start, day_end)

        output = []
        for event in events:
            # Convert DTSTART to Brisbane timezone to confirm date
            dtstart = event.get('DTSTART').dt
            if isinstance(dtstart, datetime):
                if dtstart.tzinfo is None:
                    dtstart = dtstart.replace(tzinfo=timezone.utc)
                dtstart_local = dtstart.astimezone(brisbane_tz)
                event_date = dtstart_local.date()
            else:
                event_date = dtstart

            # Double-check event falls on the target date in Brisbane time
            if event_date != target_date:
                continue

            event_data = {}
            for k, v in event.items():
                try:
                    event_data[k] = v.to_ical().decode()
                except Exception:
                    event_data[k] = str(v)
            output.append(event_data)

        return Response(json.dumps(output, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
