# mypy: ignore-errors
import re
from re import Pattern
from typing import Dict, Any, cast

from pydantic.utils import update_not_none
from pydantic.validators import constr_length_validator

"""
The below code is copied verbatim from 
https://gist.githubusercontent.com/yu-ichiro/ded4d704316a3b986b006467557850a4/raw/87eee323ea5db11f27623416f71860ea880e5eed/AnyUri.py
Which is an Apache 2.0 license.
"""


class RFC3986Regex:
    ALPHA: Pattern = r"[a-zA-Z]"
    DIGIT: Pattern = r"[0-9]"
    HEXDIG: Pattern = r"[0-9a-fA-F]"

    DEC_OCTET_1: Pattern = DIGIT  # 0-9
    DEC_OCTET_2: Pattern = rf"[1-9]{DIGIT}"  # 10-99
    DEC_OCTET_3: Pattern = rf"1{DIGIT}{{2}}"  # 100-199
    DEC_OCTET_4: Pattern = rf"2[0-4]{DIGIT}"  # 200-249
    DEC_OCTET_5: Pattern = rf"25[0-5]"  # 250-255
    DEC_OCTET: Pattern = rf"({DEC_OCTET_1}|{DEC_OCTET_2}|{DEC_OCTET_3}|{DEC_OCTET_4}|{DEC_OCTET_5})"
    IPV4ADDRESS: Pattern = rf"{DEC_OCTET}(\.{DEC_OCTET}){{3}}"

    H16: Pattern = rf"{HEXDIG}{{1,4}}"  # 0 ~ ffff
    # least-significant 32 bits of address
    LS32: Pattern = rf"({H16}:{H16}|{IPV4ADDRESS})"
    IPV6ADDRESS_1: Pattern = rf"({H16}:){{6}}{LS32}"
    IPV6ADDRESS_2: Pattern = rf"::({H16}:){{5}}{LS32}"
    IPV6ADDRESS_3: Pattern = rf"({H16})?::({H16}:){{4}}{LS32}"
    IPV6ADDRESS_4: Pattern = rf"({H16}:){{0,1}}({H16})?::({H16}:){{3}}{LS32}"
    IPV6ADDRESS_5: Pattern = rf"({H16}:){{0,2}}({H16})?::({H16}:){{2}}{LS32}"
    IPV6ADDRESS_6: Pattern = rf"({H16}:){{0,3}}({H16})?::{H16}:{LS32}"
    IPV6ADDRESS_7: Pattern = rf"({H16}:){{0,4}}({H16})?::{LS32}"
    IPV6ADDRESS_8: Pattern = rf"({H16}:){{0,5}}({H16})?::{H16}"
    IPV6ADDRESS_9: Pattern = rf"({H16}:){{0,6}}({H16})?::"
    IPV6ADDRESS: Pattern = (
        rf"(?P<ipv6>{IPV6ADDRESS_1}|{IPV6ADDRESS_2}|{IPV6ADDRESS_3}|{IPV6ADDRESS_4}|{IPV6ADDRESS_5}|"
        rf"{IPV6ADDRESS_6}|{IPV6ADDRESS_7}|{IPV6ADDRESS_8}|{IPV6ADDRESS_9})"
    )

    PCT_ENCODED: Pattern = rf"%{HEXDIG}{HEXDIG}"

    GEN_DELIMS: Pattern = rf"[:/?#\\\[\]@]"
    SUB_DELIMS: Pattern = rf"[!\$&'\(\)\*\+\,;=]"
    RESERVED: Pattern = rf"({GEN_DELIMS}|{SUB_DELIMS})"

    UNRESERVED: Pattern = rf"({ALPHA}|{DIGIT}|[\-\._~])"

    SCHEME: Pattern = rf"(?P<scheme>{ALPHA}({ALPHA}|{DIGIT}|[+\-\.])*)"

    USERINFO: Pattern = rf"(?P<user_info>({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|:)*)"

    IPV_FUTURE: Pattern = rf"(?P<ipv_future>v{HEXDIG}+\.({UNRESERVED}|{SUB_DELIMS}|:)+)"
    IP_LITERAL: Pattern = rf"\[(?P<ip_literal>{IPV6ADDRESS}|{IPV_FUTURE})\]"
    REG_NAME: Pattern = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS})*"
    HOST: Pattern = rf"(?P<host>{IP_LITERAL}|(?P<ipv4>{IPV4ADDRESS})|(?P<domain>{REG_NAME}))"

    PORT: Pattern = rf"(?P<port>\d*)"

    AUTHORITY: Pattern = rf"({USERINFO}@)?{HOST}(:{PORT})?"

    PATH_CHAR: Pattern = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|[:@])"
    SEGMENT: Pattern = rf"({PATH_CHAR})*"
    SEGMENT_NZ: Pattern = rf"({PATH_CHAR})+"
    SEGMENT_NZ_NC: Pattern = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|@)+"
    PATH_EMPTY: Pattern = rf""
    PATH_ROOTLESS: Pattern = rf"{SEGMENT_NZ}(/{SEGMENT})*"
    PATH_NO_SCHEME: Pattern = rf"{SEGMENT_NZ_NC}(/{SEGMENT})*"
    PATH_ABSOLUTE: Pattern = rf"/({SEGMENT_NZ}(/{SEGMENT})*)?"
    PATH_ABSOLUTE_EMPTY: Pattern = rf"(/{SEGMENT})*"
    PATH: Pattern = rf"(?P<path>{PATH_ABSOLUTE_EMPTY}|{PATH_ABSOLUTE}|{PATH_NO_SCHEME}|{PATH_ROOTLESS}|{PATH_EMPTY})"

    QUERY: Pattern = rf"({PATH_CHAR}|[/\?])*"
    FRAGMENT: Pattern = rf"({PATH_CHAR}|[/\?])*"

    HIERARCHY_PART: Pattern = (
        rf"(?P<hierarchy>"
        rf"//(?P<authority>{AUTHORITY})(?P<path_host>{PATH_ABSOLUTE_EMPTY})|"
        rf"(?P<path_abs>{PATH_ABSOLUTE})|"
        rf"(?P<path_rootless>{PATH_ROOTLESS})|"
        rf"{PATH_EMPTY})"
    )
    URI: Pattern = (
        rf"{SCHEME}:{HIERARCHY_PART}(?P<query_full>\?(?P<query>{QUERY}))?(?P<fragment_full>#(?P<fragment>{FRAGMENT}))?"
    )

    RELATIVE_PART: Pattern = (
        rf"(?P<relative_part>"
        rf"//(?P<authority>{AUTHORITY})(?P<path_host>{PATH_ABSOLUTE_EMPTY})|"
        rf"(?P<path_abs>{PATH_ABSOLUTE})|"
        rf"(?P<path_no_scheme>{PATH_NO_SCHEME})|"
        rf"{PATH_EMPTY})"
    )
    RELATIVE_REFERENCE: Pattern = (
        rf"{RELATIVE_PART}(?P<query_full>\?(?P<query>{QUERY}))?(?P<fragment_full>#(?P<fragment>{FRAGMENT}))?"
    )

    def __init__(self):
        self._cache = {}

    def __getattribute__(self, item):
        if item in {"_cache"}:
            return super().__getattribute__(item)
        if item not in self._cache:
            value = super().__getattribute__(item)
            self._cache[item] = value if not isinstance(
                value, str) else re.compile(value)
        return self._cache[item]


class _RegexGroupStr(str):
    _parts: Dict[str, str]
    _pattern: Pattern
    _error_msg: str = "doesn't match {pattern}"
    min_length = None
    max_length = None

    def __init__(self, some_str):
        super().__init__()
        res = self._pattern.fullmatch(some_str)
        if not res:
            raise ValueError(self._error_msg.format(
                pattern=repr(self._pattern)))
        self._parts = res.groupdict()

    def _get(self, key):
        return self._parts.get(key)

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(field_schema, minLength=cls.min_length,
                        maxLength=cls.max_length)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: "ModelField", config: "BaseConfig"):
        if isinstance(value, cls):
            return value
        return cls(cast(str, constr_length_validator(value, field, config)))


class AnyUri(_RegexGroupStr):
    _rfc3986 = RFC3986Regex()
    _pattern = _rfc3986.URI
    _error_msg = "invalid uri or missing scheme"

    def __init__(self, url):
        super().__init__(url)

    @property
    def scheme(self):
        return self._get("scheme")

    @property
    def hierarchy(self):
        return self._get("hierarchy")

    @property
    def authority(self):
        return self._get("authority")

    @property
    def user_info(self):
        return self._get("user_info")

    @property
    def host(self):
        return self._get("host")

    @property
    def domain(self):
        return self._get("domain")

    @property
    def ipv4(self):
        return self._get("ipv4")

    @property
    def ip_literal(self):
        return self._get("ip_literal")

    @property
    def ipv6(self):
        return self._get("ipv6")

    @property
    def ipv_future(self):
        return self._get("ipv_future")

    @property
    def port(self):
        return self._get("port")

    @property
    def path(self) -> str:
        return self._parts.get("path_host") or self._parts.get("path_abs") or self._parts.get("path_rootless") or ""

    @property
    def query(self):
        return self._get("query")

    @property
    def query_full(self):
        return self._get("query_full")

    @property
    def fragment(self):
        return self._get("fragment")

    @property
    def fragment_full(self):
        return self._get("fragment_full")
