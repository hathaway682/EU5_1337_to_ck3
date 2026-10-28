# One source-heightmap-pixel radius. No global heightmap override or textures.
VertexShader = {
    Code
    [[
STerrainVertex CUCalcTerrainVertex( float2 WithinNodePos, float2 NodeOffset, float NodeScale, float2 LodDirection, float LodLerpFactor )
		{
        #ifndef PDX_TERRAIN_HEIGHT_MULTISAMPLE
            return CalcTerrainVertex(WithinNodePos, NodeOffset, NodeScale, LodDirection, LodLerpFactor);
        #else

			STerrainVertex Out;

			NodeScale = 1.0 / NodeScale;
			NodeOffset = NodeOffset * NodeScale;

			float2 QuadtreePosition = WithinNodePos * NodeScale + NodeOffset;

			float2 WorldSpacePosXZ = QuadtreePosition * NormQuadtreeToWorld;

			// The world will always have an overshoot of half a terrain quadtree cell's worth of vertices. Everything works fine if we just clamp those vertices to world extents here.
			WorldSpacePosXZ = clamp(WorldSpacePosXZ, float2(0.f, 0.f), WorldExtents);

			#ifdef PDX_TERRAIN_HEIGHT_MULTISAMPLE
				float Height = GetHeightMultisample( WorldSpacePosXZ, 1.0 );
			#else
				float Height = GetHeight( WorldSpacePosXZ );
			#endif

			float2 ScaledLodDirection = ( LodDirection * NodeScale / QuadtreeLeafNodeScale ) * OriginalHeightmapToWorldSpace;
			// Use the identical one-pixel kernel at both LOD endpoints.
            // Otherwise morphing would restore unsmoothed coast heights.
            float LerpedHeight = 0.5 * (
                GetHeightMultisample( WorldSpacePosXZ - ScaledLodDirection, 1.0 ) +
                GetHeightMultisample( WorldSpacePosXZ + ScaledLodDirection, 1.0 ));
			Height = lerp( Height, LerpedHeight, LodLerpFactor / UINT16_MAX );

			Out.WorldSpacePos = float3( WorldSpacePosXZ.x, Height, WorldSpacePosXZ.y );

			return Out;
		
        #endif
    }
    ]]
}
