import os
import yaml
from dotenv import load_dotenv
from pyprojroot import here

load_dotenv()


class LoadToolsConfig:

    def __init__(self) -> None:
        with open(here("configs/tools_config.yml")) as cfg:
            app_config = yaml.load(cfg, Loader=yaml.FullLoader)

        # Set environment variables
        os.environ['OPENAI_API_KEY'] = os.environ('OPENAI_API_KEY')
        os.environ['TAVILY_API_KEY'] = os.environ('TAVILY_API_KEY')

        # Primary agent
        self.primary_agent_llm = app_config["primary_agent"]["llm"]
        self.primary_agent_llm_temperature = app_config["primary_agent"]["llm_temperature"]

        # Internet Search config
        self.tavily_search_max_results = int(
            app_config["tavily_search_api"]["tavily_search_max_results"])
        
        # Chinook SQL agent configs
        self.components_sqldb_directory = str(here(
            app_config["components_sqlagent_configs"]["components_sqldb_dir"]))
        self.components_sqlagent_llm = app_config["components_sqlagent_configs"]["llm"]
        self.components_sqlagent_llm_temperature = float(
            app_config["components_sqlagent_configs"]["llm_temperature"])

        # Graph configs
        self.thread_id = str(
            app_config["graph_configs"]["thread_id"])
