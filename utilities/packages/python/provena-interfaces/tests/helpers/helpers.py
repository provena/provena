from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.TestConfig import route_params, RouteParameters


def get_item_subtype_route_params(item_subtype: ItemSubType) -> RouteParameters:
    """Given an item subtype, will source a its RouteParmeters
    Parameters
    ----------
    item_subtype : ItemSubType
        The desired Item subtype to source route parameters for
    Returns
    -------
    RouteParameters
        the routeparametrs for the desired item subtype
    """
    for item_route_params in route_params:
        if item_route_params.subtype == item_subtype:
            return item_route_params

    raise Exception(
        f"Was not able to source route parameters for desired item_subtype = {item_subtype}")


def get_model_example(item_subtype: ItemSubType) -> DomainInfoBase:
    params = get_item_subtype_route_params(item_subtype=item_subtype)
    return params.model_examples.domain_info[0]