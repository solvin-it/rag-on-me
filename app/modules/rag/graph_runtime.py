from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.postgres import PostgresSaver

from ...core.config import settings
from .nodes import query_or_respond, retrieve, generate

def build_graph():
    """Builds the graph for handling user queries."""

    graph = StateGraph(MessagesState)

    graph.add_node(query_or_respond)
    graph.add_node(retrieve)
    graph.add_node(generate)

    graph.add_edge(START, query_or_respond)
    graph.add_conditional_edges("query_or_respond", tools_condition, {END: END, "retrieve": "retrieve"})
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph

def compile_graph():
    saver = PostgresSaver.from_conn_string(settings.get_database_url())
    saver.setup()
    graph = build_graph().compile(checkpointer=saver)
    return graph