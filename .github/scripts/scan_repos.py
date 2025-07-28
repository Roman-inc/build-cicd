from datetime import datetime, timedelta
from croniter import croniter
import requests
import yaml
import os

GIT_TOKEN = os.environ['GIT_TOKEN']
REPOS = {
    "NUNET": "Roman-inc/nunet"
}

RAW_FILE = "https://api.github.com/repos/{repo}/contents/.github/cron/schedule.yaml?ref={branch}"
BRANCHES_API = "https://api.github.com/repos/{repo}/branches?per_page={per_page}&page={page}"
TRIGGER_API = "https://api.github.com/repos/Roman-inc/build-cicd/actions/workflows/{workflow}/dispatches"

HEADERS = {
    "Authorization": f'Bearer: {GIT_TOKEN}',
    "Accept": "application/vnd.github.v3.raw"
}

def should_run(cron_expression):
    now = datetime.now()
    prev_time = now - timedelta(hours=4)
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

def scan_repo(repo_key):
    repo = REPOS[repo_key]
    all_inputs = {}
    branches = get_all_branches(repo=repo)

    for branch in branches:
        r = requests.get(RAW_FILE.format(repo=repo, branch=branch), headers=HEADERS)
        if r.status_code != 200:
            continue

        try:
            schedule = yaml.safe_load(r.text)
            for build in schedule.get('build', []):
                cron_exp = build.get('cron')
                if cron_exp and should_run(cron_exp):
                    inputs = {
                        'onefile': build['onefile']
                    }
                    trigger_workflow('build-nunet.yaml', inputs)
                    all_inputs[build['name']] = inputs
        except Exception as e:
            print(f'Error in branch {branch}\n{e}')

    # for input_data in all_inputs:
    #     trigger_workflow('build-nunet.yaml', input_data)

def scan_all_repos():
    scan_repo('NUNET')

scan_all_repos()