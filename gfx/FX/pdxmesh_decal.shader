Includes = {
	"cw/shadow.fxh"
	"cw/pdxterrain.fxh"
	"jomini/jomini_decals.fxh"
	"jomini/jomini_fog.fxh"
	"jomini/map_lighting.fxh"
	"jomini/jomini_fog_of_war.fxh"
	"bordercolor.fxh"
	"dynamic_masks.fxh"
	"legend.fxh"
	"lowspec.fxh"
	"disease.fxh"
	"shadow_tint.fxh"
	"clouds.fxh"
	"province_effects.fxh"
}

PixelShader =
{
	TextureSampler DiffuseTexture
	{
		Ref = PdxTexture0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler PropertiesTexture
	{
		Ref = PdxTexture1
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler NormalTexture
	{
		Ref = PdxTexture2
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler EnvironmentMap
	{
		Ref = JominiEnvironmentMap
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
		Type = "Cube"
	}
	TextureSampler ShadowTexture
	{
		Ref = PdxShadowmap
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
		CompareFunction = less_equal
		SamplerType = "Compare"
	}
	TextureSampler FogOfWarAlpha
	{
		Ref = JominiFogOfWar
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
}

PixelShader =
{
	Code
	[[
		float3 CalcDecal( float2 UV, float3 Bitangent, float3 WorldSpacePos, float3 Diffuse, EffectIntensities ConditionData )
		{
			float4 Properties = PdxTex2D( PropertiesTexture, UV );
			float4 NormalPacked = PdxTex2D( NormalTexture, UV );
			float3 NormalSample = UnpackRRxGNormal( NormalPacked );
			const float3 TerrainNormal = CalculateNormal( WorldSpacePos.xz );
			float3 Normal = TerrainNormal;
			#ifdef TANGENT_SPACE_NORMALS
				float3 Tangent = cross( Bitangent, Normal );
				float3x3 TBN = Create3x3( normalize( Tangent ), normalize( Bitangent ), Normal );
				Normal = normalize( mul( NormalSample, TBN ) );
			#else
				Normal = ReorientNormal( Normal, NormalSample );
			#endif

			float2 ColorMapCoords = WorldSpacePos.xz * WorldSpaceToTerrain0To1;
			ApplyProvinceEffectsDecal( ConditionData, Diffuse, ColorMapCoords );

			float SnowHighlight = 0.0f;
			ApplySnowMaterialMesh( Diffuse, Properties, Normal, WorldSpacePos.xz, ColorMapCoords, SnowHighlight, 4.0f );

			float3 ColorMap = ToLinear( PdxTex2D( ColorTexture, float2( ColorMapCoords.x, 1.0 - ColorMapCoords.y ) ).rgb );
			Diffuse = GetOverlay( Diffuse, ColorMap, 0.5 );

			float4 HighlightColor = GetHighlightColor( ColorMapCoords );
			ApplyHighlightColor( Diffuse, HighlightColor );
			CompensateWhiteHighlightColor( Diffuse, HighlightColor, SnowHighlight );

			SMaterialProperties MaterialProps = GetMaterialProperties( Diffuse, Normal, Properties.a, Properties.g, Properties.b );

			#ifdef LOW_SPEC_SHADERS
				SLightingProperties LightingProps = GetMapLightingProperties( WorldSpacePos, 1.0f );
				float3 Color = CalculateTerrainSunLightingLowSpec( MaterialProps, LightingProps );
			#else
				SLightingProperties LightingProps = GetMapLightingProperties( WorldSpacePos, ShadowTexture );
				float CloudMask = GetCloudShadowMask( WorldSpacePos.xz );
				#ifdef FAKE_TERRAIN_SHADOW
					// Use dual scenario lighting for decals
					LightingProps._ToLightDir = ToTerrainSunnySunDir;
					SShadowTintData ShadowTintData = GetShadowTintData( ColorMapCoords );
					float TerrainShadowTerm = GetShadowTintMask( ShadowTintData, LightingProps._ToLightDir, LightingProps._ShadowTerm, TerrainNormal, Normal );
					LightingProps._ShadowTerm = LightingProps._ShadowTerm * ( 1.0f - TerrainShadowTerm );

					// Use unified dual scenario lighting for decals
					float3 Color = CalculateTerrainDualScenarioLighting( LightingProps, MaterialProps, CloudMask, EnvironmentMap );

					// Apply shadow tint with cloud interaction for decals
					Color = ApplyTerrainShadowTintWithClouds( Color, WorldSpacePos.xz, CloudMask, LightingProps._ShadowTerm, Normal, TerrainNormal );
				#else
					float3 Color = CalculateMapObjectsSunnyLighting( LightingProps, MaterialProps, EnvironmentMap );

					// Apply shadow tint with cloud interaction for non-terrain-shadow decals
					Color = ApplyMapObjectsShadowTintWithClouds( Color, ColorMapCoords, CloudMask, LightingProps._ShadowTerm, Normal, TerrainNormal );
				#endif

				ApplyLegendDiffuse( Color, ColorMapCoords );
				ApplyDiseaseDiffuse( Color, ColorMapCoords );
			#endif

			//  DebugReturn( Color, MaterialProps, LightingProps, EnvironmentMap );
			return Color;
		}
	]]

	MainCode PS_world
	{
		TextureSampler DecalAlphaTexture
		{
			Ref = PdxTexture3
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "Linear"
			SampleModeU = "Clamp"
			SampleModeV = "Clamp"
		}

		Input = "VS_OUTPUT"
		Output = "PDX_COLOR"
		Code
		[[
			static const float DECAL_TILING_SCALE = 0.15;

			PDX_MAIN
			{
				float2 ColorMapCoords = Input.WorldSpacePos.xz * WorldSpaceToTerrain0To1;
				EffectIntensities ConditionData;
				SampleProvinceEffectsMask( ColorMapCoords, ConditionData );
				float Alpha = PdxTex2D( DecalAlphaTexture, Input.UV0 ).r;

				Alpha = PdxMeshApplyOpacity( Alpha, Input.Position.xy, GetOpacity( Input.InstanceIndex ) );

				float2 DetailUV = Input.WorldSpacePos.xz * float2( DECAL_TILING_SCALE, -DECAL_TILING_SCALE );

				float4 Diffuse = PdxTex2D( DiffuseTexture, DetailUV );
				float3 Color = CalcDecal( DetailUV, Input.Bitangent, Input.WorldSpacePos, Diffuse.rgb, ConditionData );
				ApplyDivergentRitesColor( ColorMapCoords, Color, ConditionData );
				Color = ApplyFogOfWar( Color, Input.WorldSpacePos, FogOfWarAlpha );
				Color = ApplyMapDistanceFogWithoutFoW( Color, Input.WorldSpacePos );
				Alpha = CalcHeightBlendFactors( float4( Diffuse.a, 0.3, 0.0, 0.0 ), float4( Alpha, 1.0 - Alpha, 0.0, 0.0 ), 0.25 ).r;

				return float4( Color, Alpha );
			}
		]]
	}

	MainCode PS_local
	{
		Input = "VS_OUTPUT"
		Output = "PDX_COLOR"
		Code
		[[
			PDX_MAIN
			{
                // Map-local building foundations follow the building visibility.
                clip(7000.0 - CameraPosition.y);

				float2 ColorMapCoords = Input.WorldSpacePos.xz * WorldSpaceToTerrain0To1;
				float4 Diffuse = PdxTex2D( DiffuseTexture, Input.UV0 );
				Diffuse.a = PdxMeshApplyOpacity( Diffuse.a, Input.Position.xy, GetOpacity( Input.InstanceIndex ) );
				clip( Diffuse.a - 1e-5);
				EffectIntensities ConditionData;
				SampleProvinceEffectsMask( ColorMapCoords, ConditionData );
				float3 BorderColor;
				float BorderPreLightingBlend;
				float BorderPostLightingBlend;
				GetBorderColorAndBlendGame( Input.WorldSpacePos.xz, Diffuse.rgb, BorderColor, BorderPreLightingBlend, BorderPostLightingBlend, ConditionData._DivergentRites );
				LerpBorderColorWithFogOfWar( Diffuse.rgb, Input.WorldSpacePos.xz, BorderColor, BorderPreLightingBlend );

				float3 Color = CalcDecal( Input.UV0, Input.Bitangent, Input.WorldSpacePos, Diffuse.rgb, ConditionData );
				ApplyDivergentRitesColor( ColorMapCoords, Color, ConditionData );
				Color = ApplyFogOfWar( Color, Input.WorldSpacePos, FogOfWarAlpha );
				Color = ApplyMapDistanceFogWithoutFoW( Color, Input.WorldSpacePos );
				Color.rgb = lerp( Color.rgb, BorderColor, BorderPostLightingBlend );
				return float4( Color, Diffuse.a );
			}
		]]
	}
}


Effect decal_world
{
	VertexShader = "VS_standard"
	PixelShader = "PS_world"
	Defines = { "FAKE_TERRAIN_SHADOW" }
}

Effect decal_world_mapobject
{
	VertexShader = "VS_mapobject"
	PixelShader = "PS_world"
	Defines = { "FAKE_TERRAIN_SHADOW" }
}

Effect decal_local
{
	VertexShader = "VS_standard"
	PixelShader = "PS_local"

	Defines = { "TANGENT_SPACE_NORMALS" "FAKE_TERRAIN_SHADOW" }
}

Effect decal_local_mapobject
{
	VertexShader = "VS_mapobject"
	PixelShader = "PS_local"

	Defines = { "TANGENT_SPACE_NORMALS" "FAKE_TERRAIN_SHADOW" }
}
