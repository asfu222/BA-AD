import json
from pathlib import Path

from rapidfuzz import process, fuzz


class CatalogFilter:
    def __init__(self, game_files_path: Path):
        self.game_files_path = game_files_path
        self.score_cutoff = 85

    def _load_game_files(self) -> dict:
        with open(self.game_files_path, 'r') as f:
            return json.load(f)

    def _get_name_from_url(self, url: str) -> str:
        return Path(url).name

    def _get_name_from_path(self, path: str) -> str:
        return Path(path).name

    def _find_matches(self, pattern: str, choices: dict) -> list:
        pattern = pattern.lower()
        matches = [
            (name, data) 
            for name, data in choices.items() 
            if pattern in name.lower()
        ]

        return matches if matches else [
            (name, data)

            for name, data in choices.items()

            if (
                match := process.extractOne(
                    query=pattern,
                    choices=[name], 
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=self.score_cutoff
                )
            )
        ]

    def filter_files(self, pattern: str) -> dict:
        game_files = self._load_game_files()
        
        asset_choices_android = {
            self._get_name_from_url(asset['url']): asset 
            for asset in game_files.get('AndroidAssetBundles', [])
        }
        asset_choices_ios = {
            self._get_name_from_url(asset['url']): asset 
            for asset in game_files.get('iOSAssetBundles', [])
        }
        
        asset_matches_android = self._find_matches(pattern, asset_choices_android)
        asset_matches_ios = self._find_matches(pattern, asset_choices_ios)
        asset_results_android = [
            {
                'url': data['url'],
                'crc': data['crc'],
                'size': data.get('size', 0),
                'name': name
            }

            for name, data in asset_matches_android
        ]
        asset_results_ios = [
            {
                'url': data['url'],
                'crc': data['crc'],
                'size': data.get('size', 0),
                'name': name
            }

            for name, data in asset_matches_ios
        ]
        table_choices = {
            self._get_name_from_url(table['url']): table
            for table in game_files.get('TableBundles', [])
        }
        
        table_matches = self._find_matches(pattern, table_choices)
        table_results = [
            {
                'url': data['url'],
                'crc': data['crc'],
                'size': data.get('size', 0),
                'name': name
            }
            for name, data in table_matches
        ]

        media_choices = {
            self._get_name_from_path(media['path']): media
            for media in game_files.get('MediaResources', [])
        }
        
        media_matches = self._find_matches(pattern, media_choices)
        media_results = [
            {
                'url': data['url'],
                'path': data['path'],
                'crc': data['crc'],
                'size': data.get('bytes', 0),
                'name': name
            }
            for name, data in media_matches
        ]

        return {
            'AndroidAssetBundles': asset_results_android,
            'iOSAssetBundles': asset_results_ios,
            'TableBundles': table_results, 
            'MediaResources': media_results
        }
        
