import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

# Paths to your files
input_file = r"C:/Chapter2_RealWork/Featuredata_preprocessing/PET_Data_Processing_New/Feature_Constant/TWI/TWI_repro_South Eastern Highlands_clipped.tif"
#reference_file = r"E:/ResampledTiffs_90_22/South_Eastern_Highlands/Responsive/2010/z_score/2010 South_Eastern_Highland z_score Autumn_clipped.tif"
reference_file= r"C:/Chapter2_RealWork/Featuredata_preprocessing/PET_Data_Processing_New/zscore_reference/Tem_1989_Autumn.tif"
output_file = r"C:/Chapter2_RealWork/Featuredata_preprocessing/PET_Data_Processing_New/Dynamic_resampled/TWI.tif"

# 1. Open the reference raster to get its transform, CRS, extent, etc.
with rasterio.open(reference_file) as ref:
    ref_profile = ref.profile.copy()   # Full profile (metadata) of the reference
    ref_transform = ref.transform     # Affine transform
    ref_crs = ref.crs                 # Coordinate Reference System
    
# 2. Open the input raster we want to reproject
with rasterio.open(input_file) as src:
    
    # 2a. Create an empty NumPy array with the same shape & data type as reference
    #     We'll store the reprojected data here.
    #     Note: ref_profile['count'] is the number of bands in the reference,
    #           but you may have a different band count in src.
    #           So let's use src.count to preserve the same number of bands as input.
    out_data = np.zeros(
        (src.count, ref_profile["height"], ref_profile["width"]),
        dtype=ref_profile["dtype"]
    )
    
    # 2b. Reproject each band from src into out_data
    for band_idx in range(1, src.count + 1):
        reproject(
            source=rasterio.band(src, band_idx),
            destination=out_data[band_idx - 1],
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=Resampling.bilinear  # 'bilinear' for continuous data; use 'nearest' for categorical
        )
    
    # 2c. Update the reference profile to match the input band count (if different)
    ref_profile.update(
        count=src.count,  # Make sure the output has the same number of bands as the input
        dtype=ref_profile["dtype"]  # Keep the reference dtype or you could use src.dtypes[0]
    )

# 3. Write out the reprojected raster
with rasterio.open(output_file, 'w', **ref_profile) as dst:
    dst.write(out_data)
