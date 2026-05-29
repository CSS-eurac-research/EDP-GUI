$(document).ready(function () {

  var searchDebounceTimer = null;

  function hasDrawnBoundingBox() {
    var hasBoundingBox = false;
    if (typeof map !== "undefined" && map && typeof map.eachLayer === "function") {
      map.eachLayer(function (layer) {
        if (layer.layerID === "boundingbox") {
          hasBoundingBox = true;
        }
      });
    }
    return hasBoundingBox;
  }

  $(".checkbox_categories_input").change(function () {
    var anyChecked = $("input[name='category']:checked").length > 0;
    var searchVal = ($("#searchbar").val() || "").trim();
    var periodBegin = ($("#period_begin").val() || "").trim();
    var periodEnd = ($("#period_end").val() || "").trim();
    var hasBoundingBox = hasDrawnBoundingBox();

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

  $("#searchbar").on("input", function () {
    clearTimeout(searchDebounceTimer);

    var searchVal = ($(this).val() || "").trim();
    var anyChecked = $("input[name='category']:checked").length > 0;
    var periodBegin = ($("#period_begin").val() || "").trim();
    var periodEnd = ($("#period_end").val() || "").trim();
    var hasBoundingBox = hasDrawnBoundingBox();

    if (!searchVal && !anyChecked && !periodBegin && !periodEnd && !hasBoundingBox) {
      if (typeof reset_search === "function") {
        reset_search();
      } else {
        location.reload();
      }
      return;
    }

    searchDebounceTimer = setTimeout(function () {
      if ((searchVal.length === 0 || searchVal.length >= 2) && typeof dosearch === "function") {
        dosearch();
      }
    }, 300);
  });

});