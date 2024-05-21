import networkx as nx
import xml.etree.ElementTree as ET


class AirlineDataset:
    def __init__(self):
        self.dataset_path = "./data/airlines.graphml"
        self.edges = self._get_edges()
        self.n_edges = len(self.edges)
        self.nodes = self._get_nodes()
        self.n_nodes = len(self.nodes)

    def _get_nodes(self) -> list:
        return [node for node in nx.read_graphml(self.dataset_path).nodes(data=True)]

    def _get_edges(self) -> list:
        with open(self.dataset_path, 'r') as file:
            graphml_data = file.read()

        root = ET.fromstring(graphml_data)
        namespace = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
        edges = []

        for edge in root.findall('.//graphml:edge', namespace):
            source = edge.attrib['source']
            target = edge.attrib['target']
            edges.append((source, target))

        return edges
