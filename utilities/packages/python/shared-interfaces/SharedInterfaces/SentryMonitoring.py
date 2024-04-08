import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from typing import Any, Optional


def init_sentry(
        environment: str,
        release: Optional[str] = None,
        dsn: Optional[str] = None,
) -> Any:
    """
    Initialize Sentry SDK with the given parameters using default configuration for our Provena system.

    Parameters
    ----------
    environment : str
        The environment name (e.g., 'production', 'staging', 'DEV', "DEV:<git_branch>).
    release : str
        The release version of the application.
    dsn : str, optional
        If not provided and the environment variable SENTRY_DSN is not set, the SDK will not send any events.

    Returns
    -------
    Any
        Returns the result of sentry_sdk.init() which is typically None, but can be a Client if one was instantiated as a result of this call.

    """

    return sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        # Other default params we like
        sample_rate=1.0,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        # sending PII "enables certain features of sentry"
        # https://docs.sentry.io/platforms/python/data-management/sensitive-data/#personally-identifiable-information-pii
        send_default_pii=False,
        include_source_context=True,
        include_local_variables=True,
        # list of string prefixes of module names that belong to our app but are probably
        # not considered to be by default so there stack traces are automatically hidden.
        in_app_include=[],
        # display error origin using url as opposed to func. name
        integrations=[
            StarletteIntegration(
                transaction_style="url"
            ),
            FastApiIntegration(
                transaction_style="url"
            ),
        ],
    )
