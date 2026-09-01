# Clase para subir ficheros a un repositorio GitLab.
from urllib.parse import quote
import requests
from uploaders.base import GitUploader


class GitlabUploader(GitUploader):

    # Función para subir el fichero al repositorio GitLab.
    def upload(self):
        filename = self.get_repo_filename()
        file_content = self.read_file().decode("utf-8")

        encoded_file = quote(filename, safe="")

        headers = {
            "PRIVATE-TOKEN": self.access_token
        }

        base_url = (
            f"{self.repo_url}/api/v4/projects/"
            f"{self.project_id}/repository/files/"
            f"{encoded_file}"
        )

        params = {
            "ref": self.branch
        }

        response = requests.get(
            base_url,
            headers=headers,
            params=params,
            verify=self.verify_ssl
        )

        payload = {
            "branch": self.branch,
            "content": file_content,
            "commit_message": self.commit_message
        }

        if response.status_code == 200:
            response = requests.put(
                base_url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl
            )
        else:
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl
            )

        response.raise_for_status()

        print(
            f"File '{filename}' uploaded successfully to GitLab"
        )