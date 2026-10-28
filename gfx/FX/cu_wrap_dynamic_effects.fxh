Includes = {
    "jomini/jomini_province_overlays.fxh"
    "province_effects_variables.fxh"
}
struct EffectIntensities
{
	float _Drought;
	float _Flood;
	float _Summer;
	float _Snow;
	float _DivergentRites;
};
TextureSampler WinterTexture {
    Ref = WinterTexture
    MagFilter = "Linear"
    MinFilter = "Linear"
    MipFilter = "Linear"
    SampleModeU = "Wrap"
    SampleModeV = "Clamp"
}
PixelShader = {
    BufferTexture ProvinceEffectDataBuffer { Ref = ProvinceEffectData type = float4 }
    Code
    [[
		float3 AdjustHsv( float3 Rgb, float Hue, float Saturation, float Value )
		{
			float3 Color = RGBtoHSV( Rgb );
			Color.x += Hue;
			Color.y *= Saturation;
			Color.z *= Value;
			return HSVtoRGB( Color );
		}

		float3 AdjustSaturation( float3 Rgb, float Saturation )
		{
			return AdjustHsv( Rgb, 0.0f, Saturation, 1.0f );
		}

		float4 SampleProvinceEffects( float2 MapCoords )
		{
			float2 ColorIndex = PdxTex2D( ProvinceColorIndirectionTexture, float2(frac(MapCoords.x), clamp(MapCoords.y, InvIndirectionMapSize.y*0.5, 1.0-InvIndirectionMapSize.y*0.5)) ).rg;
			int Index = ColorIndex.x * 255.0f + ColorIndex.y * 255.0f * 256.0f;
			return PdxReadBuffer4( ProvinceEffectDataBuffer, Index );
		}

		float BilinearConditionWeight( float4 C11, float4 C21, float4 C12, float4 C22, float2 FracCoord, float Impact, int ConditionIndex)
		{
			float v1 = lerp( C11.r == ConditionIndex, C21.r == ConditionIndex, FracCoord.x );
			float v2 = lerp( C12.r == ConditionIndex, C22.r == ConditionIndex, FracCoord.x );
			return lerp( v1, v2, FracCoord.y ) * Impact;
		}

		void BilinearSampleProvinceEffectsMask( float2 MapCoords, inout EffectIntensities ConditionData )
		{
			#ifdef LOW_SPEC_SHADERS
				ConditionData._Drought = 0.0f;
				ConditionData._Flood = 0.0f;
				ConditionData._Summer = 0.0f;
				ConditionData._Snow = 0.0f;
				ConditionData._DivergentRites = 0.0f;
				return;
			#endif

			float2 Pixel = MapCoords * IndirectionMapSize + 0.5f;
			float2 FracCoord = frac( Pixel );
			Pixel = floor( Pixel ) / IndirectionMapSize - InvIndirectionMapSize / 2.0f;
			float4 C11 = SampleProvinceEffects( Pixel );
			float4 C21 = SampleProvinceEffects( Pixel + float2( InvIndirectionMapSize.x, 0.0f ) );
			float4 C12 = SampleProvinceEffects( Pixel + float2( 0.0f, InvIndirectionMapSize.y ) );
			float4 C22 = SampleProvinceEffects( Pixel + InvIndirectionMapSize );

			// Bilinear interpolation
			float x1 = lerp( C11.g, C21.g, FracCoord.x );
			float x2 = lerp( C12.g, C22.g, FracCoord.x );

			// Opacity
			float ImpactTemp = lerp( x1, x2, FracCoord.y );
			float Impact = RemapClamped( ImpactTemp, 0.0f, OpacityLowImpactValue, 0.0f, 0.5f );
			Impact += RemapClamped( ImpactTemp, OpacityLowImpactValue, OpacityHighImpactValue, 0.0f, 0.5f );

			ConditionData._Drought = BilinearConditionWeight( C11, C21, C12, C22, FracCoord, Impact, DROUGHT_INDEX );
			ConditionData._Flood = BilinearConditionWeight( C11, C21, C12, C22, FracCoord, Impact, FLOOD_INDEX );
			ConditionData._Summer = BilinearConditionWeight( C11, C21, C12, C22, FracCoord, Impact, SUMMER_INDEX );
			ConditionData._Snow = BilinearConditionWeight( C11, C21, C12, C22, FracCoord, Impact, SNOW_INDEX );
			ConditionData._DivergentRites = BilinearConditionWeight( C11, C21, C12, C22, FracCoord, ImpactTemp, DIVERGENT_RITES_INDEX );
		}

        float4 CUReadMapConditions(float2 MapCoords)
        {
            #ifdef LOW_SPEC_SHADERS
                // Native bilinear helper disables conditions in this variant.
                float4 State = SampleProvinceEffects(MapCoords);
                float Impact = RemapClamped(State.g, 0.0, 0.1, 0.0, 0.5)
                    + RemapClamped(State.g, 0.1, 1.0, 0.0, 0.5);
                return float4(State.r == 1, State.r == 2,
                    State.r == 3, State.r == 4) * Impact;
            #else
                EffectIntensities State;
                BilinearSampleProvinceEffectsMask(MapCoords, State);
                return float4(State._Drought, State._Flood, State._Summer, State._Snow);
            #endif
        }

		float CUGetEngineWinterSeverity( in float2 Coordinate )
		{
			return float4( PdxTex2D( WinterTexture, Coordinate ) ).r * smoothstep( 0.0f, 0.2f, max( 0.0f, _SnowValue + _DebugSeasonWinter ) );
		}

        float3 CUApplyOverviewConditions(float3 Color, float2 MapCoords, float3 Normal, float4 State)
        {
            float Slope = smoothstep(0.2, 1.0, abs(Normal.y));
            float3 Dry = AdjustHsv(Color, 0.0, DroughtPreSaturation, DroughtPreValue);
            Dry = AdjustSaturation(Overlay(Dry, DroughtOverlayColor), DroughtFinalSaturation);
            Color = lerp(Color, Dry, State.x * Slope * 0.28);
            Color = lerp(Color, Overlay(Color, SummerGrassOverlayColor), State.z * Slope * 0.30);
            float Snow = saturate(CUGetEngineWinterSeverity(MapCoords));
            float2 SnowUV = CalcDetailUV(MapCoords / WorldSpaceToTerrain0To1);
            float3 SnowColor = PdxTex2D(DetailTextures,float3(SnowUV,_SnowTexIndex)).rgb;
            return lerp(Color, SnowColor, Snow * Slope * 0.72);
        }
        void CUApplyWrapConditions(inout float4 Diffuse, float2 MapCoords, float3 TerrainNormal)
        {
            // Low-cost continuation: real conditions, shared snowline, no
            // no-tile snow/flood/normal/material stack in a fullscreen shader.
            Diffuse.rgb = CUApplyOverviewConditions(Diffuse.rgb,MapCoords,
                TerrainNormal,CUReadMapConditions(MapCoords));
        }
    ]]
}
