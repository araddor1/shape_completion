#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/compute_average_spacing.h>
#include <CGAL/jet_estimate_normals.h>
#include <CGAL/mst_orient_normals.h>
#include <CGAL/property_map.h>
#include <CGAL/IO/read_ply_points.h>
#include <CGAL/IO/write_ply_points.h>
#include <utility> // defines std::pair
#include <list>
#include <fstream>
// Types
typedef CGAL::Exact_predicates_inexact_constructions_kernel Kernel;
typedef Kernel::Point_3 Point;
typedef Kernel::Vector_3 Vector;
// Point with normal vector stored in a std::pair.
typedef std::pair<Point, Vector> PointVectorPair;
// Concurrency
#ifdef CGAL_LINKED_WITH_TBB
typedef CGAL::Parallel_tag Concurrency_tag;
#else
typedef CGAL::Sequential_tag Concurrency_tag;
#endif
int main(int argc, char*argv[])
{
	const char* fname = (argc > 1) ? argv[1] : "D:/pc_normals/hips.002167.ply";
	// Reads a .xyz point set file in points[].
	std::list<PointVectorPair> points;
	std::ifstream stream(fname, std::ios::binary);
	if (!stream ||
		!CGAL::read_ply_points(stream,
			std::back_inserter(points),
			CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>())))
	{
		std::cerr << "Error: cannot read file " << fname << std::endl;
		return EXIT_FAILURE;
	}
	// Estimates normals direction.
	// Note: pca_estimate_normals() requiresa range of points
	// as well as property maps to access each point's position and normal.
	const int nb_neighbors = 20; // K-nearest neighbors = 3 rings
	if (argc > 2 && std::strcmp(argv[2], "-r") == 0) // Use a fixed neighborhood radius
	{
		// First compute a spacing using the K parameter
		double spacing
			= CGAL::compute_average_spacing<Concurrency_tag>
			(points, nb_neighbors,
				CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>()));
		// Then, estimate normals with a fixed radius
		CGAL::jet_estimate_normals<Concurrency_tag>
			(points,
				0, // when using a neighborhood radius, K=0 means no limit on the number of neighbors returns
				CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>()).
				normal_map(CGAL::Second_of_pair_property_map<PointVectorPair>()).
				neighbor_radius(2. * spacing)); // use 2*spacing as neighborhood radius
	}
	else // Use a fixed number of neighbors
	{
		CGAL::jet_estimate_normals<Concurrency_tag>
			(points, nb_neighbors,
				CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>()).
				normal_map(CGAL::Second_of_pair_property_map<PointVectorPair>()));
	}

	// Orients normals.
	// Note: mst_orient_normals() requires a range of points
	// as well as property maps to access each point's position and normal.
	std::list<PointVectorPair>::iterator unoriented_points_begin =
		CGAL::mst_orient_normals(points, 10*nb_neighbors,
			CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>()).
			normal_map(CGAL::Second_of_pair_property_map<PointVectorPair>()));

	// Saves point set.
	// Note: write_ply_points() requires property maps to access each
	// point position and normal.
	std::ofstream out("hips.002167.ply");
	out.precision(17);
	if (!out ||
		!CGAL::write_ply_points(
			out, points,
			CGAL::parameters::point_map(CGAL::First_of_pair_property_map<PointVectorPair>()).
			normal_map(CGAL::Second_of_pair_property_map<PointVectorPair>())))
	{
		return EXIT_FAILURE;
	}
	return EXIT_SUCCESS;
}