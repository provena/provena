from provena.config.config_class import ProvenaConfig, ProvenaUIOnlyConfig, GithubBootstrapConfig

def load_provena_config_from_file(path: str) -> ProvenaConfig:
    return ProvenaConfig.parse_file(path)


def get_app_config(config_id: str) -> ProvenaConfig:
    try:
        return ProvenaConfig.parse_file(f"{config_id}.json")
    except Exception:
        try:
            return ProvenaConfig.parse_file(f"{config_id.lower()}.json")
        except Exception as e:
            raise e


def get_ui_only_config(config_id: str) -> ProvenaUIOnlyConfig:
    try:
        return ProvenaUIOnlyConfig.parse_file(f"{config_id}-uionly.json")
    except Exception:
        try:
            return ProvenaUIOnlyConfig.parse_file(f"{config_id.lower()}-uionly.json")
        except Exception as e:
            raise e


def get_bootstrap_config(config_id: str) -> GithubBootstrapConfig:
    try:
        return GithubBootstrapConfig.parse_file(f"{config_id}-github.json")
    except Exception:
        try:
            return GithubBootstrapConfig.parse_file(f"{config_id.lower()}-github.json")
        except Exception as e:
            raise e