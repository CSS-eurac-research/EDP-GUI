$(document).ready(function () {

  $("#searchbutton").prop("disabled", true);
  //console.log($("#searchbar").val());
  $("#searchbar").keyup(function () {
    //console.log("INPUT --> " + $("#searchbar").val());
    if ($("#searchbar").val() != "") {
      $("#searchbutton").prop("disabled", false);
    } else {
      $("#searchbutton").prop("disabled", true);
    }
  });

  //Date picker 2013-01-01   
  var period_begin = document.getElementById('period_begin').value
  var period_end = document.getElementById('period_end').value
  $("#period_begin").datepicker({
    onSelect: function () {
      var period_begin = document.getElementById('period_begin').value
      var period_end = document.getElementById('period_end').value
      //console.log(period_begin);
      if (period_begin != "" && period_end != "") {
        $("#searchbutton").prop("disabled", false);
      } else {
        $("#searchbutton").prop("disabled", true);
      }
    }
  });

  $("#period_end").datepicker({
    onSelect: function () {
      var period_begin = document.getElementById('period_begin').value
      var period_end = document.getElementById('period_end').value
      //console.log(period_end);
      if (period_begin != "" && period_end != "") {
        $("#searchbutton").prop("disabled", false);
      } else {
        $("#searchbutton").prop("disabled", true);
      }
    }
  });

  $("#period_begin").keyup(function () {
    var period_begin = document.getElementById('period_begin').value
    var period_end = document.getElementById('period_end').value
    //console.log(period_end);
    if (period_begin != "" && period_end != "") {
      $("#searchbutton").prop("disabled", false);
    } else {
      $("#searchbutton").prop("disabled", true);
    }
  });

  $("#period_end").keyup(function () {
    var period_begin = document.getElementById('period_begin').value
    var period_end = document.getElementById('period_end').value
    //console.log(period_end);
    if (period_begin != "" && period_end != "") {
      $("#searchbutton").prop("disabled", false);
    } else {
      $("#searchbutton").prop("disabled", true);
    }
  });

  $(".checkbox_categories_input").change(function () {
    //if(this.checked) {     
    var categories_selected = [];
    $.each($("input[name='category']:checked"), function () {
      categories_selected.push($(this).val());
    });
    $.each($("input[name='category']:not(:checked)"), function () {
      var index = categories_selected.indexOf($(this).val());
      //console.log(index);         
      //categories_selected.remove();
    });
    //console.log(categories_selected.length);
    //console.log(categories_selected.join(","));
    if (categories_selected.length == 0) {
      categories_selected.push("all");
    }

    var href = window.location.href;
    var url = href + '?';//+'?categories='+categories_selected.join(",");    

    //var url = href+'?';//+'?search='+searchbar.value;
    var boundingbox = "";
    var url_params = [];

    url_params.push('categories=' + categories_selected.join(","));

    map.eachLayer(function (layer) {
      console.log(layer);
      if (layer.hasOwnProperty("layerID")) {
        if (layer.layerID == "boundingbox") {
          var polygon = layer.toGeoJSON();
          boundingbox = polygon['geometry']['coordinates'][0];
          console.log(polygon);
          console.log(boundingbox);
        }
      }
    });

    map.eachLayer(function (layer) {
      if (layer instanceof L.Rectangle) {
        //console.log(layer.layerID);
        if (layer.layerID != "boundingbox") {
          map.removeLayer(layer);
        }
      }
      if (layer instanceof L.Marker) {
        //console.log(layer);
        map.removeLayer(layer);
      }
    });

    var period_begin = document.getElementById('period_begin').value
    var period_end = document.getElementById('period_end').value

    if (boundingbox != "") {
      url_params.push('box=' + boundingbox);
    }
    if (searchbar.value != "") {
      url_params.push('search=' + searchbar.value);
    }
    if (period_begin != "" && period_end != "") {
      url_params.push('period_begin=' + period_begin + '&period_end=' + period_end);
    }

    console.log(url_params);
    var final_url_params = url_params.join("&");
    url = url + final_url_params;
    console.log(url);


    $.ajax({
      url: url,
      type: 'GET',
      //data: JSON.stringify(search_request),
      contentType: "application/json",
      success: function (response) {
        //console.log(response);
        var metadata_results = response['metadata_results'];//JSON.parse(response['metadata_results']);
        var title_list = response['title_list'];
        $("#searchbar").autocomplete({
          source: title_list.split(","),
          minLength: 2,
          max: 10,
          scroll: true
        });

        //console.log(metadata_results);
        if (metadata_results != "no results") {
          $('#number_results').html('Results: <b>' + metadata_results.length.toString() + '</b> items found');
                renderDiscoveryResults(metadata_results);

                //geometry
          for (i = 0; i < metadata_results.length; i++) {
            if (metadata_results[i][6] != null) {

              var box = JSON.parse(metadata_results[i][6])['coordinates'][0];
              correct_bounds = [];

              for (k = 0; k < box.length; k++) {
                correct_bounds[k] = [box[k][1], box[k][0]];
              }
              box
              finalBox = JSON.parse(metadata_results[i][6])['coordinates'];

              var bounds = L.latLngBounds(correct_bounds);
              //var bounds = [[box[1],box[0]],[box[3],box[2]]];
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

            } else {
              console.log("defined");
            }
          }
        } else {
          $('#number_results').html('<i class="fa fa-list" aria-hidden="true"></i> Results: <b>no item was found with this bounding box</b>');
        }
      },
    });
    //}
  });

});