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

#define TAU 6.28318530718

float hash(vec2 uv) {
    float f = fract(cos(sin(dot(uv, vec2(.009123898, .00231233))) * 48.512353) * 11111.5452313);
    return f;
}

float noise(vec2 uv) {
    vec2 fuv = floor(uv);
    vec4 cell = vec4(
        hash(fuv + vec2(0, 0)),
        hash(fuv + vec2(0, 1)),
        hash(fuv + vec2(1, 0)),
        hash(fuv + vec2(1, 1))
    );
    /* replacing this with smoother transition
    vec2 axis = mix(cell.xz, cell.yw, fract(uv.y));
    return mix(axis.x, axis.y, fract(uv.x)); */
    vec2 axis = mix(cell.xz, cell.yw, smoothstep(0., 1., fract(uv.y)));
    return mix(axis.x, axis.y, smoothstep(0., 1., fract(uv.x)));
}

float fbm(vec2 uv) {
    float f = 0.;
    float r = 1.;
    for (int i = 0; i < 4; ++i) {
        f += noise((uv += vec2(-1, 1) * iGlobalTime / 16.) * r) / (r *= 2.);
    }
    return f / (1. - 1. / r);
}

vec4 createBall(vec2 uv) {
    float f = smoothstep(0.5, 1.4, distance(uv, vec2(-.1, .1))) * .5;
    f += smoothstep(.0, .9, 1.3- distance(uv, vec2(-.3, .3))) * .5;
    f += smoothstep(.1, .5, .5- distance(uv, vec2(-.4, .4)));
    f += smoothstep(.1, .5, .4- distance(uv, vec2(.2, .6)));
    f *= 1. - smoothstep(.95, 1., distance(uv, vec2(.0, .0)));
    return vec4(f, f, f, 1.);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = fragCoord.xy / iResolution.xy * 2. - 1.;
    uv.x *= iResolution.x / iResolution.y;

    vec2 ball = vec2(.2, -.4);
    ball.y += sin(iGlobalTime * 0.) / 40.;
    float r = .2;

    // create distorted version of the space
    vec2 distuv = uv * vec2(150, 130) + vec2(0, 20);
    distuv *= distance(uv, vec2(1.5, -2)) / 3.;

    // add distortion for the ball
    distuv.x += smoothstep(1. - r * 1.5, 1., 1. - distance(uv, ball - vec2(.1, 0))) * 15.;

    // calculate distortion level from distance to lower right corner
    float t = smoothstep(0., 1., 1. - distance(uv * .5, vec2(.4, -.85)));

    // add noise to distortion weighted by distortion level
    distuv += (fbm(uv * 2.) - .5) * t * 100.;

    // calculate stripes
    float f = sin(distuv.x + distuv.y);

    // calculate distance from distorted diagonal
    float d = (distuv.x + distuv.y) / TAU;

    if (d < .5 && d > - 1.) { // inside red line
        float grad = min(1., (.75 - abs(d + .25)) * 5.);
		fragColor = vec4(mix(vec3(.92,.16,.20), vec3(.93, .64, .17), -uv.y) * grad, 1.);
    } else { // lines
        float spot = clamp(3. - distance(uv * vec2(1, 2), vec2(-1, -1)), 0., 1.);
		fragColor = vec4(vec3(.8, .68, .82) * f * spot, 1.);
    }

    // create ball color
    vec4 b = createBall((uv - ball) / r);

    // create ball mask
    float mask = 1. - smoothstep(r - .002, r + .01, distance(uv, ball));
    mask *= smoothstep(-1.2, -.9, d);

    // add ball
    fragColor = mix(fragColor, b, mask);

    // add a noise
    fragColor.rgb -= noise(uv * 300. + fract(iGlobalTime) * 10000.) / 5.;
}