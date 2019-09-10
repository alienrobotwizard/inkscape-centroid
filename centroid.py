#!/usr/bin/env python

'''
Copyright (C) 2019 Jacob Perkins

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import uuid
import inkex
from itertools import chain
import simplepath, cubicsuperpath, bezmisc, simplestyle

def seq(p0, p1, npts):
    if npts == 0 or p1 < p0:
        return []    
    if npts < 2 or p0 == p1:
        return [p0]

    d = float(p1-p0)/(npts-1)
    res = [p0 + i*d for i in range(0,npts-1)]
    res.append(p1)
    return res

def bezlinearize(bez, npts):
    return [bezmisc.bezierpointatt(bez, t) for t in seq(0,1,npts)]
    
def area(x):
    arr = sum([x[i][0]*x[i+1][1]-x[i+1][0]*x[i][1] for i in range(0, len(x)-1)])
    return arr/2.0;

def centroid(x):
    r = range(0, len(x)-1)
    a = area(x)
    cx = sum([(x[i][0]+x[i+1][0])*(x[i][0]*x[i+1][1] - x[i+1][0]*x[i][1]) for i in r])/(6*a)
    cy = sum([(x[i][1]+x[i+1][1])*(x[i][0]*x[i+1][1] - x[i+1][0]*x[i][1]) for i in r])/(6*a)
    return [cx, cy]

def centroid_and_area(sub, num_points):
    """Returns centroid and area of a path

    Args:
        sub: A sub-path of a CubicSuperPath

    Returns:
        list: Two elements, 1. coordinates of centroid and 2. area
    """
    coords = []
    
    if sub[0][0] == sub[-1][2]:                                                
        p0 = sub[0][1]
        i = 0
        while i < len(sub)-1:
            p1 = sub[i][2]
            p2 = sub[i+1][0]
            p3 = sub[i+1][1]
            bez = (p0, p1, p2, p3)
            coords.extend(bezlinearize(bez, num_points))
            p0 = p3
            i+=1
    else:
        inkex.errormsg("Path doesn't appear to be closed")
        return []
    
    c = centroid(coords)
    a = area(coords)
    return [c, a]
            
def draw_SVG_dot((cx, cy), r, name, parent):
    circ_attribs = {inkex.addNS('label','inkscape'):name,
                    'fill':'red',
                    'r':str(r),
                    'cx':str(cx), 'cy':str(cy)}
    inkex.etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )

def many_lines(x, parent):    
    [draw_SVG_line(x[i], x[i+1], parent) for i in range(0, len(x)-1)]
    
def draw_SVG_line((x1, y1),(x2, y2), parent):
    style = { 'stroke': '#000000', 'stroke-width':'1px',
              'stroke-linecap':'butt', 'stroke-linejoin':'miter'}
    line_attribs = {'style':simplestyle.formatStyle(style),
                    'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}
    inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
    
class Centroid(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--num_points",
                        action="store", type="int", 
                        dest="num_points", default=100,
                        help="Number of linear segments per curve")
        self.OptionParser.add_option("--centroid_radius",
                        action="store", type="int", 
                        dest="centroid_radius", default=10,
                        help="Radius of output centroid")

    def effect(self):
        paths = []

        #
        # Multiple paths can be selected
        #
        for id, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path','svg'):
                paths.append(node)

        if len(paths) == 0:
            inkex.errormsg("Need at least one path")
            return


        #
        # For each selected path, find the centroid and area of it
        # - If one of the selected paths is not closed, returns an error
        #
        parsed = [cubicsuperpath.parsePath(path.get('d')) for path in paths]
        
        # Unnest paths of paths in cubicsuperpath
        parsed = list(chain.from_iterable(parsed))
        
        x = []
        for p in parsed:
            c_and_a = centroid_and_area(p, self.options.num_points)
            if len(c_and_a) == 0:
                return
            x.append(c_and_a)

        #
        # We assume that the selected paths are such that:
        # 1. There are no intersecting paths
        # 2. There is an outermost path which completely contains
        #    all of the other paths
        # Sorting by area results in the outermost path being at
        # the end of the list
        #
        def by_area(y):
            return y[1]

        x = [[y[0], abs(y[1])] for y in x]
        x.sort(key=by_area)
        
        outermost = x[len(x)-1]
        outermost_centroid = outermost[0]
        outermost_area = outermost[1]

        inner = x[0:len(x)-1]
        inner_area = 0
        cx_numerator = outermost_area*outermost_centroid[0]
        cy_numerator = outermost_area*outermost_centroid[1]
        for i in range(0, len(inner)):
            a = inner[i][1]
            cx_numerator -= a*inner[i][0][0]
            cy_numerator -= a*inner[i][0][1]
            inner_area += a
            
        denominator = outermost_area - inner_area
        cx = cx_numerator/denominator
        cy = cy_numerator/denominator
        c = [cx, cy]

        name = "centroid-dot-{}".format(uuid.uuid4().hex[0:6])
        draw_SVG_dot(c, self.options.centroid_radius, name, self.current_layer)
                        
if __name__ == '__main__':
    e = Centroid()
    e.affect()

