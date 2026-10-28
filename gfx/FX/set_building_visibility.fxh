Includes = { "spherical_earth_theory.fxh" }
PixelShader = {
    Code
    [[
        #ifndef SET_BUILDING_VISIBILITY
        #define SET_BUILDING_VISIBILITY
        void SETClipSphericalBuilding()
        {
            // One source of truth for the globe's start height. Building-only
            // shader routes keep portraits, court and ordinary trees unaffected.
            clip(SETGlobeStart - CameraPosition.y);
        }
        #endif
    ]]
}
