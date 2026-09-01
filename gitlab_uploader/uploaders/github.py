# Clase para subir ficheros a un repositorio GitHub.
import base64
import requests
from uploaders.base import GitUploader


class GithubUploader(GitUploader):

    # Función para subir el fichero al repositorio GitHub.
    def upload(self):
        filename = self.get_repo_filename()

        content = self.read_file()

        encoded_content = base64.b64encode(
            content
        ).decode("utf-8")

        url = (
            f"{self.repo_url}/repos/"
            f"{self.project_id}/contents/{filename}"
        )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json"
        }

        sha = None

        response = requests.get(
            url,
            headers=headers,
            verify=self.verify_ssl
        )

        if response.status_code == 200:
            sha = response.json()["sha"]

        payload = {
            "message": self.commit_message,
            "content": encoded_content,
            "branch": self.branch
        }

        if sha:
            payload["sha"] = sha

        response = requests.put(
            url,
            headers=headers,
            json=payload,
            verify=self.verify_ssl
        )

        response.raise_for_status()

        print(
            f"File '{filename}' uploaded successfully to GitHub"
        )