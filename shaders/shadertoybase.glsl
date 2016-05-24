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