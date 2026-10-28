Includes = { "cw/camera.fxh" }
Code
[[
    #ifndef SET_GALL_GLOBE
    #define SET_GALL_GLOBE
    static const float SETGlobePi = 3.14159265359;
    static const float SETGlobeStart = 7000.000000000000000;
    static const float SETGlobeFull = 11000.0;
    static const float SETGlobeEquatorZ = 3350.76296397691203310;
    static const float SETGlobeLatScale = 6281.51479321707483905;
    static const float SETGlobeLonScale = 0.00038339914930253;
    static const float SETGlobeRadiusFull = 2608.24783210705481906;
    // Ease the engine's existing paper transition without changing its
    // endpoints, activation zoom step, or geography.
    float SETZoomPaperBlend(float nativeBlend) {
        // Use the engine's unmodified paper transition rate.
        return saturate(nativeBlend);
    }
    float SETZoomSmootherStep(float start, float end, float value) {
        // Detail visibility and background fades retain their own easing.
        float t = saturate((value-start)/(end-start));
        return t*t*t*(t*(t*6.0-15.0)+10.0);
    }
    // Preserve tactical routes nearby, then remove fine route geometry before
    // the sphere starts bending. This does not affect national borders.
    float SETZoomDetailOpacity() {
        return 1.0-SETZoomSmootherStep(4000.0,7000.0,CameraPosition.y);
    }
    float SETGlobeBlend() { return smoothstep(SETGlobeStart, SETGlobeFull, CameraPosition.y); }
    float2 SETGlobeFocus() {
        float3 direction = normalize(CameraLookAtDir);
        float distance = max(0.0, CameraPosition.y - 3.4) / max(0.05, -direction.y);
        return CameraPosition.xz + direction.xz * distance;
    }
    float SETGlobeLatitude(float z) { return 2.0 * atan((z-SETGlobeEquatorZ)/SETGlobeLatScale); }
    static const float SETGlobeDisplayScaleFull = 2.0;
    float SETGlobeLatitudeDerivative(float z) {
        float t=(z-SETGlobeEquatorZ)/SETGlobeLatScale;
        return 2.0/(SETGlobeLatScale*(1.0+t*t));
    }

    // Match the shell to the original world-Y-centered bending geometry.
    float SETGlobeRadius() {
        float blend = SETGlobeBlend();
        float displayScale = lerp(1.0,SETGlobeDisplayScaleFull,SETZoomPaperBlend(blend));
        return SETGlobeRadiusFull*displayScale/max(blend,0.02);
    }
    float3 SETGlobeCenter() {
        float2 focus = SETGlobeFocus();
        return float3(focus.x,3.4-SETGlobeRadius(),focus.y);
    }
    float SETGlobeLongitudeScale() {
        // Close the 16384-unit global mesh at a full turn. Preserve the
        // registered planar scale until the geographic bending stage.
        float geo = smoothstep(0.5,1.0,SETGlobeBlend());
        return lerp(SETGlobeLonScale,2.0*SETGlobePi/16384.0,geo);
    }
    float2 SETGlobeCoordinates(float3 radial, float2 focus) {
        float blend = SETGlobeBlend();
        float scale = max(blend,0.02);
        float geo = smoothstep(0.5,1.0,blend);
        float focusLat = SETGlobeLatitude(focus.y);
        float renderedFocusLat = focusLat*geo;
        float latitude = asin(clamp(radial.y*sin(renderedFocusLat)
            +radial.z*cos(renderedFocusLat),-1.0,1.0));
        float longitude = atan2(radial.x,radial.y*cos(renderedFocusLat)
            -radial.z*sin(renderedFocusLat))/scale;
        float delta = (latitude-renderedFocusLat)/scale;
        if (geo >= 0.99999)
            return float2(longitude,clamp(focusLat+delta,-SETGlobePi*0.5,SETGlobePi*0.5));
        float row = focus.y+delta*SETGlobeRadiusFull;
        if (geo > 0.0) {
            [loop]
            for (int i=0;i<8;++i) {
                row = clamp(row,-100000.0,100000.0);
                float derivative = (1.0-geo)/SETGlobeRadiusFull
                    +geo*SETGlobeLatitudeDerivative(row);
                float error = lerp((row-focus.y)/SETGlobeRadiusFull,
                    SETGlobeLatitude(row)-focusLat,geo)-delta;
                row -= error/max(derivative,0.0000001);
            }
        }
        return float2(longitude,clamp(SETGlobeLatitude(row),-SETGlobePi*0.5,SETGlobePi*0.5));
    }
    float3 SETGlobeNormal(float3 position) {
        float blend = SETGlobeBlend();
        float scale = max(blend, 0.02);
        float geo = smoothstep(0.5, 1.0, blend);
        float2 focus = SETGlobeFocus();
        float lon = (position.x - focus.x) * SETGlobeLongitudeScale();
        lon *= scale;
        float focusLat = SETGlobeLatitude(focus.y) * geo;
        float deltaLat = lerp((position.z-focus.y)/SETGlobeRadiusFull,
            SETGlobeLatitude(position.z)-SETGlobeLatitude(focus.y), geo) * scale;
        float lat = focusLat + deltaLat;
        float3 globe = float3(cos(lat)*sin(lon), sin(lat), cos(lat)*cos(lon));
        float3 up = float3(0.0, sin(focusLat), cos(focusLat));
        float3 north = float3(0.0, cos(focusLat), -sin(focusLat));
        return normalize(float3(globe.x, dot(globe,up), dot(globe,north)));
    }
    float3 SETGlobeWarp(float3 position) {
        float blend = SETGlobeBlend();
        if (blend <= 0.0) return position;
        float3 normal = SETGlobeNormal(position);
        float r = SETGlobeRadius();
        float2 focus = SETGlobeFocus();
        float3 curved = float3(focus.x,3.4,focus.y)
            + (normal-float3(0.0,1.0,0.0))*r + normal*(position.y - 3.4);
        return lerp(position, curved, saturate(blend/0.02));
    }
    float SETGlobeVisible(float3 position) {
        if (SETGlobeBlend() <= 0.0) return 1.0;
        return dot(SETGlobeNormal(position), normalize(CameraPosition-SETGlobeWarp(position)));
    }
    #endif
]]
