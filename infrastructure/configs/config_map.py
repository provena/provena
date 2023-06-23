from typing import Dict, Optional, List, Callable
from provena.config.config_class import ProvenaConfig, ProvenaUIOnlyConfig, GithubBootstrapConfig

# ================
# ADD IMPORTS HERE
# ================

# App configs
# add imports here
from configs.template_custom_deployment import config as template_config

# UI Only configs
# if you are deploying UI only configs, import here

# Bootstrap configs
# add imports here
from configs.template_bootstrap import config as template_bootstrap_config

# Types
AppConfigType = Optional[Callable[[], ProvenaConfig]]
UIConfigType = Optional[Callable[[], ProvenaUIOnlyConfig]]
BootstrapConfigType = Optional[Callable[[], GithubBootstrapConfig]]

AppConfigMap = Dict[str, AppConfigType]
UIConfigMap = Dict[str, UIConfigType]
BootstrapConfigMap = Dict[str, BootstrapConfigType]

# ----------
# EDIT BELOW
# ----------

APP_CONFIG_MAP: AppConfigMap = {
    # "EXAMPLE" : template_config
}


UI_CONFIG_MAP: UIConfigMap = {
}


BOOTSTRAP_CONFIG_MAP: BootstrapConfigMap = {
    # "EXAMPLE" : template_bootstrap_config
}


def get_app_config(config_id: str) -> AppConfigType:
    return APP_CONFIG_MAP.get(config_id)


def get_ui_only_config(config_id: str) -> UIConfigType:
    return UI_CONFIG_MAP.get(config_id)


def get_bootstrap_config(config_id: str) -> BootstrapConfigType:
    return BOOTSTRAP_CONFIG_MAP.get(config_id)


all_app_configs: List[str] = list(APP_CONFIG_MAP.keys())
all_ui_configs: List[str] = list(UI_CONFIG_MAP.keys())
all_bootstrap_configs: List[str] = list(BOOTSTRAP_CONFIG_MAP.keys())
