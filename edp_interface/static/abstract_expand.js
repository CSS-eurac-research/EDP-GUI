$(document).ready(function() {
    /* $(".abstract-results").click(function() {
      $(this).toggleClass("expand");
    }); */
    $("#searchbutton").prop("disabled",true);
    //console.log($("#searchbar").val());
    $("#searchbar").keyup(function() {
      //console.log("INPUT --> " + $("#searchbar").val());
      if($("#searchbar").val() != "") {
        $("#searchbutton").prop("disabled",false);
      } else {
        $("#searchbutton").prop("disabled",true);
      }
  })
});