//////// Please note that :
// Before you run this code please add shapefile for the field data (point shapefile).
// Import the eu_forest the raster tiff file for the eucalyptus forest tiff and shape file of the bioregion interrested.


// Get the feature count of the buffered points
var tablecount = table.size();

// Print the feature count to the console
print('Feature count of buffered field data:', tablecount);


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////fire mask function ///////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

var nbrvispar = {
    min: -1000, 
    max: 1000, 
    palette: [
        'black',  // Severely burned
        'red',    // Burned areas
        'orange', // Burned areas with less severity
        'yellow', // Transition areas or lightly burned
        'lightgreen', // Healthy vegetation with some stress
        'green'   // Healt hy vegetation
    ]
};



Map.centerObject(table,6)
var filterFireImg = function(year,month){
  
  if(month>0 && month<10){
    var collection1 = ee.Image('MODIS/061/MCD64A1/'+year+'_0'+month+'_01');
    var burnedArea = collection1.select('BurnDate');
   var burnedArea1 = burnedArea.reduce(ee.Reducer.max()).not();//convert burnt areas to 0, mask is still applied (i.e. unburnt areas are masked out)
    var burnedArea1 = burnedArea1.unmask(1).rename('Unburnt');
   
   
  }else{
    var collection1 = ee.Image('MODIS/061/MCD64A1/'+year+'_'+month+'_01');
    var burnedArea = collection1.select('BurnDate');
    var burnedArea1 = burnedArea.reduce(ee.Reducer.max()).not();//convert burnt areas to 0, mask is still applied (i.e. unburnt areas are masked out)
    var burnedArea1 = burnedArea1.unmask(1).rename('Unburnt');
    
  }
 


return burnedArea1;
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////Sentinel-2 NBR Function ////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

var s2SrC = ee.ImageCollection('COPERNICUS/S2');
var s2CloudsC = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY');

// Define maximum cloud probability threshold
var MAX_CLOUD_PROBABILITY = 50;

// Function to mask clouds using the cloud probability dataset
function maskClouds(img) {
  var clouds = ee.Image(img.get('cloud_mask')).select('probability');
  var isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY);
  return img.updateMask(isNotCloud);
}

// Function to add NBR band to an image
function addNBRWithYearMonth(image) {
  // Select the NIR (B8) and Red (B4) bands from the image
  var nir = image.select('B8');
  var red = image.select('B12');

  // Calculate NBR using arithmetic operations
  var nbr = nir.subtract(red).divide(nir.add(red)).multiply(1000).rename('NBR');

  return nbr;
}

// Function to generate NBR images for each month of each year in the specified range
function generateMonthlyNBRImages(startYear, endYear) {
  var monthlyNBRCollections = {};

  for (var year = startYear; year <= endYear; year++) {
    for (var month = 1; month <= 12; month++) {
      var startDate = ee.Date.fromYMD(year, month, 1);
      var endDate = startDate.advance(1, 'month');

      var s2Sr = s2SrC.filterDate(startDate, endDate).filterBounds(aoi);
      var s2Clouds = s2CloudsC.filterDate(startDate, endDate).filterBounds(aoi);

      // Join S2 SR with cloud probability dataset to add cloud mask.
      var s2SrWithCloudMask = ee.Join.saveFirst('cloud_mask').apply({
        primary: s2Sr,
        secondary: s2Clouds,
        condition: ee.Filter.equals({ leftField: 'system:index', rightField: 'system:index' })
      });

      var s2CloudMasked = ee.ImageCollection(s2SrWithCloudMask)
        .map(maskClouds)
        .map(addNBRWithYearMonth)
        .median()
        //.clip(aoi);
        
        var fireImg = filterFireImg(year,month);
       
        var unburntBand = fireImg.select('Unburnt');
        //print(unburntBand)
         
        s2CloudMasked = s2CloudMasked.updateMask(unburntBand)
        s2CloudMasked = s2CloudMasked.updateMask(eu_forest)
        
        

      // Assign the monthly NBR image to the corresponding month in the monthlyNBRCollections object
      if (!monthlyNBRCollections[month]) {
        monthlyNBRCollections[month] = ee.ImageCollection([]);
      }
      monthlyNBRCollections[month] = monthlyNBRCollections[month].merge(ee.ImageCollection([s2CloudMasked]));
    }
  }

  return monthlyNBRCollections;
}

// Generate the monthly NBR image collections
var sentinelMonthlyNBRCollections = generateMonthlyNBRImages(2017, 2022);

print('sentinel images',sentinelMonthlyNBRCollections)

// Function to get the maximum NBR value for each month
function getMaxNBRPerMonth(monthlyNBRCollections) {
  var maxNBRPerMonth = ee.List([]);

  for (var month = 1; month <= 12; month++) {
    var monthlyCollection = monthlyNBRCollections[month];
    var month_list = monthlyCollection.toList(monthlyCollection.size());
    
    var size = monthlyCollection.size().getInfo();
    
    for (var i = 0; i < size; i++) {
      var image = ee.Image(month_list.get(i));
      var maxNBR = image.reduceRegion(ee.Reducer.max(),table)
       
      var year =2017+i;
    
      
      var maxNBRRecord = ee.Feature(null, {
        'year':year,
        'month':month,
        'maxNBR': maxNBR
      });
      
      maxNBRPerMonth = maxNBRPerMonth.add(maxNBRRecord);
    }
  }
  
  return ee.FeatureCollection(maxNBRPerMonth);
}

// Generate the monthly NBR image collections
var sentinelMonthlyNBRCollections = generateMonthlyNBRImages(2017, 2022);

// Get the maximum NBR values for each month
var maxNBRPerMonthCollection = getMaxNBRPerMonth(sentinelMonthlyNBRCollections);

print('Max NBR values per month:', maxNBRPerMonthCollection);

Export.table.toDrive({
  collection: maxNBRPerMonthCollection,
  description:'Final_csv_of_NBR_MAX',
  fileFormat: 'csv'
});


// // /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// // //////////////////////////////////////////////////////////////////////////Adding Legends //////////////////////////////////////////////////////////////////////////////////////////////////////////
// // ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

var NBR_constant = 687.0149972;

var jan_month = sentinelMonthlyNBRCollections[1];
var feb_month = sentinelMonthlyNBRCollections[2];
var mar_month = sentinelMonthlyNBRCollections[3];  // March month collection
var apr_month = sentinelMonthlyNBRCollections[4];  // April month collection
var dec_month = sentinelMonthlyNBRCollections[12]; // December month collection from previous year

var jan_month_list = jan_month.toList(jan_month.size());
var feb_month_list = feb_month.toList(feb_month.size());
var mar_month_list = mar_month.toList(mar_month.size());
var apr_month_list = apr_month.toList(apr_month.size());
var dec_month_list = dec_month.toList(dec_month.size());

var tgfvispar = {
    min: -0.5, 
    max: 1.5, 
    palette: ['#FF0000', '#FFA500', '#FFFF00', '#00FF00', '#0000FF', '#800080']
};

// Create a 50m radius buffer around each point in the 'table' feature collection
var buffer_radius = 20; // 50 meters
var fieldDataBuffered = table.map(function(feature) {
  return feature.buffer(buffer_radius);
});

// Get the feature count of the buffered points
var featureCount = fieldDataBuffered.size();

// Print the feature count to the console
print('Feature count of buffered field data:', featureCount);
Map.addLayer(fieldDataBuffered, {color: 'red'}, 'Buffered Field Data');

// Create an empty FeatureCollection to store the median values
var medianValuesCollection = ee.FeatureCollection([]);

// Loop over each year and create TGF for each season (December, January, February, March, April)
for (var i = 0; i < 5; i++) {
  var year = 2018 + i;

  // Handle edge case for the first year (i=0), where we need December 2017
  var dec;
  if (i === 0) {
    dec = ee.Image(dec_month_list.get(0));  // For the first year, December 2017 is at index 0
  } else {
    dec = ee.Image(dec_month_list.get(i - 1)); // For other years, get December of the previous year
  }

  var jan = ee.Image(jan_month_list.get(i));   // January of current year
  var feb = ee.Image(feb_month_list.get(i));   // February of current year
  var mar = ee.Image(mar_month_list.get(i));   // March of current year
  var apr = ee.Image(apr_month_list.get(i));   // April of current year

  // Combine the months (December, January, February, March, April)
  var season_min = ee.ImageCollection([dec, jan, feb, mar, apr]).min();
  
  // Calculate TGF
  var TGF = season_min.divide(NBR_constant).rename('TGF_' + year);

  // Extract the median values for each buffered region (50m radius)
  var medianValuesPerField = TGF.reduceRegions({
    collection: table,
    reducer: ee.Reducer.mean(),
    scale: 10 // Adjust the scale to match the spatial resolution of the imagery
  });

  // Add year, Site, Time, and Brown properties to each feature
  medianValuesPerField = medianValuesPerField.map(function(feature) {
    return feature.set({
      'year': year,
      'Site': feature.get('site_name'),  // Get 'Site' property from the original feature
      'Time': feature.get('Time'),  // Get 'Time' property from the original feature
      'Brown': feature.get('Brown') // Get 'Brown' property from the original feature
    });
  });

  // Merge the results into the medianValuesCollection
  medianValuesCollection = medianValuesCollection.merge(medianValuesPerField);

  // Optionally, add the TGF layer to the map
  Map.addLayer(TGF, tgfvispar, 'TGF_' + year);
  
  Export.image.toDrive({
  image: TGF,
  description: 'TGF_'+year,
  crs: 'EPSG:3577',
  scale: 30,
  region: eu_forest,
  maxPixels: 1e10});

}

// Print the median values for review
print('Median TGF values for buffered regions:', medianValuesCollection);


// Export the median values as a CSV
Export.table.toDrive({
  collection: medianValuesCollection,
  description: 'Median_TGF_Values_Buffered_new',
  fileFormat: 'CSV',
  selectors: ['year', 'Site', 'Time', 'Brown', 'mean'] // Choose which columns to include in the CSV
});




// Function to create a legend
function createLegend(title, palette, labels, position) {
  var legend = ui.Panel({
    style: {
      position: position,
      padding: '8px 15px'
    }
  });

  var legendTitle = ui.Label({
    value: title,
    style: {fontWeight: 'bold', fontSize: '14px', margin: '0 0 4px 0', padding: '0'}
  });
  legend.add(legendTitle);

  for (var i = 0; i < palette.length; i++) {
    var colorBox = ui.Label({
      style: {
        backgroundColor: palette[i],
        padding: '8px',
        margin: '0 0 4px 0'
      }
    });
    var description = ui.Label({
      value: labels[i],
      style: {margin: '0 0 4px 6px'}
    });
    var row = ui.Panel({
      widgets: [colorBox, description],
      layout: ui.Panel.Layout.Flow('horizontal')
    });
    legend.add(row);
  }
  Map.add(legend);
}

// Adding TGF Legend
createLegend('TGF Index', ['#FF0000', '#FFA500', '#FFFF00', '#00FF00', '#0000FF', '#800080'], ['-0.5 to -0.2', '-0.2 to -0.1', '-0.1 to 0', '0 to 0.3', '0.3 to 0.7', '0.7  to 1.5', ], 'bottom-right');

// Adding NBR Legend
//createLegend('NBR Values', ['black', 'red', 'orange', 'yellow', 'lightgreen', 'green'], ['-1000 to -600', '-600 to -300', '-300 to 0', '0 to 300', '300 to 600', '600 to 1000'], 'bottom-left');



//Map.addLayer(eu_forest)

var pointAsset = ee.FeatureCollection(table);

// Define visualization parameters for the point
var pointVis = {
  color: 'red',
  pointSize: 5,
  pointShape: 'circle',
  width: 1
};

// Add the point to the map
Map.addLayer(pointAsset, pointVis, 'Point Asset');

// Center the map on the point
Map.centerObject(pointAsset, 10);
