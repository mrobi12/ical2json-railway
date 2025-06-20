import json
import requests
import icalendar
from flask import Flask, Response
from urllib.parse import unquote

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
        for component in cal.walk():
            if component.name == "VEVENT":
                events.append({k: str(v) for k, v in component.items()})
        return Response(json.dumps(events, indent=2), mimetype='application/json')
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
