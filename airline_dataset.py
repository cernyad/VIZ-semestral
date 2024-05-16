import networkx as nx
import xml.etree.ElementTree as ET


class AirlineDataset:
    def __init__(self):
        self.dataset_path = "./data/airlines.graphml"

    def get_nodes(self) -> list:
        return [node for node in nx.read_graphml(self.dataset_path).nodes(data=True)]

    def get_edges(self) -> list:
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


if __name__ == "__main__":
    airline_dataset = AirlineDataset()
    print(len(airline_dataset.get_nodes()))
    #print(airline_dataset.get_edges())
