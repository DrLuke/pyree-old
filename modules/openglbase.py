__author__ = 'drluke'


from baseModule import BaseNode, Pin

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PyQt5.QtWidgets import QDialog

import numpy as np

import traceback

import os

import PIL
from PIL import Image, ImageFont, ImageDraw

__nodes__ = ["Quad", "ShaderProgram", "RenderVAO", "UniformsContainer", "TextureContainer"]

class Quad(BaseNode):
    nodeName = "drluke.openglbase.Quad"
    name = "Quad"
    desc = "This is a quad shape, consisting of 2 triangles."
    category = "Shapes"
    placable = True

    class settingsDialog(QDialog):
        """ Dialog for setting vertex points """
        def __init__(self, extraData, sheetview, sheethandler):
            super().__init__()
            print(extraData)

            self.data = {"Test": "yes"}


    def init(self):
        vertices = np.array([
            [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0],   # Top right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0, 1.0],    # Top Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0],    # Bottom Right
            [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0, 0],      # Bottom Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0],  # Bottom Right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0, 1.0]  # Top Left
        ], 'f')

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, None)
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, ctypes.c_void_p(6 * vertices.itemsize))
        glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindVertexArray(0)

    def delete(self):
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])

    def getVao(self):
        return self.vao

    def getVbo(self):
        return self.vbo

    def getTricount(self):
        return int(2)

    inputDefs = [
    ]

    outputDefs = [
        Pin("vbo", "vbo", getVbo),
        Pin("vao", "vao", getVao),
        Pin("tricount", "int", getTricount)
    ]


class ShaderProgram(BaseNode):
    nodeName = "drluke.openglbase.ShaderProgram"
    name = "Shader Program"
    desc = "Generate shader program from vertex and fragment shader."
    category = "Shaders"
    placable = True

    def init(self):
        self.defaultFragmentShaderCode = """
        #version 330 core

        in vec3 ourColor;
        in vec2 ourTexcoord;

        out vec4 outColor;

        void main()
        {
            outColor = vec4(ourColor.r, ourColor.g, ourColor.b, 1.0);
        }
        """

        self.defaultVertexShaderCode = """
        #version 330 core

        layout (location = 0) in vec3 position;
        layout (location = 1) in vec3 color;
        layout (location = 2) in vec2 texcoord;

        out vec3 ourColor;
        out vec2 ourTexcoord;

        void main()
        {
            gl_Position = vec4(position.x, position.y, position.z, 1.0);

            ourColor = color;
            ourTexcoord = texcoord;

        }
        """

    def run(self):
        self.vertexShaderCode = self.getInput(1)
        self.fragmentShaderCode = self.getInput(2)

        # -- Fragment Shader
        if not self.fragmentShaderCode or not isinstance(self.fragmentShaderCode, str):
            self.fragmentShaderCode = self.defaultFragmentShaderCode

        try:
            self.fragmentShader = shaders.compileShader(self.fragmentShaderCode, GL_FRAGMENT_SHADER)
        except:
            print(traceback.print_exc())
            self.fragmentShader = shaders.compileShader(self.defaultFragmentShaderCode, GL_FRAGMENT_SHADER)

        # -- Vertex Shader
        if not self.vertexShaderCode or not isinstance(self.vertexShaderCode, str):
            self.vertexShaderCode = self.defaultVertexShaderCode

        try:
            self.vertexShader = shaders.compileShader(self.vertexShaderCode, GL_VERTEX_SHADER)
        except:
            print(traceback.print_exc())
            self.vertexShader = shaders.compileShader(self.defaultVertexShaderCode, GL_VERTEX_SHADER)

        # -- Generate Shader program
        if isinstance(self.fragmentShader, int) and isinstance(self.vertexShader, int):
            self.shaderprogram = shaders.compileProgram(self.fragmentShader, self.vertexShader)

        self.fireExec(0)

    def getShaderprogram(self):
        return self.shaderprogram

    inputDefs = [
        Pin("Generate", "exec", run, "Create the shaderprogram with new input"),
        Pin("Vertex Shader Code", "string", None),
        Pin("Fragment Shader Code", "string", None)
    ]

    outputDefs = [
        Pin("exec", "exec", None),
        Pin("Shader Program", "shaderprogram", getShaderprogram)
    ]

class RenderVAO(BaseNode):
    nodeName = "drluke.openglbase.RenderVAO"
    name = "Render VAO"
    desc = "Render shader program with VAO"
    category = "Shaders"
    placable = True

    def init(self):
        pass

    def run(self):

        glEnable(GL_TEXTURE_2D)
        #glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.shaderprogram = self.getInput(1)
        self.vao = self.getInput(2)

        self.uniformsContainer = self.getInput(4)
        self.textureContainer = self.getInput(5)

        glUseProgram(self.shaderprogram)

        if self.uniformsContainer is not None:
            for uniformName in self.uniformsContainer:
                uniformLoc = glGetUniformLocation(self.shaderprogram, uniformName)
                if not uniformLoc == -1 and None not in self.uniformsContainer[uniformName]:    # Location is valid
                    if len(self.uniformsContainer[uniformName]) == 1:
                        glUniform1f(uniformLoc, self.uniformsContainer[uniformName][0])
                    elif len(self.uniformsContainer[uniformName]) == 2:
                        glUniform2f(uniformLoc, self.uniformsContainer[uniformName][0], self.uniformsContainer[uniformName][1])
                    elif len(self.uniformsContainer[uniformName]) == 2:
                        glUniform3f(uniformLoc, self.uniformsContainer[uniformName][0], self.uniformsContainer[uniformName][1], self.uniformsContainer[uniformName][2])
                    elif len(self.uniformsContainer[uniformName]) == 2:
                        glUniform4f(uniformLoc, self.uniformsContainer[uniformName][0], self.uniformsContainer[uniformName][1], self.uniformsContainer[uniformName][2], self.uniformsContainer[uniformName][3])

        if self.textureContainer is not None:
            for key in self.textureContainer:
                if key == 0:
                    glActiveTexture(GL_TEXTURE0)
                    glBindTexture(GL_TEXTURE_2D, self.textureContainer[0])
                elif key == 1:
                    glActiveTexture(GL_TEXTURE1)
                    glBindTexture(GL_TEXTURE_2D, self.textureContainer[1])
                elif key == 2:
                    glActiveTexture(GL_TEXTURE2)
                    glBindTexture(GL_TEXTURE_2D, self.textureContainer[2])
                elif key == 3:
                    glActiveTexture(GL_TEXTURE3)
                    glBindTexture(GL_TEXTURE_2D, self.textureContainer[3])

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.getInput(3)*3)
        glBindVertexArray(0)

        #glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

    inputDefs = [
        Pin("exec", "exec", run, "Start render"),
        Pin("Shader Program", "shaderprogram", None),
        Pin("VAO", "vao", None),
        Pin("Tricount", "int", None, "Number of Tris to render"),
        Pin("Uniforms", "uniformscontainer", None),
        Pin("Textures", "texturecontainer", None)
    ]

    outputDefs = [
    ]

class UniformsContainer(BaseNode):
    nodeName = "drluke.openglbase.UniformsContainer"
    name = "Uniforms Container"
    desc = "Add Uniforms to a container, and then pass them into a render node!"
    category = "Shaders"
    placable = True

    def init(self):
        self.uniformsContainer = None

    def run(self):
        self.uniformsContainer = self.getInput(1)

        if self.uniformsContainer is None:
            self.uniformsContainer = {}

        if isinstance(self.getInput(2), str) and isinstance(self.getInput(3), list):
            self.uniformsContainer[self.getInput(2)] = self.getInput(3)

        self.fireExec(0)

    def getContainer(self):
        return self.uniformsContainer

    inputDefs = [
        Pin("Add", "exec", run, "Add Uniform to Container"),
        Pin("Container", "uniformscontainer", None, "Leave this unconnected to create new container"),
        Pin("Uniform Name", "string", None),
        Pin("Uniform", "list", None)
    ]

    outputDefs = [
        Pin("exec", "exec", None),
        Pin("Container", "uniformscontainer", getContainer),
    ]

class TextureContainer(BaseNode):
    nodeName = "drluke.openglbase.TextureContainer"
    name = "Texture Container"
    desc = "Add Uniforms to a container, and then pass them into a render node!"
    category = "Shaders"
    placable = True

    def init(self):
        self.textureContainer = None

    def run(self):
        self.textureContainer = {}

        if self.getInput(1) is not None and os.path.exists(self.getInput(1)):
            img = Image.open(self.getInput(1))
            img = img.convert('RGBA').transpose(PIL.Image.FLIP_TOP_BOTTOM)
            img_data = np.array(list(img.getdata()), 'B')
            self.textureContainer[0] = glGenTextures(1)
            glPixelStorei(GL_UNPACK_ALIGNMENT,1)
            glBindTexture(GL_TEXTURE_2D, self.textureContainer[0])
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.size[0], img.size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)

        #glBindTexture(0)

    def getContainer(self):
        return self.textureContainer

    inputDefs = [
        Pin("Create", "exec", run, "Add Uniform to Container"),
        Pin("Path 0", "string", None),
        Pin("Path 1", "string", None),
        Pin("Path 2", "string", None),
        Pin("Path 3", "string", None)
    ]

    outputDefs = [
        Pin("exec", "exec", None),
        Pin("Textures", "texturecontainer", getContainer),
    ]