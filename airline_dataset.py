import networkx as nx
import numpy as np

import xml.etree.ElementTree as ET
import re


class AirlineDataset:
    def __init__(self, path):
        self.dataset_path = path
        self.edges = self._get_edges()
        self.n_edges = len(self.edges)
        self.nodes = self._get_nodes()
        self.n_nodes = len(self.nodes)

    def _get_nodes(self) -> list:
        def convert_format(index, node_data):
            tooltip = node_data['tooltip']

            # Extracting the name, longitude, and latitude using regex
            name_match = re.search(r'([A-Z]+)\(lngx', tooltip)
            coord_match = re.search(r'lngx=([-+]?\d*\.\d+|\d+),laty=([-+]?\d*\.\d+|\d+)', tooltip)

            if name_match and coord_match:
                name = name_match.group(1)
                longitude = float(coord_match.group(1))
                latitude = float(coord_match.group(2))
            else:
                raise ValueError("Invalid format for tooltip")

            return {
                'edges' : [],
                'index' : index,
                'name': name,
                'latitude': latitude,
                'longitude': longitude
            }

        graph = nx.read_graphml(self.dataset_path)
        nodes = []

        for node, data in graph.nodes(data=True):
            if 'tooltip' in data:
                formatted_node = convert_format(int(node), data)
                nodes.append(formatted_node)
            else:
                raise ValueError(f"Node {node} does not contain 'tooltip' attribute")

        return nodes

    def _get_edges(self) -> list:
        with open(self.dataset_path, 'r') as file:
            graphml_data = file.read()

        root = ET.fromstring(graphml_data)
        namespace = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
        edges = []

        for edge in root.findall('.//graphml:edge', namespace):
            source = int(edge.attrib['source'])
            target = int(edge.attrib['target'])
            edges.append((source, target))

        return edges

    def transform_edges(self) -> np.ndarray:
        transformed_edges = np.zeros((self.n_edges, 2, 2))

        for idx, (from_edge, to_edge) in enumerate(self.edges):
            from_coords = np.array([self.nodes[from_edge][1]["x"], self.nodes[from_edge][1]["y"]])
            to_coords = np.array([self.nodes[to_edge][1]["x"], self.nodes[to_edge][1]["y"]])
            transformed_edges[idx, 0, :] = from_coords
            transformed_edges[idx, 1, :] = to_coords

        return transformed_edges

if __name__ == '__main__':
    dataset = AirlineDataset("data/airlines.graphml")
    print(dataset.nodes[:10])
    print(dataset.edges[:10])
