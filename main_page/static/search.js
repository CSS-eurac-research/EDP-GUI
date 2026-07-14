function dosearch() {
    $('#metadata_results').empty();
    $('#metadata_results').prepend("<div class='loader'></div>");

    var searchbar = document.getElementById("searchbar");
    var url = window.location.pathname + '?';
    var boundingbox = "";
    var url_params = [];
    var categories_selected = [];

    map.eachLayer(function (layer) {
        if (layer.hasOwnProperty("layerID")) {
            if (layer.layerID == "boundingbox") {
                var polygon = layer.toGeoJSON();
                boundingbox = polygon['geometry']['coordinates'][0];
            }
        }
    });

    $.each($("input[name='category']:checked"), function () {
        categories_selected.push($(this).val());
    });

    var period_begin = document.getElementById('period_begin').value;
    var period_end = document.getElementById('period_end').value;
    var hasSearch = searchbar.value.trim() !== "";
    var hasDates = period_begin !== "" && period_end !== "";
    var hasCategories = categories_selected.length > 0;
    var hasBox = boundingbox !== "";

    if (!hasSearch && !hasDates && !hasCategories && !hasBox) {
        if (typeof reset_search === "function") {
            reset_search();
        } else {
            location.reload();
        }
        return false;
    }

    map.eachLayer(function (layer) {
        if (layer instanceof L.Rectangle) {
            if (layer.layerID != "boundingbox") {
                map.removeLayer(layer);
            }
        }
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    if (categories_selected.length == 0) {
        categories_selected.push("all");
    }

    url_params.push('categories=' + encodeURIComponent(categories_selected.join(",")));

    if (boundingbox != "") {
        url_params.push('box=' + encodeURIComponent(boundingbox));
    }
    if (searchbar.value != "") {
        url_params.push('search=' + encodeURIComponent(searchbar.value));
    }
    if (period_begin != "" && period_end != "") {
        url_params.push('period_begin=' + encodeURIComponent(period_begin));
        url_params.push('period_end=' + encodeURIComponent(period_end));
    }
    url_params.push('json=yes');

    url = url + url_params.join("&");

    $.ajax({
        url: url,
        type: 'GET',
        contentType: "application/json",
        success: function (response) {
            var metadata_results = response['metadata_results'];
            var title_list = response['title_list'];
            if (typeof title_list === "string" && title_list.length > 0) {
                $("#searchbar").autocomplete({
                    source: title_list.split(","),
                    minLength: 2,
                    max: 10,
                    scroll: true
                });
            }

            if (metadata_results && metadata_results !== "no results") {
                $('#number_results').html('Results: <b>' + metadata_results.length.toString() + '</b> items found');
                renderDiscoveryResults(metadata_results);

                for (var i = 0; i < metadata_results.length; i++) {
                    if (metadata_results[i][6] != null) {
                        var box = JSON.parse(metadata_results[i][6])['coordinates'][0];
                        var correct_bounds = [];
                        for (var k = 0; k < box.length; k++) {
                            correct_bounds[k] = [box[k][1], box[k][0]];
                        }
                        var bounds = L.latLngBounds(correct_bounds);
                        var rectangle = L.rectangle(bounds, { color: "#DF1B12", weight: 2, fill: false });
                        if (metadata_results[i][3] != null) {
                            if (metadata_results[i][3] == "SOS") {
                                rectangle.addTo(map);
                                var center_coords = rectangle.getCenter();
                                L.marker(center_coords).bindTooltip(metadata_results[i][1]).openTooltip().addTo(map);
                            } else {
                                rectangle.bindTooltip(metadata_results[i][1]).openTooltip().addTo(map);
                            }
                        }
                    }
                }
            } else {
                $('#metadata_results').empty();
                $('#number_results').html('Results: <b>no items were found</b>');
            }
        },
        error: function () {
            $('#metadata_results').empty();
            $('#number_results').html('Results: <b>search failed, please try again</b>');
        }
    });
    return false;
}