import numpy as np

from airline_dataset import AirlineDataset
from tqdm import tqdm


class MyFdeb:
    def __init__(self):
        self.K = 0.1
        self.n_iter = 30
        self.n_iter_reduction = 2 / 3
        self.lr = 0.04
        self.lr_reduction = 0.5
        self.n_cycles = 4
        self.initial_segpoints = 1
        self.segpoint_increase = 2
        self.compat_threshold = 0.5

    def get_edge_compatibility(self, edges: np.ndarray):
        vec = np.array([edge[-1] - edge[0] for edge in edges])
        vec_norm = np.linalg.norm(vec, axis=1, keepdims=True)

        # Angle compatability
        compat_angle = np.abs(np.matmul(vec, np.transpose(vec)) / (np.matmul(vec_norm, np.transpose(vec_norm)) + 1e-8))

        # Length compatibility
        l_avg = (vec_norm + np.transpose(vec_norm)) / 2
        compat_length = []

        for i in range(len(vec_norm)):
            row = []
            for j in range(len(vec_norm)):
                min_val = min(vec_norm[i], vec_norm[j])
                max_val = max(vec_norm[i], vec_norm[j])
                avg_val = l_avg[i][j]
                comp_length = (2 / ((avg_val / (min_val + 1e-8)) + (max_val / (avg_val + 1e-8)) + 1e-8))[0]
                row.append(comp_length)
            compat_length.append(row)

        compat_length = np.array(compat_length)

        # Distance compatibility
        midpoint = (edges[:, 0] + edges[:, -1]) / 2
        midpoint_dist = np.linalg.norm(midpoint[None, :] - midpoint[:, None], axis=-1)
        compat_dist = l_avg / (l_avg + midpoint_dist + 1e-8)

        # Visibility compatibility
        ap = edges[None, ...] - edges[:, None, None, 0]

        # Calculate t
        t = []
        for i in range(len(vec)):
            t_i = []
            for j in range(len(edges)):
                t_ij = []
                for k in range(len(edges[0])):
                    numerator = sum(ap[i][j][k][l] * vec[i][l] for l in range(len(vec[0])))
                    denominator = sum(vec[i][l] ** 2 for l in range(len(vec[0]))) + 1e-8
                    t_ij.append(numerator / denominator)
                t_i.append(t_ij)
            t.append(t_i)
        t = np.array(t)

        # Calculate I
        I = []
        for i in range(len(edges)):
            I_i = []
            for j in range(len(edges)):
                I_ij = []
                for k in range(len(t[i][j])):
                    I_ijk = []
                    for l in range(len(vec[0])):
                        I_ijk.append(edges[i][0][l] + t[i][j][k] * vec[i][l])
                    I_ij.append(I_ijk)
                I_i.append(I_ij)
            I.append(I_i)
        I = np.array(I)

        # Extract i0 and i1 from I
        i0 = []
        i1 = []

        for i in range(len(I)):
            i0_i = []
            i1_i = []
            for j in range(len(I[i])):
                i0_i.append(I[i][j][0])
                i1_i.append(I[i][j][1])
            i0.append(i0_i)
            i1.append(i1_i)

        i0 = np.array(i0)
        i1 = np.array(i1)

        # Calculate the midpoint Im
        Im = []
        for i in range(len(i0)):
            Im_i = []
            for j in range(len(i0[i])):
                Im_ij = [(i0[i][j][k] + i1[i][j][k]) / 2 for k in range(len(i0[i][j]))]
                Im_i.append(Im_ij)
            Im.append(Im_i)

        Im = np.array(Im)

        """
        t = np.sum(ap * vec[:, None, None, :], axis=-1) / (
                np.sum(vec ** 2, axis=-1)[:, None, None] + 1e-8
        )
        I = edges[:, None, 0, None] + t[..., None] * vec[:, None, None, :]
        i0, i1 = I[..., 0, :], I[..., 1, :]
        Im = (i0 + i1) / 2
        """

        denom = np.sqrt(np.sum((i0 - i1) ** 2, axis=-1))
        num = 2 * np.linalg.norm(midpoint[:, None, ...] - Im, axis=-1)
        compat_visibility = np.maximum(0, 1 - num / (denom + 1e-8))
        compat_visibility = np.minimum(compat_visibility, compat_visibility.T)
        compatibility_matrix = compat_angle * compat_length * compat_dist * compat_visibility
        compatibility_matrix = np.where(compatibility_matrix > self.compat_threshold, 1, 0)

        return compatibility_matrix

    def my_fdeb(self, edges):
        # edges = airline_dataset.transform_edges()
        initial_vecs = edges[:, 0] - edges[:, -1]
        initial_edge_lengths = np.linalg.norm(initial_vecs, axis=-1, keepdims=True)
        edge_compatibilities = self.get_edge_compatibility(edges)
        #edge_compatibilities = (edge_compatibilities > self.compat_threshold).astype(np.float32)
        segments = self.initial_segpoints
        lr_val = self.lr
        n_iter_val = self.n_iter

        for cycle in tqdm(range(self.n_cycles)):
            edges = self.subdivide_edges(edges, segments + 2)  # Including endpoints
            segments = int(np.ceil(segments * self.segpoint_increase))

            kp_values = self.K / (initial_edge_lengths * segments + 1e-8)
            kp_values = kp_values[..., None]

            for epoch in range(n_iter_val):
                forces = self.compute_forces(edges, edge_compatibilities, kp_values)
                edges += forces * lr_val

            n_iter_val = int(np.ceil(self.n_iter * self.n_iter_reduction))
            lr_val = lr_val * self.lr_reduction

        return edges

    def subdivide_edges(self, edges: np.ndarray, num_points: int) -> np.ndarray:
        # Calculate vectors and their lengths
        """
        vectors = edges[:, 1:] - edges[:, :-1]
        lengths = np.linalg.norm(vectors, axis=-1)

        # Cumulative lengths
        cum_lengths = np.cumsum(lengths, axis=1)
        cum_lengths = np.hstack([np.zeros((cum_lengths.shape[0], 1)), cum_lengths])

        # Total lengths of each edge
        total_lengths = cum_lengths[:, -1]

        # Interpolated lengths for new points
        t = np.linspace(0, 1, num=num_points, endpoint=True)
        interpolated_lengths = t * total_lengths[:, None]

        # Determine segments for new points
        segment_indices = np.argmax(interpolated_lengths[:, :, None] < cum_lengths[:, None, :], axis=2)

        # Calculate interpolation factors
        previous_lengths = np.take_along_axis(cum_lengths, segment_indices - 1, axis=1)
        segment_lengths = np.take_along_axis(lengths, segment_indices - 1, axis=1)
        interpolation_factors = (interpolated_lengths - previous_lengths) / (segment_lengths + 1e-8)

        # Interpolate new points
        n_edges = edges.shape[0]
        new_points = np.zeros((n_edges, num_points, 2))
        for i in range(n_edges):
            for j in range(num_points):
                idx = segment_indices[i, j]
                start_point = edges[i, idx - 1]
                end_point = edges[i, idx]
                factor = interpolation_factors[i, j]
                new_points[i, j] = (1 - factor) * start_point + factor * end_point

        return new_points
        """
        segment_vecs = edges[:, 1:] - edges[:, :-1]
        segment_lens = np.linalg.norm(segment_vecs, axis=-1)
        cum_segment_lens = np.cumsum(segment_lens, axis=1)
        cum_segment_lens = np.hstack(
            [np.zeros((cum_segment_lens.shape[0], 1)), cum_segment_lens]
        )

        total_lens = cum_segment_lens[:, -1]

        # At which lengths do we want to generate new points
        t = np.linspace(0, 1, num=num_points, endpoint=True)
        desired_lens = t * total_lens[:, None]
        # Which segment should the new point be interpolated on
        i = np.argmax(desired_lens[:, None] < cum_segment_lens[..., None], axis=1)
        # At what percentage of the segment does this new point actually appear
        pct = (desired_lens - np.take_along_axis(cum_segment_lens, i - 1, axis=-1)) / (
                np.take_along_axis(segment_lens, i - 1, axis=-1) + 1e-8
        )

        row_indices = np.arange(edges.shape[0])[:, None]
        new_points = (
                (1 - pct[..., None]) * edges[row_indices, i - 1]
                + pct[..., None] * edges[row_indices, i]
        )

        return new_points

    def compute_forces(self, e: np.ndarray, e_compat: np.ndarray, kp: np.ndarray) -> np.ndarray:
        # Compute left-mid and right-mid spring velocities
        v_spring_l = np.array([[e[i][j] - e[i][j + 1] for j in range(len(e[i]) - 1)] for i in range(len(e))])
        v_spring_r = np.array([[e[i][j + 1] - e[i][j] for j in range(len(e[i]) - 1)] for i in range(len(e))])
        v_spring_l_new = np.zeros((v_spring_l.shape[0], v_spring_l.shape[1]+1, v_spring_l.shape[-1]))
        v_spring_r_new = np.zeros((v_spring_r.shape[0], v_spring_r.shape[1]+1, v_spring_r.shape[-1]))

        for i in range(v_spring_l.shape[0]):
            sub_arr_l = np.zeros((v_spring_l.shape[1]+1, v_spring_l.shape[-1]))
            sub_arr_l[1:, :] = v_spring_l[i, :, :]
            v_spring_l_new[i, :, :] = sub_arr_l

            sub_arr_r = np.zeros((v_spring_r.shape[1]+1, v_spring_r.shape[-1]))
            sub_arr_r[:-1, :] = v_spring_r[i, :, :]
            v_spring_r_new[i, :, :] = sub_arr_r

        f_spring_l = np.sum(v_spring_l_new ** 2, axis=-1, keepdims=True)
        f_spring_r = np.sum(v_spring_r_new ** 2, axis=-1, keepdims=True)
        F_spring = kp * (f_spring_l * v_spring_l_new + f_spring_r * v_spring_r_new)

        # Calculate electrostatic forces
        v_electro = e[:, np.newaxis, :, :] - e[np.newaxis, :, :, :]
        distances = np.linalg.norm(v_electro, axis=-1) + 1e-8
        f_electro = e_compat[:, :, np.newaxis] / distances
        F_electro = np.sum(f_electro[:, :, :, np.newaxis] * v_electro, axis=0)
        F = F_spring + F_electro

        F[:, 0, :] = F[:, -1, :] = 0

        return F
