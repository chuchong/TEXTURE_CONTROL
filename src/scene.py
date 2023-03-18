import os
from os.path import dirname, realpath
import sys
ROOT = dirname(realpath(__file__))
sys.path.append(ROOT)

from mesh import Mesh
from shape import Shape

class Scene:
    def __init__(self):
        self.shapes_ = []

    def AddShapeFromFile(self, fn, loadTexture=True):
        obj = Shape()
        obj.LoadFromOBJFile(fn, loadTexture)
        self.shapes_.append(obj)

    def UpdateTexture(self, camera, uuid, depth, color, depthThres=1e-2):
        for s in self.shapes_:
            for m in s.meshes_:
                m.UpdateTexture(camera, uuid, depth, color, depthThres)

    def Render(self, program):
        for s in self.shapes_:
            s.Render(program)
