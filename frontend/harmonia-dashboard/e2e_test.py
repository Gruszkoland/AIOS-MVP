#!/usr/bin/env python3
"""E2E test — wszystkie endpointy Harmonia 369"""
import urllib.request, json, sys, time

B = 'http://localhost:3691'
D = 'http://localhost:3690'
p = 0
f = 0

def get(name, url):
    global p, f
    time.sleep(0.2)
    try:
        r = urllib.request.urlopen(url, timeout=8)
        r.read()
        print(f'  OK  {name:25s} -> {r.status}', flush=True)
        p += 1
    except BaseException as e:
        print(f'  ERR {name:25s} -> {type(e).__name__}', flush=True)
        f += 1

def post(name, url, body):
    global p, f
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={'Content-Type':'application/json'})
        r = urllib.request.urlopen(req, timeout=8)
        r.read()
        print(f'  OK  {name:25s} -> {r.status}', flush=True)
        p += 1
    except BaseException as e:
        print(f'  ERR {name:25s} -> {type(e).__name__}', flush=True)
        f += 1

print('=== E2E Test Harmonia 369 ===', flush=True)

# Dashboard static
get('Dashboard HTML', D)
get('Dashboard app.js', f'{D}/app.js')
get('Dashboard style.css', f'{D}/style.css')

# GET endpoints
get('Health', f'{B}/health')
get('Stats', f'{B}/api/stats')
get('Leads', f'{B}/api/leads')
get('Genesis', f'{B}/api/genesis')
get('Swarm Status', f'{B}/api/swarm/status')
get('Pipeline Status', f'{B}/api/pipeline/status')
get('Feedback Status', f'{B}/api/feedback/status')
get('Feedback Decide', f'{B}/api/feedback/decide')
get('Golden GET', f'{B}/api/golden')
get('Memory Stats', f'{B}/api/memory/stats')
get('Blacklist', f'{B}/api/blacklist')
get('Search Leads', f'{B}/api/leads/search?q=krak')

# POST endpoints
post('Feedback Observe', f'{B}/api/feedback/observe',
     {'prompt':'E2E test','response':'OK','category':'general','latency_ms':50})
post('Golden POST', f'{B}/api/golden',
     {'prompt':'E2E benchmark','golden_response':'Standard answer','category':'general'})
post('Outreach Analyze', f'{B}/api/outreach/analyze', {'lead_id':1})

print(f'\n  === E2E: {p} PASS / {f} FAIL ===', flush=True)
sys.exit(0 if f == 0 else 1)
