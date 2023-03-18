import OpenGL.GL as gl
import numpy as np
import cv2
class FrameBuffer:
	def __init__(self, size=(1024,768)):
		self.width_ = size[0]
		self.height_ = size[1]
		self.frameBuffer_ = gl.glGenFramebuffers(1)
		gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frameBuffer_)

		self.renderedTexture_ = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderedTexture_)

		gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width_, self.height_, 0, gl.GL_RGB, gl.GL_FLOAT,None)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR); 
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE);
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE);

		self.depthRenderBuffer_ = gl.glGenRenderbuffers(1);
		gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depthRenderBuffer_);
		gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, self.width_, self.height_);
		gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.depthRenderBuffer_);

		gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, self.renderedTexture_, 0);
		gl.glDrawBuffers(1, [gl.GL_COLOR_ATTACHMENT0])
		if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
			print('Fail to init frame buffer!')
			exit(0)

	def Render(self,default_color=(0.5,0.5,0.5)):
		gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frameBuffer_)
		gl.glViewport(0,0,self.width_,self.height_)
		gl.glClearColor(default_color[0],default_color[1],default_color[2],1)


	def FetchData(self):
		pixels = np.zeros((self.height_,self.width_,3),dtype='float32')

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderedTexture_)
		gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, gl.GL_FLOAT, pixels)

		return np.ascontiguousarray(np.flipud(pixels))

	def Release(self):
		gl.glDeleteFramebuffers(1, [self.frameBuffer_])
		gl.glDeleteTextures(1,[self.renderedTexture_])
		gl.glDeleteRenderbuffers(1, [self.depthRenderBuffer_])