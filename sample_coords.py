import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def fibonacci_sphere(samples=1, randomize=True):
    rnd = 1.0
    if randomize:
        rnd = np.random.random() * samples

    points = []
    offset = 2.0 / samples
    increment = np.pi * (3.0 - np.sqrt(5.0))

    for i in range(samples):
        y = ((i * offset) - 1) + (offset / 2)
        r = np.sqrt(1 - y * y)

        phi = ((i + rnd) % samples) * increment

        x = np.cos(phi) * r
        z = np.sin(phi) * r

        points.append([x, y, z])

    return np.array(points)


def cartesian_to_spherical(cartesian_coords):
    spherical_coords = []
    for coord in cartesian_coords:
        r = np.linalg.norm(coord)
        theta = np.arccos(coord[2] / r)
        phi = np.arctan2(coord[1], coord[0])
        spherical_coords.append([r, theta, phi])

    return np.array(spherical_coords)


def plot_points_on_sphere(points):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot points on the sphere
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], c='r', marker='o')

    # Set axis aspect ratio
    ax.set_box_aspect([1, 1, 1])

    plt.show()


def uniform_sampling_on_sphere(num_samples):
    points = fibonacci_sphere(samples=num_samples, randomize=True)
    spherical_points = cartesian_to_spherical(points)

    # Convert theta and phi to longitude and latitude
    longitudes = np.degrees(spherical_points[:, 2])
    latitudes = 90 - np.degrees(spherical_points[:, 1])

    # Combine longitudes and latitudes as tuples
    coord_tuples = [{'lat': latitudes[i], 'lon': longitudes[i]}
                    for i in range(num_samples)]

    return coord_tuples


if __name__ == '__main__':
    num_points = 100

    # Get uniformly sampled points' longitudes and latitudes as tuples
    sampled_points = uniform_sampling_on_sphere(num_points)

    # Print point coordinates
    for i, coord in enumerate(sampled_points):
        print(
            f"Point {i + 1}: Longitude {coord[0]:.6f}, Latitude {coord[1]:.6f}")

    # Get Cartesian points and plot points on the sphere
    points = fibonacci_sphere(samples=num_points, randomize=True)
    plot_points_on_sphere(points)
