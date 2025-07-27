from datetime import datetime, timedelta
from croniter import croniter
import requests
import os

GIT_TOKEN = os.environ['GIT_TOKEN']

BRANCHES_API = "https://https://api.github.com/repos/RomaOnyshkiv/{repo}/branches?per_page={per_page}&page={page}"
TRIGGER_API = "https://api.github.com/repos/RomaOnyshkiv/multi_inf/actions/workflows/{workflow}/dispatches"

HEADERS = {
    "Authorization": f'Bearer: {GIT_TOKEN}',
    "Accept": "application/vnd.github.v3.raw"
}

def should_run(cron_expression):
    now = datetime.now()
    prev_time = now - timedelta(minutes=60)
    next_run = croniter(cron_expression, prev_time).get_next(datetime)
    return prev_time < next_run <= now

def trigger_workflow(workflow_file, inputs):
    data = {
        "ref": "main",
        "inputs": inputs
    }
    response = requests.post(TRIGGER_API.format(workflow=workflow_file), headers=HEADERS, json=data)
    print(f'Status: {response.status_code} - {response.text}')

def get_all_branches(repo):
    all_branches = []
    page = 1
    per_page = 100
    while True:
        response = requests.get(BRANCHES_API.format(repo=repo, per_page=per_page, page=page), headers=HEADERS)
        response.raise_for_status()
        current_branches = response.json()
        all_branches.extend(branch['name'] for branch in current_branches)
        link_header = response.headers.get('Link')
        if link_header and 'rel=next' in link_header:
            page += 1
        else:
            break
    print(f'found {len(all_branches)} in {repo}')
    return all_branches