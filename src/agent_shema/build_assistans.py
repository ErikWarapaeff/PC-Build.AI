from langchain_core.runnables import Runnable, RunnableConfig

from pydantic import BaseModel, Field
from typing import Dict, List, Any



class CoordinatorAgent:
    """
    Агент-координатор, который управляет взаимодействием между агентами и формирует промпты для выполнения задач.
    """

    def __init__(self, agents: Dict[str, Runnable]):
        """
        Инициализация координатора с доступными агентами.

        Args:
            agents (dict): Словарь агентов с ключами, описывающими их функционал.
        """
        self.runnable = runnable

    def __call__(self, task: str, inputs: Dict[str, Any], state: Dict[str, Any] = None):
        """
        Выполняет задачу, распределяя её между агентами.

        Args:
            task (str): Тип задачи (например, "подбор сборки").
            inputs (dict): Входные данные для выполнения задачи.
            state (dict): Дополнительное состояние, если требуется.

        Returns:
            dict: Результат выполнения задачи.
        """
        state = state or {"messages": []}

        while True:
            # Определяем, какой агент должен быть вызван
            agent_name, prompt = self.formulate_prompt(task, inputs, state)

            if agent_name not in self.agents:
                return {"error": f"Unknown agent: {agent_name}"}

            agent = self.agents[agent_name]

            # Вызов агента с его задачей
            try:
                result = agent.invoke({"messages": state["messages"] + [("user", prompt)]})
            except Exception as e:
                state["messages"].append(("system", f"Error invoking {agent_name}: {str(e)}"))
                break

            # Проверяем результат: должны быть содержательные данные
            if not result or not self.is_valid_response(result):
                state["messages"].append(("user", "Попробуй снова сгенерировать содержательный ответ."))
                continue

            # Добавляем результат в состояние и возвращаем, если задача завершена
            state["messages"].append(("system", result))
            if self.is_task_complete(task, result):
                return {"messages": state["messages"], "result": result}
            
            
            
            
class ToSQLAgent(BaseModel):
    """Transfers work to a specialized agent for SQL query generation and cost calculation."""

    query_type: str = Field(
        description="The type of query, e.g., 'cost calculation' or 'data retrieval'."
    )
    components: Dict[str, Any] = Field(
        description="Details of the components for the assembly, e.g., CPU, GPU, etc."
    )
    request: str = Field(
        description="Any additional information or specific requirements for the SQL query."
    )

    class Config:
        schema_extra = {
            "example": {
                "query_type": "cost calculation",
                "components": {"CPU": "Ryzen 5 5600X", "GPU": "RTX 3060", "RAM": "16GB"},
                "request": "Calculate the cost percentage of each component in the assembly.",
            }
        }
    
        
class ToCompatibilityAgent(BaseModel):
    """Transfers work to a specialized agent for compatibility checks and bottleneck analysis."""

    task_type: str = Field(
        description="The type of compatibility task, e.g., 'game compatibility', 'bottleneck analysis', or 'component compatibility'."
    )
    components: Dict[str, Any] = Field(
        description="Details of the components for compatibility analysis, e.g., motherboard, CPU, GPU, etc."
    )
    request: str = Field(
        description="Any additional information or specific requirements for the compatibility check."
    )

    class Config:
        schema_extra = {
            "example": {
                "task_type": "component compatibility",
                "components": {
                    "motherboard": "MSI B450 TOMAHAWK",
                    "CPU": "Ryzen 7 5800X",
                    "GPU": "RTX 3070",
                    "RAM": "16GB DDR4",
                    "case": "NZXT H510",
                },
                "request": "Check the compatibility of all components for a gaming setup.",
            }
        }


class ToPricingAgent(BaseModel):
    """Transfers work to a specialized agent for price parsing, comparison, and offer generation."""

    task_type: str = Field(
        description="The type of pricing task, e.g., 'price parsing', 'price comparison', or 'offer generation'."
    )
    products: List[str] = Field(
        description="A list of product names or IDs for which prices need to be retrieved or compared."
    )
    request: str = Field(
        description="Any additional information or requirements for the pricing task."
    )

    class Config:
        schema_extra = {
            "example": {
                "task_type": "price comparison",
                "products": ["RTX 3060", "Ryzen 5 5600X", "16GB DDR4 RAM"],
                "request": "Compare prices across three websites and suggest the best deals.",
            }
        }
        
class ToPeripheryAgent(BaseModel):
    """Transfers work to a specialized agent for peripheral selection based on user needs."""

    user_needs: str = Field(
        description="The user's needs for peripherals, e.g., 'gaming', 'graphic design', 'office work', etc."
    )
    additional_info: Dict[str, Any] = Field(
        description="Additional details about the user's setup or preferences, if any."
    )
    request: str = Field(
        description="Any specific requirements or preferences for the peripheral selection."
    )

    class Config:
        schema_extra = {
            "example": {
                "user_needs": "gaming",
                "additional_info": {"budget": "2000 USD", "preferred brands": ["Logitech", "Razer"]},
                "request": "Suggest a gaming mouse, keyboard, and monitor suitable for competitive FPS games.",
            }
        }
        
        

