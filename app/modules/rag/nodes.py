from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from .adapters import get_vector_store, get_llm

vector_store = get_vector_store()
llm = get_llm()

@tool(response_format="content_and_artifact")
def retrieve_tool(query: str):
    """Retrieve information related to a query."""
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
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\nContext:\n"
        f"{docs_content}"
    )
    conversation_messages = [message for message in state["messages"] if message.type in ("human", "system") or (message.type == "ai" and not message.tool_calls)]

    prompt = [SystemMessage(content=system_message_content)] + conversation_messages

    response = llm.invoke(prompt)
    return {"messages": [response]}