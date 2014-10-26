#!/usr/bin/env python

import inkex
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
        for id, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path','svg'):
                p = cubicsuperpath.parsePath(node.get('d'))
                coords = []
                openPath = False
                for sub in p:
                    if sub[0][0] == sub[-1][2]:                                                
                        p0 = sub[0][1]
                        i = 0
                        while i < len(sub)-1:
                            p1 = sub[i][2]
                            p2 = sub[i+1][0]
                            p3 = sub[i+1][1]
                            bez = (p0, p1, p2, p3)
                            coords.extend(bezlinearize(bez, self.options.num_points))
                            p0 = p3
                            i+=1
                    else:
                        openPath = True
                        inkex.errormsg("Path doesn't appear to be closed")
                        

                if not openPath:
                    c = centroid(coords)
                
                    ## debug linearization
                    # many_lines(coords, self.current_layer)
                    #                
                    draw_SVG_dot(c, self.options.centroid_radius, "centroid-dot", self.current_layer)
                        
if __name__ == '__main__':
    e = Centroid()
    e.affect()

