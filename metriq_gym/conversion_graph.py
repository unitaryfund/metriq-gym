from qbraid import ConversionGraph

graph = ConversionGraph()

len(graph.nodes())  # 10
len(graph.edges())  # 25

graph.plot(legend=True)
