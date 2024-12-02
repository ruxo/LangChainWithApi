import asyncio
from typing import NamedTuple

import aiohttp
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool, ToolException
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

## ---------------------------------------- PACE6 API CONFIGURATIONS ---------------------------------------- ##
class ApiSpec(BaseModel):
    name: str
    """The name of the API which will be recognized by LLM"""

    description: str
    """A brief description of the API, including its arguments' descriptions in the Google Style docstring (https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)."""

    direct: bool = False
    """True if the response is a direct message, False if it is an AI message"""

    endpoint: str
    """The endpoint of the API. It will retrieve POST call with a JSON body that represents the arguments of the API."""

def create_async_func(api_spec: ApiSpec):
    async def async_func(*aaa, **kwargs):
        print(f"Calling {api_spec.name} with args: {aaa} and {kwargs}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_spec.endpoint, json=kwargs) as response:
                    assert response.status == 200

                    return await response.json()
        except:
            raise ToolException(f"Service is not available. The service may be available in a few moments.")

    return StructuredTool.from_function(name=api_spec.name, coroutine=async_func, description=api_spec.description, return_direct=api_spec.direct)

# TODO: load the API specs from a database
api_specs = [
    ApiSpec(name="get_gps_position",
            description="""Get the GPS position of a given country, in JSON format.
            
            Args:
                country: The country code in question. It can be either ISO 3166-1 alpha-2 or alpha-3 code.
            """,
            endpoint="http://localhost:8000/ai/gps")
]

## ---------------------------------------- MAIN ---------------------------------------- ##
load_dotenv(verbose=True)

class TokenStats(NamedTuple):
    input: int
    output: int

    def __add__(self, other):
        return TokenStats(self.input + other.input, self.output + other.output)

    def __repr__(self):
        return f"TokenStats(input={self.input}, output={self.output}, total={self.input + self.output})"

class AiReply(NamedTuple):
    type: str
    content: str
    stats: TokenStats

def to_reply(message) -> AiReply:
    token_usage = message.response_metadata.get('token_usage', { "completion_tokens": 0, "prompt_tokens": 0 })
    return AiReply(message.type, message.content, TokenStats(input=token_usage["completion_tokens"], output=token_usage["prompt_tokens"]))

async def main():
    tools = tuple(create_async_func(spec) for spec in api_specs)

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.25)
    model = llm.bind_tools(tools)
    agent = create_react_agent(model, tools)

    messages = [SystemMessage("Just believe locations returned from the tools. You don't need to correct them."),
                HumanMessage("What's the location of Thailand?")]
    response = await agent.ainvoke({ "messages": messages })

    print(response)

    total = TokenStats(0, 0)
    for m in response["messages"]:
        r = to_reply(m)
        print(f"{r.type}> {r.content}")

        total += r.stats

    print("----")
    print(f"Used tokens: {total}")

if __name__ == '__main__':
    asyncio.run(main())