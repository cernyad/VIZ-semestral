import numpy as np
import networkx as nx

from airline_dataset import AirlineDataset
from fdeb_original import fdeb
from my_fdeb import MyFdeb

import matplotlib.pyplot as plt
import matplotlib.collections as collections


def example_from_repo():
    print("Original example")

    # Setup embedding and graph
    g = nx.karate_club_graph()
    x = np.array(list(nx.spring_layout(g).values()))
    adj = nx.to_scipy_sparse_array(g).tocoo()

    # Extract edges from embedding and adjacency matrix
    edges = np.stack([x[adj.row], x[adj.col]], axis=1)
    # Compute FDEB
    edges_fdeb = fdeb(AirlineDataset("./data/airlines.graphml").transform_edges())
    #print(x)
    #print(adj)
    #print(edges_fdeb)

    print("\n")
    print("My example")

    airline_dataset = AirlineDataset("./data/airlines.graphml")
    #print(airline_dataset.edges)
    #print(airline_dataset.nodes)
    edges_fdeb_my = MyFdeb().my_fdeb(airline_dataset.transform_edges())
    #print(edges_fdeb_my)

    #assert np.array_equal(edges_fdeb_my, edges_fdeb) == True

    counter = 0
    for i in range(airline_dataset.n_edges):
        for j in range(10):
            if any(edges_fdeb_my[i, j, k] != edges_fdeb[i, j, k] for k in range(edges_fdeb.shape[2])):
                counter += 1
                print(f"Mismatch #{counter}")
                print(f"Theirs: {edges_fdeb[i, j, :]}")
                print(f"My: {edges_fdeb_my[i, j, :]}")
                print("\n")


if __name__ == "__main__":
    example_from_repo()