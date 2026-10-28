Includes = { "spherical_earth_theory.fxh" "cw/utility.fxh" "cu_native_paper_brightness.fxh" }
PixelShader =
{
    TextureSampler SETBackgroundMap
    {
        Index = 11
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Clamp"
        srgb = no
        File = "gfx/map/terrain/flat_maps/flatmap.dds"
    }
    TextureSampler SETPolarLandMask
    {
        Index = 12
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Clamp"
        srgb = no
        File = "gfx/map/spherical_background/polar_land_mask.dds"
    }
    TextureSampler SETActiveFlatMap
    {
        # The engine chooses this texture for the current player's paper style.
        Ref = TerrainFlatMap
        srgb = no
        MagFilter = "Linear"
        MinFilter = "Linear"
        MipFilter = "Linear"
        SampleModeU = "Wrap"
        SampleModeV = "Clamp"
    }
    Code
    [[
        #ifndef SET_CLOTH_SHELL
        #define SET_CLOTH_SHELL
        // The restore pass covers the whole viewport, including the parts for
        // which the regional terrain mesh supplies no vertices.


        // Continue from the cropped map edge to the geometric pole. Inverting
        // the planar transition beyond the crop and clamping latitude to 90
        // degrees repeats the pole over a cap/ring instead of one point.

        float SETPaperHash(float3 p)
        {
            p = frac(p*0.1031);
            p += dot(p,p.yzx+33.33);
            return frac((p.x+p.y)*p.z);
        }
        float SETPaperNoise(float3 p)
        {
            float3 cell = floor(p);
            float3 f = frac(p);
            f = f*f*(3.0-2.0*f);
            float z0 = lerp(lerp(SETPaperHash(cell),SETPaperHash(cell+float3(1,0,0)),f.x),
                lerp(SETPaperHash(cell+float3(0,1,0)),SETPaperHash(cell+float3(1,1,0)),f.x),f.y);
            float z1 = lerp(lerp(SETPaperHash(cell+float3(0,0,1)),SETPaperHash(cell+float3(1,0,1)),f.x),
                lerp(SETPaperHash(cell+float3(0,1,1)),SETPaperHash(cell+float3(1,1,1)),f.x),f.y);
            return lerp(z0,z1,f.z)*2.0-1.0;
        }
        float3 SETParchmentPaper(float longitude, float latitude)
        {
            // Continuous geographic paper grain: no repeated source-image tiles.
            float3 globe = float3(cos(latitude)*sin(longitude),sin(latitude),cos(latitude)*cos(longitude));
            float3 offset = float3(17.3,29.1,41.7);
            // Keep one noise body instead of four compiler-expanded copies.
            const float frequencies[4] = {7.0,23.0,71.0,223.0};
            const float amplitudes[4] = {0.010,0.006,0.003,0.0015};
            float grain = 0.0;
            [loop]
            for (int octave=0; octave<4; ++octave)
                grain += SETPaperNoise(globe*frequencies[octave]+offset)*amplitudes[octave];
            return saturate(float3(0.4705882353,0.4823529412,0.4284313725)+grain*float3(1.0,0.98,0.92));
        }
        float3 SETPolarSurface(float longitude, float latitude, float3 oceanPaper)
        {
            // The mask is equirectangular WGS84 (-180..180, 90..-90),
            // independent of the Gall/Miller map and its cropped latitude range.
            float2 polarUV = float2(frac(longitude/(2.0*SETGlobePi)+0.5),
                saturate(0.5-latitude/SETGlobePi));
            // Across the longitude seam, automatic derivatives see a full
            // texture-width jump and select coarse mips, creating a stripe.
            // Use the shortest periodic U gradient; preserve latitude filtering.
            float2 polarDx = ddx(polarUV);
            float2 polarDy = ddy(polarUV);
            polarDx.x -= floor(polarDx.x+0.5);
            polarDy.x -= floor(polarDy.x+0.5);
            float2 mask = PdxTex2DGrad(SETPolarLandMask,polarUV,polarDx,polarDy).rg;
            float land = smoothstep(0.25,0.75,mask.r);
            // Northern land uses normal parchment colors; ice is Antarctic only.
            float ice = smoothstep(62.0,78.0,-latitude*180.0/SETGlobePi);
            float3 landColor = lerp(float3(0.6953823530,0.6427843138,0.5511078431),
                float3(0.7977377330,0.8209798483,0.8036309869),ice*0.78);
            // Height exists only where supplied by the DEM. Antarctic contour
            // comes from Natural Earth; no Antarctic elevation is invented.
            landColor *= 1.0-0.14*mask.g;
            // Reuse the existing ocean-paper grain; do not evaluate the
            // four-layer procedural paper noise again for every shell pixel.
            float3 grain = clamp(oceanPaper-float3(0.4705882353,0.4823529412,0.4284313725),-0.015,0.015);
            landColor += grain*0.45;
            return saturate(lerp(oceanPaper,landColor,land));
        }
        float3 SETBackgroundSample(float3 radial, float2 focus, float blend)
        {
            float2 coordinates = SETGlobeCoordinates(radial,focus);
            float latitude = coordinates.y;
            // Invert the same closing correction used by the terrain mesh.
            // This keeps texture pixels aligned without changing the source map.
            float mapX = coordinates.x/SETGlobeLongitudeScale()+focus.x;
            float globalU = frac((mapX+0.5)/16384.0);
            // Polar decoration uses one continuous geographic turn as well.
            float longitude = (mapX+0.5)*(2.0*SETGlobePi/16384.0)+(-2.94909610793353938);
            float projectedY = (10888160.92403682135045528)*tan(latitude*0.5);
            float pixelY = (projectedY-(8389899.80818169005215168))/(-1733.36548308285591702);
            float2 uv = float2(globalU,(pixelY+0.5)/8192.0);
            // Source projection ends before the poles. Fade into matching
            // parchment sea rather than exposing the table cloth or stretching land.
            float edgeFade = smoothstep(0.0,0.015,uv.y)*smoothstep(0.0,0.015,1.0-uv.y);
            float2 sampleUV = float2(uv.x,saturate(uv.y));
            // Wrapped U jumps from 1 to 0 at the join. Automatic derivatives
            // would select a coarse mip there and expose a thin color stripe.
            float2 sampleDx = ddx(sampleUV);
            float2 sampleDy = ddy(sampleUV);
            sampleDx.x -= floor(sampleDx.x+0.5);
            sampleDy.x -= floor(sampleDy.x+0.5);
            float3 fallbackColor = PdxTex2DGrad(SETBackgroundMap,sampleUV,sampleDx,sampleDy).rgb;
            float3 activeColor = PdxTex2DGrad(SETActiveFlatMap,sampleUV,sampleDx,sampleDy).rgb;
            float activeValid = step(0.005,max(activeColor.r,max(activeColor.g,activeColor.b)));
            float3 mapColor = lerp(fallbackColor,activeColor,activeValid);
            float3 oceanColor = (
                PdxTex2DLod(SETActiveFlatMap,float2(0.08,0.40),5.0).rgb
                +PdxTex2DLod(SETActiveFlatMap,float2(0.92,0.40),5.0).rgb
                +PdxTex2DLod(SETActiveFlatMap,float2(0.08,0.65),5.0).rgb
                +PdxTex2DLod(SETActiveFlatMap,float2(0.92,0.65),5.0).rgb)*0.25;
            float3 paperMean = float3(0.4705882353,0.4823529412,0.4284313725);
            float oceanValid = step(0.005,max(oceanColor.r,max(oceanColor.g,oceanColor.b)));
            float3 paper = SETParchmentPaper(longitude,latitude)
                +lerp(paperMean,oceanColor,oceanValid)-paperMean;
            float3 diffuse = saturate(mapColor);
            float3 polarSurface = SETPolarSurface(longitude,latitude,paper);
            return saturate(lerp(polarSurface,diffuse,edgeFade));
        }
        float3 SETStarLayer(float2 sky, float density, float seedOffset, float occupancy)
        {
            float2 grid = sky*density;
            float2 cell = floor(grid);
            float seed = SETPaperHash(float3(cell,seedOffset));
            float a = SETPaperHash(float3(cell,seedOffset+11.0));
            float b = SETPaperHash(float3(cell,seedOffset+23.0));
            float2 delta = frac(grid)-(float2(a,b)*0.5+0.25);
            float a2 = a*a;
            float radius = 0.028+0.065*a2*a2;
            float radius2 = radius*radius;
            float d2 = dot(delta,delta);
            float core = saturate(1.0-d2/radius2);
            float halo = saturate(1.0-d2/(radius2*6.0));
            float visible = step(1.0-occupancy,seed);
            float3 tint = lerp(float3(0.84,0.91,1.0),float3(1.0,0.93,0.83),b);
            // Many dim, small stars and a small population of brighter ones.
            float light = core*core*(0.045+0.65*a2*a2*a2)
                +halo*halo*0.008*a2*a2;
            return tint*light*visible;
        }
        float3 SETSkyPlanet(float3 ray, float3 direction, float radius, float3 tint, float brightness)
        {
            // Fixed decorative sky directions, not astronomical ephemerides.
            float3 delta = ray-normalize(direction);
            float d2 = dot(delta,delta);
            float radius2 = radius*radius;
            float core = saturate(1.0-d2/radius2);
            float halo = saturate(1.0-d2/(radius2*16.0));
            return tint*brightness*(core*core+halo*halo*0.018);
        }
        float4 SETStarBackground(float4 scene, float3 ray, float blend, float atmosphere)
        {
            // Fixed four-layer loops limit compiler expansion; no new samplers or derivatives.
            float latitude = asin(clamp(ray.y,-1.0,1.0));
            float2 sky = float2(atan2(ray.z,ray.x)/(2.0*SETGlobePi)+0.5,
                latitude/SETGlobePi+0.5);
            // Frame the galaxy across the upper sky as soon as the globe appears.
            float forward = max(dot(ray,normalize(CameraLookAtDir)),0.05);
            float skyUp = dot(ray,normalize(CameraUpDir))/forward;
            float skyRight = dot(ray,normalize(CameraRightDir))/forward;
            float bandAxis = skyUp-0.40+0.18*skyRight;
            // Lightweight directional waves replace 16 lattice hash evaluations.
            // The galaxy retains continuous cloud and dust variation without tiles.
            float bend = sin(dot(ray,float3(9.0,-13.0,17.0)));
            float cloud = 0.5+0.28*sin(dot(ray,float3(17.0,11.0,7.0))+2.0*bend)
                +0.16*sin(dot(ray,float3(-31.0,19.0,23.0)));
            float detail = 0.5+0.25*sin(dot(ray,float3(53.0,-37.0,41.0)))
                +0.20*sin(dot(ray,float3(-29.0,71.0,31.0)));
            float band = exp(-bandAxis*bandAxis*70.0);
            float dustAxis = bandAxis+0.045*(cloud-0.5);
            float dust = exp(-dustAxis*dustAxis*420.0)*(0.35+0.55*detail);
            float cloudLight = band*(0.20+0.80*cloud)*(0.60+0.40*detail)*(1.0-0.75*dust);
            float3 galaxyTint = lerp(float3(0.0018,0.0035,0.0100),float3(0.0080,0.0050,0.0120),cloud);
            float3 galaxy = galaxyTint*cloudLight;
            float occupancy = (0.10+0.14*band)*max(0.12,cos(latitude));
            // Preserve all four star populations with one compiled layer body.
            const float densities[4] = {480.0,720.0,960.0,220.0};
            const float seeds[4] = {71.0,157.0,233.0,311.0};
            const float occupancies[4] = {1.0,1.0,0.65,0.75};
            const float weights[4] = {1.0,0.50,0.25,1.40};
            float3 stars = float3(0.0,0.0,0.0);
            [loop]
            for (int layer=0; layer<4; ++layer)
                stars += SETStarLayer(sky,densities[layer],seeds[layer],occupancy*occupancies[layer])*weights[layer];
            const float3 directions[4] = {float3(-0.55,-0.65,0.52),float3(0.58,-0.70,0.42),
                float3(0.72,-0.61,-0.33),float3(-0.70,-0.62,-0.36)};
            const float radii[4] = {0.0018,0.0012,0.0016,0.0011};
            const float3 tints[4] = {float3(1.0,0.97,0.88),float3(1.0,0.72,0.53),
                float3(1.0,0.93,0.81),float3(1.0,0.90,0.70)};
            const float brightness[4] = {1.8,0.85,1.3,0.70};
            float3 planets = float3(0.0,0.0,0.0);
            [loop]
            for (int planet=0; planet<4; ++planet)
                planets += SETSkyPlanet(ray,directions[planet],radii[planet],tints[planet],brightness[planet]);
            // In globe mode the original table is replaced by sky, even when
            // its original color is bright. Flat mode never enters this pass.
            float3 skyColor = float3(0.00035,0.00050,0.00085)+galaxy+stars+planets
                +float3(0.018,0.045,0.100)*atmosphere;
            return float4(skyColor,scene.a); // The table has already been discarded.
        }
        float4 SETClothFill(float4 scene, float2 screenUV, float sceneCoverage)
        {
            float blend = SETGlobeBlend();
            // Use exactly the table color/depth cutoff. Leaving a later
            // background fade exposes the clear buffer as a black fog interval.
            if (blend <= 0.001) return scene;
            float opacity = 1.0;
            float2 focus = SETGlobeFocus();
            float baseRadius = SETGlobeRadius();
            float radius = baseRadius + 0.52;
            float3 center = SETGlobeCenter();
            float3 farPoint = WorldSpacePositionFromDepth(0.5, screenUV);
            float3 ray = normalize(farPoint-CameraPosition);
            float3 offset = CameraPosition-center;
            float along = dot(offset,ray);
            float discriminant = along*along-dot(offset,offset)+radius*radius;
            // Distance of the view ray from the same moving globe center.
            // The exterior halo follows the true silhouette, not a GUI circle.
            float closestRadius = sqrt(max(dot(offset,offset)-along*along,0.0));
            float atmosphere = exp(-max(closestRadius-radius,0.0)/max(radius*0.009,1.0));
            atmosphere *= 1.0-step(0.0,along);
            bool missesSphere = discriminant <= 0.0 || along >= 0.0;
            float distance = -along-sqrt(max(discriminant,0.0));
            [branch]
            if (missesSphere || distance <= 0.0)
            {
                // Keep actual rendered geometry even beyond the analytic shell.
                if (sceneCoverage >= 0.999) return scene;
                return SETStarBackground(scene,ray,blend,missesSphere ? atmosphere : 0.0);
            }
            float3 radial = normalize(offset+ray*distance);
            // Coverage is captured from the raw scene before bloom/fog blur.
            // It does not depend on geographic bounds or distance to the shell.
            // Fast path preserves normal map pixels without sampling the fill.
            if (sceneCoverage >= 0.999)
                return scene; // Native geometry keeps its original colour.

            float3 diffuse = SETBackgroundSample(radial,focus,blend);
            // Same texture encoding and brightness function as native paper.
            // Exposure, contrast, tone mapping and output gamma remain shared.
            float3 color = CUNativePaperBrightness(diffuse);
            // Smooth only near-black clear fragments at the rendered seam.
            float3 filled = lerp(color,scene.rgb,sceneCoverage);
            return float4(lerp(scene.rgb,filled,opacity),1.0);
        }
        #endif
    ]]
}
