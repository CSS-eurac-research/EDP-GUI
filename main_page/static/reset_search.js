function reset_search() {
    
    var searchbar = document.getElementById("searchbar");
    searchbar.value = "";

    var period_begin_input = document.getElementById("period_begin");
    period_begin_input.value = "";
    var period_end_input = document.getElementById("period_end");
    period_end_input.value = "";

    var checkboxes = document.getElementsByClassName("checkbox_categories_input")
    
    for (i=0; i<checkboxes.length; i++) {
        checkboxes[i].checked = false;
    }

    location.reload();

    /*
    //console.log("searchbar reset");

    var metadata_results = document.getElementById("metadata_results");
    //metadata_results.innerHTML = "";
    $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results<b>');
    $('#metadata_results').empty();
    //console.log("metadata result div reset");

    map.eachLayer(function (layer) {
        map.removeLayer(layer);
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/voyager/{z}/{x}/{y}.png', {
        attribution: attribution,
        subdomains: 'abcd',
        maxZoom: 19,
        crossOrigin: true
    }).addTo(map);

    map.setView([48, 10], 5);

    //console.log("Search keyword and bounding box reset!");*/
  }