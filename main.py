from datetime import datetime, timedelta, timezone
from flask import request

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

        # Check for today filter
        today_filter = request.args.get('today', 'false').lower() == 'true'
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('DTSTART').dt
                if isinstance(dtstart, datetime):
                    if today_filter and not (start_of_day <= dtstart < end_of_day):
                        continue  # Skip events not today
                event = {k: str(v) for k, v in component.items()}
                events.append(event)

        return Response(json.dumps(events, indent=2), mimetype='application/json')

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)
