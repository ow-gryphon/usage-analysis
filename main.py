import json
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

payload = {}
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer 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'
}


def get_repository_list():
    http_response = requests.get("https://ow-gryphon.github.io/grypi/")
    assert http_response.status_code == 200

    soup = BeautifulSoup(http_response.text)
    cards = soup.findAll("a", **{"class": "card"})
    return list(map(lambda a: a['href'][:-1], cards))


def get_repository_data(repo_name):
    url = f"https://api.github.com/repos/ow-gryphon/{repo_name}/traffic/clones"
    response = requests.request("GET", url, headers=headers, data=payload)
    assert response.status_code == 200

    return json.loads(response.text)


repositories = get_repository_list()
repositories.append("gryphon")

for repo in repositories:
    def write_data(data):
        (
            data
                .reset_index()
                .to_csv(repo_data, header=True, index=False)
        )
    repo_data = Path.cwd() / "data" / f"{repo}.csv"
    clones = get_repository_data(repo)["clones"]

    df = pd.DataFrame(clones)

    if not len(df):
        continue

    df.timestamp = df.timestamp.map(lambda x: pd.Timestamp(x).date())
    df = df.set_index("timestamp")

    # if len(df) != 14:
    #     days = pd.date_range(end=pd.Timestamp.now().date() - pd.Timedelta("1D"), periods=14)
    #     days = pd.DataFrame(dict(timestamp=days))
    #     days.timestamp = days.timestamp.map(lambda x: pd.Timestamp(x).date())
    #     days = days.set_index("timestamp")
    #     df = days.join(df)

    try:
        existing = pd.read_csv(repo_data)
        existing.timestamp = existing.timestamp.map(lambda x: pd.Timestamp(x).date())
        existing = existing.set_index("timestamp")
    except FileNotFoundError:
        write_data(df.dropna())
        continue

    final_df = (
        pd.concat([existing, df])
            .dropna()
            .drop_duplicates()
            .sort_values("timestamp")
    )

    print()
    print(repo)
    print(final_df)

    write_data(final_df)
