$(document).ready(function () {

  $(".checkbox_categories_input").change(function () {
    var anyChecked = $("input[name='category']:checked").length > 0;
    var searchVal = ($("#searchbar").val() || "").trim();
    var periodBegin = ($("#period_begin").val() || "").trim();
    var periodEnd = ($("#period_end").val() || "").trim();
    var hasBoundingBox = false;

    if (typeof map !== "undefined" && map && typeof map.eachLayer === "function") {
      map.eachLayer(function (layer) {
        if (layer.layerID === "boundingbox") {
          hasBoundingBox = true;
        }
      });
    }

    if (!anyChecked && !searchVal && !periodBegin && !periodEnd && !hasBoundingBox) {
      if (typeof reset_search === "function") {
        reset_search();
      } else {
        location.reload();
      }
      return;
    }

    if (typeof dosearch === "function") {
      dosearch();
    }
  });

});