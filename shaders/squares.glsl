#version 400 core

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

float n = 120.;
float a = 4.*2.*3.1416;



void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = 2.*(fragCoord.xy / iResolution.y -vec2(.9,.5));
    float luv = length(uv)/sqrt(2.);


    float t = cos(.1*iGlobalTime);
    a = a/n*pow(t,3.);   float  c=cos(a),s=sin(a);
    float z=(0.98+.03*cos(.1*iGlobalTime))/(abs(s)+abs(c)),  l=1.;
    mat2 m=mat2(c,-s,s,c)/z;
    vec4 paint = vec4(pow(.1,1.),pow(.11,1.),pow(.16,1.),1.), col=vec4(1.), p=vec4(1.);

    for (float i=0.; i<50.; i++) {
        if (l<luv) break;
        float w = l/n;
        p *= pow(paint,vec4(w,w,w,1.));
        float d = max(abs(uv.x),abs(uv.y));
        vec4 col0 = smoothstep(.9+.008*l,.9-.008*l,d)*p;
           col0.a = smoothstep(.9+.008*l,.9-.008*l*(1.-abs(t)),d);
        col = col0 + (1.-col0.a)*col;
        l /= z;
        uv *= m;
    }

    col = clamp(col, 0., 1.);
    col.rgb = vec3(1) - col.rgb;
	fragColor = col;
}