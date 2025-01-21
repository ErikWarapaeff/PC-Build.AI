from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains.openai_tools import create_extraction_chain_pydantic
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_core.tools import tool
from src.agents.load_config_tools import LoadToolsConfig

TOOLS_CFG = LoadToolsConfig()


class Table(BaseModel):
    """
    Represents a table in the SQL database.

    Attributes:
        name (str): The name of the table in the SQL database.
    """

    name: str = Field(description="Name of table in SQL database.")


def get_tables(categories: List[Table]) -> List[str]:
    """Maps category names to corresponding SQL table names.

    Args:
        categories (List[Table]): A list of `Table` objects representing different categories.

    Returns:
        List[str]: A list of SQL table names corresponding to the provided categories.
    """
    tables = []
    for category in categories:
        if category.name == "GPU":
            tables.extend(
                [
                    'gpu_full_info',
                    'gpu_hierarchy',
                    'gpu_average_prices'
                ]
            )
        elif category.name == "CPU":
            tables.extend(
                ["cpu", "cpu_merged", "cpu_ratings"])
        else:
            tables.append(category.name)  # Use `category.name` instead of `category`
    return tables



class ComponentsSQLAgent:
    """
    A specialized SQL agent that interacts with the PC_accessories SQL database using an LLM (Large Language Model).

    The agent handles SQL queries by mapping user questions to relevant SQL tables based on categories like "gpu" and "cpu".
    It uses an extraction chain to determine relevant tables based on the question and then
    executes queries against the database using the appropriate tables.

    Attributes:
        sql_agent_llm (ChatOpenAI): The language model used for interpreting and interacting with the database.
        db (SQLDatabase): The SQL database object, representing the Chinook database.
        full_chain (Runnable): A chain of operations that maps user questions to SQL tables and executes queries.

    Methods:
        __init__: Initializes the agent by setting up the LLM, connecting to the SQL database, and creating query chains.

    Args:
        sqldb_directory (str): The directory where the Chinook SQLite database file is located.
        llm (str): The name of the LLM model to use (e.g., "gpt-3.5-turbo").
        llm_temperature (float): The temperature setting for the LLM, controlling the randomness of responses.
    """

    def __init__(self, sqldb_directory: str, llm: str, llm_temerature: float) -> None:
        """Initializes the ComponentsSQLAgent with the LLM and database connection.

        Args:
            sqldb_directory (str): The directory path to the SQLite database file.
            llm (str): The LLM model identifier (e.g., "gpt-3.5-turbo").
            llm_temerature (float): The temperature value for the LLM, determining the randomness of the model's output.
        """
        self.sql_agent_llm = ChatOpenAI(
            model=llm, temperature=llm_temerature)

        self.db = SQLDatabase.from_uri(f"sqlite:///{sqldb_directory}")
        print(self.db.get_usable_table_names())
        category_chain_system = """Return the names of the SQL tables that are relevant to the user question. \
        The tables are:
        gpu_full_info, gpu_hierarchy, gpu_average_prices, cpu, cpu_merged
        
        """
        category_chain = create_extraction_chain_pydantic(
            Table, self.sql_agent_llm, system_message=category_chain_system)
        table_chain = category_chain | get_tables  # noqa
        query_chain = create_sql_query_chain(self.sql_agent_llm, self.db)
        # Convert "question" key to the "input" key expected by current table_chain.
        table_chain = {"input": itemgetter("question")} | table_chain
        # Set table_names_to_use using table_chain.
        self.full_chain = RunnablePassthrough.assign(
            table_names_to_use=table_chain) | query_chain


@tool
def query_components_sqldb(query: str) -> str:
    """Query the PC_accessories SQL Database. Input should be a search query."""
    # Create an instance of ComponentsSQLAgent
    agent = ComponentsSQLAgent(
        sqldb_directory=TOOLS_CFG.components_sqldb_directory,
        llm=TOOLS_CFG.components_sqlagent_llm,
        llm_temerature=TOOLS_CFG.components_sqlagent_llm_temperature
    )

    query = agent.full_chain.invoke({"question": query})

    return agent.db.run(query)