from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QSpacerItem, QVBoxLayout, QSizePolicy, QDoubleSpinBox, QLineEdit

from baseModule import SimpleBlackbox

import numpy as np
import traceback


from baseModule import SimpleBlackbox, BaseImplementation, execType

__nodes__ = ["FullScreenQuad", "ShaderProgram", "RenderVao", "RenderFBO", "UniformContainer"]

class vboVaoContainer:
    def __init__(self, vbo, vao, tricount):
        self.vbo = vbo
        self.vao = vao
        self.tricount = tricount

class FullScreenQuadImplementation(BaseImplementation):
    def init(self):
        self.uvxoffset = 0
        self.uvyoffset = 0

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

    def receiveNodedata(self, data):
        if "xoffset" in data:
            self.uvxoffset = data["xoffset"]
        if "yoffset" in data:
            self.uvyoffset = data["yoffset"]

        if self.vbo:
            vertices = np.array([
                # X     Y     Z    R    G    B    U    V
                [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0 + self.uvxoffset, 1.0 + self.uvyoffset],  # Top right
                [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0 + self.uvxoffset, 1.0 + self.uvyoffset],  # Top Left
                [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Right
                [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Left
                [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Right
                [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0 + self.uvxoffset, 1.0 + self.uvyoffset]  # Top Left
            ], 'f')

            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)

class FullScreenQuad(SimpleBlackbox):
    author = "DrLuke"
    name = "Fullscreen Quad"
    modulename = "drluke.opengl.fullscreenquad"

    Category = ["OpenGL", "Primitives"]

    placeable = True

    implementation = FullScreenQuadImplementation

    def __init__(self, *args, **kwargs):
        super(FullScreenQuad, self).__init__(*args, **kwargs)

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()

        self.xoffsetWidget = QDoubleSpinBox()
        self.xoffsetWidget.setMaximum(9999)
        self.xoffsetWidget.setMinimum(-9999)
        self.yoffsetWidget = QDoubleSpinBox()
        self.yoffsetWidget.setMaximum(9999)
        self.yoffsetWidget.setMinimum(-9999)
        self.vlayout.addWidget(self.xoffsetWidget)
        self.vlayout.addWidget(self.yoffsetWidget)

        self.xoffsetWidget.valueChanged.connect(self.offsetchange)
        self.yoffsetWidget.valueChanged.connect(self.offsetchange)

        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)


    def defineIO(self):
        self.addOutput(vboVaoContainer, "vbovaoout", "Quad Out")

    def offsetchange(self, value):
        self.sendDataToImplementations({"xoffset": self.xoffsetWidget.value(), "yoffset": self.yoffsetWidget.value()})

    def serialize(self):
        return {"xoffset": self.xoffsetWidget.value(), "yoffset": self.yoffsetWidget.value()}

    def deserialize(self, data):
        if "xoffset" in data:
            self.xoffsetWidget.setValue(data["xoffset"])
        if "yoffset" in data:
            self.yoffsetWidget.setValue(data["yoffset"])

    def getPropertiesWidget(self):
        return self.propertiesWidget

class ShaderProgramImplementation(BaseImplementation):
    def init(self):
        self.fragmentShader = 0
        self.vertexShader = 0
        self.shaderProgram = None

        self.defaultFragmentShaderCode = """
                #version 330 core
                in vec3 ourColor;
                in vec2 ourTexcoord;
                layout(location = 0) out vec4 outColor;
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
            try:
                self.shaderProgram = shaders.compileProgram(self.fragmentShader, self.vertexShader)
            except:
                pass

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
        fbo = self.runtime.fbo
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)

        vboVaoContainer = self.getReturnOfFirstFunction("vaoin")
        shaderProgram = self.getReturnOfFirstFunction("shaderprogramin")
        uniforms = self.getReturnOfFirstFunction("uniformsin")


        if vboVaoContainer is not None and shaderProgram is not None:
            glUseProgram(shaderProgram)

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.runtime.fbotexture)
            glUniform1i(glGetUniformLocation(shaderProgram, "texIn"), 0)

            # Uniforms
            uniformLoc = glGetUniformLocation(shaderProgram, "t")
            if not uniformLoc == -1:
                glUniform1f(uniformLoc, self.runtime.time)

            uniformLoc = glGetUniformLocation(shaderProgram, "dt")
            if not uniformLoc == -1:
                glUniform1f(uniformLoc, self.runtime.deltatime)

            uniformLoc = glGetUniformLocation(shaderProgram, "res")
            if not uniformLoc == -1:
                glUniform2f(uniformLoc, self.runtime.width, self.runtime.height)

            glBindVertexArray(vboVaoContainer.vao)
            glDrawArrays(GL_TRIANGLES, 0, vboVaoContainer.tricount * 3)
            glBindVertexArray(0)

            uniformsin = self.getReturnOfFirstFunction("uniformsin")
            if type(uniformsin) is dict:
                for uniformname in uniformsin:
                    uniformLoc = glGetUniformLocation(shaderProgram, uniformname)
                    if type(uniformsin[uniformname]) is int or type(uniformsin[uniformname]) is float:
                        if not uniformLoc == -1:
                            glUniform1f(uniformLoc, uniformsin[uniformname])

        self.fireExec("execout")

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
        self.addInput(dict, "uniformsin", "Uniforms")

        self.addOutput(execType, "execout", "Exec Out")

class RenderFboImplementation(BaseImplementation):
    def init(self):
        vertices = np.array([
            # X     Y     Z    R    G    B    U    V
            [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Top right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0, 1.0],  # Top Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0],  # Bottom Right
            [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0, 0],  # Bottom Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0],  # Bottom Right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0, 1.0]  # Top Left
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

        self.fragmentShader = 0
        self.vertexShader = 0
        self.shaderProgram = None

        self.defaultFragmentShaderCode = """
                        #version 330 core
                        in vec3 ourColor;
                        in vec2 ourTexcoord;
                        out vec4 outColor;
                        uniform sampler2D texIn;
                        void main()
                        {
                            outColor = texture(texIn, ourTexcoord);
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

                            ourColor = vec3(0.0);
                            ourTexcoord = texcoord;
                        }
                        """



        vertexCode = self.defaultVertexShaderCode
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

    def render(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        if self.shaderProgram is not None:
            glUseProgram(self.shaderProgram)


            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.runtime.fbotexture)
            glUniform1i(glGetUniformLocation(self.shaderProgram, "texIn"), 0)

            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, 2 * 3)
            glBindVertexArray(0)



    def defineIO(self):
        self.registerFunc("render", self.render)

class RenderFBO(SimpleBlackbox):
    author = "DrLuke"
    name = "Render FBO"
    modulename = "drluke.opengl.renderfbo"

    Category = ["OpenGL"]

    placeable = True

    implementation = RenderFboImplementation

    def defineIO(self):
        self.addInput(execType, "render", "Render")
        self.addOutput(execType, "execOut", "Exec Out")

class UniformContainerImplementation(BaseImplementation):
    def init(self):
        self.value = ""

    def defineIO(self):
        self.registerFunc("contout", self.getContainer)

    def receiveNodedata(self, data):
        self.value = data

    def getContainer(self):
        contin = self.getReturnOfFirstFunction("contin")
        valin = self.getReturnOfFirstFunction("valin")
        if type(contin) is dict and valin is not None:
            contin[self.value] = valin
            return contin
        else:
            return {self.value: valin}

class UniformContainer(SimpleBlackbox):
    author = "DrLuke"
    name = "Uniform Container"
    modulename = "drluke.builtin.uniformcontainer"

    Category = ["OpenGL"]

    placeable = True

    implementation = UniformContainerImplementation

    def __init__(self, *args, **kwargs):
        super(UniformContainer, self).__init__(*args, **kwargs)

        self.text = ""

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.textChanged)

        self.vlayout.addWidget(self.lineEdit)
        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)

    def textChanged(self, text):
        self.text = text
        self.sendDataToImplementations(text)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def defineIO(self):
        self.addInput(dict, "contin", "Container in")
        self.addInput([float, int, list], "valin", "Value in")

        self.addOutput(dict, "contout", "Container out")

    def serialize(self):
        return self.text

    def deserialize(self, data):
        if type(data) is str:
            self.text = data
            self.lineEdit.setText(self.text)