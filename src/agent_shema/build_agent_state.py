from typing import Annotated, Literal, Optional, List
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


def update_build_history(history: List[dict], new_build: Optional[dict]) -> List[dict]:
    """
    Updates the build history by adding a new build or clearing the history.

    Args:
        history (List[dict]): The current build history.
        new_build (Optional[dict]): If provided, the new build is added to the history.
                                     If `new_build` is None, the history is returned unchanged.

    Returns:
        List[dict]: The updated build history.
    """
    if new_build is None:
        return history
    if new_build == "clear":
        return []  # Clears the build history.
    return history + [new_build]


class PCBuild(TypedDict):
    """
    Represents a single PC component in a build.

    Attributes:
        type (str): The type of the component (e.g., "cpu", "gpu", "memory").
        name (str): The name of the component.
        price (int): The price of the component.
    """
    component: str
    name: str
    price: int
    characteristics: Optional[dict] = None
    bottleneck: Optional[dict] = None
    game_runs: Optional[dict] = None
    


class State(TypedDict):
    """
    Represents the state of the PC building system.

    Attributes:
        build_type (Literal): The type of the build, e.g., "gaming", "office", "workstation".
        budget (int): The total budget for the PC build.
        current_build (List[PCBuild]): The components in the current PC build.
        build_history (List[dict]): A list of previously completed builds.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    build_type: Literal["gaming", "office", "workstation"]
    budget: int
    current_build: Optional[List[PCBuild]] = None
    build_history: Annotated[List[dict], update_build_history]



