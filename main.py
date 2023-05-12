import json
import os
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Suppress a specific warning related to not using SSL verify
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made to host")


token = os.getenv("API_TOKEN_GITHUB")

payload = {}
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {token}'
}

def get_repository_list():
    http_response = requests.get("https://ow-gryphon.github.io/grypi/", verify=False)
    if http_response.status_code != 200:
        raise RuntimeError(f"Status code: {http_response.status_code}\n{http_response.text}")

    soup = BeautifulSoup(http_response.text, features="html.parser")
    cards = soup.findAll("a", **{"class": "card"})
    return list(map(lambda a: a['href'][:-1], cards))


def get_repository_data(repo_name):
    url = f"https://api.github.com/repos/ow-gryphon/{repo_name}/traffic/clones"
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    if response.status_code != 200:
        print(f"Failed to get repo information for {repo_name}")
        raise RuntimeError(f"Status code: {response.status_code}\n{response.text}")

    return json.loads(response.text)


def write_data(data, path):
    data.to_csv(path, header=True, index=False)


repositories = get_repository_list()
repositories.append("gryphon")

for repo in repositories:
    repo_data = Path.cwd() / "data" / f"{repo}.csv"
    try:
        clones = get_repository_data(repo)["clones"]
    except:
        continue
    df = pd.DataFrame(clones)
    print(f"{repo}: {df}")

    if df.shape[0] == 0:
        continue

    df['timestamp'] = df['timestamp'].map(lambda x: pd.Timestamp(x).date())
    
    # if len(df) != 14:
    #     days = pd.date_range(end=pd.Timestamp.now().date() - pd.Timedelta("1D"), periods=14)
    #     days = pd.DataFrame(dict(timestamp=days))
    #     days.timestamp = days.timestamp.map(lambda x: pd.Timestamp(x).date())
    #     days = days.set_index("timestamp")
    #     df = days.join(df)

    try:
        existing = pd.read_csv(repo_data)
        existing['timestamp'] = existing['timestamp'].map(lambda x: pd.Timestamp(x).date())
    except FileNotFoundError:
        print(f"Path does not exist yet {repo_data}")
        write_data(df.dropna(), repo_data)
        continue

    final_df = (
        pd.concat([existing, df])
            .dropna()
            .reset_index(drop=True)
            .drop_duplicates(subset=['timestamp'], keep='last')
            .sort_values("timestamp")
    )

    write_data(final_df, repo_data)
