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

        # 📅 DATE FILTER: ?date=YYYY-MM-DD
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response("Invalid date format. Use YYYY-MM-DD.", status=400)
        else:
            # Default to today
            target_date = datetime.now(timezone.utc).date()

        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('DTSTART').dt

                # Filter events by date (support datetime or date types)
                if isinstance(dtstart, datetime):
                    if dtstart.date() != target_date:
                        continue
                elif isinstance(dtstart, datetime.date):
                    if dtstart != target_date:
                        continue

                event = {k: str(v) for k, v in component.items()}
                events.append(event)

        return Response(json.dumps(events, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
