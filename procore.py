import requests
import re
from typing import List, Optional, Dict
import os.path


class Procore:
    session = requests.session()

    username: Optional[str] = None
    password: Optional[str] = None

    is_logged_in = False

    def login(self) -> None:
        assert self.username
        assert self.password

        # get token
        res1 = self.session.get('https://login.procore.com')
        res1.raise_for_status()

        csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)" />', res1.text)[1]

        # login
        res2 = self.session.post('https://login.procore.com/sessions', params={
            "utf8": "✓",
            "authenticity_token": csrf_token,
            "session[sso_target_url]": "",
            "session[email]": self.username,
            "session[password]": self.password,
        })
        res2.raise_for_status()

    def get_companies(self) -> List[Dict]:
        res = self.session.get('https://app.procore.com/vapid/companies')
        res.raise_for_status()
        return res.json()
        
    def get_projects(self, company_id: str) -> List[Dict]:
        res = self.session.get('https://app.procore.com/vapid/projects', params={
            'company_id': company_id,
        })
        res.raise_for_status()
        return res.json()

    def get_file_info(self, project_id: str, file_id: str) -> Dict:
        res = self.session.get(f'https://app.procore.com/vapid/files/{file_id}', params={
            'project_id': project_id,
        })
        res.raise_for_status()
        return res.json()

    def get_folder_info(self, project_id: str, folder_id: Optional[str]) -> Dict:
        if folder_id:
            url = f'https://app.procore.com/vapid/folders/{folder_id}'
        else:
            url = 'https://app.procore.com/vapid/folders'

        res = self.session.get(url, params={
            'project_id': project_id,
            'view': 'web_normal',
        })

        res.raise_for_status()
        return res.json()

    # do not use
    def get_tree(self, project_id: str, root_folder_id: Optional[str]) -> Dict:
        print(root_folder_id)
        tree = self.get_folder_info(project_id, root_folder_id)

        for i in range(len(tree['folders'])):
            if tree['folders'][i]['has_children']:
                tree['folders'][i] = self.get_tree(project_id, tree['folders'][i]['id'])

        return tree

    def get_files(self, project_id: str, ext: Optional[str]) -> List[Dict]:
        if ext and not ext.startswith('.'):
            # prepend file extension with '.'
            ext = '.' + ext
        else:
            ext = ''

        ext = ext.lower()

        def _get_file_count() -> int:
            res = self.session.head(f'https://app.procore.com/rest/v0.1/projects/{project_id}/documents', params={
                'filters[is_in_recycle_bin]': False,
                'filters[document_type]': 'file',
                'filters[search]': ext,
            })

            res.raise_for_status()
            total = res.headers.get('total')
            assert total
            return int(total)

        def _get_files(page: int) -> List[Dict]:
            res = self.session.get(f'https://app.procore.com/rest/v0.1/projects/{project_id}/documents', params={
                'page': page,
                'sort': '-document_type_then_created_at',
                'view': 'context_search',
                'filters[is_in_recycle_bin]': False,
                'filters[document_type]': 'file',
                'filters[search]': ext,
            })

            res.raise_for_status()
            data = res.json()
            assert data
            return data

        file_count = _get_file_count()
        files = []

        i = 1
        while len(files) < file_count:
            files.extend(_get_files(i))
            i += 1

        if ext:
            # filter by file extension
            files = [x for x in files if os.path.splitext(x['name'])[1].lower() == ext]
        
        return files

    def get_folders(self, project_id: str) -> List[Dict]:
        def _get_folder_count() -> int:
            res = self.session.head(f'https://app.procore.com/rest/v0.1/projects/{project_id}/documents', params={
                'filters[is_in_recycle_bin]': False,
                'filters[document_type]': 'folder',
            })

            res.raise_for_status()
            total = res.headers.get('total')
            assert total
            return int(total)

        def _get_folders(page: int) -> List[Dict]:
            res = self.session.get(f'https://app.procore.com/rest/v0.1/projects/{project_id}/documents', params={
                'page': page,
                'sort': '-document_type_then_created_at',
                'view': 'context_search',
                'filters[is_in_recycle_bin]': False,
                'filters[document_type]': 'folder',
            })

            res.raise_for_status()
            data = res.json()
            assert data
            return data

        folder_count = _get_folder_count()
        folders = []

        i = 1
        while len(folders) < folder_count:
            folders.extend(_get_folders(i))
            i += 1

        return folders

