from typing import Optional, TypeVar, Type, Union

from smorest_crud import _crud, config_keys

from smorest_crud.access_control.models import AccessControlUser, AccessControlQuery

T = TypeVar("T", bound=AccessControlUser)


def get_for_current_user_or_404(model: Type[T], id_value: Union[str, int], key_attr: str = "extid") -> Optional[T]:
    """
    Get an object by unique column and check if the current user can read it.
    :param model: date base model of the instance
    :param id_value: the id value of the interested instance
    :param key_attr: name of the key attribute for filtering, extid be default
    """
    return model.get_for_user_or_404(_get_current_user(), id_value, key_attr=key_attr)


def query_for_current_user(model: Type[T]) -> AccessControlQuery:
    """
    Get query for the current authorized user using access checks.
    :param model: date base model of the instance
    """
    return model.query.query_for_user(_get_current_user())


def _get_current_user() -> Optional[T]:
    get_user_func = _crud.app.config.get(config_keys["get_user"])
    if not get_user_func:
        return None
    return get_user_func()
