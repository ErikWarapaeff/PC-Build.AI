import os
import yaml
from dotenv import load_dotenv
from pyprojroot import here

load_dotenv()

with open(here("configs/project_config.yml")) as cfg:
    app_config = yaml.load(cfg, Loader=yaml.FullLoader)


class LoadProjectConfig:
    def __init__(self) -> None:

        # Load langsmith config
        os.environ["LANGCHAIN_API_KEY"] = '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'
        os.environ["LANGCHAIN_TRACING_V2"] = app_config["langsmith"]["tracing"]
        os.environ["LANGCHAIN_PROJECT"] = app_config["langsmith"]["project_name"]

        # Load memory config
        self.memory_dir = here(app_config["memory"]["directory"])
