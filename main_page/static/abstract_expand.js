$(document).ready(function () {

  $(".checkbox_categories_input").change(function () {
    if (typeof dosearch === "function") {
      dosearch();
    }
  });

});