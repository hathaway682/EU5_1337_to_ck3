Includes = { "cw/camera.fxh" "standardfuncsgfx.fxh" }
Code
[[
    #ifndef TNH_GALL_GLOBE
    #define TNH_GALL_GLOBE
    static const float TNHGlobePi = 3.14159265359;
    static const float TNHGlobeStart = 7000.0;
    static const float TNHGlobeFull = 11000.0;
    static const float TNHGlobeEquatorZ = 3345.934846653462;
    static const float TNHGlobeLatScale = 6296.721960964037;
    static const float TNHGlobeLonScale = 0.000383373697;
    static const float TNHGlobeRadiusFull = 2608.420997560873;
    float TNHGlobeBlend() { return smoothstep(TNHGlobeStart, TNHGlobeFull, CameraPosition.y); }
    float2 TNHGlobeFocus() {
        float3 direction = normalize(CameraLookAtDir);
        float distance = max(0.0, CameraPosition.y) / max(0.05, -direction.y);
        return CameraPosition.xz + direction.xz * distance;
    }
    float TNHGlobeLatitude(float z) { return 2.0 * atan((z - TNHGlobeEquatorZ) / TNHGlobeLatScale); }
    float3 TNHGlobeNormal(float3 position) {
        float blend = TNHGlobeBlend();
        float scale = max(blend, 0.02);
        float geo = smoothstep(0.5, 1.0, blend);
        float2 focus = TNHGlobeFocus();
        float lon = (position.x - focus.x) * TNHGlobeLonScale;
        lon -= floor(lon / (2.0 * TNHGlobePi) + 0.5) * (2.0 * TNHGlobePi);
        lon *= scale;
        float focusLat = TNHGlobeLatitude(focus.y) * geo;
        float deltaLat = lerp((position.z-focus.y)/TNHGlobeRadiusFull,
            TNHGlobeLatitude(position.z)-TNHGlobeLatitude(focus.y), geo) * scale;
        float lat = focusLat + deltaLat;
        float3 globe = float3(cos(lat)*sin(lon), sin(lat), cos(lat)*cos(lon));
        float3 up = float3(0.0, sin(focusLat), cos(focusLat));
        float3 north = float3(0.0, cos(focusLat), -sin(focusLat));
        return normalize(float3(globe.x, dot(globe,up), dot(globe,north)));
    }
    float3 TNHGlobeWarp(float3 position) {
        float blend = TNHGlobeBlend();
        if (blend <= 0.0) return position;
        float3 normal = TNHGlobeNormal(position);
        float r = TNHGlobeRadiusFull / max(blend,0.02);
        float2 focus = TNHGlobeFocus();
        float3 curved = float3(focus.x,0.0,focus.y)
            + (normal-float3(0.0,1.0,0.0))*r + normal*position.y;
        return lerp(position, curved, saturate(blend/0.02));
    }
    float TNHGlobeVisible(float3 position) {
        if (TNHGlobeBlend() <= 0.0) return 1.0;
        return dot(TNHGlobeNormal(position), normalize(CameraPosition-TNHGlobeWarp(position)));
    }
    #endif
]]
