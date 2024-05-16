import networkx as nx


class AirlineDataset:
    def __init__(self):
        self.dataset_path = "./data/airlines.graphml"
        self.G = None

    def load_data(self):
        self.G = nx.read_graphml(self.dataset_path)

    def get_data_points(self) -> list:
        return [node for node in self.G.nodes(data=True)]


if __name__ == "__main__":
    airline_dataset = AirlineDataset()
    airline_dataset.load_data()
    print(airline_dataset.get_data_points())
