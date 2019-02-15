# =======================================================================
# 2019 Changes by Natalia Clementi @ncclementi
# =======================================================================
# 2016 Changes by ARM (abhilashreddy.com)
#  - made to work with Python 3+
#  - made to work with recent versions of matplotlib
# =======================================================================
# Author: William G.K. Martin (wgm2111@cu where cu=columbia.edu)
# copyright (c) 2010
# licence: BSD style
# ======================================================================

import numpy 
import matplotlib.tri as Triang


def get_points():
    '''
    Creates the coordinates of the vertices of the base icosahedron using
    the golden ratio https://en.wikipedia.org/wiki/Regular_icosahedron.

    Returns
    -------
    p[reorder_index, :] array, contains the points of the icosahedron, with
    indices reordered in downward spiral
    '''

    # Define the vertices with the golden ratio
    a = (1. + numpy.sqrt(5.)) / 2.0   # golden ratio

    p = numpy.array([[a, -a, -a, a, 1, 1, -1, -1, 0, 0, 0, 0],
                    [0, 0, 0, 0, a, -a, -a, a, 1, 1, -1, -1],
                    [1, 1, -1, -1, 0, 0, 0, 0, a, -a, -a, a]]).transpose()
    #normalize to fall into a unit sphere.
    p = p / numpy.sqrt((p**2).sum(1))[0]

    # rotate top point to the z-axis
    ang = numpy.arctan(p[0, 0] / p[0, 2])
    ca, sa = numpy.cos(ang), numpy.sin(ang)
    rotation = numpy.array([[ca, 0, -sa], [0, 1.0, 0], [sa, 0, ca]])
    p = numpy.inner(rotation, p).transpose()      
    # reorder in a downward spiral
    reorder_index = [0, 3, 4, 8, -1, 5,-2, -3, 7, 1, 6, 2]
    return p[reorder_index, :]


def get_barymat(n):
    '''
    Define the barycentric matrix that will refine points on a triangle.

    Arguments
    ---------
    n : integer, number of points in a triangle edge after refinement.

    Returns
    -------
    bcmat : matrix,  dimensions (n*(n+1)/2, 3). Each row contains the
    barycentric coordinates of each point after division.
    '''

    numrows = n*(n+1)//2

    # define the values that will be needed
    ns = numpy.arange(n)
    vals = ns / float(n-1)

    # initialize array
    bcmat = numpy.zeros((numrows, 3))  
    # loop over blocks to fill in the matrix
    shifts = numpy.arange(n, 0, -1)
    starts = numpy.zeros(n, dtype=int)
    starts[1:] += numpy.cumsum(shifts[:-1])  # starts are the cumulative shifts
    stops = starts + shifts
    for n_, start, stop, shift in zip(ns, starts, stops, shifts):
        bcmat[start:stop, 0] = vals[shift-1::-1]
        bcmat[start:stop, 1] = vals[:shift]
        bcmat[start:stop, 2] = vals[n_]
    return bcmat


class icosahedron(object):
    """
    The vertices of an icosahedron, together with triangles, edges,
    triangle midpoints and edge midpoints.  
    """

    # define points (vertices)
    p = get_points()
    # define triangles (faces)
    tri = numpy.array([
            [1, 2, 3, 4, 5, 6, 2, 7, 2, 8, 3, 9, 10, 10, 6, 6, 7, 8, 9, 10],
            [0, 0, 0, 0, 0, 1, 7, 2, 3, 3, 4, 4, 4, 5, 5, 7, 8, 9, 10, 6],
            [2, 3, 4, 5, 1, 7, 1, 8, 8, 9, 9, 10, 5, 6, 1, 11, 11, 11, 11, 11]
            ]).transpose()

    trimids = (p[tri[:, 0]] + p[tri[:, 1]] + p[tri[:, 2]]) / 3.0

    # define bars (edges)
    bar = list()
    for t in tri:
        bar += [numpy.array([i, j]) for i, j
                in [t[0:2], t[1:], t[[2, 0]]] if j > i]
    bar = numpy.array(bar)
    barmids = (p[bar[:, 0]] + p[bar[:, 1]]) / 2.0


def triangulate_bary(bary):
    """
    Triangulate a single barycentric triangle using matplotlib.

    Argument
    --------
    bary: barycentric matrix obtained using get_barymat.

    Return
    ------
    dely.edges: array (nedges, 2) that contains the indices of the two vertices
                 that form each edge after the triangulation.
    dely.triangles:array (ntriangles, 3) that contains the indices of the three
                   vertices that form each triangle after the triangulation. 
    """

    x, y = numpy.cos(-numpy.pi/4.) * bary[:, 0] + //
    numpy.sin(-numpy.pi/4.) * bary[:, 1], bary[:, 2]

    dely = Triang.Triangulation(x, y)
    return dely.edges, dely.triangles


def get_triangulation(n, ico=icosahedron()):
    """
    Compute the triangulation of the sphere by refineing each face of the
    icosahedron to an nth order barycentric triangle.  There are two key issues
    that this routine addresses.

    1) calculate the triangles (unique by construction)
    2) remove non-unique nodes and edges
    """
    verts = numpy.array([ico.p[ico.tri[:,0]],
                      ico.p[ico.tri[:,1]],
                      ico.p[ico.tri[:,2]]])
    bary = get_barymat(n)
    newverts = numpy.tensordot(verts, bary,  axes=[(0,), (-1,)]).transpose(0,2,1)
    numverts = newverts.shape[1]
    if newverts.size/3 > 1e6: print("newverts.size/3 is high: {0}".format(
            newverts.size/3))
    flat_coordinates = numpy.arange(newverts.size/3).reshape(20, numverts)

    barbary, tribary = triangulate_bary(bary)

    newtri = numpy.zeros((20, tribary.shape[0], 3), dtype=int)
    newbar = numpy.zeros((20, barbary.shape[0], 2), dtype=int)

    for i in range(20):
        for j in range(3):
            newtri[i, :, j] = flat_coordinates[i, tribary[:,j]]
            if j < 2: newbar[i, :, j] = flat_coordinates[i, barbary[:,j]]

    newverts = newverts.reshape(newverts.size//3, 3)
    newtri = newtri.reshape(newtri.size//3, 3)
    newbar = newbar.reshape(newbar.size//2, 2)
    # normalize vertices
    scalars = numpy.sqrt((newverts**2).sum(-1))
    newverts = (newverts.T / scalars).T
    # remove repeated vertices
    aux, iunique, irepeat = numpy.unique(numpy.dot(newverts//1e-8, 100*numpy.arange(1,4,1)),
                                      return_index=True, return_inverse=True)

    univerts = newverts[iunique]
    unitri = irepeat[newtri]
    unibar = irepeat[newbar]
    mid = .5 * (univerts[unibar[:,0]] + univerts[unibar[:,1]])
    aux, iu  = numpy.unique(numpy.dot(mid//1e-8, 100*numpy.arange(1,4,1)), return_index=True)
    unimid = mid[iu]
    unibar = unibar[iu,:]
    return univerts, unitri, unibar

class icosphere(icosahedron):
    """
    """
    def __init__(self, n):
        """
        define an icosahedron based discretization of the sphere
        n is the order of barycentric triangles used to refine each
        face of the icosaheral base mesh.
        """
        self.p, self.tri, self.bar = get_triangulation(n+1, icosahedron)

def cart2sph(xyz):
    """
    Convert Cartesian coordinates to spherical coordinates.
    https://stackoverflow.com/q/4116658
    """
    ptsnew = numpy.zeros_like(xyz)
    xy = xyz[:,0]**2 + xyz[:,1]**2
    ptsnew[:,0] = numpy.sqrt(xy + xyz[:,2]**2)
    ptsnew[:,1] = numpy.arctan2(numpy.sqrt(xy), xyz[:,2]) # for elevation angle defined from Z-axis down
    #ptsnew[:,1] = numpy.arctan2(xyz[:,2], numpy.sqrt(xy)) # for elevation angle defined from XY-plane up
    ptsnew[:,2] = numpy.arctan2(xyz[:,1], xyz[:,0])
    return ptsnew


if __name__ == "__main__":
    import numpy
    from matplotlib import pyplot
    from mpl_toolkits.mplot3d import Axes3D

    # Get a unit sphere triangulation with a specified level of refinement. 
    # A refinement level of N will have (20*N^2) faces and (10*N^2 + 2) vertices
    isph=icosphere(10)
    vertices=isph.p
    faces=isph.tri

    # get spherical coordinates for each point and project it to the corresponding
    # point on the ellipsoid. a,b,c are the semi-major axes of the ellipsoid
    spvert=cart2sph(vertices)
    a,b,c=1.0,1.0,0.5
    vertices[:,0]=a*numpy.cos(spvert[:,2])*numpy.sin(spvert[:,1])
    vertices[:,1]=b*numpy.sin(spvert[:,2])*numpy.sin(spvert[:,1])
    vertices[:,2]=c*numpy.cos(spvert[:,1])

    # plotting
    fig = pyplot.figure(figsize=(10,10))
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(vertices[:,0],vertices[:,1],vertices[:,2],cmap='cool', triangles=faces, linewidth=0.20,edgecolor='black',alpha=1.0)


    # Create cubic bounding box to simulate equal aspect ratio for x,y and z axes
    X,Y,Z=vertices[:,0],vertices[:,1],vertices[:,2]
    
    max_range = numpy.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max()
    Xb = 0.5*max_range*numpy.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(X.max()+X.min())
    Yb = 0.5*max_range*numpy.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(Y.max()+Y.min())
    Zb = 0.5*max_range*numpy.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(Z.max()+Z.min())
    # Comment or uncomment following both lines to test the fake bounding box:
    for xb, yb, zb in zip(Xb, Yb, Zb):
       ax.plot([xb], [yb], [zb], 'w')

    pyplot.show()