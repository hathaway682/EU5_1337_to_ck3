Includes = {
	"jomini/jomini_fog_of_war.fxh"
	"jomini/jomini_vertical_border.fxh"
	"jomini/jomini_fog.fxh"
	"jomini/jomini_water.fxh"
	"standardfuncsgfx.fxh"
	"legend.fxh"

	"spherical_earth_theory.fxh"
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

PixelShader =
{
	MainCode PixelShader_1x
	{
		Input = "VS_OUTPUT_PDX_BORDER"
		Output = "PDX_COLOR"
		Code
		[[
			float4 ApplyVerticalBordersFog( float4 Diffuse, float3 WorldSpacePos )
			{
				Diffuse.rgb = ApplyFogOfWar( Diffuse.rgb, WorldSpacePos, FogOfWarAlpha );
				Diffuse.rgb = ApplyMapDistanceFogWithoutFoW( Diffuse.rgb, WorldSpacePos );
				Diffuse.a *= Alpha;

				return Diffuse;
			}
			PDX_MAIN
			{
				clip( SETGlobeVisible( Input.WorldSpacePos ) );
				float4 TexColor0 = PdxTex2D( BorderTexture0, Input.UV0 );
				float3 Diffuse = CalculateLayerColor( TexColor0.rgb, Color.rgb );

				return ApplyVerticalBordersFog( float4( Diffuse, TexColor0.a ), Input.WorldSpacePos );
			}
		]]
	}

	MainCode PS_LegendBorder
	{
		Input = "VS_OUTPUT_PDX_BORDER"
		Output = "PDX_COLOR"
		Code
		[[
			struct RaySettings
			{
				float2 _UV0;
				float2 _UV1;
				float _FadeTop;
				float _FadeBottom;
				bool _TopFadoutWave;
				float _WaveScale;
				float _WaveMoveSpeed;
				float _WaveFerquence;
				float _RaySpeed;
				float _RayDensity1;
				float _RayDensity2;
				float _RayIntensity;
			};

			float4 ApplyVerticalBordersFog(in float4 Diffuse, in float3 WorldSpacePos )
			{
				float4 DiffuseColor = Diffuse;
				DiffuseColor.rgb =  ApplyFogOfWar( Diffuse.rgb, WorldSpacePos, FogOfWarAlpha );
				DiffuseColor.rgb = ApplyDistanceFog( DiffuseColor.rgb, WorldSpacePos );
				DiffuseColor.a *= Alpha;

				return DiffuseColor;
			}

			float CalcLegendRay( in RaySettings RayData )
			{
				float StrengthScale = 1.2f;
				float Speed = GlobalTime * 0.1f * RayData._RaySpeed;
				float SpeedScale = RayData._RayDensity1 * 0.2f;
				float2 Ray1 = float2( RayData._UV0.x * RayData._RayDensity1 + sin( Speed ) * SpeedScale, 1.0f );
				float2 Ray2 = float2( RayData._UV0.x * RayData._RayDensity2 + sin( Speed * 2 ) * SpeedScale, 1.0f );

				float Rays;
				float BorderTextureNoise1 = PdxTex2D( BorderTexture0, Ray1 ).b;
				float BorderTextureNoise2 = PdxTex2D( BorderTexture0, Ray2 ).b;
				Rays = clamp( BorderTextureNoise1 + ( BorderTextureNoise2 * RayData._RayIntensity ), 0.0f, 1.0f );

				// Fade out top
				if( RayData._TopFadoutWave )
				{
					float FadeOutOffset = RayData._WaveScale * sin( RayData._UV0.x * RayData._WaveFerquence + GlobalTime * RayData._WaveMoveSpeed );
					Rays *= smoothstep( 0.0f, RayData._FadeTop, ( RayData._UV0.y + FadeOutOffset ) );
				}
				else
				{
					Rays *= smoothstep( 0.0f, RayData._FadeTop, RayData._UV0.y );
				}

				// Fade out bottom
				Rays *= smoothstep( 0.0001f , RayData._FadeBottom , (  1.0f - RayData._UV0.y ) );
				return Rays * StrengthScale;
			}

			PDX_MAIN
			{
				clip( SETGlobeVisible( Input.WorldSpacePos ) );
				float GodRays = 0.0f;
				if( Input.UV0.y < 0.79f && Input.UV0.y > 0.45f)
				{
					RaySettings GodRaySettings;
					GodRaySettings._UV0 = float2( Input.UV0.x * 20, Input.UV0.y );
					GodRaySettings._UV1 = Input.UV1;
					GodRaySettings._FadeTop = 2.3f;
					GodRaySettings._FadeBottom = 0.5f;
					GodRaySettings._TopFadoutWave = false;
					GodRaySettings._WaveScale = 0.15f;
					GodRaySettings._WaveMoveSpeed = .0f;
					GodRaySettings._WaveFerquence = 10.0f;
					GodRaySettings._RaySpeed = 3.0f;
					GodRaySettings._RayDensity1 = 1.0f;
					GodRaySettings._RayDensity2 = 0.5f;
					GodRaySettings._RayIntensity = 0.5f;
					GodRays = CalcLegendRay( GodRaySettings );
				}

				float BorderRays = 0.0f;
				float YOffect = Input.UV0.y - 0.975f;
				if(YOffect > 0)
				{
					RaySettings BorderRaySettings;
					BorderRaySettings._UV0 = float2( Input.UV0.x *27, YOffect );
					BorderRaySettings._UV1 =  Input.UV2 * 27;
					BorderRaySettings._FadeTop = 0.03f;
					BorderRaySettings._FadeBottom = 0.25f;
					BorderRaySettings._TopFadoutWave = true;
					BorderRaySettings._WaveScale = 0.005f;
					BorderRaySettings._WaveMoveSpeed = 2.0f;
					BorderRaySettings._WaveFerquence = 10.0f;
					BorderRaySettings._RaySpeed = 3.0f;
					BorderRaySettings._RayDensity1 = 1.0f;
					BorderRaySettings._RayDensity2 = 3.0f;
					BorderRaySettings._RayIntensity = 0.3f;
					BorderRays = CalcLegendRay( BorderRaySettings );
					BorderRays *= smoothstep( 0.0001f , 0.005f , ( 1 - Input.UV0.y ) );
				}

				static float3 GodRaysColor = float3( 0.98f, 0.95f, 0.47f );
				static float3 LegendColor = float3( 0.68f, 0.65f, 0.27f );


				float3 Diffuse = ( GodRays * GodRaysColor ) + ( BorderRays * LegendColor );
				const float ZoomBlendOut = clamp( 1.0f - ( _WaterZoomedInZoomedOutFactor * 2.5f ), 0.0f, 1.0f );

				return ApplyVerticalBordersFog( float4( Diffuse, lerp( BorderRays, GodRays , GodRays ) * ZoomBlendOut ), Input.WorldSpacePos );
			}
		]]
	}
}
RasterizerState rasterizer_no_culling
{
	DepthBias = -70000
	SlopeScaleDepthBias = -2
	CullMode = "none"
}
RasterizerState RasterizerState
{
	DepthBias = -70000
	SlopeScaleDepthBias = -2
}


Effect VerticalBorder_1x
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader_1x"
}

Effect legend_vertical_border
{
	VertexShader = "VertexShader"
	PixelShader = "PS_LegendBorder"
	RasterizerState = "rasterizer_no_culling"
	Defines = { "PDX_BORDER_UV1" "PDX_BORDER_UV2" }
}
