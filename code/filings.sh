python3 filings-geojson.py > ../maps.data/filings.epsg2236.geojson
if [ -f ../maps.data/filings.epsg4326.geojson ]; then
	rm ../maps.data/filings.epsg4326.geojson
fi
ogr2ogr -f GeoJSON -s_srs EPSG:2236 -t_srs EPSG:4326 ../maps.data/filings.epsg4326.geojson ../maps.data/filings.epsg2236.geojson
python3 strip-crs.py ../maps.data/filings.epsg4326.geojson
date
