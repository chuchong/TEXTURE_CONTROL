import os
from os.path import dirname, realpath
import sys
ROOT = dirname(realpath(__file__)) + '/..'
sys.path.append(ROOT + '/src')
import numpy as np
import ctypes

from PyQt5.QtWidgets import QApplication,QWidget,QOpenGLWidget
from PyQt5.QtGui import QOpenGLWindow
import OpenGL.GL as gl
from PyQt5 import QtCore, QtGui

from scene import Scene
from camera import Camera
from mesh import Mesh
from shader_programs import *
from framebuffer import FrameBuffer

import cv2
class Paint3DWidget(QOpenGLWidget):
    def __init__(self,parent):
        QOpenGLWidget.__init__(self,parent)
        self.setMouseTracking(True)
        self.imgSize_ = (2000,1600)
        self.fov_ = 60.0
        self.ruler_ = 1.0
        self.minD_ = 0.0
        self.maxD_ = 10.0

        self.offlineTask_ = None
        self.camera_ = Camera(camPos=(0,0,-5.0 * self.ruler_),fov=self.fov_,windowSize=self.imgSize_)

    def initializeGL(self):
        self.mouseLoc_ = np.array([0,0])

        self.scene_ = Scene()
        self.scene_.AddShapeFromFile(ROOT + '/data/cube.obj', loadTexture=False)
        self.scene_.AddShapeFromFile(ROOT + '/data/plane.obj', loadTexture=False)

        self.refScene_ = Scene()
        self.refScene_.AddShapeFromFile(ROOT + '/data/cube.obj')

        self.quad_ = Mesh()
        self.quad_.V_ = np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]).astype('float32')
        self.quad_.F_ = np.array([[0,1,2],[0,2,3]]).astype('int32')
        self.quad_.UpdateRenderData()

        self.frameBuffer_ = None

        self.programs_ = {
            'position': PositionShader(),
            'normal': NormalShader(),
            'depth': DepthShader(),
            'texture': TextureShader(),
            'uv': UVShader(),
            'quad': QuadShader(),
            'uuid': UUIDShader(),
        }
        self.program_ = 'texture'

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_R:
            self.camera_.UpdateStatus('rotate')
        elif event.key() == QtCore.Qt.Key_G:
            self.camera_.UpdateStatus('translate')
        elif event.key() == QtCore.Qt.Key_Z:
            self.camera_.UpdateStatus('zoom')
        elif event.key() == QtCore.Qt.Key_S:
            self.saveImg()
        event.accept()

    def saveImg(self):
        img = self.frameBuffer_.FetchData()
        from PIL import Image
        print(img.shape)
        img = (img * 255).astype(np.uint8) 
        image = Image.fromarray(img)
        image.save('test.png')

    def mouseMoveEvent(self, event):
        loc = np.array([event.pos().x(),event.pos().y()])
        self.camera_.UpdateEvent(loc)
        if self.camera_.status_ != 'rest':
            self.update()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == 1:
            if self.camera_.status_ != 'rest':
                self.camera_.Finalize()
                self.update()
        else:
            if self.camera_.status_ != 'rest':
                self.camera_.Drop()
                self.update()
        
    def paintGL(self):
        viewport = np.zeros((4),dtype='int32')
        gl.glGetIntegerv(gl.GL_VIEWPORT, viewport)
        if self.offlineTask_ is not None:
            self.offlineTask_()
            self.offlineTask_ = None

        if self.program_ == 'edge':
            depth = self.RenderToCPU('depth', self.scene_)[:,:,0]
            normal = self.RenderToCPU('normal', self.scene_) * 2 - 1
            edge = self.EdgeFromDepthAndNormal(depth, normal, distThres=2e-1, angleThres=20.0)
            # send it back to render buffer
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.frameBuffer_.renderedTexture_)
            gl.glTexImage2D(gl.GL_TEXTURE_2D,0,3,edge.shape[1], edge.shape[0],0,gl.GL_RGB,gl.GL_FLOAT, np.flipud(edge))

            gl.glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
            self.RenderFrameBuffer(self.frameBuffer_)
        else:
            self.RenderToFrameBuffer(self.program_, self.scene_)
            gl.glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
            self.RenderFrameBuffer(self.frameBuffer_)

    def RenderToFrameBuffer(self, programName, scene, default_color=(0.5,0.5,0.5)):
        if not programName in self.programs_:
            return
        if self.frameBuffer_ is None:
            self.frameBuffer_ = FrameBuffer(size=self.imgSize_)

        self.frameBuffer_.Render(default_color)
        program = self.programs_[programName]
        gl.glUseProgram(program)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        self.camera_.UpdateWindow(self.imgSize_)
        self.camera_.Render(program)
        if self.program_ == 'depth':
            uMinD = gl.glGetUniformLocation(program, "minDepth")
            uMaxD = gl.glGetUniformLocation(program, "maxDepth")
            gl.glUniform1f(uMinD, self.minD_)
            gl.glUniform1f(uMaxD, self.maxD_)

        scene.Render(program)

    def RenderFrameBuffer(self, frameBuffer):
        program = self.programs_['quad']
        gl.glUseProgram(program)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.defaultFramebufferObject())
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, frameBuffer.renderedTexture_)
        uImg = gl.glGetUniformLocation(program, "img")
        gl.glUniform1i(uImg, 0)
        self.quad_.Render(program)

    def EdgeFromDepthAndNormal(self, depth, normal, distThres=1e-1, angleThres=20.0):
        mask = depth.copy()
        mask[:] = 0
        mask[:-1] += np.abs(np.sum(normal[:-1] * normal[1:], axis=-1)) < np.cos(angleThres / 180.0 * np.pi)
        mask[:,:-1] += np.abs(np.sum(normal[:,:-1] * normal[:,1:], axis=-1)) < np.cos(angleThres / 180.0 * np.pi)
        mask[depth==0] = 0

        mask[:-1] += np.abs(depth[:-1] - depth[1:]) > distThres
        mask[:,:-1] += np.abs(depth[:,:-1] - depth[:,1:]) > distThres
        return (np.stack([mask,mask,mask],axis=-1) > 0).astype('float32')

    def RenderToCPU(self, programName, scene):
        self.RenderToFrameBuffer(programName, scene, default_color=(0,0,0))
        return self.frameBuffer_.FetchData()

    def SetOfflineRender(self, call):
        self.offlineTask_ = call


if __name__ == '__main__':
    app = QApplication([])
    widget = MinimalGLWidget()
    widget.show()
    app.exec_()
