import json
import requests
import icalendar
from flask import Flask, Response, request
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from dateutil.rrule import rrulestr

app = Flask(__name__)

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

        # Parse iCal
        cal = icalendar.Calendar.from_ical(response.content)
        events = []

        # Target date (default to today)
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response("Invalid date format. Use YYYY-MM-DD.", status=400)
        else:
            target_date = datetime.now(timezone.utc).date()

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get('DTSTART').dt
            dtend = component.get('DTEND').dt if component.get('DTEND') else None

            # Handle recurring events
            rrule_raw = component.get('RRULE')
            if rrule_raw:
                # Generate occurrences using rrulestr
                rrule_text = '\n'.join([f"{key}={','.join(value)}" for key, value in rrule_raw.items()])
                rule = rrulestr(rrule_text, dtstart=dtstart)
                occurrences = rule.between(
                    datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
                    datetime.combine(target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
                    inc=True
                )
                if not occurrences:
                    continue  # Skip if not happening on this date
                dtstart = occurrences[0]  # Set to the actual occurrence datetime
            else:
                # Non-repeating event: filter by date
                dt = dtstart.date() if isinstance(dtstart, datetime) else dtstart
                if dt != target_date:
                    continue

            # Convert event fields safely
            event = {}
            for k, v in component.items():
                try:
                    event[k] = v.to_ical().decode()
                except Exception:
                    event[k] = str(v)
            events.append(event)

        return Response(json.dumps(events, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
