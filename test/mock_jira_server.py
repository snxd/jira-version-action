"""
A lightweight mock Jira REST API server for testing the GitHub action
end-to-end without a real Jira instance.

Implements just enough of the Jira v3 API to support:
  - GET  /rest/api/3/project/{key}          (get project)
  - GET  /rest/api/3/project/{id}/versions  (list versions)
  - POST /rest/api/3/version                (create version)
  - PUT  /rest/api/3/version/{id}           (update/release version)
  - DELETE /rest/api/3/version/{id}         (delete version)
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PROJECT_KEY = "TEST"
PROJECT_ID = 10001

# In-memory version store keyed by version id
versions = {}
next_version_id = 10100


class JiraHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, message):
        self._send_json({"errorMessages": [message]}, status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        # GET /rest/api/3/project/{key}
        if self.path.startswith("/rest/api/3/project/"):
            parts = self.path.split("?")[0].rstrip("/").split("/")

            # /rest/api/3/project/{id}/versions
            if len(parts) == 7 and parts[6] == "versions":
                project_id = parts[5]
                project_versions = [v for v in versions.values() if str(v["projectId"]) == project_id]
                self._send_json(project_versions)
                return

            # /rest/api/3/project/{key}
            if len(parts) == 6:
                key = parts[5]
                if key == PROJECT_KEY:
                    self._send_json({"id": str(PROJECT_ID), "key": PROJECT_KEY})
                else:
                    self._send_error(404, f"No project could be found with key '{key}'.")
                return

        self._send_error(404, "Not found")

    def do_POST(self):
        global next_version_id

        # POST /rest/api/3/version
        if self.path.rstrip("/") == "/rest/api/3/version":
            data = self._read_body()
            name = data.get("name", "")

            for v in versions.values():
                if v["name"] == name and v["projectId"] == data.get("projectId"):
                    self._send_error(
                        400,
                        "A version with this name already exists in this project.",
                    )
                    return

            version_id = str(next_version_id)
            next_version_id += 1

            version = {
                "id": version_id,
                "name": name,
                "archived": data.get("archived", False),
                "released": False,
                "projectId": data.get("projectId"),
                "startDate": data.get("startDate"),
            }
            versions[version_id] = version
            self._send_json(version, 201)
            return

        self._send_error(404, "Not found")

    def do_PUT(self):
        # PUT /rest/api/3/version/{id}
        if self.path.startswith("/rest/api/3/version/"):
            version_id = self.path.rstrip("/").split("/")[-1]
            if version_id not in versions:
                self._send_error(404, "Version not found")
                return

            data = self._read_body()
            versions[version_id].update(data)
            self._send_json(versions[version_id])
            return

        self._send_error(404, "Not found")

    def do_DELETE(self):
        # DELETE /rest/api/3/version/{id}
        if self.path.startswith("/rest/api/3/version/"):
            version_id = self.path.rstrip("/").split("/")[-1]
            if version_id not in versions:
                self._send_error(404, "Version not found")
                return

            del versions[version_id]
            self.send_response(204)
            self.end_headers()
            return

        self._send_error(404, "Not found")

    # Suppress request logging to keep CI output clean
    def log_message(self, format, *args):
        print(f"[mock-jira] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description="Mock Jira API server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--project-key", default="TEST")
    args = parser.parse_args()

    global PROJECT_KEY
    PROJECT_KEY = args.project_key

    server = HTTPServer(("0.0.0.0", args.port), JiraHandler)
    print(f"Mock Jira server listening on port {args.port} (project: {PROJECT_KEY})")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
