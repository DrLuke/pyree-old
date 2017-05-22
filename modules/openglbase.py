from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *


from baseModule import SimpleBlackbox

import numpy as np
import traceback


from baseModule import SimpleBlackbox, BaseImplementation, execType

__nodes__ = ["FullScreenQuad", "ShaderProgram", "RenderVao"]

class vboVaoContainer:
    def __init__(self, vbo, vao, tricount):
        self.vbo = vbo
        self.vao = vao
        self.tricount = tricount

class FullScreenQuadImplementation(BaseImplementation):
    def init(self):
        vertices = np.array([
            # X     Y     Z    R    G    B    U    V
            [1.0,  1.0,  0.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Top right
            [-1.0, 1.0,  0.0, 0.0, 1.0, 1.0, 0,   1.0],  # Top Left
            [1.0,  -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0  ],  # Bottom Right
            [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0,   0  ],  # Bottom Left
            [1.0,  -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0  ],  # Bottom Right
            [-1.0,  1.0, 0.0, 0.0, 1.0, 1.0, 0,   1.0]  # Top Left
        ], 'f')

        # Generate vertex buffer object and fill it with vertex data from above
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Generate vertex array object and pass vertex data into it
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # XYZ
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, None)
        glEnableVertexAttribArray(0)

        # RGB
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        # UV
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, ctypes.c_void_p(6 * vertices.itemsize))
        glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.container = vboVaoContainer(self.vbo, self.vao, 2)

    def defineIO(self):
        self.registerFunc("vbovaoout", lambda: self.container)

class FullScreenQuad(SimpleBlackbox):
    author = "DrLuke"
    name = "Fullscreen Quad"
    modulename = "drluke.opengl.fullscreenquad"

    Category = ["OpenGL", "Primitives"]

    placeable = True

    implementation = FullScreenQuadImplementation

    def defineIO(self):
        self.addOutput(vboVaoContainer, "vbovaoout", "Quad Out")


class ShaderProgramImplementation(BaseImplementation):
    def init(self):
        self.fragmentShader = 0
        self.vertexShader = 0
        self.shaderProgram = None

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

    def compile(self):
        vertexCode = self.getReturnOfFirstFunction("vertexin")
        fragmentCode = self.getReturnOfFirstFunction("fragmentin")

        if vertexCode is None:
            vertexCode = self.defaultVertexShaderCode
        if fragmentCode is None:
            fragmentCode = self.defaultFragmentShaderCode

        self.vertexShaderCode = vertexCode
        self.fragmentShaderCode = fragmentCode

        try:
            self.fragmentShader = shaders.compileShader(self.fragmentShaderCode, GL_FRAGMENT_SHADER)
        except:
            print(traceback.print_exc())
            self.fragmentShader = shaders.compileShader(self.defaultFragmentShaderCode, GL_FRAGMENT_SHADER)

        try:
            self.vertexShader = shaders.compileShader(self.vertexShaderCode, GL_VERTEX_SHADER)
        except:
            print(traceback.print_exc())
            self.vertexShader = shaders.compileShader(self.defaultVertexShaderCode, GL_VERTEX_SHADER)

        # -- Generate Shader program
        if isinstance(self.fragmentShader, int) and isinstance(self.vertexShader, int):
            self.shaderProgram = shaders.compileProgram(self.fragmentShader, self.vertexShader)

        self.fireExec("execout")

    def defineIO(self):
        self.registerFunc("compile", self.compile)
        self.registerFunc("shaderout", lambda: self.shaderProgram)

class ShaderProgram(SimpleBlackbox):
    author = "DrLuke"
    name = "Shader Program"
    modulename = "drluke.opengl.shaderprogram"

    Category = ["OpenGL"]

    placeable = True

    implementation = ShaderProgramImplementation

    def defineIO(self):
        self.addInput(execType, "compile", "Compile Program")
        self.addInput(str, "vertexin", "Vertex Shader Code")
        self.addInput(str, "fragmentin", "Fragment Shader Code")

        self.addOutput(execType, "execout", "Exec")
        self.addOutput(shaders.ShaderProgram, "shaderout", "Shader Program")


class RenderVaoImplementation(BaseImplementation):
    def init(self):
        pass

    def render(self):
        vboVaoContainer = self.getReturnOfFirstFunction("vaoin")
        shaderProgram = self.getReturnOfFirstFunction("shaderprogramin")
        uniforms = self.getReturnOfFirstFunction("uniformsin")


        if vboVaoContainer is not None and shaderProgram is not None:
            glUseProgram(shaderProgram)

            glBindVertexArray(vboVaoContainer.vao)
            glDrawArrays(GL_TRIANGLES, 0, vboVaoContainer.tricount * 3)
            glBindVertexArray(0)

    def defineIO(self):
        self.registerFunc("render", self.render)

class RenderVao(SimpleBlackbox):
    author = "DrLuke"
    name = "Render VAO"
    modulename = "drluke.opengl.rendervao"

    Category = ["OpenGL"]

    placeable = True

    implementation = RenderVaoImplementation

    def defineIO(self):
        self.addInput(execType, "render", "Render")
        self.addInput(vboVaoContainer, "vaoin", "Vao")
        self.addInput(shaders.ShaderProgram, "shaderprogramin", "Shader Program")
        self.addInput(str, "uniformsin", "Uniforms")