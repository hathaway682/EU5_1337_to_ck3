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

# Shared constant buffer
ConstantBuffer( 0 )
{
	float AnimationLength;
	float MoveLength;
	float ClipLength;
	float TotalLength;
	float Width;
};


# Travel arrow specific constant buffer
ConstantBuffer( 1 )
{
	float NextDestination;
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
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	MainCode PixelShader
	{
		Input = VS_OUTPUT
		Output = PDX_COLOR

		Code
		[[
			PDX_MAIN
			{
				clip( SETGlobeVisible( Input.vPos ) );
				float vPassed = Input.vTexCoord.y < MoveLength ? 1.0f : 0.0f;

				float Tiling = 12.0 * Width;
				float NumTiles = floor( TotalLength / Tiling );
				float Offset = ( TotalLength - ( Tiling * NumTiles ) ) / Tiling;

				float Animation = 0.0f;
				float Speed = 0.15f;
				#ifdef FLAT_MAP
					Speed = 0.2f;
				#endif

				Animation = -GlobalTime * Speed;

				float2 UV = Input.vTexCoord.yx;
				UV.x /= Tiling;
				UV.x = UV.x + 1.0 - Offset;
				UV.y *= 0.5;
				UV.x += Animation;

				float2 texDdx = ddx(UV);
				float2 texDdy = ddy(UV);

				float2 UVPass = UV;
				UVPass.y += 0.5;

				float4 OutColor = PdxTex2DGrad( DiffuseTexture, UV, texDdx, texDdy );
				float4 OutColorMoved = PdxTex2DGrad( DiffuseTexture, UVPass, texDdx, texDdy );

				// Transition from regular arrow to already crossed terrain (darker)
				OutColor = lerp( OutColor, OutColorMoved, vPassed );

				float vFadeLength = ClipLength + 4.0f;
				float DestinationFadeDistance = abs( NextDestination - Input.vTexCoord.y );
				float vAlpha = DestinationFadeDistance - vFadeLength;
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