#version 330 core

in vec3 ourColor;
in vec2 ourTexcoord;

out vec4 outCol;

uniform vec2 res;
uniform float t;

uniform float colorangle;

uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;

float iGlobalTime;
vec2 iResolution;

void mainImage(out vec4 fragColor, in vec2 fragCoord);

void main() {
    iResolution = res;
    iGlobalTime = t;
    mainImage(outCol, gl_FragCoord.xy);
}

#define MARCHLIMIT 70

vec3 camPos = vec3(0.0, 0.0, -1.0);
vec3 ld = vec3(0.0, 0.0, 1.0);
vec3 up = vec3(0.0, 1.0, 0.0);
vec3 right = vec3(1.0, 0.0, 0.0);
vec3 lightpos = vec3(1.5, 1.5, 1.5);


// Smooth HSV to RGB conversion
vec3 hsv2rgb_smooth( in vec3 c )
{
    vec3 rgb = clamp( abs(mod(c.x*6.0+vec3(0.0,4.0,2.0),6.0)-3.0)-1.0, 0.0, 1.0 );

	rgb = rgb*rgb*(3.0-2.0*rgb); // cubic smoothing

	return c.z * mix( vec3(1.0), rgb, c.y);
}

vec4 range(vec3 p)
{

    // Sphere with Radius
    vec3 spherepos = vec3(0.0, 0.0, 0.0);
    float radius = log(sin(iGlobalTime*0.1)*0.05+1.0)+0.1;

    p = mod(p + vec3(0.5,0.5,0.5), vec3(1.0,1.0,1.0)) - vec3(0.5,0.5,0.5);
    spherepos = mod(spherepos + vec3(0.5,0.5,0.5), vec3(1.0,1.0,1.0)) - vec3(0.5,0.5,0.5);

    vec3 diff = p - spherepos;

    vec3 normal = normalize(diff);


    return vec4(normal, length(diff)-radius);
}

vec3 lerp(vec3 a, vec3 b, float p)
{
    p = clamp(p,0.,1.);
 	return a*(1.0-p)+b*p;
}


vec4 march(vec3 cam, vec3 n)
{

    float len = 1.0;
    vec4 ret;

    for(int i = 0; i < MARCHLIMIT; i++)
    {
        ret = range(camPos + len*n)*0.5;
		len += ret.w;
    }

	return vec4(ret.xyz, len);
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = (ourTexcoord*2.0) - vec2(1, 1);
    uv.y *= iResolution.y / iResolution.x;

    float rotangle = iGlobalTime*0.08;
    vec2 newuv;
    newuv.x = uv.x*cos(rotangle)-uv.y*sin(rotangle);
    newuv.y = uv.x*sin(rotangle)+uv.y*cos(rotangle);
    uv = newuv;

    camPos = vec3(0.5, 0.5, iGlobalTime*0.3);

    ld = normalize(vec3(0.0, sin(iGlobalTime*0.3)*0.1, cos(iGlobalTime*0.3)*0.5));
    float zoom = sqrt(1.5 + sin(iGlobalTime/10.0) * 1.0);
    vec3 n = normalize(vec3(sin(uv.x*3.1415*zoom),sin(uv.y*3.1415*zoom) ,ld.z*cos(uv.x*3.1415*zoom)*cos(uv.y*3.1415*zoom)));
    vec4 rangeret = march(camPos, n);
    float d = log(rangeret.w / 1.0 + 1.0);
    vec3 normal = rangeret.xyz;

    vec3 p = camPos + n*d;
    float angle = acos(dot(normal, n)/length(normal)*length(n));

	fragColor = vec4(hsv2rgb_smooth(lerp(vec3(d*0.1 + (colorangle + iGlobalTime)*0.01 + atan(uv.y/uv.x)*3.1415 , 2.0, max(1.0 - log(d),0.0)),vec3(d*0.1 + ((colorangle + iGlobalTime)+120.0)*0.01 , 2.0, max(1.0 - log(d),0.0)),cos(angle/9.0))),1.0);
}