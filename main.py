import json
import requests
import icalendar
from flask import Flask, Response, request
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

@app.route('/<path:url>')
def ical_to_json(url):
    try:
        decoded_url = unquote(url)
        if not decoded_url.startswith('http'):
            decoded_url = 'https://' + decoded_url

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(decoded_url, headers=headers)
        if response.status_code != 200:
            return Response(f"Failed to fetch calendar: {response.status_code}", status=500)

        cal = icalendar.Calendar.from_ical(response.content)
        events = []

        # Set up date filtering
        today_filter = request.args.get('today', 'false').lower() == 'true'
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('DTSTART').dt

                # Ensure dtstart is a datetime object
                if isinstance(dtstart, datetime):
                    if today_filter and not (today_start <= dtstart < today_end):
                        continue
                elif isinstance(dtstart, datetime.date):
                    if today_filter and dtstart != now.date():
                        continue

                event = {k: str(v) for k, v in component.items()}
                events.append(event)

        return Response(json.dumps(events, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
