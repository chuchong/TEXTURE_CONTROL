import os
import numpy as np
from mesh import Mesh
import cv2
class Shape:
    def __init__(self):
        self.meshes_ = []
        self.visible_ = 1
        self.name_ = ''

    def LoadFromOBJFile(self, fn, loadTexture = True):
        self.name_ = os.path.basename(fn)
        lines = [l.strip() for l in open(fn)]
        vertices = []
        texcoords = []
        faces = []
        faceTexs = []
        faceMat = []
        matId = 0
        mat2tex = {}
        mat2id = {}
        textureName = []
        mid = 0
        for l in lines:
            words = [w for w in l.split(' ') if w != '']
            if len(words) == 0:
                continue
            if words[0] == 'mtllib':
                matName = words[1]
                if not os.path.isabs(matName):
                    matName = os.path.dirname(fn) + '/' + words[1]
                mat2tex = self.LoadMTLFile(matName)
                mid = 0
                for mat,tex in mat2tex.items():
                    mat2id[mat] = mid
                    textureName.append(tex)
                    mid += 1

            if len(words) == 0:
                continue
            if words[0] == 'usemtl':
                mid = mat2id[words[1]]
            if words[0] == 'v':
                vertices.append([float(words[i]) for i in range(1,4)])
            if words[0] == 'vt':
                texcoords.append([float(words[i]) for i in range(1,3)])
            if words[0] == 'f':
                fIdx = [words[i].split('/') for i in range(1, len(words))]
                for i in range(0,len(fIdx)-2,1):
                    faces.append([int(fIdx[0][0]),int(fIdx[i+1][0]),int(fIdx[i+2][0])])
                    faceMat.append(mid)
                    if len(fIdx[0]) > 1:
                        faceTexs.append([int(fIdx[0][1]),int(fIdx[i+1][1]),int(fIdx[i+2][1])])

        faceMat = np.array(faceMat).astype('int32')

        V = np.array(vertices).astype('float32')
        T = np.array(texcoords).astype('float32')
        F = np.array(faces).astype('int32') - 1
        FT = np.array(faceTexs).astype('int32') - 1
        if len(textureName) == 0:
            textureName.append(None)
        for i in range(len(textureName)):
            mask = np.where(faceMat == i)[0]
            if mask.shape[0] == 0:
                continue
            mesh = Mesh()
            mesh.V_ = V
            mesh.T_ = T
            mesh.F_ = F[mask]
            mesh.FT_ = FT[mask]

            if textureName[i] is not None and loadTexture:
                mesh.texImg_ = cv2.imread(textureName[i])
                mesh.texImg_ = cv2.cvtColor(mesh.texImg_, cv2.COLOR_BGR2RGB)
            elif mesh.FT_.shape[0] > 0:
                mesh.texImg_ = np.zeros((1024,1024,3),dtype='uint8')
                mesh.texImg_[:,:,0] = 255
                mesh.texImg_[:,:,2] = 255

            mesh.texImg_ = (mesh.texImg_ / 255.0).astype('float32')
            mesh.UpdateRenderData()
            self.meshes_.append(mesh)

    def LoadMTLFile(self, fn):
        lines = [l.strip() for l in open(fn)]
        matName = None
        parentDir = os.path.dirname(fn)
        mat2tex = {}
        for l in lines:
            words = [w for w in l.split(' ') if w != '']
            if len(words) == 0:
                continue
            if words[0] == 'newmtl':
                matName = words[1]
                mat2tex[matName] = None
            elif words[0] == 'map_Kd':
                textureName = words[1]
                if not os.path.isabs(textureName):
                    textureName = parentDir + '/'+ textureName
                    mat2tex[matName] = textureName
        return mat2tex

    def rotate(self, R):
        for mesh in self.meshes_:
            print(mesh.V_.shape, R.shape)
            print(R)
        for mesh in self.meshes_:
            mesh.V_ = mesh.V_ @ R[:3,:3]
            mesh.UpdateRenderData()

    def Render(self, program):
        if not self.visible_:
            return
        for m in self.meshes_:
            m.Render(program)