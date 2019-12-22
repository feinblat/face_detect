import logging
from typing import List

from aiohttp import ClientSession, ClientResponseError

LOG = logging.getLogger('AzureApi')


async def get_smiles_data(session: ClientSession, path: str) -> dict:
    # https://{endpoint}/face/v1.0/detect
    with open(path, 'rb') as img:
        async with session.post('https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect',
                                data=img.read(),
                                headers={'content-type': 'application/octet-stream'}
                                ) as resp:
            try:
                r = await resp.json()
                return r
            except ClientResponseError as e:
                LOG.exception('Error during detect API %s', e)
                raise


async def group_images(session: ClientSession, face_ids: List[str]) -> dict:
    # https://{endpoint}/face/v1.0/group
    async with session.post('https://westcentralus.api.cognitive.microsoft.com/face/v1.0/group',
                            json={"faceIds": face_ids},
                            headers={'content-type': 'application/json'}
                            ) as resp:
        try:
            r = await resp.json()
            return r
        except ClientResponseError as e:
            LOG.exception('Error during group API %s', e)
        raise
