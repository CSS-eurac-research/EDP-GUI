$(document).ready(function () {

  $("#period_begin").datepicker();
  $("#period_end").datepicker();

  $(".checkbox_categories_input").change(function () {
    if (typeof dosearch === "function") {
      dosearch();
    }
  });

});