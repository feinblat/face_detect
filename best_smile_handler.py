import copy
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Any, Dict, Union

from aiohttp import ClientSession

from azure_api import group_images
from single_image_process import ImageFaceData
from single_image_process import SingleImageProcess

MAX_IDS_IN_GROUPING_REQUEST = 1000


class ImageNotExistException(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{self.path} does not exist or it is not a file'


@dataclass
class HandlerResult:
    data: Any
    path: str


@dataclass
class GroupData:
    best_face: ImageFaceData
    count: int = 1


class ImageDetectResultsHandler:
    MAX_GROUPS_IN_GROUPING_REQUEST = 500

    def __init__(self, session):
        self._session = session
        self._groups = dict()  # type: Dict[str, GroupData]
        self._faces_to_group = dict()
        self._best_faces_data = dict()  # type: Dict[str, ImageFaceData]
        self._faces_count = defaultdict(int)
        self._log = logging.getLogger('ImageDetectResultsHandler')

    def add_result(self, result: Iterable[ImageFaceData]):
        for face in result:
            self._log.debug(f'image data {face}')
            self._faces_to_group[face.face_id] = face

    async def group_images(self):
        faces_to_group = copy.deepcopy(self._faces_to_group)
        groups = await group_images(self._session, [face_id for face_id in faces_to_group])
        self._handle_grouping_result(groups['groups'])
        for member in groups['messyGroup']:
            self._add_members_to_group(None, [member])

    def _handle_grouping_result(self, groups: List[List[str]]):
        for group_members in groups:
            matched_groups = [m for m in group_members if m in self._groups]
            if matched_groups:
                group_id = matched_groups[0]
            else:
                group_id = None
            self._add_members_to_group(group_id, group_members)

    def _add_members_to_group(self, group_id: Union[str, None], members_ids: List[str]):
        best_face = max((self._faces_to_group[m] for m in members_ids if m in self._faces_to_group), key=lambda x: x.ratio)
        if group_id:
            self._groups[group_id].count += len(members_ids) - 1
            if best_face.ratio > self._groups[group_id].best_face.ratio:
                # replace the group id
                self._groups[best_face.face_id] = GroupData(best_face, self._groups[group_id].count)
                self._groups.pop(group_id)
        else:
            self._groups[best_face.face_id] = GroupData(best_face, len(members_ids))

    async def get_most_common_best_smile(self) -> ImageFaceData:
        await self.group_images()
        most_common_group_data = max(self._groups.values(), key=lambda x: x.count)
        self._log.debug(f'most common best {most_common_group_data.best_face.face_id} count {most_common_group_data.count}')
        return most_common_group_data.best_face


class BestSmileHandler:
    def __init__(self, key: str, base_path: str):
        self._key = key
        self._base_path = base_path
        self._log = logging.getLogger('BestSmileHandler')

    def _validate_exists(self, paths: List[str]):
        for p in paths:
            if not os.path.isfile(os.path.join(self._base_path, p)):
                raise ImageNotExistException(p)

    async def handle_request(self, file_names: List[str]) -> HandlerResult:
        self._log.debug(f'processing new request: {file_names}')
        self._validate_exists(file_names)
        async with ClientSession(headers={'Ocp-Apim-Subscription-Key': self._key},
                                 raise_for_status=True) as session:
            results_handler = ImageDetectResultsHandler(session)
            for file_name in file_names:
                result = await SingleImageProcess(os.path.join(self._base_path, file_name), file_name, session).run()
                results_handler.add_result(result)
            most_common_best_smile = await results_handler.get_most_common_best_smile()
            return HandlerResult(data=most_common_best_smile.metadata,
                                 path=most_common_best_smile.image_name)
