Includes = {
    "spherical_earth_cloth.fxh"
    "cw/pdxterrain.fxh"
    "jomini/jomini.fxh"
    "cw/lighting_util.fxh"
    "jomini/jomini_fog.fxh"
    "jomini/jomini_water.fxh"
    "jomini/jomini_province_overlays.fxh"
    "standardfuncsgfx.fxh"
    "spherical_earth_theory.fxh"
    "cw/utility.fxh"
    "cu_wrap_dynamic_effects.fxh"
}

PixelShader = {
    TextureSampler CUFlatWrapFog
    {
        Ref = JominiFogOfWar
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Clamp"
    }
    TextureSampler CUFlatWrapWaterColor
    {
        Ref = JominiWaterTexture0
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Clamp"
    }
    TextureSampler CUFlatWrapPoliticalPattern
    {
        Index = 13
        File = "gfx/map/textures/political_mapmode_pattern.dds"
        srgb = yes
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Wrap"
    }
    TextureSampler CUFlatWrapTerrainSky
    {
        Index = 14
        File = "gfx/map/environment/environment_terrain_sunny.dds"
        srgb = yes
        Type = "Cube"
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Clamp"
        SampleModeV = "Clamp"
    }
    Code
    [[
        #ifndef ALPHA
        #ifndef CU_FLAT_WRAP_CODE
        #define CU_FLAT_WRAP_CODE
        // Rendering-only continuation. World data and mouse picking remain
        // in the original map. Nothing translates or folds existing vertices.
        float2 CUFlatWrapSource(float2 virtualXZ)
        {
            return float2(virtualXZ.x-16384.0*floor(virtualXZ.x/16384.0),virtualXZ.y);
        }
        float CUFlatWrapSurfaceHeight(float2 virtualXZ, float paper)
        {
            float2 source = CUFlatWrapSource(virtualXZ);
            return lerp(max(_WaterHeight,GetHeight(source)),FlatMapHeight,paper);
        }
        float3 CUFlatWrapNormal(float2 virtualXZ, float paper)
        {
            // Both samples wrap BEFORE packed-heightmap lookup. Clamping the
            // lookup to the border would create a flat vertical seam.
            float stepX = max(NormalStepSize.x,1.0);
            float stepZ = max(NormalStepSize.y,1.0);
            float dx = CUFlatWrapSurfaceHeight(virtualXZ+float2(stepX,0),paper)
                -CUFlatWrapSurfaceHeight(virtualXZ-float2(stepX,0),paper);
            float dz = CUFlatWrapSurfaceHeight(virtualXZ+float2(0,stepZ),paper)
                -CUFlatWrapSurfaceHeight(virtualXZ-float2(0,stepZ),paper);
            return normalize(float3(-dx/(2.0*stepX),1.0,-dz/(2.0*stepZ)));
        }
		void CUFlatWrapDetails( float2 WorldSpacePosXZ, float2 WorldDX, float2 WorldDY, out float4 DetailDiffuseHeight, out float3 DetailNormal, out float4 DetailMaterial )
		{
			float2 DetailCoordinates = WorldSpacePosXZ * WorldSpaceToDetail;
			float2 DetailCoordinatesScaled = DetailCoordinates * DetailTextureSize;
			float2 DetailCoordinatesScaledFloored = floor( DetailCoordinatesScaled );
			float2 DetailCoordinatesFrac = DetailCoordinatesScaled - DetailCoordinatesScaledFloored;
			DetailCoordinates = DetailCoordinatesScaledFloored * DetailTexelSize + DetailTexelSize * 0.5;

			float4 Factors = float4(
				(1.0 - DetailCoordinatesFrac.x) * (1.0 - DetailCoordinatesFrac.y),
				DetailCoordinatesFrac.x * (1.0 - DetailCoordinatesFrac.y),
				(1.0 - DetailCoordinatesFrac.x) * DetailCoordinatesFrac.y,
				DetailCoordinatesFrac.x * DetailCoordinatesFrac.y
			);

			float4 DetailIndex = PdxTex2DLod0( DetailIndexTexture, DetailCoordinates ) * 255.0;
			float4 DetailMask = PdxTex2DLod0( DetailMaskTexture, DetailCoordinates ) * Factors[0];

			float2 Offsets[3];
			Offsets[0] = float2( DetailTexelSize.x, 0.0 );
			Offsets[1] = float2( 0.0, DetailTexelSize.y );
			Offsets[2] = float2( DetailTexelSize.x, DetailTexelSize.y );

			for ( int k = 0; k < 3; ++k )
			{
				float2 DetailCoordinates2 = DetailCoordinates + Offsets[k];

				float4 DetailIndices = PdxTex2DLod0( DetailIndexTexture, DetailCoordinates2 ) * 255.0;
				float4 DetailMasks = PdxTex2DLod0( DetailMaskTexture, DetailCoordinates2 ) * Factors[k+1];

				for ( int i = 0; i < 4; ++i )
				{
					for ( int j = 0; j < 4; ++j )
					{
						if ( DetailIndex[j] == DetailIndices[i] )
						{
							DetailMask[j] += DetailMasks[i];
						}
					}
				}
			}

			float2 DefaultDetailUV = CalcDetailUV( WorldSpacePosXZ );
			float2 DDX = ApplyUpscaleLodBiasMultiplier( WorldDX * DetailTileFactor );
			float2 DDY = ApplyUpscaleLodBiasMultiplier( WorldDY * DetailTileFactor );

			float2 DetailUVs[4];
			for ( int n = 0; n < 4; ++n )
            {
				DetailUVs[n] = CalcDetailUVForDetailMaterial( WorldSpacePosXZ, DetailIndex[n] );
            }

			float4 DetailTexture0 = PdxTex2DGrad( DetailTextures, float3( DetailUVs[0], DetailIndex[0] ), DDX, DDY ) * smoothstep( 0.0, 0.1, DetailMask[0] );
			float4 DetailTexture1 = PdxTex2DGrad( DetailTextures, float3( DetailUVs[1], DetailIndex[1] ), DDX, DDY ) * smoothstep( 0.0, 0.1, DetailMask[1] );
			float4 DetailTexture2 = PdxTex2DGrad( DetailTextures, float3( DetailUVs[2], DetailIndex[2] ), DDX, DDY ) * smoothstep( 0.0, 0.1, DetailMask[2] );
			float4 DetailTexture3 = PdxTex2DGrad( DetailTextures, float3( DetailUVs[3], DetailIndex[3] ), DDX, DDY ) * smoothstep( 0.0, 0.1, DetailMask[3] );

			float4 BlendFactors = CalcHeightBlendFactors( float4( DetailTexture0.a, DetailTexture1.a, DetailTexture2.a, DetailTexture3.a ), DetailMask, DetailBlendRange );

			DetailDiffuseHeight = 	DetailTexture0 * BlendFactors[0] +
									DetailTexture1 * BlendFactors[1] +
									DetailTexture2 * BlendFactors[2] +
									DetailTexture3 * BlendFactors[3];

			DetailMaterial = vec4( 0.0 );
			float4 DetailNormalSample = vec4( 0.0 );

			for ( int i = 0; i < 4; ++i )
			{
				float BlendFactor = BlendFactors[i];
				if ( BlendFactor > 0.0 )
				{
					float3 ArrayUV = float3( DetailUVs[i], DetailIndex[i] );
					float4 NormalTexture = PdxTex2DGrad( NormalTextures, ArrayUV, DDX, DDY );
					float4 MaterialTexture = PdxTex2DGrad( MaterialTextures, ArrayUV, DDX, DDY );

					DetailNormalSample += NormalTexture * BlendFactor;
					DetailMaterial += MaterialTexture * BlendFactor;
				}
			}

			DetailNormal = UnpackRRxGNormal( DetailNormalSample ).xyz;
		}
        float3 CUFlatWrapShade(float3 virtualPosition, float paper, float2 worldDX, float2 worldDY)
        {
            float2 source = CUFlatWrapSource(virtualPosition.xz);
            float2 uv = source*WorldSpaceToTerrain0To1;
            float2 paperUV = float2(uv.x,1.0-uv.y);
            // Explicit periodic gradients prevent coarse mip stripes at U=0/1.
            float2 dx = worldDX*WorldSpaceToTerrain0To1*float2(1.0,-1.0);
            float2 dy = worldDY*WorldSpaceToTerrain0To1*float2(1.0,-1.0);
            dx.x -= floor(dx.x+0.5);
            dy.x -= floor(dy.x+0.5);
            // Identical non-sRGB paper encoding to native FlatMapTexture.
            float3 flat = PdxTex2DGrad(SETActiveFlatMap,paperUV,dx,dy).rgb;
            float3 base = flat;
            float sourceHeight = GetHeight(source);
            bool water = sourceHeight <= _WaterHeight+0.01;
            if (paper < 0.999 && !water)
            {
                float4 detail;
                float3 detailNormal;
                float4 material;
                CUFlatWrapDetails(source,worldDX,worldDY,detail,detailNormal,material);
                float3 tint = ToLinear(PdxTex2DGrad(ColorTexture,paperUV,dx,dy)).rgb;
                float3 normal = CUFlatWrapNormal(virtualPosition.xz,paper);
                CUApplyWrapConditions(detail,uv,normal);
                // Retain the native material and height relief. Shadow-map
                // samples from the opposite CPU frustum are not valid here.
                float3 diffuse = SoftLight(detail.rgb,tint,1.0-material.r);
                float3 surfaceNormal = normalize(float3(
                    normal.x+detailNormal.x,normal.y*max(detailNormal.z,0.1),normal.z+detailNormal.y));
                SMaterialProperties props = GetMaterialProperties(diffuse,surfaceNormal,
                    material.a,material.g,material.b);
                float3 directDiffuse;
                float3 directSpecular;
                CalculateLightingFromLight(props,normalize(CameraPosition-virtualPosition),
                    normalize(ToTerrainSunnySunDir),float3(1.0,0.9,0.8)*8.0,
                    directDiffuse,directSpecular);
                float3 skyDiffuse;
                float3 skySpecular;
                SLightingProperties sky = (SLightingProperties)0;
                sky._ToCameraDir = normalize(CameraPosition-virtualPosition);
                sky._CubemapIntensity = 0.25*DefaultEnvironmentCubemapIntensity;
                sky._CubemapYRotation = CubemapYRotation;
                CalculateLightingFromIBL(props,sky,CUFlatWrapTerrainSky,skyDiffuse,skySpecular);
                float3 terrain = directDiffuse+directSpecular+skyDiffuse+skySpecular;
                base = terrain;
            }
            else if (paper < 0.999)
            {
                // Native water-color atlas; do not shade ocean-floor materials.
                float3 waterColor = PdxTex2DGrad(CUFlatWrapWaterColor,paperUV,dx,dy).rgb;
                waterColor = lerp(waterColor,_WaterColorMapTint,_WaterColorMapTintFactor);
                base = waterColor;
            }
            // This is the live province-color atlas, including current map mode,
            // occupation stripes and alternate overlays, not a stored screenshot.
            float3 provinceColor;
            float preBlend;
            float postBlend;
            GetProvinceOverlayAndBlend(uv,provinceColor,preBlend,postBlend,0.0);
            // Same desaturation, political pattern and parchment blend as
            // native GetBorderColorAndBlendGameLerp; no second TerrainFlatMap Ref.
            float luminance = dot(provinceColor,float3(0.299,0.587,0.114));
            provinceColor = lerp(provinceColor,luminance.xxx,0.1);
            float2 patternUV = float2(uv.x*30.0,1.0-uv.y*15.0);
            float3 pattern = PdxTex2DGrad(CUFlatWrapPoliticalPattern,patternUV,
                worldDX*WorldSpaceToTerrain0To1*float2(30.0,-15.0),
                worldDY*WorldSpaceToTerrain0To1*float2(30.0,-15.0)).rgb;
            provinceColor = lerp(provinceColor,Overlay(pattern,provinceColor,1.0),1.0-paper*0.5);
            float3 gray = dot(flat,float3(0.333333,0.333333,0.333333)).xxx;
            provinceColor = HardLight(provinceColor,gray,paper*0.9);
            float fog = PdxTex2D(CUFlatWrapFog,uv).r;
            base = lerp(base,provinceColor,saturate(preBlend+postBlend)*fog);
            // Match native: brighten the paper endpoint once, then blend
            // lit terrain toward it. Never brighten an already mixed scene.
            float3 paperColor = lerp(flat,provinceColor,saturate(preBlend+postBlend));
            paperColor = CUNativePaperBrightness(paperColor);
            // Source coordinates address FoW; displayed coordinates measure
            // distance to the actual camera. Mixing these roles makes a whole
            // translated image receive the wrong distance fog.
            if (paper < 0.999)
            {
                float3 sourcePosition = float3(source.x,virtualPosition.y,source.y);
                float3 fogged = water
                    ? ApplyFogOfWarMultiSampled(base,sourcePosition,CUFlatWrapFog)
                    : ApplyFogOfWar(base,sourcePosition,CUFlatWrapFog);
                float distanceFactor = CalculateDistanceFogFactor(virtualPosition)
                    *CalculateZoomFogFactor();
                if (!water) distanceFactor *= 0.3+0.7*fog;
                fogged = CalculateFogColor(fogged,virtualPosition,distanceFactor);
                // The final native paper blend removes terrain fog gradually.
                base = fogged;
            }
            return max(lerp(base,paperColor,paper),0.0);
        }
        float4 CUFlatWrapScene(float4 scene, float2 screenUV, float4 rawScene, PdxTextureSampler2D nativeScene, out float reconstructedCoverage)
        {
            reconstructedCoverage = 0.0;
            if (SETGlobeBlend() > 0.0) return scene;
            // The shell uses this same inverse view-projection convention.
            float3 farPoint = WorldSpacePositionFromDepth(0.5,screenUV);
            float3 ray = normalize(farPoint-CameraPosition);
            if (ray.y >= -0.01) return scene;
            float paper = saturate(FlatMapLerp);
            float floorY = lerp(_WaterHeight,FlatMapHeight,paper);
            float floorDistance = (floorY-CameraPosition.y)/ray.y;
            if (floorDistance <= 0.0) return scene;
            float3 floorHit = CameraPosition+ray*floorDistance;
            // Evaluate on the continuous virtual plane before any per-pixel
            // map-boundary, coast or ray-convergence branch.
            float2 worldDX = ddx(floorHit.xz);
            float2 worldDY = ddy(floorHit.xz);
            if (floorHit.z < 0.0 || floorHit.z > 8192.0) return scene;
            float2 edgeGradient = float2(worldDX.x,worldDY.x);
            float pixelWidth = max(length(edgeGradient),0.01);
            float originalEdgeDistance = min(floorHit.x,16384.0-floorHit.x);
            bool originalMap = floorHit.x >= 0.0 && floorHit.x <= 16384.0;
            // Repair the raster fringe with actual native HDR pixels. Do not
            // regenerate terrain/province colours inside the original map:
            // those include boundary geometry and its own material masks.
            if (originalMap && originalEdgeDistance > 2.0*pixelWidth) return scene;
            if (originalEdgeDistance >= -pixelWidth)
            {
                float inward = floorHit.x < 8192.0 ? 1.0 : -1.0;
                float edgeX = floorHit.x < 8192.0 ? 0.0 : 16384.0;
                float nativeX = edgeX+inward*4.0*pixelWidth;
                float deltaX = nativeX-floorHit.x;
                float2 pixelOffset = edgeGradient*(deltaX/max(dot(edgeGradient,edgeGradient),0.0001));
                float2 nativeUV = screenUV+pixelOffset*InvScreenResolution;
                float4 nativePixel = PdxTex2DLod0(nativeScene,nativeUV);
                // Preserve name markers; do not spread their encoded alpha.
                if (nativePixel.a >= 0.0 && all(nativeUV >= 0.0) && all(nativeUV <= 1.0))
                {
                    reconstructedCoverage = 1.0;
                    return float4(nativePixel.rgb,scene.a);
                }
                if (originalMap) return scene;
            }

            float3 hit = floorHit;
            bool waterAtPlane = GetHeight(CUFlatWrapSource(floorHit.xz)) <= _WaterHeight+0.01;
            if (paper < 0.999 && !waterAtPlane)
            {
                float top = min(CameraPosition.y-0.1,max(floorY,HeightScale));
                float start = max(0.0,(top-CameraPosition.y)/ray.y);
                float previous = start;
                bool found = false;
                // Bounded traversal: 48 coarse steps and 10 binary refinements.
                // Only pixels outside the native map pay this cost.
                [loop]
                for (int i=0;i<=48;++i)
                {
                    float distance = lerp(start,floorDistance,float(i)/48.0);
                    float3 p = CameraPosition+ray*distance;
                    if (p.z >= 0.0 && p.z <= 8192.0
                        && p.y <= CUFlatWrapSurfaceHeight(p.xz,paper))
                    {
                        float lo = previous;
                        float hi = distance;
                        [unroll]
                        for (int j=0;j<10;++j)
                        {
                            float mid = (lo+hi)*0.5;
                            float3 q = CameraPosition+ray*mid;
                            if (q.y > CUFlatWrapSurfaceHeight(q.xz,paper)) lo=mid;
                            else hi=mid;
                        }
                        hit = CameraPosition+ray*((lo+hi)*0.5);
                        found = true;
                        break;
                    }
                    previous = distance;
                }
                if (!found) return scene;
            }
            if (hit.x >= 0.0 && hit.x <= 16384.0) return scene;
            if (hit.z < 0.0 || hit.z > 8192.0) return scene;
            float3 surface = CUFlatWrapShade(hit,paper,worldDX,worldDY);
            // Wrapped name draws carry negative coverage in HDR alpha. They
            // are composited here after the substitute surface, not overwritten.
            if (rawScene.a < -0.0001)
                surface = lerp(surface,rawScene.rgb,saturate(-rawScene.a));
            reconstructedCoverage = 1.0;
            return float4(surface,scene.a);
        }
        #endif
        #endif // ALPHA: no map reconstruction functions in portrait variants
    ]]
}
