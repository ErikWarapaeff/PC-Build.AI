import os
from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import create_engine
from langchain.sql_database import SQLDatabase
from dotenv import load_dotenv
from langchain_core.tools import tool

# Загрузка конфигурации
load_dotenv()

# Инициализация API ключа и модели
os.environ['OPENAI_API_KEY'] = ''
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

# Подключение к базе данных
db_file = "path_to_your_db_file.db"  # Укажите путь к файлу базы данных
engine = create_engine(f"sqlite:///{db_file}")
db = SQLDatabase(engine=engine)

# Создание агента для выполнения SQL запросов
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

@tool
def build_pc_with_budget_and_type(build_type: str = None, budget: float = 150000, max_variants: int = 5, input_prompt: str = None):
    """Собирает ПК в зависимости от типа сборки и бюджета.
    
    Если тип сборки не распознан, LLM предложит подходящий тип сборки.

    Args:
        build_type (str): Тип сборки (например, "игровая", "офисная", "серверная"). Если не указан, спрашиваем у LLM.
        budget (float): Общий бюджет для сборки ПК.
        max_variants (int): Максимальное количество вариантов для каждого компонента.
        input_prompt (str): Исходный промпт для формирования запроса.

    Returns:
        dict: Словарь с компонентами и их вариантами.
    """
    # Список типов сборок
    possible_builds = ["игровая", "офисная", "серверная"]
    
    components_percentages = {
        "игровая": {
            "chipset": 0.4,  # Видеокарта 40% бюджета
            "cpu": 0.3,      # Процессор 30% бюджета
            "ram": 0.2,            # Оперативная память 20% бюджета
            "motherboard": 0.1     # Материнская плата 10% бюджета
        },
        "офисная": {
            "chipset": 0.2,  # Видеокарта 20% бюджета
            "cpu": 0.4,      # Процессор 40% бюджета
            "ram": 0.3,            # Оперативная память 30% бюджета
            "motherboard": 0.1     # Материнская плата 10% бюджета
        },
        "серверная": {
            "cpu": 0.4,      # Процессор 40% бюджета
            "ram": 0.3,            # Оперативная память 30% бюджета
            "motherboard": 0.1,    # Материнская плата 10% бюджета
            "storage": 0.2         # Хранение данных 20% бюджета
        }
    }

    # Получаем процентные соотношения для каждого компонента
    selected_components = components_percentages[build_type]

    # Сборка всех компонентов на основе расчетных цен
    components = []
    for component, percentage in selected_components.items():
        component_budget = budget * percentage
        
        # Формируем запрос для компонента с учетом его стоимости и исходного промпта
        query = f"{input_prompt}. Собери мне 5 уникальных {component} со стоимостью от {component_budget * 0.9} до {component_budget * 1.1}. Укажи все характеристики компонента."
        
        # Выполняем запрос через агент, ограничивая количество вариантов
        result = agent_executor.invoke({"input": query})
        
        # Ограничиваем количество вариантов до max_variants
        limited_result = result[:max_variants]
        
        # Добавляем результат в список компонентов
        components.append({
            "component": component,
            "variants": limited_result,
            "total_budget_allocated": component_budget
        })

    # Выводим информацию о собранных компонентах и вариантах
    print(f"\nТип сборки: {build_type}")
    for component in components:
        print(f"\nКомпонент: {component['component']}")
        print(f"  Бюджет, выделенный на компонент: {component['total_budget_allocated']} руб.")
        for idx, variant in enumerate(component['variants'], 1):
            print(f"  Вариант {idx}: {variant}")
    
    return components


@tool
def check_compatibility(components: list) -> dict:
    """Проверяет совместимость компонентов ПК (например, совместимость процессора с материнской платой, количество ОЗУ и тип корпуса).
    
    Args:
        components (list): Список компонентов для проверки совместимости.

    Returns:
        dict: Словарь с результатами проверок совместимости.
    """
    compatibility_results = {}

    # Инициализация переменных для хранения конкретных компонентов
    cpu = next((comp for comp in components if comp['component'] == 'cpu'), None)
    motherboard = next((comp for comp in components if comp['component'] == 'motherboard'), None)
    ram = next((comp for comp in components if comp['component'] == 'ram'), None)
    case = next((comp for comp in components if comp['component'] == 'case'), None)
    
    # Если процессор и материнская плата найдены, проверяем их совместимость
    if cpu and motherboard:
        query_cpu_motherboard = f"Проверь, совместим ли процессор {cpu['variants'][0]} с материнской платой {motherboard['variants'][0]}."
        compatibility_results['cpu_motherboard'] = agent_executor.invoke({"input": query_cpu_motherboard})

    # Если оперативная память найдена, проверяем её совместимость с максимальным объемом и количеством слотов
    if ram:
        max_memory = ram['variants'][0].get('max_memory', None)  # Максимально допустимый объём памяти для материнской платы
        memory_slots = ram['variants'][0].get('memory_slots', None)  # Количество слотов памяти
        if max_memory and memory_slots:
            query_ram = f"Проверь, соответствует ли количество оперативной памяти {ram['variants'][0]} максимальному объему {max_memory} и количеству слотов памяти {memory_slots}."
            compatibility_results['ram'] = agent_executor.invoke({"input": query_ram})

    # Если корпус и материнская плата найдены, проверяем их совместимость по типу
    if case and motherboard:
        case_type = case['variants'][0].get('type', None)  # Тип корпуса
        motherboard_form_factor = motherboard['variants'][0].get('form_factor', None)  # Форм-фактор материнской платы
        if case_type and motherboard_form_factor:
            query_case_motherboard = f"Проверь, совпадает ли тип корпуса {case_type} с форм-фактором материнской платы {motherboard_form_factor}."
            compatibility_results['case_motherboard'] = agent_executor.invoke({"input": query_case_motherboard})
    
    # Возвращаем результаты проверок совместимости
    return compatibility_results
