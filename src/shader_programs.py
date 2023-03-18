import OpenGL.GL as gl

def CompileShader(vertex_code, fragment_code):
    program = gl.glCreateProgram()
    vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

    # Set shaders source
    gl.glShaderSource(vertex, vertex_code)
    gl.glShaderSource(fragment, fragment_code)

    # Compile shaders
    gl.glCompileShader(vertex)
    if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
        error = gl.glGetShaderInfoLog(vertex).decode()
        print("Vertex shader compilation error: %s", error)
        raise RuntimeError("Vertex shader compilation error")

    gl.glCompileShader(fragment)
    if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
        error = gl.glGetShaderInfoLog(fragment).decode()
        print(error)
        raise RuntimeError("Fragment shader compilation error")

    gl.glAttachShader(program, vertex)
    gl.glAttachShader(program, fragment)
    gl.glLinkProgram(program)

    if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
        print(gl.glGetProgramInfoLog(program))
        raise RuntimeError('Linking error')

    gl.glDetachShader(program, vertex)
    gl.glDetachShader(program, fragment)
    return program

global_shaders = {}
def PositionShader():
    global global_shaders
    if not 'position' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        varying vec3 vpos;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
          vpos = position;
        }
        '''

        fragment_code = '''
        #version 130
        varying vec3 vpos;
        void main()
        {
          gl_FragColor = vec4(vpos * 0.5 + vec3(0.5,0.5,0.5), 1.0);
        }
        '''
        global_shaders['position'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['position']

def NormalShader():
    global global_shaders
    if not 'normal' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        attribute vec3 normal;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        varying vec3 vpos;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          // projection
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
          vpos = normal;
        }
        '''

        fragment_code = '''
        #version 130
        varying vec3 vpos;
        void main()
        {
          gl_FragColor = vec4(vpos * 0.5 + vec3(0.5,0.5,0.5), 1.0);
        }
        '''
        global_shaders['normal'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['normal']

def DepthShader():
    global global_shaders
    if not 'depth' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        varying float depth;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
          depth = camPosition.z;
        }
        '''

        fragment_code = '''
        #version 130
        varying float depth;
        uniform float minDepth;
        uniform float maxDepth;
        void main()
        {
          float z = 0.0;
          if (maxDepth <= minDepth)
            gl_FragColor = vec4(depth, depth, depth, 1);
          else {
            z = (depth - minDepth) / (maxDepth - minDepth);
            gl_FragColor = vec4(z, z, z, 1);
          }
        }
        '''
        global_shaders['depth'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['depth']

def TextureShader():
    global global_shaders
    if not 'texture' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        attribute vec2 texCoord;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        varying vec2 uv;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
          uv = texCoord;
        }
        '''

        fragment_code = '''
        #version 130
        varying vec2 uv;
        uniform sampler2D texImg;
        void main()
        {
          gl_FragColor = texture2D(texImg, uv);
        }
        '''
        global_shaders['texture'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['texture']

def UVShader():
    global global_shaders
    if not 'uv' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        attribute vec2 texCoord;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        varying vec2 uv;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
          uv = texCoord;
        }
        '''

        fragment_code = '''
        #version 130
        varying vec2 uv;
        void main()
        {
          gl_FragColor = vec4(uv, 1, 1);
        }
        '''
        global_shaders['uv'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['uv']

def QuadShader():
    global global_shaders
    if not 'quad' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        varying vec2 uv;
        void main()
        {
          gl_Position = vec4(position, 1.0);
          uv = vec2(position.xy * 0.5 + vec2(0.5,0.5));
        }
        '''

        fragment_code = '''
        #version 130
        varying vec2 uv;
        uniform sampler2D img;
        void main()
        {
          gl_FragColor = texture2D(img, uv);
        }
        '''
        global_shaders['quad'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['quad']

def TextileShader():
    global global_shaders
    if not 'textile' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        attribute vec2 texCoord;
        varying vec3 vpos;
        void main()
        {
          gl_Position = vec4(texCoord.x * 2.0 - 1.0,
            texCoord.y * 2.0 - 1.0,
            0, 1);
          vpos = position;
        }
        '''

        fragment_code = '''
        #version 130
        varying vec3 vpos;
        void main()
        {
          gl_FragColor = vec4(vpos, 1);
        }
        '''
        global_shaders['textile'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['textile']

def UUIDShader():
    global global_shaders
    if not 'uuid' in global_shaders:
        vertex_code = '''
        #version 130
        attribute vec3 position;
        uniform float fx, fy, cx, cy;
        uniform mat4 view;
        void main()
        {
          vec3 camPosition = (view * vec4(position.xyz,1.0)).xyz;
          gl_Position = vec4(camPosition.x * fx + cx,
            camPosition.y * fy + cy,
            (camPosition.z - 0.1) / (1000.0 - 0.1) * 2.0 - 1.0,
            camPosition.z);
        }
        '''

        fragment_code = '''
        #version 130
        varying vec3 vpos;
        uniform float uuid;
        void main()
        {
          gl_FragColor = vec4(uuid, uuid, uuid, 1.0);
        }
        '''
        global_shaders['uuid'] = CompileShader(vertex_code, fragment_code)
    return global_shaders['uuid']
