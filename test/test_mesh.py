import os
from os.path import dirname, realpath
import sys
ROOT = dirname(realpath(__file__)) + '/..'
sys.path.append(ROOT + '/src')

from mesh import Mesh

cube = Mesh()
cube.LoadFromOBJFile(ROOT + '/data/cube.obj')

if not os.path.exists(ROOT + '/result'):
	os.mkdir(ROOT + '/result')
cube.SaveToOBJFile(ROOT + '/result/cube.obj')


