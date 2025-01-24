


def build_CoordinatorAgent_runnable(self):
        primary_assistant_tools = [
            TavilySearchResults(max_results=CFG.tavily_search_max_results),
            search_flights,
            lookup_policy,
        ]
        primary_assistant_runnable = AGENT_PROMPTS.primary_assistant_prompt | CFG.llm.bind_tools(
            primary_assistant_tools
            + [
                ToFlightBookingAssistant,
                ToBookCarRentalAssistant,
                ToHotelBookingAssistant,
                ToBookExcursionAssistant,
            ]
        )
        return primary_assistant_tools, primary_assistant_runnable