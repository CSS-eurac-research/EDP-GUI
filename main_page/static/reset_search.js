function reset_search() {
    var searchbar = document.getElementById("searchbar");
    searchbar.value = "";
    //console.log("searchbar reset");

    var metadata_results = document.getElementById("metadata_results");
    //metadata_results.innerHTML = "";
    $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results<b>');
    $('#metadata_results').empty();
    //console.log("metadata result div reset");

    map.eachLayer(function (layer) {
        map.removeLayer(layer);
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: attribution }).addTo(map);

    map.setView([48, 10], 5);

    //console.log("Search keyword and bounding box reset!");
  }