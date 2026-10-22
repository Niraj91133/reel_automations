import requests

url = 'https://api.github.com/repos/Niraj91133/reel_automations/actions/runs'
r = requests.get(url, timeout=15)
if r.status_code == 200:
    runs = r.json().get('workflow_runs', [])
    print(f"Total runs found: {len(runs)}")
    for run in runs[:6]:
        r_id = run.get('id')
        event = run.get('event')
        status = run.get('status')
        conclusion = run.get('conclusion')
        created_at = run.get('created_at')
        print(f"Run {r_id} | Event: {event} | Status: {status} | Conclusion: {conclusion} | Time: {created_at}")
else:
    print('Failed to fetch runs:', r.status_code, r.text[:200])
