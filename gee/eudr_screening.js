// ============================================================
// EUDR PLOT SCREENING — STEP 1: SITE + POST-2020 LOSS + DRAW PLOTS
// Cocoa belt, Western North Region, Ghana (Juaboso / Bia area)
// ============================================================

// --- 1. Centre on a real Ghanaian cocoa district ---
var site = ee.Geometry.Point([-2.90, 6.40]);   // Western North cocoa belt
Map.centerObject(site, 12);

// --- 2. Recent Sentinel-2 true colour (what the land looks like now) ---
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(site)
  .filterDate('2024-01-01', '2024-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .median();
Map.addLayer(s2, {bands: ['B4','B3','B2'], min: 0, max: 3000}, 'Sentinel-2 2024');

// --- 3. Hansen forest loss, highlighting loss AFTER the 2020 cutoff ---
var gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11');
var lossYear = gfc.select('lossyear');          // 1..23 = year 2001..2023
var postCutoffLoss = lossYear.gte(21);          // 21+ = 2021 onward (after cutoff)
Map.addLayer(postCutoffLoss.selfMask(), {palette: ['red']}, 'Loss after 2020');

// Older loss (2001-2020), off by default, for context if you want it
Map.addLayer(lossYear.gte(1).and(lossYear.lte(20)).selfMask(),
  {palette: ['orange']}, 'Loss 2001-2020', false);
  // ============================================================
// EUDR PLOT SCREENING — STEP 2: PER-PLOT RISK ASSESSMENT
// ============================================================

// --- 1. Give each drawn plot an ID (1..n) so results are traceable ---
var plotList = plots.toList(plots.size());
var plotsWithId = ee.FeatureCollection(plotList.map(function(f) {
  var i = plotList.indexOf(f);
  return ee.Feature(f).set('plot_id', ee.Number(i).add(1));
}));

// --- 2. Post-2020 forest loss layer, as area per pixel (m2) ---
var gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11');
var postCutoffLoss = gfc.select('lossyear').gte(21);   // 2021 onward
var lossArea = postCutoffLoss.multiply(ee.Image.pixelArea()).rename('loss_m2');

// --- 3. For each plot: plot area + post-2020 loss area inside it ---
var screened = plotsWithId.map(function(plot) {
  var plotAreaHa = plot.geometry().area(1).divide(10000);
  var lossHa = ee.Number(
    lossArea.reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: plot.geometry(),
      scale: 30,                 // Hansen resolution
      maxPixels: 1e9
    }).get('loss_m2')
  ).divide(10000);

  var lossPct = lossHa.divide(plotAreaHa).multiply(100);

  // --- 4. Risk rule (transparent, threshold-based) ---
  // RED   : clear post-2020 loss inside the plot (>1% of area)
  // AMBER : a trace of loss, near the resolution limit (0-1%)
  // GREEN : no post-2020 loss detected
  var risk = ee.Algorithms.If(lossPct.gt(1), 'RED',
             ee.Algorithms.If(lossPct.gt(0), 'AMBER', 'GREEN'));

  return plot.set({
    plot_area_ha: plotAreaHa,
    loss_after_2020_ha: lossHa,
    loss_pct: lossPct,
    risk_flag: risk
  });
});

// --- 5. Print the results table ---
print('EUDR screening results:', screened);

// --- 6. Colour the plots by risk on the map ---
var red   = screened.filter(ee.Filter.eq('risk_flag', 'RED'));
var amber = screened.filter(ee.Filter.eq('risk_flag', 'AMBER'));
var green = screened.filter(ee.Filter.eq('risk_flag', 'GREEN'));
Map.addLayer(red,   {color: 'red'},    'Risk: RED');
Map.addLayer(amber, {color: 'orange'}, 'Risk: AMBER');
Map.addLayer(green, {color: 'green'},  'Risk: GREEN');
// ============================================================
// EUDR PLOT SCREENING — STEP 3: EXPORT RESULTS FOR THE REPORT
// ============================================================

// Drop the geometry-heavy bits, keep the screening result columns
var resultsTable = screened.select([
  'plot_id', 'plot_area_ha', 'loss_after_2020_ha', 'loss_pct', 'risk_flag'
]);

// Export the per-plot results as a CSV
Export.table.toDrive({
  collection: resultsTable,
  description: 'eudr_screening_results',
  folder: 'eudr_tool',
  fileNamePrefix: 'eudr_screening_results',
  fileFormat: 'CSV'
});

// Also export the plots WITH geometry as GeoJSON (for the map in the report)
Export.table.toDrive({
  collection: screened,
  description: 'eudr_plots_geojson',
  folder: 'eudr_tool',
  fileNamePrefix: 'eudr_plots',
  fileFormat: 'GeoJSON'
});