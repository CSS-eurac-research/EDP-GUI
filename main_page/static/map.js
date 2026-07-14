$("#maploader").remove();
const attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
const map = L.map('map').setView([48, 10], 5);
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png', {
    attribution: attribution,
    subdomains: 'abcd',
    maxZoom: 19
}).addTo(map);

var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);
var drawControl = new L.Control.Draw({
    draw: {
        polygon: false,
        marker: false,
        circle: false,
        polyline: false
    },
    edit: {
        featureGroup: drawnItems,
        edit: false
    }
});
map.addControl(drawControl);
map.addLayer(drawnItems);

map.on('draw:created', function (e) {

    $('#metadata_results').empty();
    $('#metadata_results').prepend("<div class='loader'></div>");


    map.eachLayer(function (layer) {
        if (layer instanceof L.Rectangle) {
            // console.log(layer);
            if (layer.layerID != "boundingbox") {
                map.removeLayer(layer);
            }
        }
        if (layer instanceof L.Marker) {
            //console.log(layer);
            map.removeLayer(layer);
        }
    });

    drawnItems.clearLayers();
    var type = e.layerType, layer = e.layer;
    var coords = layer.getLatLngs();
    //console.log(coords);
    map.fitBounds(coords);
    //console.log(coords[0][1]);
    var overlayMaps = {
        layerName: "boundingbox",
    };
    layer.layerID = "boundingbox";
    //console.log(layer.layerID);
    map.addLayer(layer);
    drawnItems.addLayer(layer);
    //console.log(map);
    //console.log(coords);    
    var polygon = layer.toGeoJSON();
    //console.log(polygon['geometry']['coordinates'][0]);
    //$('#boundingbox').val(coords[0][0] + ", " + coords[0][1] + ", " + coords[0][2] + ", " + coords[0][3]);

    var boundingbox = polygon.geometry.coordinates[0];
    var searchbar = document.getElementById("searchbar");
    var url = window.location.pathname + "?";
    var url_params = [];

    var categories_selected = [];
    $.each($("input[name='category']:checked"), function () {
        categories_selected.push($(this).val());
    });

    if (categories_selected.length === 0) {
        categories_selected.push("all");
    }

    url_params.push("categories=" + encodeURIComponent(categories_selected.join(",")));

    var period_begin = document.getElementById("period_begin").value;
    var period_end = document.getElementById("period_end").value;

    if (boundingbox !== "") {
        url_params.push("box=" + encodeURIComponent(boundingbox));
    }
    if (searchbar && searchbar.value.trim() !== "") {
        url_params.push("search=" + encodeURIComponent(searchbar.value.trim()));
    }
    if (period_begin !== "" && period_end !== "") {
        url_params.push("period_begin=" + encodeURIComponent(period_begin));
        url_params.push("period_end=" + encodeURIComponent(period_end));
    }

    url = url + url_params.join("&");

    $.ajax({
        url: url,
        type: "GET",
        contentType: "application/json",
        success: function (response) {
            var metadata_results = response.metadata_results;
            var title_list = response.title_list;

            if (typeof title_list === "string" && title_list.length > 0) {
                $("#searchbar").autocomplete({
                    source: title_list.split(","),
                    minLength: 2,
                    max: 10,
                    scroll: true
                });
            }

            if (metadata_results && metadata_results !== "no results" && metadata_results.length > 0) {
                $("#number_results").html(
                    "Results: <b>" + metadata_results.length.toString() + "</b> items found"
                );
                renderDiscoveryResults(metadata_results);

                for (var i = 0; i < metadata_results.length; i++) {
                    if (metadata_results[i][6] == null) {
                        continue;
                    }

                    var geom = JSON.parse(metadata_results[i][6]);
                    var ring = geom.coordinates[0];
                    var correct_bounds = [];

                    for (var k = 0; k < ring.length; k++) {
                        correct_bounds[k] = [ring[k][1], ring[k][0]];
                    }

                    var bounds = L.latLngBounds(correct_bounds);
                    var rectangle = L.rectangle(bounds, {
                        color: "#DF1B12",
                        weight: 2,
                        fill: false
                    });

                    if (metadata_results[i][3] != null) {
                        if (metadata_results[i][3] === "SOS") {
                            rectangle.addTo(map);
                            var center_coords = rectangle.getCenter();
                            L.marker(center_coords)
                                .bindTooltip(metadata_results[i][1])
                                .openTooltip()
                                .addTo(map);
                        } else {
                            rectangle
                                .bindTooltip(metadata_results[i][1])
                                .openTooltip()
                                .addTo(map);
                        }
                    }
                }
            } else {
                $("#metadata_results").empty();
                $("#number_results").html(
                    "Results: <b>no items were found with this bounding box</b>"
                );
            }
        },
        error: function () {
            $("#metadata_results").empty();
            $("#number_results").html(
                "Results: <b>search failed, please try again</b>"
            );
        }
    });
});