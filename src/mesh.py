import numpy as np

import OpenGL.GL as gl
import ctypes
import cv2
from shader_programs import *
from framebuffer import FrameBuffer

class Mesh:
    global_uuid_ = 0
    def __init__(self):
        self.V_ = np.zeros((0,3),dtype='float32')
        self.F_ = np.zeros((0,3),dtype='int32')
        self.T_ = np.zeros((0,2),dtype='float32')
        self.FT_ = np.zeros((0,3),dtype='int32')
        self.texImg_ = None
        self.textiles_ = None
        self.texture_ = None

        Mesh.global_uuid_ += 1
        self.uuid_ = Mesh.global_uuid_

        self.VRender_ = None
        self.NRender_ = None
        self.TRender_ = None
        self.vbo_ = None
        self.tbo_ = None
        self.nbo_ = None
        self.renderVertexNum_ = 0

    def SaveToOBJFile(self, fn):
        fp = open(fn,'w')
        for i in range(self.V_.shape[0]):
            v = self.V_[i]
            fp.write('v %f %f %f\n'%(v[0],v[1],v[2]))
        for i in range(self.F_.shape[0]):
            f = self.F_[i]
            fp.write('f %d %d %d\n'%(f[0]+1,f[1]+1,f[2]+1))
        fp.close()

    def UpdateRenderData(self):
        if self.vbo_ is None:
            self.vbo_ = gl.glGenBuffers(1)
            self.nbo_ = gl.glGenBuffers(1)
            self.tbo_ = gl.glGenBuffers(1)

        diff1 = self.V_[self.F_[:,1]] - self.V_[self.F_[:,0]]
        diff2 = self.V_[self.F_[:,2]] - self.V_[self.F_[:,0]]
        normal = np.cross(diff1, diff2, axis=1).astype('float32')
        l = np.linalg.norm(normal,axis=1).reshape(-1,1)
        normal /= (l + (l == 0))
        self.VRender_ = np.ascontiguousarray(self.V_[self.F_.reshape(-1)])
        self.NRender_ = np.ascontiguousarray(np.hstack([normal,normal,normal])).reshape(-1,3)
        self.TRender_ = np.ascontiguousarray(self.T_[self.FT_.reshape(-1)])
        self.renderVertexNum_ = self.VRender_.shape[0]

        # Create a buffer
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.VRender_.nbytes, self.VRender_, gl.GL_DYNAMIC_DRAW)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tbo_)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.TRender_.nbytes, self.TRender_, gl.GL_DYNAMIC_DRAW)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.nbo_)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.NRender_.nbytes, self.NRender_, gl.GL_DYNAMIC_DRAW)

        if self.texImg_ is not None:
            self.texture_ = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
            gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
            gl.glTexImage2D(gl.GL_TEXTURE_2D,0,3,self.texImg_.shape[1], self.texImg_.shape[0],0,gl.GL_RGB,gl.GL_FLOAT, np.flipud(self.texImg_))

    def Render(self, program):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_)

        stride = self.VRender_.strides[0]
        offset = ctypes.c_void_p(0)
        loc = gl.glGetAttribLocation(program, "position")
        if loc >= 0:
            gl.glEnableVertexAttribArray(loc)
            gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.nbo_)
        loc = gl.glGetAttribLocation(program, "normal")
        if loc >= 0:
            gl.glEnableVertexAttribArray(loc)
            gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.tbo_)
        loc = gl.glGetAttribLocation(program, "texCoord")
        if loc >= 0:
            gl.glEnableVertexAttribArray(loc)
            gl.glVertexAttribPointer(loc, 2, gl.GL_FLOAT, False, self.TRender_.strides[0], offset)

        loc = gl.glGetUniformLocation(program, 'texImg')
        if loc >= 0 and self.texture_ is not None:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_)
            gl.glUniform1i(loc, 0)

        loc = gl.glGetUniformLocation(program, 'uuid')
        if loc >= 0:
            gl.glUniform1f(loc, float(self.uuid_))
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.renderVertexNum_)

    def GenerateTextiles(self):
        program = TextileShader()
        frame = FrameBuffer(size=(self.texImg_.shape[1], self.texImg_.shape[0]))
        frame.Render(default_color=(0,0,0))
        gl.glUseProgram(program)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        self.Render(program)
        textilePositions = frame.FetchData()
        xx, yy = np.meshgrid([i for i in range(self.texImg_.shape[1])], [i for i in range(self.texImg_.shape[0])])
        coordIdx = yy.reshape(-1) * self.texImg_.shape[1] + xx.reshape(-1)
        points = textilePositions.reshape(-1,3)
        mask = np.where(np.sum(np.abs(points)<1e-6,axis=1) != 3)[0]
        self.textiles_ = (coordIdx[mask], points[mask])

    def UpdateTexture(self, camera, uuid, depth, color, depthThres=1e-2):
        if self.texImg_ is None:
            return
        if self.textiles_ is None:
            self.GenerateTextiles()

        # depth test for each textile
        pointsCam = (self.textiles_[1] - camera.renderCam_[:3,3].reshape(1,-1)) @ camera.renderCam_[:3,:3]
        imgX = pointsCam[:,0] / pointsCam[:,2] * camera.intrinsic_['fx'] + camera.intrinsic_['cx']
        imgY = pointsCam[:,1] / pointsCam[:,2] * camera.intrinsic_['fy'] + camera.intrinsic_['cy']
        imgD = pointsCam[:,2]

        validImgMask = (imgX >= 0) * (imgX < camera.intrinsic_['w']) * (imgY >= 0) * (imgY < camera.intrinsic_['h'])
        imgX = imgX[validImgMask]
        imgY = imgY[validImgMask]
        imgD = imgD[validImgMask]
        imgCoord = imgY.astype('int32') * depth.shape[1] + imgX.astype('int32')

        sampleD = depth.reshape(-1)[imgCoord]
        sampleUUID = uuid.reshape(-1)[imgCoord]
        validDMask = np.where((sampleUUID == self.uuid_) * (np.abs(imgD - sampleD) < depthThres))[0]
        if validDMask.shape[0] == 0:
            return
        texCoord = self.textiles_[0][validImgMask]
        texCoord = texCoord[validDMask]
        sampleC = color.reshape(-1,3)[imgCoord[validDMask]]

        self.texImg_.reshape(-1,3)[texCoord] = sampleC

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_)
        gl.glTexImage2D(gl.GL_TEXTURE_2D,0,3,self.texImg_.shape[1], self.texImg_.shape[0],0,gl.GL_RGB,gl.GL_FLOAT, np.flipud(self.texImg_))