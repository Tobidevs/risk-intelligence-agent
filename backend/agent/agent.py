from langgraph.graph import END, START, StateGraph

from agent.state import WorkflowState


def build_graph():
    """Build and compile the risk intelligence agent graph."""
    builder = StateGraph(WorkflowState)

    # TODO: add nodes
    # builder.add_node("node_name", node_fn)

    # TODO: add edges
    # builder.add_edge(START, "node_name")
    # builder.add_edge("node_name", END)

    return builder.compile()


graph = build_graph()
