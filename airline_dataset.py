import networkx as nx
import numpy as np

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
            edges.append((int(source), int(target)))

        return edges

    def transform_edges(self) -> np.ndarray:
        transformed_edges = np.zeros((self.n_edges, 2, 2))

        for idx, (from_edge, to_edge) in enumerate(self.edges):
            from_coords = np.array([self.nodes[from_edge][1]["x"], self.nodes[from_edge][1]["y"]])
            to_coords = np.array([self.nodes[to_edge][1]["x"], self.nodes[to_edge][1]["y"]])
            transformed_edges[idx, 0, :] = from_coords
            transformed_edges[idx, 1, :] = to_coords

        return transformed_edges
