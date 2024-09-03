import os
import yaml

def load_config(config_filename='config.yaml'):
    # Determine the path to the config.yaml relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, config_filename)

    print(f"Loading configuration from {config_path}")


    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    # Recursively replace environment variables in the configuration
    def replace_env_vars(conf):
        if isinstance(conf, dict):
            return {k: replace_env_vars(v) for k, v in conf.items()}
        elif isinstance(conf, list):
            return [replace_env_vars(i) for i in conf]
        elif isinstance(conf, str) and conf.startswith('${') and conf.endswith('}'):
            env_var = conf[2:-1]
            return os.getenv(env_var, '')
        return conf

    return replace_env_vars(config)


config = load_config()

