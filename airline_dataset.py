import networkx as nx
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
        def convert_format(node_data):
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
                'name': name,
                'latitude': latitude,
                'longitude': longitude
            }

        graph = nx.read_graphml(self.dataset_path)
        nodes = []

        for node, data in graph.nodes(data=True):
            if 'tooltip' in data:
                formatted_node = convert_format(data)
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
            source = edge.attrib['source']
            target = edge.attrib['target']
            edges.append((source, target))

        return edges

if __name__ == '__main__':
    dataset = AirlineDataset("data/airlines.graphml")
    print(dataset.nodes[:10])
    print(dataset.edges[:10])
