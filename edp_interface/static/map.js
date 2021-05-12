$("#maploader").remove();
const attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const map = L.map('map').setView([48, 10], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: attribution }).addTo(map);

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
$("#searchbutton").prop("disabled",false);
$("#searchbar").prop("disabled",false);

map.on('draw:created', function (e) {

    $('#metadata_results').empty();
    $('#metadata_results').prepend("<div class='loader'></div>");

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

    var boundingbox = polygon['geometry']['coordinates'][0];
    var search_request = {'boundingbox': boundingbox };

    var csrftoken = Cookies.get('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    } 

    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    map.eachLayer(function(layer) {
        if(layer instanceof L.Rectangle) {
            // console.log(layer);
            map.removeLayer(layer);
        }
        if(layer instanceof L.Marker) {
            //console.log(layer);
            map.removeLayer(layer);
        }
    });

    //console.log(csrftoken);

    var href = window.location.href;
    var url = href;//+'?search='+searchbar.value;

    if(boundingbox != ""){
        //console.log("keybox ok");
        url = url + '?search='+searchbar.value + '&' + 'box=' + boundingbox;
        //search_request.keyword = searchbar.value;
    } else {
        //console.log("keybox no");
        url = url + '?search='+searchbar.value;
    }

    //console.log(search_request);
    //console.log(url);

    //console.log(data);

    $.ajax({
        url: url,
        type: 'GET',        
        contentType: "application/json",
        success: function(response){
            //console.log(response['metadata_results']);
            var metadata_results = response['metadata_results'];//JSON.parse(response['metadata_results']);
            var title_list = response['title_list'];
            $("#searchbar").autocomplete({
                source: title_list.split(","),
                minLength: 2,
                max: 10,
                scroll: true              
            });

            //console.log(metadata_results);
            if(metadata_results != "no results") {
                $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results: <b>' + metadata_results.length.toString() + '</b> items found');
                $('#metadata_results').empty();
                //console.log(metadata_results.length);
                var col = 0;
                var row = 0;
                var key = 0;
                for (i=metadata_results.length-1; i>-1; i--) {
                    if (col == 0){
                        $('#metadata_results').prepend(`<div id="row-${row}" class="row">`);
                    }
                    var result_box = "";
                    result_box = result_box + '<div class="col"> <div class="card" style="width: 55rem;">';
                    
                    //image
                    if(metadata_results[i][5] != null) {
                        result_box = result_box + '<img src="'+metadata_results[i][5]+'" class="card-img-top">';
                    } 
                    // result_box = result_box + '</div>';
                    // result_box = result_box + '<div class="col">';
                    result_box = result_box + '<div class="card-body">';
                    //uuid and title
                    if(metadata_results[i][0] != null) {
                        result_box = result_box + '<a class="card-title" style="color: #DE4624; font-size: 20px;" href="/discovery/'+metadata_results[i][0]+'" target="_blank">'+metadata_results[i][1]+'</a>';
                    }

                    //abstract
                    if(metadata_results[i][2] != null) {
                        result_box = result_box + '<div class="card-text abstract-results">'+metadata_results[i][2]+'</div>';
                    } 

                    //category
                    if(metadata_results[i][3] != null) {
                        result_box = result_box + '<p class="card-text" style="font-weight: bold">'+metadata_results[i][3]+'</p>';
                    } 

                    //keyword
                    if(metadata_results[i][4] != null) {
                        key = key + 1;
                        result_box = result_box + '<p class="card-text" style="font-size: 12px; font-style:italic;">'+metadata_results[i][4]+'</p>';
                    } 
                    result_box = result_box + '</div> </div> </div>';

                    $('#row-'+row.toString()).prepend(result_box);

                    col = col + 1;
                    if (col == 3) {
                        $('#row-'+row.toString()).prepend(`</div>`);
                        col = 0;
                        row = row + 1;
                    } else if (i == metadata_results.length-1) {
                        $('#row-'+row.toString()).prepend(`</div>`);
                    } 
                
                }

                //geometry
                for (i=0; i<metadata_results.length; i++) {
                    if(metadata_results[i][6] != null) {
                        
                        var box = JSON.parse(metadata_results[i][6])['coordinates'][0];
                        correct_bounds = [];

                        for (k=0; k<box.length; k++) {
                            correct_bounds[k] = [box[k][1], box[k][0]];
                        }
                        box
                        finalBox = JSON.parse(metadata_results[i][6])['coordinates'];

                        var bounds = L.latLngBounds(correct_bounds);
                        //var bounds = [[box[1],box[0]],[box[3],box[2]]];
                        var rectangle = L.rectangle(bounds, {color: "#DE4624", weight: 2, fill: false});
                        if (metadata_results[i][3] != null){
                            if(metadata_results[i][3] == "SOS") {
                                rectangle.addTo(map);
                                var center_coords = rectangle.getCenter();
                                L.marker(center_coords).bindTooltip(metadata_results[i][1]).openTooltip().addTo(map);
                            } else {                        
                                rectangle.bindTooltip(metadata_results[i][1]).openTooltip().addTo(map);
                        }   
                    }                
                        
                    } else {
                        console.log("defined");
                    }
                }
            } else {
                $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results: <b>no item was found with this bounding box</b>');
            }
            },
        });
});