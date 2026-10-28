Includes = { "standardfuncsgfx.fxh" }
PixelShader = {
    Code
    [[
	float3 CUNativePaperBrightness( float3 Color )
	{
		// S-curve adjustment parameters
		float contrast = 1.35f;  // Curve steepness ( 1.0f - 2.0f )
		float brightness = 0.16f; // Overall brightness ( -0.2f to 0.3f )
		// Apply S-curve transformation
		Color = Color - 0.5f;
		Color = Color * contrast;
		Color = Color + 0.5f + brightness;
		Color = saturate( Color ); // Clamp to 0-1 range

		// Apply subtle gamma for fine-tuning
		float gamma = lerp( 1.15f, 0.75f, FlatMapBrightnessIntensity ); // Slight brightening, default value is 0.95f
		Color *= lerp( 0.5f, 1.5f, FlatMapBrightnessIntensity );

		Color = pow( Color, gamma );
		Color = saturate(Color);
		return Color;
	}
    ]]
}
