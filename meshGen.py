import math as m
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay

class meshGen:
    def __init__(self, d, w, l, s):
        self.d = d
        self.r = d/2.
        self.w = w
        self.l = l
        self.s = s

        self.nodes = {}
        self.elements = {}
        self.n_count = 1

        self.nodes[self.n_count] = {}
        self.nodes[self.n_count]['xy'] = [w, l]
        self.nodes[self.n_count]['typ'] = 'C'
        self.nodes[self.n_count]['e'] = []
        self.n_count += 1

    def getEdges(self):
        edges = [
            [self.l, self.w, '~'],
            [self.l - self.r, 0.0, '~'],
            [self.w, '~', self.l],
            [self.w - self.r, '~', 0.0]
        ]

        count = 1
        for e in edges:
            n_count = int(m.ceil(e[0]/self.s))
            delta = e[0]/n_count
            for i in range(0, n_count):
                coord = i * delta
                if (count % 2) == 0:
                    coord = coord + self.r
                xy = [e[1], e[2]]
                if xy[0] == '~':
                    xy[0] = coord
                else:
                    xy[1] = coord

                self.nodes[self.n_count] = {}
                self.nodes[self.n_count]['xy'] = xy
                if i == 0:
                    self.nodes[self.n_count]['typ'] = 'C'
                else:
                    self.nodes[self.n_count]['typ'] = 'e'
                self.nodes[self.n_count]['e'] = []
                self.n_count += 1
            count += 1

    def getCircumfrence(self):
        c = (2 * m.pi * self.r)/4
        n_count = int((m.ceil(c/self.s)) * 1.2)

        delta = 90 / n_count
        delta_list = []

        for i in range(1, n_count):
            delta_list.append(i * delta)

        for d in delta_list:
            x = round(m.cos(m.radians(d))*self.r, 5)
            y = round(m.sin(m.radians(d))*self.r, 5)

            self.nodes[self.n_count] = {}
            self.nodes[self.n_count]['xy'] = [x, y]
            if d == delta_list[0] or d == delta_list[-1]:
                self.nodes[self.n_count]['typ'] = 'C'
            else:
                self.nodes[self.n_count]['typ'] = 'e'
            self.nodes[self.n_count]['e'] = []
            self.n_count += 1

    def getInternal(self):
        r_count = int(m.ceil(self.l/self.s))
        r_delta = self.l/r_count
        c_count = int(m.ceil(self.w/self.s))
        c_delta = self.w/c_count

        for r in range(1, r_count):
            for c in range(1, c_count):
                x = c * c_delta
                y = r * r_delta

                if m.sqrt(x**2 + y**2) > self.r + (self.s * 0.25):
                    self.nodes[self.n_count] = {}
                    self.nodes[self.n_count]['xy'] = [x, y]
                    self.nodes[self.n_count]['typ'] = 'i'
                    self.nodes[self.n_count]['e'] = []
                    self.n_count += 1

    def getMesh(self, s):
        nodes = []
        for node in self.nodes:
            nodes.append(self.nodes[node]['xy'])
        self.points = np.array(nodes)
        tri = Delaunay(self.points, furthest_site=False)

        #print(tri.simplices)
        #print(tri.points[1])
        #print(points[tri.simplices])

        find_points = []
        for d in range(0, 90):
            x = m.cos(m.radians(d)) * (self.r * s)
            y = m.sin(m.radians(d)) * (self.r * s)
            find_points.append([x,y])

        find_points = np.array(find_points)

        el_del = []
        for e in tri.find_simplex(find_points):
            if e != -1:
                if e not in el_del:
                    el_del.append(e)

        self.mesh = np.delete(tri.simplices, el_del, 0)

        #Add mid side nodes

        mesh_mid = []
        self.points_mid = self.points
        for e in self.mesh:
            e_mid = []
            for n in range(0, len(e)):
                e_mid.append(e[n])

                if n != 2:
                    offset = n + 1
                else:
                    offset = 0

                xy_1 = self.points[e[n]]
                xy_2 = self.points[e[offset]]
                x_m = round((xy_1[0] + xy_2[0]) / 2.0, 5)
                y_m = round((xy_1[1] + xy_2[1]) / 2.0, 5)
                xy_m = [x_m, y_m]

                test = False
                for i in range(0, len(self.points_mid)):
                    if self.points_mid[i][0] == xy_m[0]:
                        if self.points_mid[i][1] == xy_m[1]:
                            test = True
                            n_mid = i
                            break

                if test == False:
                    self.points_mid = np.append(self.points_mid, [xy_m], axis=0)
                    n_mid = len(self.points_mid) - 1
                    e_mid.append(n_mid)
                elif test == True:
                    e_mid.append(n_mid)

            mesh_mid.append(e_mid)

        self.mesh_mid = np.array(mesh_mid)

        '''
        plt.triplot(self.points[:,0], self.points[:,1], self.mesh)
        plt.plot(self.points_mid[:,0], self.points_mid[:,1], 'o')

        for i, p in enumerate(self.points_mid, 1):
            plt.text(p[0], p[1], i, ha='right')

        for j, s in enumerate(self.mesh, 1):
            p = self.points[s].mean(axis=0)
            plt.text(p[0], p[1], '#%d' % j, ha='center')

        plt.gca().set_aspect('equal', adjustable='box')
        plt.savefig('mesh_mid_plot.png')
        '''

    def plotMesh(self, nLabel=False, eLabel=False, mid=False):
        plt.triplot(self.points[:,0], self.points[:,1], self.mesh)

        if mid == False:
            plt.plot(self.points[:,0], self.points[:,1], 'o')
        elif mid == True:
            plt.plot(self.points_mid[:, 0], self.points_mid[:, 1], 'o')

        if nLabel == True:
            if mid == False:
                for i, p in enumerate(self.points, 1):
                    plt.text(p[0], p[1], i, ha='right')
            elif mid == True:
                for i, p in enumerate(self.points_mid, 1):
                    plt.text(p[0], p[1], i, ha='right')

        if eLabel == True:
            for j, s in enumerate(self.mesh, 1):
                p = self.points[s].mean(axis=0)
                plt.text(p[0], p[1], '#%d' % j, ha='center')

        #plt.xlim((0, self.w))
        #plt.ylim((0, self.l))
        plt.gca().set_aspect('equal', adjustable='box')
        plt.savefig('mesh_plot.png')

    def generate_inp(self):
        with open('mesh.inp', 'w') as f:
            f.write('*NODE,NSET=Nall')
            for i, n in enumerate(self.points_mid, 1):
                f.write('\n' + ' {}, {}, {}'.format(i, n[0], n[1]))

            f.write('\n' + '*ELEMENT, ELSET=Eall, TYPE=CPS6')
            for i, el in enumerate(self.mesh_mid, 1):
                f.write('\n' + ' {}, {}, {}, {}, {}, {}, {}'.format(i, el[0]+1, el[1]+1, el[2]+1, el[3]+1, el[4]+1, el[5]+1))

            f.write('\n' + 'NSET=Xsym')
            n_list = []
            for i, n in enumerate(self.points_mid, 1):
                if n[0] == 0:
                    n_list.append(i)
            f.write('\n' + ' ' + str(n_list).strip('[').strip(']'))

            f.write('\n' + 'NSET=Ysym')
            n_list = []
            for i, n in enumerate(self.points_mid, 1):
                if n[1] == 0:
                    n_list.append(i)
            f.write('\n' + ' ' + str(n_list).strip('[').strip(']'))

            f.write('\n' + 'NSET=EdgeSide')
            n_list = []
            for i, n in enumerate(self.points_mid, 1):
                if n[0] == self.w:
                    n_list.append(i)
            f.write('\n' + ' ' + str(n_list).strip('[').strip(']'))

            f.write('\n' + 'NSET=EdgeTop')
            n_list = []
            for i, n in enumerate(self.points_mid, 1):
                if n[1] == self.l:
                    n_list.append(i)
            f.write('\n' + ' ' + str(n_list).strip('[').strip(']'))


diameter = 400
width = 300
length = 600
seed = 100

mg = meshGen(
    diameter,
    width,
    length,
    seed
)

mg.getEdges()
mg.getCircumfrence()
mg.getInternal()
mg.getMesh(0.98)
mg.plotMesh(nLabel=True, eLabel=True, mid=True)
mg.generate_inp()

###~~~~~~~~~~ OLD ~~~~~~~~~~###

'''
def getCornerNodes(self):
    corner_list = [[0.0, self.l], [self.w, 0]]

    for corner in corner_list:
        self.nodes[self.n_count] = {}
        self.nodes[self.n_count]['xy'] = corner
        self.nodes[self.n_count]['typ'] = 'C'
        self.nodes[self.n_count]['e'] = []
        self.n_count += 1

def genElements(self):
    n_ignore = [1]
    elem = 1
    self.elements[elem] = {}
    xy = self.nodes[1]['xy']
    r_ = m.sqrt(xy[0] ** 2 + xy[1] ** 2)

    n = [1]
    r = [r_]
    x = [xy[0]]
    y = [xy[1]]

    while len(n) < 3:
        n__min = 0
        r__min = self.l
        for node in self.nodes.keys():
            if node not in n:
                if node not in n_ignore:
                    xy = self.nodes[node]['xy']
                    r_ = m.sqrt(xy[0] ** 2 + xy[1] ** 2)
                    x_ = x[0] - xy[0]
                    y_ = y[0] - xy[1]
                    r__ = m.sqrt(x_ ** 2 + y_ ** 2)

                    if r__ < r__min:
                        n__min = node
                        r__min = r__

        n.append(n__min)
        r.append(r__min)
        x.append(self.nodes[n__min]['xy'][0])
        y.append(self.nodes[n__min]['xy'][1])

    self.elements[1]['n'] = n
    for node in n:
        self.nodes[node]['e'].append(elem)

    elem += 1

    # new_n = n[2]
    new_n = 20
    self.elements[new_n] = {}
    xy = self.nodes[new_n]['xy']
    r_ = m.sqrt(xy[0] ** 2 + xy[1] ** 2)

    n = [new_n]
    r = [r_]
    x = [xy[0]]
    y = [xy[1]]

    while len(n) < 3:
        n__min = 0
        r__min = self.l
        for node in self.nodes.keys():
            if node != 1:
                if node not in n:
                    xy = self.nodes[node]['xy']
                    r_ = m.sqrt(xy[0] ** 2 + xy[1] ** 2)
                    x_ = x[0] - xy[0]
                    y_ = y[0] - xy[1]
                    r__ = m.sqrt(x_ ** 2 + y_ ** 2)

                    if r__ < r__min:
                        n__min = node
                        r__min = r__

        # if len
        n.append(n__min)
        r.append(r__min)
        x.append(self.nodes[n__min]['xy'][0])
        y.append(self.nodes[n__min]['xy'][1])

    self.elements[1]['n'] = n
    for node in n:
        self.nodes[node]['e'].append(elem)

    print(n, r, x, y)
    plt.scatter(x, y)
    plt.xlim(0, self.w)
    plt.ylim(0, self.l)
    plt.savefig('elements_plot.png')


def getSweppedNodes(self):
    ll = max(self.w, self.l)
    edge_count = int(m.ceil(ll / self.s))
    for node in range(0, edge_count):
        r = self.r + (node * self.s)
        c = (2 * m.pi * r) / 4
        n_count = int(m.ceil(c / self.s))

        delta = 90 / n_count
        delta_list = []

        for i in range(0, n_count + 1):
            delta_list.append(i * delta)

        for d in delta_list:
            x = m.cos(m.radians(d)) * r
            y = m.sin(m.radians(d)) * r
            if x <= self.w and y <= self.l:
                self.nodes[self.n_count] = {}
                self.nodes[self.n_count]['xy'] = [x, y]
                self.nodes[self.n_count]['typ'] = 'e'
                self.nodes[self.n_count]['e'] = []
                self.n_count += 1

def plotMesh(self):
    x = []
    y = []
    print(len(self.nodes))
    for node in self.nodes.keys():
        xy = self.nodes[node]['xy']
        x.append(xy[0])
        y.append(xy[1])

    plt.scatter(x, y)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig('mesh_plot.png')
'''