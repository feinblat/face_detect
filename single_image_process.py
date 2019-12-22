from dataclasses import dataclass
import logging
from typing import Iterable

from PIL import Image
from aiohttp import ClientSession

from azure_api import get_smiles_data

LOG = logging.getLogger(name=__name__)


@dataclass
class ImageFaceData:
    image_name: str
    face_id: str
    ratio: float
    metadata: dict

    def __str__(self):
        return f'name={self.image_name} faceId={self.face_id} ration={self.ratio}'


class SingleImageProcess:
    def __init__(self, path: str, file_name: str,  session: ClientSession):
        self._path = path
        self._file_name = file_name
        self._session = session

    def _get_image_size(self) -> int:
        with Image.open(self._path) as img:
            width, height = img.size
            return width * height

    async def run(self) -> Iterable[ImageFaceData]:
        image_size = self._get_image_size()
        return (ImageFaceData(image_name=self._file_name,
                              face_id=smile_data['faceId'],
                              ratio=float(smile_data['faceRectangle']['width'] * smile_data['faceRectangle']['height']) / image_size,
                              metadata=smile_data) for smile_data in await get_smiles_data(self._session, path=self._path))
