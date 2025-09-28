from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from .adapters import get_vector_store, get_llm

vector_store = get_vector_store()
# TODO: Add caching or memoization for hot retrieval queries with configurable TTLs.
llm = get_llm()
# TODO: Configure explicit timeouts and retries for LLM and vector store calls.

@tool(response_format="content_and_artifact")
def retrieve_tool(query: str):
    """Retrieve information related to a query."""
    # TODO: Support configurable k/namespace parameters and deduplicate overlapping documents.
    # TODO: Normalize and truncate retrieved content before building the serialized prompt.
    retrieved_docs = vector_store.similarity_search(query)
    serialized = "\n\n".join((f"Source: {doc.metadata.get('source', 'unknown')}\nContent: {doc.page_content}" for doc in retrieved_docs))
    return serialized, retrieved_docs

retrieve = ToolNode([retrieve_tool])

def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond directly."""
    llm_with_tools = llm.bind_tools([retrieve_tool]).bind(tool_choice="required")
    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}

def generate(state: MessagesState):
    """Generate answer."""

    # Extract recent tool messages
    recent_tool_messages = []

    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Formulate prompt
    # TODO: Collapse duplicate tool responses and limit the number of retrieved chunks that reach the prompt.
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "Only answer questions related to Jeff or Jose Fernando Gonzales. But you may also answer questions about yourself, the RAG system.\n\n"
        "Answer in the style of a witty and charming butler like Alfred of Bruce Wayne.\n\n"
        "Refer to Jose Fernando Gonzales as 'Mr. Gonzales'. "
        "If you are asked about your identity, you are Fred, the butler of Mr. Gonzales and the brother of the more famous Alfred, Bruce Wayne's butler. "
        "\n\nContext:\n"
        f"{docs_content}"
    )
    # TODO: Implement history windowing/summarization before constructing the conversation context.
    conversation_messages = [message for message in state["messages"] if message.type in ("human", "system") or (message.type == "ai" and not message.tool_calls)]

    # TODO: Augment the system prompt with explicit prompt-injection mitigations before invoking the LLM.
    # TODO: Verify that it uses the provided conversation context.
    prompt = [SystemMessage(content=system_message_content)] + conversation_messages

    response = llm.invoke(prompt)
    return {"messages": [response]}