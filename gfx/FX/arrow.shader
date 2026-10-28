Includes = {
	"cw/camera.fxh"
	"standardfuncsgfx.fxh"

	"spherical_earth_theory.fxh"
}


VertexStruct VS_INPUT
{
    float3 vPosition  : POSITION;
	float2 vTexCoord  : TEXCOORD0;
};

VertexStruct VS_OUTPUT
{
    float4 vPosition : PDX_POSITION;
    float2 vTexCoord : TEXCOORD0;
	float3 vPos		 : TEXCOORD1;
};


ConstantBuffer( 0 )
{
	float AnimationLength;
	float MoveLength;
	float ClipLength;
	float TotalLength;
	float Width;
};


VertexShader =
{
	MainCode VertexShader
	{
		Input = "VS_INPUT"
		Output = "VS_OUTPUT"
		Code
		[[
			PDX_MAIN
			{
				VS_OUTPUT Out;
				float4 pos = float4( Input.vPosition, 1.0f );
			#ifdef FLAT_MAP
				pos.y = lerp( pos.y, FlatMapHeight, SETZoomPaperBlend(FlatMapLerp) );
			#endif
				pos.y += 1.0f;

				Out.vPos = pos.xyz;
				Out.vPosition  = FixProjectionAndMul( ViewProjectionMatrix, float4( SETGlobeWarp( pos.xyz ), pos.w ) );
				Out.vTexCoord = Input.vTexCoord;

				return Out;
			}
		]]
	}
}


PixelShader =
{
	TextureSampler DiffuseTexture
	{
		Index = 0
		MipFilter = "Linear"
		MinFilter = "Linear"
		MagFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}
	#TextureSampler NormalMap
	#{
	#	Index = 1
	#	MipFilter = "Linear"
	#	MinFilter = "Linear"
	#	MagFilter = "Linear"
	#	SampleModeU = "Clamp"
	#	SampleModeV = "Clamp"
	#}
	#TextureSampler SpecularMap
	#{
	#	Index = 2
	#	MipFilter = "Linear"
	#	MinFilter = "Linear"
	#	MagFilter = "Linear"
	#	SampleModeU = "Clamp"
	#	SampleModeV = "Clamp"
	#}

	MainCode PixelShader
	{
		Input = VS_OUTPUT
		Output = PDX_COLOR

		Code
		[[
			PDX_MAIN
			{
				clip( SETGlobeVisible( Input.vPos ) );
				//return float4( mod( Input.vTexCoord.yyy, 1 ), 1.0f );

				clip( AnimationLength - Input.vTexCoord.y );
				clip( Input.vTexCoord.y - ClipLength );

				float vPassed = Input.vTexCoord.y < MoveLength ? 1.0f : 0.0f;

				float Tiling = 12.0 * Width;
				float NumTiles = floor( TotalLength / Tiling );
				float Offset = ( TotalLength - ( Tiling * NumTiles ) ) / Tiling;
				float2 UV = Input.vTexCoord.yx;
				UV.x /= Tiling;
				UV.x = UV.x + 1.0 - Offset;
				UV.y *= 0.5;

				float2 texDdx = ddx(UV);
				float2 texDdy = ddy(UV);

				float Tile = UV.x;
				UV.x = mod( UV.x, 0.5 );

				if( Tile >= NumTiles + 0.5 )
				{
					UV.x += 0.5;
				}
				else if( frac( Tile ) > 0.5 )
				{
					UV.x = 0.5 - UV.x;
				}

				float2 UVPass = UV;
				UVPass.y += 0.5;

				float4 OutColor = PdxTex2DGrad( DiffuseTexture, UV, texDdx, texDdy );
				float4 OutColorPass = PdxTex2DGrad( DiffuseTexture, UVPass, texDdx, texDdy );
				OutColor = lerp( OutColor, OutColorPass, vPassed );

				float vFadeLength = ClipLength + 2.0f;
				float vAlpha = Input.vTexCoord.y - vFadeLength;
				vAlpha = saturate( vAlpha * saturate( 1.0f - ( vAlpha/-vFadeLength ) ) );

			#ifdef FLAT_MAP
				vAlpha = lerp( 0.0, vAlpha, SETZoomPaperBlend(FlatMapLerp) );
			#else
				vAlpha = lerp( vAlpha, 0.0, SETZoomPaperBlend(FlatMapLerp) );
			#endif
				return float4( OutColor.rgb, OutColor.a * vAlpha * SETZoomDetailOpacity() );
			}
		]]
	}
}


BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}

RasterizerState RasterizerState
{
	DepthBias = -60000
	#fillmode = wireframe
}

DepthStencilState DepthStencilState
{
	DepthEnable = yes
	DepthWriteEnable = no
}


Effect ArrowEffect
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"
}

Effect ArrowEffectFlatMap
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "FLAT_MAP" }
}