# Jira Version Action

Create and release Jira versions automatically with this GitHub action.

## Options

| Name        | Type    | Description                             |
|-------------|---------|-----------------------------------------|
| email       | string  | Email address associated with api token |
| api_token   | string  | Jira api token                          |
| host        | string  | Jira project host                       |
| project_key | string  | Project key                             |
| version     | string  | Name of version                         |
| release     | boolean | Release the version                     |
| delete      | boolean | Delete the version                      |

## Usage

*Creating a version*

```yaml
- name: Create version
  uses: snxd/jira-version-action
  with:
    email: ${{ secrets.JIRA_EMAIL }}
    api_token: ${{ secrets.JIRA_API_TOKEN }}
    host: ${{ secrets.JIRA_HOST }}
    project_key: ${{ secrets.JIRA_PROJECT_KEY }}
    version: '1.0.0'
```

*Releasing a version*

```yaml
- name: Release version
  uses: snxd/jira-version-action
  with:
    email: ${{ secrets.JIRA_EMAIL }}
    api_token: ${{ secrets.JIRA_API_TOKEN }}
    host: ${{ secrets.JIRA_HOST }}
    project_key: ${{ secrets.JIRA_PROJECT_KEY }}
    version: '1.0.0'
    release: true
```

*Deleting a version*

```yaml
- name: Delete version
  uses: snxd/jira-version-action
  with:
    email: ${{ secrets.JIRA_EMAIL }}
    api_token: ${{ secrets.JIRA_API_TOKEN }}
    host: ${{ secrets.JIRA_HOST }}
    project_key: ${{ secrets.JIRA_PROJECT_KEY }}
    version: '1.0.0'
    delete: true
```
