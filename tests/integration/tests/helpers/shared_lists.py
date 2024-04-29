from ProvenaInterfaces.RegistryModels import ItemSubType, IdentifiedResource
from typing import List, Tuple

cleanup_items: List[Tuple[ItemSubType, IdentifiedResource]] = []
cleanup_group_ids: List[str] = []

# list of usernames which should have associations cleared
cleanup_links: List[str] = []
