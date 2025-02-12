import shutil
import pandas as pd
import sqlite3
from typing import Callable
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from agent_shema.build_agent_state import State


def handle_tool_error(state) -> dict:
    """
    Обрабатывает ошибки, форматируя их в сообщение и добавляя в историю чата.

    Эта функция извлекает ошибку из переданного состояния и форматирует её в объект `ToolMessage`,
    который затем добавляется в историю чата. Для прикрепления сообщения об ошибке используются последние вызовы инструментов из состояния.

    Аргументы:
        state (dict): Текущее состояние инструмента, содержащее информацию об ошибке и вызовы инструментов.

    Возвращает:
        dict: Словарь, содержащий список объектов `ToolMessage` с информацией об ошибке.
    """
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Ошибка: {repr(error)}\nПожалуйста, исправьте ваши ошибки.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    """
    Создает объект `ToolNode` с обработкой ошибок через fallback.

    Эта функция создает объект `ToolNode` и настраивает его на использование fallback-функции для обработки ошибок.
    Fallback-функция обрабатывает ошибки, вызывая функцию `handle_tool_error`.

    Аргументы:
        tools (list): Список инструментов, которые будут включены в объект `ToolNode`.

    Возвращает:
        dict: Объект `ToolNode`, настроенный с использованием fallback-обработки ошибок.
    """
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    """
    Выводит текущее состояние и сообщения события с возможным усечением длинных сообщений.

    Эта функция выводит информацию о текущем состоянии диалога и последнем сообщении в событии.
    Если сообщение слишком длинное, оно обрезается до указанной максимальной длины.

    Аргументы:
        event (dict): Событие, содержащее состояние диалога и сообщения.
        _printed (set): Множество идентификаторов сообщений, которые уже были выведены, чтобы избежать дублирования.
        max_length (int, optional): Максимальная длина сообщения для вывода до усечения. По умолчанию 1500.
    """
    current_state = event.get("dialog_state")
    if current_state:
        print("Текущее состояние: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (обрезано)"
            print(msg_repr)
            _printed.add(message.id)


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """
    Создает функцию для перехода в новый этап диалога с указанием состояния и инструмента.

    Аргументы:
        assistant_name (str): Название помощника, который будет использоваться в сообщении.
        new_dialog_state (str): Новое состояние диалога после перехода.

    Возвращает:
        Callable: Функция, которая при вызове с объектом `State` возвращает словарь с инструментом и обновленным состоянием диалога.

    Функция выполняет следующие действия:
        - Извлекает `tool_call_id` из последнего сообщения с первым вызовом инструмента в `State`.
        - Строит сообщение для инструмента, информируя пользователя, что сейчас работает указанный помощник.
        - Обновляет состояние диалога с учетом нового состояния.
        - Сообщение инструмента информирует помощника, что задача не завершена до тех пор, пока не будет успешно вызван подходящий инструмент.
        - Если пользователь изменит свое решение или потребуется помощь по другим задачам, сообщение советует вызвать функцию `CompleteOrEscalate`, чтобы вернуть управление основному помощнику.
    """
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=(
                        f"The {assistant_name} assistant is currently active. Please review the previous conversation "
                        f"between the main assistant and the user. The user's goal has not been completed. "
                        f"Use the provided tools to complete the task. Remember, you are {assistant_name}, and the action "
                        "is not complete until the necessary tool has been successfully invoked. "
                        "If the user changes their mind or requires help with other matters, invoke the CompleteOrEscalate function "
                        "to return control to the main assistant."
                    ),
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node
