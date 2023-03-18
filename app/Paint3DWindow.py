import os
from os.path import dirname, realpath
import sys
ROOT = dirname(realpath(__file__)) + '/..'
sys.path.append(ROOT + '/src')
sys.path.append(ROOT + '/ui')

from PyQt5 import QtCore, QtGui, QtWidgets

from Ui_Paint3DWindow import Ui_Paint3DWindow
import numpy as np
import cv2

class Paint3DWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_Paint3DWindow() #code from designer!!
        self.ui.setupUi(self)

        self.ui.radioObject.setChecked(True)
        self.ui.radioTexture.setChecked(True)

        self.ui.radioCamera.clicked.connect(lambda: self.UpdateConfig())
        self.ui.radioObject.clicked.connect(lambda: self.UpdateConfig())

        self.ui.radioPosition.clicked.connect(lambda: self.UpdateConfig())
        self.ui.radioTexture.clicked.connect(lambda: self.UpdateConfig())
        self.ui.radioDepth.clicked.connect(lambda: self.UpdateConfig())
        self.ui.radioNormal.clicked.connect(lambda: self.UpdateConfig())
        self.ui.radioEdge.clicked.connect(lambda: self.UpdateConfig())

        self.ui.editMinD.setValidator(QtGui.QDoubleValidator())
        self.ui.editMaxD.setValidator(QtGui.QDoubleValidator())
        self.ui.editMinD.setText('0.0')
        self.ui.editMaxD.setText('10.0')

        self.ui.editMinD.textChanged.connect(lambda: self.UpdateConfig())
        self.ui.editMaxD.textChanged.connect(lambda: self.UpdateConfig())

        self.ui.editMinD.returnPressed.connect(lambda: self.ReleaseFocus())
        self.ui.editMaxD.returnPressed.connect(lambda: self.ReleaseFocus())

        self.ui.buttonPaint.clicked.connect(lambda: self.Paint())
        self.UpdateConfig()
        self.ReleaseFocus()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            exit(0)
        self.ui.renderWidget.keyPressEvent(event)

    def UpdateConfig(self):
        if self.ui.radioCamera.isChecked():
            self.ui.renderWidget.camera_.controlMode_ = 'camera'
        else:
            self.ui.renderWidget.camera_.controlMode_ = 'object'

        if self.ui.radioPosition.isChecked():
            self.ui.renderWidget.program_ = 'position'
        elif self.ui.radioTexture.isChecked():
            self.ui.renderWidget.program_ = 'texture'
        elif self.ui.radioDepth.isChecked():
            self.ui.renderWidget.program_ = 'depth'
        elif self.ui.radioNormal.isChecked():
            self.ui.renderWidget.program_ = 'normal'
        elif self.ui.radioEdge.isChecked():
            self.ui.renderWidget.program_ = 'edge'

        self.ui.renderWidget.minD_ = float(self.ui.editMinD.text())
        self.ui.renderWidget.maxD_ = float(self.ui.editMaxD.text())

        self.ui.renderWidget.update()

    def ReleaseFocus(self):
        self.ui.renderWidget.setFocus()

    def Paint(self):
        self.ui.renderWidget.SetOfflineRender(self.RunPaint)
        self.ui.renderWidget.update()

    def RunPaint(self):
        uuid = (self.ui.renderWidget.RenderToCPU('uuid', self.ui.renderWidget.scene_)[:,:,0] + 0.5).astype('int32')
        uv = self.ui.renderWidget.RenderToCPU('uv', self.ui.renderWidget.scene_)
        depth = self.ui.renderWidget.RenderToCPU('depth', self.ui.renderWidget.scene_)[:,:,0]
        normal = self.ui.renderWidget.RenderToCPU('normal', self.ui.renderWidget.scene_) * 2 - 1
        edge = self.ui.renderWidget.EdgeFromDepthAndNormal(depth, normal, distThres=2e-1, angleThres=20.0)

        # we should generate color based on the depth/normal, etc.
        color = self.ui.renderWidget.RenderToCPU('texture', self.ui.renderWidget.refScene_)

        self.ui.renderWidget.scene_.UpdateTexture(self.ui.renderWidget.camera_, uuid, depth, color)
        self.ui.renderWidget.update()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Paint3DWindow()

    window.show()
    sys.exit(app.exec_())
