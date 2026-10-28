Includes = {
	"cw/camera.fxh"

	"spherical_earth_theory.fxh"
}


ConstantBuffer( 1 )
{
	float3		Scale;
	float		Padding;
	float2		UVSpeed0;
	float2		UVSpeed1;
	float2		UVSpeed2;
	float2		UVSpeed3;
	float2		UVScale0;
	float2		UVScale1;
	float2		UVScale2;
	float2		UVScale3;
}

ConstantBuffer( 2 )
{
	float		Alpha;
	float3		Color;
}

ConstantBuffer( 3 )
{
	float VerticalBordersTime;
	float HeightOffset;
}

VertexStruct VS_INPUT_PDX_BORDER
{
	float3 Position				: POSITION;
	float  Extrusion			: TEXCOORD0;
	float  DistanceToStart		: TEXCOORD1;
	float  DistanceToEnd		: TEXCOORD2;
	float2 UV					: TEXCOORD3;
};

VertexStruct VS_OUTPUT_PDX_BORDER
{
	float4 Position				: PDX_POSITION;
	float3 WorldSpacePos		: TEXCOORD0;
	float  DistanceToStart		: TEXCOORD1;
	float  DistanceToEnd		: TEXCOORD2;
	float2 UV0					: TEXCOORD3;
@ifdef PDX_BORDER_UV1
	float2 UV1					: TEXCOORD4;
@endif
@ifdef PDX_BORDER_UV2
	float2 UV2					: TEXCOORD5;
@endif
@ifdef PDX_BORDER_UV3
	float2 UV3					: TEXCOORD6;
@endif
};

Code
[[
	float3 ScaleAndExtrudePosition( float3 InputPosition, float Extrusion )
	{
		float3 Position = InputPosition * float3( Scale.x, 1.0, Scale.z );
		float ExtrusionFactor = Scale.y * Extrusion;
		Position.y += HeightOffset + ExtrusionFactor + abs( ExtrusionFactor );

		return Position;
	}
	float2 ScaleAndAnimateUV( float2 UV, float2 UVScale, float2 UVSpeed )
	{
		return UV * UVScale + UVSpeed * VerticalBordersTime;
	}
]]


VertexShader =
{
	MainCode VertexShader
	{
		Input = "VS_INPUT_PDX_BORDER"
		Output = "VS_OUTPUT_PDX_BORDER"
		Code
		[[
			PDX_MAIN
			{
				VS_OUTPUT_PDX_BORDER Out;

				Out.DistanceToStart = Input.DistanceToStart;
				Out.DistanceToEnd = Input.DistanceToEnd;
				Out.WorldSpacePos = ScaleAndExtrudePosition( Input.Position, Input.Extrusion );
				Out.Position = FixProjectionAndMul( ViewProjectionMatrix, float4( SETGlobeWarp( Out.WorldSpacePos ), 1.0 ) );
				Out.UV0 = ScaleAndAnimateUV( Input.UV, UVScale0, UVSpeed0 );
			#ifdef PDX_BORDER_UV1
				Out.UV1 = ScaleAndAnimateUV( Input.UV, UVScale1, UVSpeed1 );
			#endif
			#ifdef PDX_BORDER_UV2
				Out.UV2 = ScaleAndAnimateUV( Input.UV, UVScale2, UVSpeed2 );
			#endif
			#ifdef PDX_BORDER_UV3
				Out.UV3 = ScaleAndAnimateUV( Input.UV, UVScale3, UVSpeed3 );
			#endif
				return Out;
			}
		]]
	}

}


PixelShader =
{
	TextureSampler BorderTexture0
	{
		Ref = JominiVerticalBordersMask0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler BorderTexture1
	{
		Ref = JominiVerticalBordersMask1
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler BorderTexture2
	{
		Ref = JominiVerticalBordersMask2
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
	TextureSampler BorderTexture3
	{
		Ref = JominiVerticalBordersMask3
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}

	Code
	[[
		static const float3 LUMINOSITY_FUNCTION = float3( 0.2126, 0.7152, 0.0722 );

		float3 CalculateLayerColor( float3 TextureColor, float3 LayerColor )
		{
			return dot( TextureColor, LUMINOSITY_FUNCTION ) * LayerColor;
		}

		float4 DefaultOverlayColor( float4 Base, float4 Overlay )
		{
			float3 Diffuse = lerp( Base, Overlay, step( Overlay.a, 0.5 ) ).rgb;
			return float4( Diffuse, max( Base.a, Overlay.a ) );
		}
	]]
}


BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
	WriteMask = "RED|GREEN|BLUE"
}

RasterizerState RasterizerState
{
	DepthBias = -10000
	SlopeScaleDepthBias = -2
	CullMode = "none"
}

DepthStencilState DepthStencilState
{
	DepthWriteEnable = no
}
