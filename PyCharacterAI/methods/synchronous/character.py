import uuid
import json

from typing import List, Dict, Union
from urllib.parse import quote

from ...types import Character, CharacterShort
from ...exceptions import (FetchError, EditError, CreateError, SearchError,
                           ActionError, InvalidArgumentError)
from ...requester import Requester


class CharacterMethods:
    def __init__(self, client, requester: Requester):
        self.__client = client
        self.__requester = requester

    def fetch_characters_by_category(self) -> Dict[str, List[CharacterShort]]:
        request = self.__requester.request(
            url="https://plus.character.ai/chat/curated_categories/characters/",
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            characters_by_category = {}
            raw = request.json().get('characters_by_curated_category', {})

            for category in raw.keys():
                characters_raw = raw.get(category)
                characters = []

                for character_raw in characters_raw:
                    characters.append(CharacterShort(character_raw))
                characters_by_category[category] = characters
            return characters_by_category

        raise FetchError('Cannot fetch characters by category.')

    def fetch_recommended_characters(self) -> List[CharacterShort]:
        request = self.__requester.request(
            url=f'https://neo.character.ai/recommendation/v1/user',
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            characters_raw = request.json().get('characters', [])
            characters = []

            for character_raw in characters_raw:
                characters.append(CharacterShort(character_raw))
            return characters

        raise FetchError('Cannot fetch recommended characters.')

    def fetch_featured_characters(self) -> List[CharacterShort]:
        request = self.__requester.request(
            url='https://plus.character.ai/chat/characters/featured_v2/',
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            characters_raw = request.json().get('characters', [])
            characters = []

            for character_raw in characters_raw:
                characters.append(CharacterShort(character_raw))
            return characters

        raise FetchError('Cannot fetch featured characters.')

    def fetch_similar_characters(self, character_id: str) -> List[CharacterShort]:
        request = self.__requester.request(
            url=f'https://neo.character.ai/recommendation/v1/character/{character_id}',
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            characters_raw = request.json().get('characters', [])
            characters = []

            for character_raw in characters_raw:
                characters.append(CharacterShort(character_raw))
            return characters

        raise FetchError('Cannot fetch similar characters.')

    def fetch_character_info(self, character_id: str) -> Character:
        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/character/info/",
            options={
                "method": 'POST',
                "headers": self.__client.get_headers(),
                "body": json.dumps({"external_id": character_id})
            }
        )

        if request.status_code == 200:
            response = request.json()

            if response.get("status", "") == "NOT_OK":
                error = response.get("error", "")
                raise FetchError(f'Cannot fetch character information. {error}')

            return Character(response['character'])
        raise FetchError('Cannot fetch character information.')

    def search_characters(self, character_name: str) -> List[CharacterShort]:
        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/characters/search/?query={quote(character_name)}",
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            raw_characters = request.json().get('characters', [])
            return [CharacterShort(raw_character) for raw_character in raw_characters]

        raise SearchError('Cannot search for characters.')

    def search_creators(self, creator_name: str) -> List[str]:
        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/creators/search/?query={quote(creator_name)}",
            options={"headers": self.__client.get_headers()}
        )

        if request.status_code == 200:
            raw_creators = request.json().get('creators')
            return [creator['name'] for creator in raw_creators]

        raise SearchError('Cannot search for creators.')
 
    def character_vote(self, character_id: str, vote: Union[bool, None]) -> bool:
        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/character/vote/",
            options={
                "method": 'POST',
                "headers": self.__client.get_headers(),
                "body": json.dumps({"external_id": character_id, "vote": vote})
            }
        )

        if request.status_code == 200:
            if (request.json()).get("status", None) == "OK":
                return True
            return False

        raise ActionError('Cannot vote for character.')

    def create_character(self, name: str, greeting: str, title: str = "", description: str = "",
                               definition: str = "", copyable: bool = False, visibility: str = "private",
                               avatar_rel_path: str = "", default_voice_id: str = "") -> Character:
        if len(name) < 3 or len(name) > 20:
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Name must be at least 3 characters and no more than 20.")

        if len(greeting) < 3 or len(greeting) > 2048:
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Greeting must be at least 3 characters and no more than 2048.")

        visibility = visibility.upper()

        if visibility not in ["UNLISTED", "PUBLIC", "PRIVATE"]:
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Visibility must be \"unlisted\", \"public\" or \"private\"")

        if title and (len(title) < 3 or len(title) > 50):
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Title must be at least 3 characters and no more than 50.")

        if description and len(description) > 500:
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Description must be no more than 500 characters.")

        if definition and len(definition) > 32000:
            raise InvalidArgumentError(f"Cannot create character. "
                                       f"Definition must be no more than 32000 characters.")

        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/character/create/",
            options={
                "method": 'POST',
                "headers": self.__client.get_headers(),
                "body": json.dumps({
                    "avatar_rel_path": avatar_rel_path,
                    "base_img_prompt": "",
                    "categories": [],
                    "copyable": copyable,
                    "default_voice_id": default_voice_id,
                    "definition": definition,
                    "description": description,
                    "greeting": greeting,
                    "identifier": f"id:{str(uuid.uuid4())}",
                    "img_gen_enabled": False,
                    "name": name,
                    "strip_img_prompt_from_msg": False,
                    "title": title,
                    "visibility": visibility,
                    "voice_id": ""
                })
            }
        )

        if request.status_code == 200:
            response = request.json()
            if response.get("status", None) == "OK" and response.get("character", None) is not None:
                return Character(response.get("character"))

            raise CreateError(f"Cannot create character. {response.get('error', '')}")
        raise CreateError(f"Cannot create character.")

    def edit_character(self, character_id: str, name: str, greeting: str, title: str = "", description: str = "",
                             definition: str = "", copyable: bool = False, visibility: str = "private",
                             avatar_rel_path: str = "", default_voice_id: str = "") -> Character:
        if len(name) < 3 or len(name) > 20:
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Name must be at least 3 characters and no more than 20.")

        if len(greeting) < 3 or len(greeting) > 2048:
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Greeting must be at least 3 characters and no more than 2048.")

        visibility = visibility.upper()

        if visibility not in ["UNLISTED", "PUBLIC", "PRIVATE"]:
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Visibility must be \"unlisted\", \"public\" or \"private\"")

        if title and (len(title) < 3 or len(title) > 50):
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Title must be at least 3 characters and no more than 50.")

        if description and len(description) > 500:
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Description must be no more than 500 characters.")

        if definition and len(definition) > 32000:
            raise InvalidArgumentError(f"Cannot edit character. "
                                       f"Definition must be no more than 32000 characters.")

        request = self.__requester.request(
            url=f"https://plus.character.ai/chat/character/update/",
            options={
                "method": 'POST',
                "headers": self.__client.get_headers(),
                "body": json.dumps({
                    "archived": False,
                    "avatar_rel_path": avatar_rel_path,
                    "base_img_prompt": "",
                    "categories": [],
                    "copyable": copyable,
                    "default_voice_id": default_voice_id,
                    "definition": definition,
                    "description": description,
                    "external_id": character_id,
                    "greeting": greeting,
                    "img_gen_enabled": False,
                    "name": name,
                    "strip_img_prompt_from_msg": False,
                    "title": title,
                    "visibility": visibility,
                    "voice_id": ""
                })
            }
        )

        if request.status_code == 200:
            response = request.json()
            if response.get("status", None) == "OK" and response.get("character", None) is not None:
                return Character(response.get("character"))

            raise EditError(f"Cannot edit character. {response.get('error', '')}")
        raise EditError(f"Cannot edit character.")