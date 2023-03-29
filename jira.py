import argparse
import json
import sys
import time
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class JiraConfig:
    host: str
    email: str
    api_token: str


# Retrieve the id of a project with its key
def jira_version_get_project_id(config, project_key):
    response = requests.get(
        url=f"https://{config.host}/rest/api/3/project/{project_key}",
        auth=(config.email, config.api_token),
        headers={"Content-Type": "application/json"},
        params={"properties": "id"},
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err.response.text)
        raise

    response_json = response.json()
    if "id" in response_json:
        return int(response_json["id"])

    return None


# Get a project version
def jira_version_get(config, project_id, version):
    # Missing key errors can also be caused by missing user permissions
    response = requests.get(
        url=f"https://{config.host}/rest/api/3/project/{project_id}/versions",
        auth=(config.email, config.api_token),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err.response.text)
        raise

    for item in response.json():
        if item["name"] == version:
            return item

    return None


# Add a project version
def jira_version_add(config, project_id, version):
    params = {
        "name": version,
        "archived": False,
        "projectId": project_id,
        "startDate": time.strftime("%Y-%m-%d"),
    }
    print(params)
    response = requests.post(
        url=f"https://{config.host}/rest/api/3/version",
        auth=(config.email, config.api_token),
        headers={"Content-Type": "application/json"},
        data=json.dumps(params),
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if "already exists" in err.response.text:
            return None
        print(err.response.text)
        raise

    return response.json()


# Delete a project version
def jira_version_delete(config, version):
    response = requests.delete(
        url=f"https://{config.host}/rest/api/3/version/{version['id']}",
        auth=(config.email, config.api_token),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err.response.text)
        raise


# Release an existing project version
def jira_version_release(config, version):
    version["released"] = True

    # Can't have startDate and userStartDate
    if "startDate" in version and "userStartDate" in version:
        del version["startDate"]

    # Can't have releaseDate and userReleaseDate
    if "userReleaseDate" in version:
        version["userReleaseDate"] = time.strftime("%d/%b/%Y")
    else:
        version["releaseDate"] = time.strftime("%Y-%m-%d")

    response = requests.put(
        url=f"https://{config.host}/rest/api/3/version/{version['id']}",
        auth=(config.email, config.api_token),
        headers={"Content-Type": "application/json"},
        data=json.dumps(version),
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err.response.text)
        raise

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Jira releases")
    parser.add_argument("--email", help="E-mail address", action="store", required=True)
    parser.add_argument("--api_token", help="Api token", action="store", required=True)
    parser.add_argument("--project_key", help="Project key", action="store", required=True)
    parser.add_argument("--host", help="Jira hostname", action="store", required=True)
    parser.add_argument("--version", help="Version name", action="store", required=True)
    parser.add_argument("--release", help="Release", action="store_true", required=False)
    parser.add_argument("--delete", help="Delete", action="store_true", required=False)
    args, _ = parser.parse_known_args()

    config = JiraConfig(host=args.host, email=args.email, api_token=args.api_token)

    project_id = jira_version_get_project_id(
        config=config,
        project_key=args.project_key,
    )
    if not project_id:
        raise RuntimeError("Project does not exist")

    version = jira_version_get(
        config=config,
        project_id=project_id,
        version=args.version,
    )
    if not version:
        print("Version does not exist")

    if args.delete:
        if version:
            print("Deleting version")
            jira_version_delete(
                config=config,
                version=version,
            )
    else:
        if not version:
            print("Creating version")
            version = jira_version_add(
                config=config,
                project_id=project_id,
                version=args.version,
            )
        else:
            print("Version already exists")

        if args.release:
            print("Releasing version")
            if version["released"]:
                print("Version already released")
            else:
                jira_version_release(
                    config=config,
                    version=version,
                )


if __name__ == "__main__":
    sys.exit(main())
