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

map.on('draw:created', function (e) {
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

    var href = window.location.href;
    var url = href;//+'?search='+searchbar.value;

    if(searchbar.value!=''){
        //console.log("keybox ok");
        url = url + '?search='+searchbar.value + '&keybox=true';
        search_request.keyword = searchbar.value;
    } else {
        //console.log("keybox no");
        url = url + '?box=true';
    }

    //console.log(search_request);
    //console.log(url);

    //console.log(data);

    $.ajax({
        url: url,
        type: 'POST',        
        data: JSON.stringify(search_request),
        contentType: "application/json",
        success: function(response){
            //console.log(response);
            //$('#bb_response').text(response['metadata_results']);
            //console.log(response['metadata_results']);
            var metadata_results = response['metadata_results'];//JSON.parse(response['metadata_results']);

            $(function () { 
                var searchbar = document.getElementById("searchbar"); 
                $("#searchbar").autocomplete({
                    source: metadata_results,
                    minLength: 2,
                    max: 10,
                    scroll: true              
                });
            });

            console.log(metadata_results);
            if(metadata_results != "no results") {
                $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results: <b>' + metadata_results.length.toString() + '</b> items found');
                $('#metadata_results').empty();
                console.log(metadata_results.length);
                //console.log("predicted number of rows: " + Math.ceil(metadata_results.length/3).toString());
                var col = 0;
                var row = 0;
                var key = 0;
                for (i=metadata_results.length-1; i>-1; i--) {

                    //console.log(metadata_results[i]["geonet:info"]["uuid"]);

                    if (col == 0){
                        //onsole.log("col equal 0");
                        $('#metadata_results').prepend(`<div id="row-${row}" class="row">`);
                        $('#metadata_results').prepend(`<div id="deck-${row}" class="card-deck">`);
                    } 
                    //$('#metadata_results').prepend(`<div id="row-${row}" class="row">`);
                    var result_box = "";

                    //result_box = result_box + '<div class="col"> <div class="card" style="width: 55rem;">';
                    result_box = result_box + '<div class="col"> <div class="card" style="width: 55rem;">';
                    //result_box = result_box + '<div class="col">';
                    //console.log(metadata_results[i]["title"]);
                    //console.log(metadata_results[i].hasOwnProperty("image"));
                    
                    if(metadata_results[i].hasOwnProperty("image")) {
                        result_box = result_box + '<img src="'+metadata_results[i]["image"].split("|")[1]+'" class="card-img-top">';
                    } 
                    result_box = result_box + '</div>';
                    result_box = result_box + '<div class="col">';
                    result_box = result_box + '<div class="card-body">';
                    if(metadata_results[i]["geonet:info"].hasOwnProperty("uuid")) {
                        result_box = result_box + '<a class="card-title" style="color: #DF1B12; font-size: 20px;" href="/discovery/'+metadata_results[i]["geonet:info"]["uuid"]+'" target="_blank" rel="noopener noreferrer">'+metadata_results[i]["title"]+'</a>';
                    }

                    if(metadata_results[i].hasOwnProperty("abstract")) {
                        result_box = result_box + '<div class="card-text abstract-results">'+metadata_results[i]["abstract"]+'</div>';
                    } 

                    if(metadata_results[i].hasOwnProperty("category")) {
                        result_box = result_box + '<p class="card-text" style="font-weight: bold">'+metadata_results[i]["category"]+'</p>';
                    } 

                    if(metadata_results[i].hasOwnProperty("keyword")) {
                        key = key + 1;
                        //console.log(metadata_results[i]["keyword"].join(","));
                        result_box = result_box + '<p class="card-text" style="font-size: 12px; font-style:italic;">'+metadata_results[i]["keyword"].join(",")+'</p>';
                    } 
                    //result_box = result_box + '</div>';
                    result_box = result_box + '</div> </div> </div>';
    
                    $('#row-'+row.toString()).prepend(result_box);
                   // $('#row-'+row.toString()).prepend(`</div>`);
 
                    col = col + 1;
                    //console.log("col " + col.toString());
                    if (col == 3) {
                        $('#row-'+row.toString()).prepend(`</div></div>`);
                        //$('#metadata_results').prepend(`<div  id="row-${i+1}" class="row">`);
                        col = 0;
                        row = row + 1;
                    } else if (i == metadata_results.length-1) {
                        //console.log(i == metadata_results.length);
                        $('#row-'+row.toString()).prepend(`</div></div>`);
                    } 
                
                }


                //console.log("final number of rows: " + row.toString());

                for (i=0; i<metadata_results.length; i++) {
                    //console.log(typeof(metadata_results[i]["geoBox"]));
                    if(metadata_results[i].hasOwnProperty("geoBox")) {
        
                        var box = metadata_results[i]["geoBox"].split("|");
                        var bounds = [[box[1],box[0]],[box[3],box[2]]];
                        //console.log(bounds);
                        // create an orange rectangle
                        //var randomColor = Math.floor(Math.random()*16777215).toString(16);
                        var rectangle = L.rectangle(bounds, {color: "#DF1B12", weight: 2, fill: false});
                        //rectangle.addTo(map);
                        if (metadata_results[i].hasOwnProperty("category")){
                            if(metadata_results[i]["category"] == "SOS") {
                                rectangle.addTo(map);
                                var center_coords = rectangle.getCenter();
                                L.marker(center_coords).bindTooltip(metadata_results[i]["title"]).openTooltip().addTo(map);
                            } else {                        
                            rectangle.bindTooltip(metadata_results[i]["title"]).openTooltip().addTo(map);
                        }   
                    }                
                        
                    } else {
                        console.log("defined");
                    }
                }
                //console.log("set keywords found " + key.toString());
            } else {
                $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results: <b>no item was found with this bounding box</b>');
            }

        },
        });

    //$('#boundingbox').val(polygon['geometry']['coordinates'][0]);

    //$('#boundingbox_form').submit();

});