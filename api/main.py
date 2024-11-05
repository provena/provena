import warnings
from typing import Dict
from fastapi import Depends
from config import get_settings, Config
import pydantic
import sentry_sdk
import uvicorn  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from ProvenaSharedFunctionality.SentryMonitoring import init_sentry
from pydantic.fields import ModelField
from config import base_config, dispatch_cors
from routes.registry import app as RegistryRouter
from routes.registry.admin import general_admin
from routes.registry.check_access import checks

app = FastAPI()
init_sentry(
    dsn=base_config.sentry_dsn if base_config.monitoring_enabled else None,
    environment=base_config.sentry_environment,
    release=base_config.git_commit_id,
)
sentry_sdk.set_tag("API", "registry")
sentry_sdk.set_tag("Environment", base_config.sentry_environment)

# Get CORS middleware established

# Get the desired origins
origin_info = dispatch_cors(stage=base_config.stage,
                            base_domain=base_config.domain_base)

# If it is an origin list
if isinstance(origin_info, list):
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origins=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])
# Otherwise it is an origin regex
else:
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origin_regex=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])

# Access check
app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])

# General admin
app.include_router(
    general_admin.router,
    prefix="/admin",
    tags=['Admin']
)

# Registry component
app.include_router(
    RegistryRouter,
)


@app.get("/", operation_id="root")
async def root(
    config: Config = Depends(get_settings)
) -> Dict[str, str]:
    """
    Function Description
    --------------------

    Demonstration unauthenticated endpoint.


    Returns
    -------
    Json
        Basic message response



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return {"message": "Health check successful."}

"""
==============
PYDANTIC PATCH
==============
"""

# FROM https://github.com/pydantic/pydantic/issues/1270#issuecomment-1209704699
# Explanation: Pydantic (as of 05/09/22) has improper JSON schema/open api generation
# for optional fields - the null type isn't in allowable list. The openAPI spec
# doesn't like multiple types, so instead used the anyOf with a null type to
# enable this optional functionality. (nullable=True is also possible but is not
# going to be supported in upcoming openAPI specs). This below method matches the
# field schema generator method and also the openapi generator method.
# There is a unit test in tests/test_functionality called test_nullable_property
# which asserts the output of this patch.


pydantic_field_type_schema = pydantic.schema.field_type_schema


def patch_pydantic_field_type_schema() -> None:
    """
    This ugly patch fixes the serialization of models containing Optional in them.
    https://github.com/samuelcolvin/pydantic/issues/1270
    """
    warnings.warn("Patching fastapi.applications.get_openapi")
    import fastapi.applications
    from fastapi.openapi.utils import get_openapi
    fastapi.applications.get_openapi = get_openapi

    warnings.warn("Patching pydantic.schema.field_type_schema")

    def field_type_schema(field: ModelField, **kwargs):  # type: ignore
        null_type_schema = {"type": "null", "title": "None"}
        f_schema, definitions, nested_models = pydantic_field_type_schema(
            field, **kwargs)
        if field.allow_none:
            s_type = f_schema.get('type')
            if s_type:
                # Hack to detect whether we are generating for openapi
                # fastapi sets the ref_prefix to '#/components/schemas/'.
                # When using for openapi, swagger does not seem to support an array
                # for type, so use anyOf instead.
                if kwargs.get('ref_prefix') == '#/components/schemas/':
                    f_schema = {'anyOf': [f_schema, null_type_schema]}
                else:
                    if not isinstance(s_type, list):
                        f_schema['type'] = [s_type]
                    f_schema['type'].append("null")
            elif "$ref" in f_schema:
                f_schema["anyOf"] = [
                    {**f_schema},
                    null_type_schema,
                ]
                del f_schema["$ref"]

            elif "allOf" in f_schema:
                f_schema['anyOf'] = f_schema['allOf']
                del f_schema['allOf']
                f_schema['anyOf'].append(null_type_schema)

            elif "anyOf" in f_schema or "oneOf" in f_schema:
                one_or_any = f_schema.get('anyOf') or f_schema.get('oneOf')
                for item in one_or_any:  # type: ignore
                    if item.get('type') == 'null':
                        break
                else:
                    one_or_any.append(null_type_schema)  # type: ignore

        return f_schema, definitions, nested_models

    pydantic.schema.field_type_schema = field_type_schema


patch_pydantic_field_type_schema()

"""
========
HANDLERS
========
"""

# Add lambda function
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
