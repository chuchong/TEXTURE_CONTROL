import numpy as np
import OpenGL.GL as gl

class Camera:
    def __init__(self, camPos=(0,0,-5), lookAt=(0,0,1), windowSize=(640,480), fov=60.0):
        zAxis = np.array(lookAt)
        yAxis = np.array([0,1,0])
        xAxis = np.cross(yAxis,zAxis)
        self.cam2world_ = np.eye(4).astype('float32')
        self.cam2world_[:3,0] = xAxis
        self.cam2world_[:3,1] = yAxis
        self.cam2world_[:3,2] = zAxis
        self.cam2world_[:3,3] = camPos

        self.renderCam_ = self.cam2world_.copy()

        self.fov_ = fov
        self.intrinsic_ = {}
        self.UpdateWindow(windowSize)

        self.controlMode_ = 'object'
        self.status_ = 'rest'
        self.pos_ = np.array([0,0])

    def ApplyRotation(self, vec):
        angleY = vec[0] * np.pi / self.intrinsic_['w'] * 2
        angleX = vec[1] * np.pi / self.intrinsic_['h'] * 2

        rotX = np.array([
            [1, 0, 0, 0],
            [0, np.cos(angleX), -np.sin(angleX), 0,],
            [0, np.sin(angleX), np.cos(angleX), 0,],
            [0, 0, 0, 1]
            ], dtype='float32')

        rotY = np.array([
            [np.cos(angleY), 0, -np.sin(angleY), 0,],
            [0, 1, 0, 0],
            [np.sin(angleY), 0, np.cos(angleY), 0,],
            [0, 0, 0, 1]
            ], dtype='float32')

        if self.controlMode_ == 'camera':
            self.renderCam_ = self.renderCam_ @ (rotX @ rotY)
        else:
            world2cam = np.linalg.inv(self.renderCam_)
            world2cam[:3,:3] = ((rotY @ rotX) @ world2cam)[:3,:3]
            self.renderCam_ = np.linalg.inv(world2cam)

    def ApplyTranslation(self, vec):
        xAxis = self.renderCam_[:3,0]
        yAxis = self.renderCam_[:3,1]
        l = np.linalg.norm(self.renderCam_[:3,3]) * 2
        self.renderCam_[:3,3] -= (xAxis * vec[0] / self.intrinsic_['w'] + yAxis * vec[1] / self.intrinsic_['h']) * l

    def ApplyZoom(self, v):
        zAxis = self.renderCam_[:3,2]
        l = np.linalg.norm(self.renderCam_[:3,3]) * 2
        self.renderCam_[:3,3] -= (zAxis * v / self.intrinsic_['h']) * l

    def UpdateStatus(self, status):
        self.status_ = status

    def UpdateEvent(self, pos):
        if self.status_ == 'rotate':
            self.ApplyRotation(pos - self.pos_)
        elif self.status_ == 'translate':
            self.ApplyTranslation(pos - self.pos_)
        elif self.status_ == 'zoom':
            self.ApplyZoom(np.sum(pos - self.pos_))
        self.pos_ = pos

    def Finalize(self):
        self.cam2world_ = self.renderCam_.copy()
        self.status_ = 'rest'

    def Drop(self):
        self.renderCam_ = self.cam2world_.copy()
        self.status_ = 'rest'

    def UpdateWindow(self,windowSize):
        self.intrinsic_['fx'] = windowSize[0] * 0.5 / np.tan(0.5 * self.fov_ / 180.0 * np.pi)
        self.intrinsic_['fy'] = windowSize[1] * 0.5 / np.tan(0.5 * self.fov_ / 180.0 * np.pi)
        self.intrinsic_['cx'] = windowSize[0] * 0.5
        self.intrinsic_['cy'] = windowSize[1] * 0.5
        self.intrinsic_['w'] = windowSize[0]
        self.intrinsic_['h'] = windowSize[1]

    def Render(self, program):
        world2cam = np.linalg.inv(self.renderCam_).astype('float32')
        world2cam = np.ascontiguousarray(np.transpose(world2cam))

        uMatrixID = gl.glGetUniformLocation(program, "view");
        gl.glUniformMatrix4fv(uMatrixID, 1, gl.GL_FALSE, world2cam)

        uFx = gl.glGetUniformLocation(program, "fx");
        uFy = gl.glGetUniformLocation(program, "fy");
        uCx = gl.glGetUniformLocation(program, "cx");
        uCy = gl.glGetUniformLocation(program, "cy");

        gl.glUniform1f(uFx, self.intrinsic_['fx'] / self.intrinsic_['w'] * 2)
        gl.glUniform1f(uFy, -self.intrinsic_['fy'] / self.intrinsic_['h'] * 2)
        gl.glUniform1f(uCx, (self.intrinsic_['cx'] - self.intrinsic_['w'] * 0.5) / self.intrinsic_['w'] * 2)
        gl.glUniform1f(uCy, -(self.intrinsic_['cy'] - self.intrinsic_['h'] * 0.5) / self.intrinsic_['h'] * 2)

