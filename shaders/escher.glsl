#version 330 core

in vec3 ourColor;
in vec2 ourTexcoord;

out vec4 outCol;

uniform vec2 iResolution;
uniform float iGlobalTime;

uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;

void mainImage(out vec4 fragColor, in vec2 fragCoord);

void main() {
    mainImage(outCol, gl_FragCoord.xy);
}

void mainImage( out vec4 O, vec2 U )
{
	U *= 12./iResolution.y;
    O-=O;
    vec2 f = floor(U), u = 2.*fract(U)-1.;  // ceil cause line on some OS
    float b = mod(f.x+f.y,2.), y;

    for(int i=0; i<4; i++) 
        u *= mat2(0,-1,1,0),
        y = 2.*fract(.2*iDate.w+U.x*.01)-1.,
	    O += smoothstep(.55,.45, length(u-vec2(.5,1.5*y)));
   
    if (b>0.) O = 1.-O; // try also without :-)
}