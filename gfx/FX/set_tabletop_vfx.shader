Includes = {
    "spherical_earth_theory.fxh"
	"pdxmesh_vfx.fxh"
	"cw/pdxmesh.fxh"
	"standardfuncsgfx.fxh"
	"cw/camera.fxh"
	"cw/pdxgui.fxh"
	"cw/utility.fxh"
}

PixelShader =
{
	TextureSampler DiffuseMap
	{
		Ref = PdxTexture0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
		srgb = yes
	}
	TextureSampler PropertiesMap
	{
		Ref = PdxTexture1
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler NormalMap
	{
		Ref = PdxTexture2
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	
	VertexStruct PS_COLOR_SSAO
	{
		float4 Color : PDX_COLOR0;
		float4 SSAOColor : PDX_COLOR1;
	};
}

PixelShader =
{
	MainCode PS_mesh_vfx_standard
	{
		Input = "VS_OUTPUT_PDXMESH_VFX"
		Output = "PS_COLOR_SSAO"
		Code
		[[
			PDX_MAIN
			{
                // Discard table fragments before color and depth writes in globe mode.
                clip(0.001 - SETGlobeBlend());
				PS_COLOR_SSAO Out;

				#ifdef SIMPLE_UNLIT_DIFFUSE
					Out.Color.rgb = PdxTex2D( DiffuseMap, Input.UV0 ).rgb;
					Out.Color.a = 1.0f;
				#endif

				#ifdef UI_PANNING_TEXTURE

					float FadeDistance = 1.0f;
					float EdgeFade = 1.0f;
					float EdgeAlpha = 1.0f;

					// Mask for the lower edge
					float LowerEdgeMask = saturate( ( Input.UV1.y - LOWER_EDGE_FALLOFF ) );
					float4 NoiseTextureSample = PdxTex2D( DiffuseMap, Input.UV1.xy );

					// Distorted and Base UV Sets used to sample textures later
					float2 BaseUV = float2( Input.UV2.x, Input.UV2.y );
					float2 DistortedUVs = BaseUV + float2(NoiseTextureSample.r, NoiseTextureSample.g) * UV_DIST_STRENGTH;

					float4 NoiseTexture;
					float4 NoiseTextureDistorted2 = PdxTex2D( DiffuseMap, DistortedUVs );

					NoiseTexture = NoiseTextureSample * NoiseTextureDistorted2;

					// Texture Masks for the Upper and Lower Edge
					float UpperEdge = saturate( ( ( saturate( 1.0f - Input.UV1.y + NoiseTexture.a ) ) + UPPER_EDGE_FALLOFF ) );
					float LowerEdge = LowerEdgeMask + ( LowerEdgeMask * NoiseTexture.a ) * LOWER_EDGE_MULT;
					float LowerEdge2 = LowerEdgeMask + ( LowerEdgeMask * NoiseTexture.g ) * LOWER_EDGE_MULT;

					// Final Composite RGB
					float4 Composite;

					float LowerCut = smoothstep( 0.0f, LOWER_EDGE_CUT, LowerEdge * LowerEdge2 );

					Composite.rgb = lerp( NoiseTexture.a, NoiseTexture.r, LowerEdge ) + LowerEdge;
					Composite.rgb = PdxTex2D( PropertiesMap, saturate(float2( Composite.r + LOWER_EDGE_COL_SLIDE, Composite.g ))).rgb;
					Composite.rgb = lerp(Composite.rgb, UPPER_EDGE_COL, UpperEdge );

					// Final Composite Alpha
					Composite.a = saturate( LowerEdgeMask + Input.UV1.g * NoiseTextureDistorted2.a * FINAL_ALPHA_MULT );
					Composite.a = saturate( Composite.a - LowerCut );
					Composite.a*= NoiseTextureSample.b;

					Out.Color = Composite;
					Out.Color.rgb *= FINAL_COL_MULT;
					Out.Color.a *= PdxMeshGetOpacity(Input.InstanceIndex);

				#endif

				#ifdef UI_SCREEN_BURN
					float4 UVDistortion = ( PdxTex2D( DiffuseMap, Input.UV1 ) + 1.0f ) * 0.5f;
					float UVDistortionStrength = 0.1f;

					Out.Color = PdxTex2D( DiffuseMap, Input.UV0 + UVDistortion.zw * UVDistortionStrength );

					float a = ( sin( GlobalTime * 2.0f ) + 1.0f ) * 0.5f;

					float Alpha = smoothstep(a, saturate( a - 0.025f ), 1.0f - Out.Color.a );
					float Alpha2 = Alpha - smoothstep(a, saturate( a - 0.05f), 1.0f - Out.Color.a );

					Out.Color.a = Alpha;
					Out.Color.rgb = lerp( float3( 0.0f, 0.0f, 0.0f ), float3( 0.0f, 0.0f, 0.0f ), a * a * a ) + Alpha2 * float3( 3.0f, 0.0f, 0.0f );
					Out.Color.a = ApplyOpacity(Out.Color.a, Input.Position.xy, Input.InstanceIndex);
				#endif

				return Out;
			}
		]]
	}

	MainCode PS_mesh_vfx_candle
	{
		Input = "VS_OUTPUT_PDXMESH_VFX"
		Output = "PS_COLOR_SSAO"
		Code
		[[
			PDX_MAIN
			{
                // Discard table fragments before color and depth writes in globe mode.
                clip(0.001 - SETGlobeBlend());
				PS_COLOR_SSAO Out;
				#if defined( OFFSET )
					float2 NoiseUv = Input.UV0 + OFFSET.xy;
				#else
					float2 NoiseUv = Input.UV0;
				#endif
				
				float2 PanSpeed = float2( 0.125f, 0.055f );
				float NoiseStrength = 0.15f;
				
				#if defined( DISTORTION_STRENGTH )
					float DistortionStrength = DISTORTION_STRENGTH;
				#else
					float DistortionStrength = 0.2f;
				#endif

				NoiseUv *= NoiseStrength;
				NoiseUv += GuiTime * PanSpeed;

				float2 NormalNoise = PdxTex2D( NormalMap, NoiseUv ).rg;
				NormalNoise -= 0.5;
				NormalNoise *= DistortionStrength;

				float VerticalGradient = smoothstep( 1.0f, 0.0f, Input.UV0.y );
				float2 UvDistortion = lerp( float2( 0.0f, 0.0f ), NormalNoise, VerticalGradient );
				float4 Diffuse = PdxTex2D( DiffuseMap, Input.UV0 + UvDistortion );
				Diffuse.a = ApplyOpacity( Diffuse.a, Input.Position.xy, Input.InstanceIndex );

				clip( Diffuse.a - 0.1f );

				Out.Color = Diffuse;
				Out.SSAOColor = float4( 1.0f, 1.0f, 1.0f, Diffuse.a );
				return Out;
			}
		]]
	}

	MainCode PS_mesh_vfx_glow
	{
		Input = "VS_OUTPUT_PDXMESH_VFX"
		Output = "PS_COLOR_SSAO"
		Code
		[[
			PDX_MAIN
			{
                // Discard table fragments before color and depth writes in globe mode.
                clip(0.001 - SETGlobeBlend());
				PS_COLOR_SSAO Out;
				float2 NoiseOffset = vec2( ( GuiTime % 100.0f ) * 0.025f );
				float Noise = PdxTex2D( PropertiesMap, NoiseOffset ).r;
				float4 Diffuse = PdxTex2D( DiffuseMap, Input.UV0 );
				Diffuse.a *= Noise;
				Diffuse.rgb = float3( 0.78f, 0.22f, 0.01f );
				Out.Color = Diffuse;
				Out.SSAOColor = float4( 1.0f, 1.0f, 1.0f, Diffuse.a );
				return Out;
			}
		]]
	}

	MainCode PS_mesh_vfx_smoke
	{
		Input = "VS_OUTPUT_PDXMESH_VFX"
		Output = "PS_COLOR_SSAO"
		Code
		[[
			PDX_MAIN
			{
                // Discard table fragments before color and depth writes in globe mode.
                clip(0.001 - SETGlobeBlend());
				PS_COLOR_SSAO Out;

				#if defined( ALPHA_MULTIPLIER )
					float AlphaMultiplier = ALPHA_MULTIPLIER;
				#else
					float AlphaMultiplier = 0.6f;
				#endif

				#if defined( SMOKE_SPEED )
					float Speed = SMOKE_SPEED;
				#else
					float Speed = 0.2f;
				#endif

				float2 TimeOffset = GuiTime * float2( -Speed, 0.0f );
				float2 NoiseOffset = ( PdxTex2D( DiffuseMap, Input.UV0 ).a - 0.5f ) * 0.2f;
				float2 DistortedUV = Input.UV0 + NoiseOffset + TimeOffset;

				float4 Tex = PdxTex2D( DiffuseMap, DistortedUV );
				float Fresnel = 1.0f - pow( 1.0f - saturate( dot( normalize( CameraPosition - Input.WorldSpacePos ), normalize( Input.Normal ) ) ), 0.2f );

				Out.Color.rgb = Tex.rgb;
				Out.Color.a = Tex.r * Fresnel * AlphaMultiplier;

				return Out;
			}
		]]
	}


}

RasterizerState RasterizerStateNoCulling
{
	CullMode = "none"
}

BlendState BlendState
{
	BlendEnable = no
}

BlendState alpha_blend
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
	WriteMask = "RED|GREEN|BLUE"
}

BlendState AdditiveBlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "ONE"
	WriteMask = "RED|GREEN|BLUE|ALPHA"
}

BlendState additive_blend
{
	BlendEnable = yes
	SourceBlend = "ONE"
	DestBlend = "ONE"
}

DepthStencilState depth_test_no_write
{
	DepthEnable = yes
	DepthWriteEnable = no
}

# Standard
Effect mesh_vfx_standard
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
}

# Standard + candle distortion
Effect mesh_vfx_candle
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_candle"
	BlendState = "alpha_blend"
	RasterizerState = "RasterizerStateNoCulling"
	Defines = { "BILLBOARD_MESH" }

	DepthStencilState = "depth_test_no_write"
}

Effect mesh_vfx_glow
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_glow"
	BlendState = "alpha_blend"
	RasterizerState = "RasterizerStateNoCulling"	
	DepthStencilState = "depth_test_no_write"
	Defines = { "BILLBOARD_MESH" }	
}

# Standard
Effect mesh_vfx_standard_billboard
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
	Defines = { "BILLBOARD_MESH_SKINNED" "SIMPLE_UNLIT_DIFFUSE" }
}

# Standard + alpha blend
Effect standard_alpha_blend
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
	BlendState = "alpha_blend"
	DepthStencilState = "depth_test_no_write"
}

# Standard + alpha blend, used for panning textures on UI quads
Effect vfx_ui_panning_texture
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
	BlendState = "alpha_blend"
	DepthStencilState = "depth_test_no_write"
	Defines = { "UI_PANNING_TEXTURE" }
}

# Standard + alpha blend, used for dissolving textures on UI quads
Effect vfx_ui_screen_burn
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
	BlendState = "alpha_blend"
	DepthStencilState = "depth_test_no_write"
	Defines = { "UI_SCREEN_BURN" }
}

# Standard + additive blend
Effect standard_additive_blend
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_standard"
	BlendState = "additive_blend"
	DepthStencilState = "depth_test_no_write"
}

Effect mesh_vfx_smoke
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_smoke"
	BlendState = "alpha_blend"
	DepthStencilState = "depth_test_no_write"
	Defines = { "SMOKE_MESH" }
}