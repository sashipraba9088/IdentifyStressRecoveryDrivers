//////// Please note that :
// Before you run this code please add LandTrender.js to your GEE directory.
// Import the eu_forest the raster tiff file for the eucalyptus forest tiff and shape file of the bioregion interrested.



Map.centerObject(aoi, 7);


var nbrVis = {
    min: -1000, 
    max: 1000, 
    palette: [
        'black',  // Severely burned
        'red',    // Burned areas
        'orange', // Burned areas with less severity
        'yellow', // Transition areas or lightly burned
        'lightgreen', // Healthy vegetation with some stress
        'green'   // Healthy vegetation
    ]
};

var ZVis = {
    min: -5, 
    max: 5, 
    palette: [
        'black',  // Severely burned
        'red',    // Burned areas
        'orange', // Burned areas with less severity
        'yellow', // Transition areas or lightly burned
        'lightgreen', // Healthy vegetation with some stress
        'green'   // Healthy vegetation
    ]
};

////////////////////////////////////////////////////// Import LandTrender Js ////////////////////////////////////////////////////////////////
var LandTrender = require('users/nuwanthisashipraba/PHD_Chapter1:LandTrendr.js');
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////Fire Mask Function //////////////////////////////////////////////////////////////////////

function getSeasonalBurnArea(year, season) {
  // Define the start and end months for each season, considering the Southern Hemisphere
  var seasonDefinition = {
    'Summer': {startMonth: 12, endMonth: 2, endYearOffset: 1},
    'Autumn': {startMonth: 3, endMonth: 5, endYearOffset: 0},
    'Winter': {startMonth: 6, endMonth: 8, endYearOffset: 0},
    'Spring': {startMonth: 9, endMonth: 11, endYearOffset: 0}
  };

  var seasonInfo = seasonDefinition[season];
  var startMonth = seasonInfo.startMonth;
  var endMonth = seasonInfo.endMonth;
  var endYear = year + seasonInfo.endYearOffset;

  // Adjust the year for the start of Summer season
  var startYear = season === 'Summer' && startMonth === 12 ? year : endYear;

  // Create date strings for filtering
  var startDate = ee.Date.fromYMD(startYear, startMonth, 1);
  var endDate = ee.Date.fromYMD(endYear, endMonth + 1, 1).advance(-1, 'day'); // Last day of end month

  // Filter MODIS fire dataset for the specified season and year
  var fireCollection = ee.ImageCollection('MODIS/061/MCD64A1')
                      .filterDate(startDate, endDate)
                      .select('BurnDate');
                      
                     
    
    //print(fireCollection)

  // Combine monthly burn data into a single season-wide burn mask
  // Burned areas are marked with BurnDate > 0
  var burnMask = fireCollection.reduce(ee.Reducer.max()).not();
      burnMask = burnMask.unmask(1).clip(aoi).rename('Unburnt');
  
  //print(burnMask)
  //Map.addLayer(burnMask)

  return burnMask;
}



////////////////////////////////////////////////////////Load Landsat Seasonal images 1990 to 2016///////////////////////////////////////////

var maskConditions = ['cloud', 'shadow', 'water'];
var startYear = 1990; // Start year for analysis
var endYear = 2016; // End year for analysis

// NBR Transformation function
var nbrTransform = function(img) {
    return img.normalizedDifference(['B4', 'B7'])
              .multiply(1000)
              .rename('NBR')
              .toFloat()
              .set('system:time_start', img.get('system:time_start'));
};

// Function to process seasonal collection
var processSeasonalCollection = function(year, season, startDate, endDate, aoi, maskConditions, LandTrender, nbrTransform) {
  var collection = LandTrender.getCombinedSRcollection(year.toString(), startDate, endDate, aoi, maskConditions)
                      .map(nbrTransform);
    
    // Apply fire mask only for years greater than 2000
    if (year > 2003) {
        var fireMasks = getSeasonalBurnArea(year, season);
        collection = collection.map(function(image) {
            return image.updateMask(fireMasks);
        });
    }

    return collection.median().select('NBR');
    
    
};

// Initialize a dictionary to store image collections
var seasonalNBRImageCollections = {
    'Autumn': ee.ImageCollection([]),
    'Winter': ee.ImageCollection([]),
    'Spring': ee.ImageCollection([]),
    'Summer': ee.ImageCollection([])
};

// Iterate over each year and add to the seasonal image collections
for (var year = startYear; year <= endYear; year++) {
    var seasons = {
        'Autumn': {start: '03-01', end: '05-31'},
        'Winter': {start: '06-01', end: '08-31'},
        'Spring': {start: '09-01', end: '11-30'}
    };
    Object.keys(seasons).forEach(function(season) {
        var startDate = seasons[season].start;
        var endDate = seasons[season].end;
        var seasonalImage = processSeasonalCollection(year, season, startDate, endDate, aoi, maskConditions, LandTrender, nbrTransform);
        seasonalNBRImageCollections[season] = seasonalNBRImageCollections[season].merge(seasonalImage);
    });

    // Process Summer season separately due to year boundary
    
    
    var nextYear = year + 1;
    var decCollection = LandTrender.getCombinedSRcollection(year.toString(), '12-01', '12-31', aoi, maskConditions).map(nbrTransform);
    var janFebCollection = LandTrender.getCombinedSRcollection(nextYear.toString(), '01-01', '02-' + new Date(nextYear, 2, 0).getDate(), aoi, maskConditions).map(nbrTransform);
    var summerImage = decCollection.merge(janFebCollection).median().clip(aoi).select('NBR');
    if(year>2003){
      var season ='Summer'
      var fireMasks = getSeasonalBurnArea(year, season);
      summerImage = summerImage.updateMask(fireMasks)
    }
    seasonalNBRImageCollections['Summer'] = seasonalNBRImageCollections['Summer'].merge(summerImage);
    
    
}

// Print the seasonal NBR image collections
// Object.keys(seasonalNBRImageCollections).forEach(function(season) {
//     print(season + ' NBR Image Collection:', seasonalNBRImageCollections[season]);
// });

//////////////////////////////////////////////////////////Predicted sentinel images using coefient ///////////////////////////////////////////

var predictionCoefficients = {
    'Summer': {intercept: 74.32425058, slope: 0.755380510},
    'Autumn': {intercept: 144.7916255, slope: 0.66789412},
    'Winter': {intercept: 198.32637548, slope: 0.60385706},
    'Spring': {intercept: 103.4930753, slope: 0.73227437}
};


function predictSentinel2NBR(seasonalNBRImageCollections, predictionCoefficients) {
    var predictedSeasonalNBRImageCollections = {
        'Autumn': ee.ImageCollection([]),
        'Winter': ee.ImageCollection([]),
        'Spring': ee.ImageCollection([]),
        'Summer': ee.ImageCollection([])
    };

    Object.keys(predictedSeasonalNBRImageCollections).forEach(function(season) {
        var seasonalCollection = seasonalNBRImageCollections[season];
        var coefficients = predictionCoefficients[season];
        
        var predictedCollection = seasonalCollection.map(function(image) {
            // Apply prediction model: NBR' = intercept + slope * NBR
            var predictedNBR = image.select('NBR').multiply(coefficients.slope).add(coefficients.intercept).rename('sentiNBR').toFloat();
            return (predictedNBR);
        });
        
        predictedSeasonalNBRImageCollections[season] = predictedCollection;
    });

    return predictedSeasonalNBRImageCollections;
}

var predictedSeasonalNBRImageCollections = predictSentinel2NBR(seasonalNBRImageCollections, predictionCoefficients);
//print(predictedSeasonalNBRImageCollections,'Predicted sentinel images 1990 to 2016')


// ///////////////////////////////////////////////////////////////Visualize Predicted Sentinel images//////////////////////////////////////////
// function visualizeSeasonalPredictionsForYear(year) {
//     // Calculate the index based on the year. Assuming 1990 is the first year in the collection.
//     var index = year - 1990;  // Adjust based on your collection's start year if necessary
//     print(index)
//     // Define seasons
//     var seasons = ['Summer', 'Autumn', 'Winter', 'Spring'];
    
//     // Iterate through each season and visualize the corresponding NBR image for the given year
//     seasons.forEach(function(season) {
//         var seasonCollection = predictedSeasonalNBRImageCollections[season];
//         var listOfImages = seasonCollection.toList(seasonCollection.size());
//         var image = ee.Image(listOfImages.get(index)).select("PredictedNBR");
//         //print(image)
//         Map.addLayer(image, nbrVis, season + ' ' + year + ' Predicted NBR');
//     });
// }

// // Example: Visualize the predicted NBR for all four seasons of a specific year
// visualizeSeasonalPredictionsForYear(2010);  // Pass the year you want to visualize

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////Get sentinel 2 From 2017 to 2022 //////////////////////////////////////////////////


var s2SrC = ee.ImageCollection('COPERNICUS/S2_HARMONIZED');
var s2CloudsC = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY');
var aoi; // Ensure that 'aoi' (Area of Interest) is defined

// Define maximum cloud probability threshold
var MAX_CLOUD_PROBABILITY = 50;

// Function to mask clouds using the cloud probability dataset
function maskClouds(img) {
  var clouds = ee.Image(img.get('cloud_mask')).select('probability');
  var isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY);
  return img.updateMask(isNotCloud);
}

// Function to add NBR band to an image
function addNBR(image) {
  // Select the NIR (B8A) and SWIR (B12) bands from the image
  var nir = image.select('B8');
  var swir = image.select('B12');
  // Calculate NBR using arithmetic operations
  var nbr = nir.subtract(swir).divide(nir.add(swir)).multiply(1000).rename('sentiNBR');
  return image.addBands(nbr);
}

// Function to generate NBR images for each season of each year in the specified range
function generateSeasonalNBRImages(startYear, endYear) {
  var seasonalNBRCollections = {
    'Summer': ee.ImageCollection([]),
    'Autumn': ee.ImageCollection([]),
    'Winter': ee.ImageCollection([]),
    'Spring': ee.ImageCollection([])
  };

  for (var year = startYear; year <= endYear; year++) {
    var seasons = {
      'Summer': [ee.Date.fromYMD(year, 12, 1), ee.Date.fromYMD(year + 1, 3, 1)], // Dec-Feb
      'Autumn': [ee.Date.fromYMD(year, 3, 1), ee.Date.fromYMD(year, 6, 1)],      // Mar-May
      'Winter': [ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 1)],      // Jun-Aug
      'Spring': [ee.Date.fromYMD(year, 9, 1), ee.Date.fromYMD(year, 12, 1)]      // Sep-Nov
    };

    Object.keys(seasons).forEach(function(season) {
      var dateRange = seasons[season];
      var s2Sr = s2SrC.filterDate(dateRange[0], dateRange[1]).filterBounds(aoi);
      var s2Clouds = s2CloudsC.filterDate(dateRange[0], dateRange[1]).filterBounds(aoi);

      // Join S2 SR with cloud probability dataset to add cloud mask.
      var s2SrWithCloudMask = ee.Join.saveFirst('cloud_mask').apply({
        primary: s2Sr,
        secondary: s2Clouds,
        condition: ee.Filter.equals({ leftField: 'system:index', rightField: 'system:index' })
      });

      var s2CloudMasked = ee.ImageCollection(s2SrWithCloudMask)
        .map(maskClouds)
        .map(addNBR)
        .median()
        .select('sentiNBR')
        .clip(aoi)
       
        
        var fireMasks = getSeasonalBurnArea(year, season);
        s2CloudMasked = s2CloudMasked.updateMask(fireMasks);
        
        //Map.addLayer(s2CloudMasked,nbrVis,year+"_"+season)

      seasonalNBRCollections[season] = seasonalNBRCollections[season].merge(s2CloudMasked);
    });
  }

  return seasonalNBRCollections;
}

// Generate the seasonal NBR image collections
var sentinelSeasonalNBRCollections = generateSeasonalNBRImages(2017, 2022);

// Print the seasonal NBR image collections
// Object.keys(sentinelSeasonalNBRCollections).forEach(function(season) {
//   print(season + ' NBR Image Collection:', sentinelSeasonalNBRCollections[season]);
// });




////////////////////////////////////////////////////// combine and obtain mean and SD //////////////////////////////////////////////////////////////////


// Define a function to merge two image collections, calculate the mean and standard deviation
function mergeAndCalculateStats(landsatCollection, sentinelCollection) {
  // Merge the two collections
  var mergedCollection = landsatCollection.merge(sentinelCollection);
  
  //print(mergedCollection)
  
  // Calculate mean and standard deviation
  var meanImage = mergedCollection.mean();
  var stdDevImage = mergedCollection.reduce(ee.Reducer.stdDev());
  
  //print(meanImage,"mean image")
  //print(stdDevImage,"sd image")
  
  // Return an object containing the mean and standard deviation images
  return {
    mean: meanImage,
    stdDev: stdDevImage
  };
}

// Ensure the 'seasonalNBRImageCollections' and 'sentinelSeasonalNBRCollections' are correctly populated from previous code

// Initialize an object to store the combined statistics for each season
var combinedSeasonalStats = {
  'Summer': ee.ImageCollection([]),
  'Autumn': ee.ImageCollection([]),
  'Winter': ee.ImageCollection([]),
  'Spring': ee.ImageCollection([])
};

// Compute the combined stats for each season
Object.keys(combinedSeasonalStats).forEach(function(season) {
  combinedSeasonalStats[season] = mergeAndCalculateStats(
    predictedSeasonalNBRImageCollections[season],
    sentinelSeasonalNBRCollections[season]
  );
});



//Print out the mean and standard deviation for each season
// Object.keys(combinedSeasonalStats).forEach(function(season) {
//   var stats = combinedSeasonalStats[season];
//   print(season + ' Mean NBR Image:', stats.mean);
//   print(season + ' Standard Deviation NBR Image:', stats.stdDev);
// });


// // Function to visualize mean and standard deviation images
// function visualizeStats(stats, season, aoi) {
//   var meanVisParams = {
//     min: -1000,
//     max: 1000,
//     palette: ['blue', 'white', 'green']
//   };

//   var stdDevVisParams = {
//     min: 0,
//     max: 500,
//     palette: ['white', 'black']
//   };

//   // Add the mean image to the map with a specific visualization parameters
//   Map.addLayer(stats.mean.clip(aoi), meanVisParams, season + ' Mean NBR');

//   // Add the standard deviation image to the map with different visualization parameters
//   Map.addLayer(stats.stdDev.clip(aoi), stdDevVisParams, season + ' Standard Deviation NBR');
// }

// // Visualize the combined stats for each season
// Object.keys(combinedSeasonalStats).forEach(function(season) {
//   var stats = combinedSeasonalStats[season];
//   visualizeStats(stats, season, aoi);
// });



// //////////////////////////////////////////////////////////////////// Z Score Function ////////////////////////////////////////////////////


// Function to calculate Z-score for the predicted seasonal NBR image collections
function calculateZScores(sentinelSeasonalNBRCollections, combinedSeasonalStats) {
    var zScoreSeasonalNBRImageCollections = {};
    //print(predictedSeasonalNBRImageCollections)
    //print(combinedSeasonalStats)
    // Iterate over each season
    Object.keys(sentinelSeasonalNBRCollections).forEach(function(season) {
        var sentinelCollection = sentinelSeasonalNBRCollections[season];
        //print(predictedCollection)
        var stats = combinedSeasonalStats[season];
        
        var meanImage = stats.mean.select('sentiNBR');
        var stdDevImage = stats.stdDev.select('sentiNBR_stdDev'); 
        
        //print(meanImage)
        //print(stdDevImage)

        // Calculate the Z-score for each image in the collection
        var zScoreCollection = sentinelCollection.map(function(image) {
            // Ensure you are working with the PredictedNBR band
            var sentiNBR = image.select('sentiNBR');
            //print(predictedNBR)
            // Calculate the Z-score
            var zScore = sentiNBR.subtract(meanImage).divide(stdDevImage).rename('ZScore');
            zScore = zScore.clip(aoi);
            zScore = zScore.updateMask(eu_forest);
            //print(zScore)
            // Return the original image with the added ZScore band
            return image.addBands(zScore);
        });

        // Store the Z-score image collection for the current season
        zScoreSeasonalNBRImageCollections[season] = zScoreCollection;
    });

    return zScoreSeasonalNBRImageCollections;
}

// Usage of the function
var zScoreSeasonalNBRImageCollections = calculateZScores(sentinelSeasonalNBRCollections, combinedSeasonalStats);

//print(zScoreSeasonalNBRImageCollections['Summer'])
// Function to compute cumulative non-burned area (fire mask) over a date range
var getCumulativeNonBurnedArea = function(startDate, endDate) {
  var burnedAreaCollection = ee.ImageCollection('MODIS/061/MCD64A1')
    .filterDate(startDate, endDate)
    .select('BurnDate');

  var burnedMaskCollection = burnedAreaCollection.map(function(image) {
    return image.gt(0).rename('Burned').selfMask();
  });

  var cumulativeBurnedArea = burnedMaskCollection.max().rename('Cumulative_Burned');
  var cumulativeNonBurnedArea = cumulativeBurnedArea.not().unmask(1).rename('Cumulative_NonBurned');
  return cumulativeNonBurnedArea;
};

// Define seasons with respective cumulative date ranges
var seasons = [
  {name: 'Summer_2016-2017', startDate: '2016-12-01', endDate: '2017-02-28'},
  {name: 'Autumn_2017',      startDate: '2016-12-01', endDate: '2017-05-31'},
  {name: 'Winter_2017',      startDate: '2016-12-01', endDate: '2017-08-31'},
  {name: 'Spring_2017',      startDate: '2016-12-01', endDate: '2017-11-30'},
  {name: 'Summer_2017-2018', startDate: '2016-12-01', endDate: '2018-02-28'},
  {name: 'Autumn_2018',      startDate: '2016-12-01', endDate: '2018-05-31'},
  {name: 'Winter_2018',      startDate: '2016-12-01', endDate: '2018-08-31'},
  {name: 'Spring_2018',      startDate: '2016-12-01', endDate: '2018-11-30'},
  {name: 'Summer_2018-2019', startDate: '2016-12-01', endDate: '2019-02-28'},
  {name: 'Autumn_2019',      startDate: '2016-12-01', endDate: '2019-05-31'},
  {name: 'Winter_2019',      startDate: '2016-12-01', endDate: '2019-08-31'},
  {name: 'Spring_2019',      startDate: '2016-12-01', endDate: '2019-11-30'},
  {name: 'Summer_2019-2020', startDate: '2016-12-01', endDate: '2020-02-29'},
  {name: 'Autumn_2020',      startDate: '2016-12-01', endDate: '2020-05-31'},
  {name: 'Winter_2020',      startDate: '2016-12-01', endDate: '2020-08-31'},
  {name: 'Spring_2020',      startDate: '2016-12-01', endDate: '2020-11-30'},
  {name: 'Summer_2020-2021', startDate: '2016-12-01', endDate: '2021-02-28'},
  {name: 'Autumn_2021',      startDate: '2016-12-01', endDate: '2021-05-31'},
  {name: 'Winter_2021',      startDate: '2016-12-01', endDate: '2021-08-31'},
  {name: 'Spring_2021',      startDate: '2016-12-01', endDate: '2021-11-30'},
  {name: 'Summer_2021-2022', startDate: '2016-12-01', endDate: '2022-02-28'},
  {name: 'Autumn_2022',      startDate: '2016-12-01', endDate: '2022-05-31'},
  {name: 'Winter_2022',      startDate: '2016-12-01', endDate: '2022-08-31'},
  {name: 'Spring_2022',      startDate: '2016-12-01', endDate: '2022-11-30'}
];

// Initialize a dictionary to store fire mask image collections for each season
var fireMaskImageCollections = {
  'Autumn': ee.ImageCollection([]),
  'Winter': ee.ImageCollection([]),
  'Spring': ee.ImageCollection([]),
  'Summer': ee.ImageCollection([])
};

// Compute and organize fire masks into seasonal collections
seasons.forEach(function(season) {
  var fireMask = getCumulativeNonBurnedArea(season.startDate, season.endDate);

  if (season.name.indexOf('Summer') !== -1) {
    fireMaskImageCollections['Summer'] = fireMaskImageCollections['Summer'].merge(ee.ImageCollection([fireMask]));
  } else if (season.name.indexOf('Autumn') !== -1) {
    fireMaskImageCollections['Autumn'] = fireMaskImageCollections['Autumn'].merge(ee.ImageCollection([fireMask]));
  } else if (season.name.indexOf('Winter') !== -1) {
    fireMaskImageCollections['Winter'] = fireMaskImageCollections['Winter'].merge(ee.ImageCollection([fireMask]));
  } else if (season.name.indexOf('Spring') !== -1) {
    fireMaskImageCollections['Spring'] = fireMaskImageCollections['Spring'].merge(ee.ImageCollection([fireMask]));
  }
});

// Function to export Z-Score images after masking with fire masks
function exportZScoreImages(year, zScoreSeasonalNBRImageCollections, fireMaskImageCollections) {
  var yearIndex = year - 2016; // Adjust based on the start year of your collection

  var seasons = ['Summer', 'Autumn', 'Winter', 'Spring'];
  seasons.forEach(function(season) {
    var seasonCollection = zScoreSeasonalNBRImageCollections[season];
    var fireMaskCollection = fireMaskImageCollections[season];

    if (seasonCollection && fireMaskCollection) {
      var image = ee.Image(seasonCollection.toList(1, yearIndex).get(0)).select('ZScore');
      var fireMask = ee.Image(fireMaskCollection.median());

      // Apply the fire mask to the Z-Score image
      var maskedImage = image.updateMask(fireMask);

      // Export the masked Z-Score image
      Export.image.toDrive({
        image: maskedImage,
        description: year + '_South_Eastern_Highland_' + season + '_Masked',
        folder: 'NSW_North_Coast_' + year,
        scale: 30,
        region: aoi,
        crs: 'EPSG:3577',
        fileFormat: 'GeoTIFF',
        maxPixels: 1e10
      });

      // Optionally visualize
      Map.addLayer(maskedImage, {min: -3, max: 3, palette: ['blue', 'white', 'red']}, season + ' Masked ' + year);
    } else {
      print('No data found for season:', season, 'in year:', year);
    }
  });
}

// Example usage
exportZScoreImages(2019, zScoreSeasonalNBRImageCollections, fireMaskImageCollections);
