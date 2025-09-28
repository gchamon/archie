#version 300 es
precision highp float;

in vec2 v_texcoord;
out vec4 FragColor;
uniform sampler2D tex;

// Night mode settings
const float temperature = 4000.0;
const float temperatureStrength = 1.0;

#define WithQuickAndDirtyLuminancePreservation
const float LuminancePreservationFactor = 1.0;

// Vibrance settings
const vec3 VIB_RGB_BALANCE = vec3(1.4, 0.8, 0.1);
const float VIB_VIBRANCE = -0.3; // Negative value reduces saturation
const vec3 VIB_coeffVibrance = VIB_RGB_BALANCE * -VIB_VIBRANCE;
const vec3 VIB_coefLuma = vec3(0.212656, 0.715158, 0.072186);

vec3 colorTemperatureToRGB(const in float temperature) {
    mat3 m = (temperature <= 6500.0) ? mat3(vec3(0.0, -2902.1955373783176, -8257.7997278925690),
            vec3(0.0, 1669.5803561666639, 2575.2827530017594),
            vec3(1.0, 1.3302673723350029, 1.8993753891711275)) : mat3(vec3(1745.0425298314172, 1216.6168361476490, -8257.7997278925690),
            vec3(-2666.3474220535695, -2173.1012343082230, 2575.2827530017594),
            vec3(0.55995389139931482, 0.70381203140554553, 1.8993753891711275));
    return mix(clamp(vec3(m[0] / (vec3(clamp(temperature, 1000.0, 40000.0)) + m[1]) + m[2]), vec3(0.0), vec3(1.0)),
        vec3(1.0), smoothstep(1000.0, 0.0, temperature));
}

void main() {
    vec4 pixColor = texture(tex, v_texcoord);
    vec3 color = pixColor.rgb;

    // First: Apply luminance preservation (from night mode)
    #ifdef WithQuickAndDirtyLuminancePreservation
    color *= mix(1.0, dot(color, vec3(0.2126, 0.7152, 0.0722)) / max(dot(color, vec3(0.2126, 0.7152, 0.0722)), 1e-5),
            LuminancePreservationFactor);
    #endif

    // Second: Apply color temperature (warm night mode effect)
    color = mix(color, color * colorTemperatureToRGB(temperature), temperatureStrength);

    // Third: Apply vibrance/saturation adjustment
    float luma = dot(VIB_coefLuma, color);
    float max_color = max(color.r, max(color.g, color.b));
    float min_color = min(color.r, min(color.g, color.b));
    float color_saturation = max_color - min_color;
    vec3 p_col = (sign(VIB_coeffVibrance) * color_saturation - 1.0) * VIB_coeffVibrance + 1.0;
    color = mix(vec3(luma), color, p_col);

    FragColor = vec4(color, pixColor.a);
}
