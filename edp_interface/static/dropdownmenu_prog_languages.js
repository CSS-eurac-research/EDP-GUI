$(document).ready(function() {

  var values = $('#programming_languages_list');
  var programming_languages_list = values[0].innerText.split("\n");
  //console.log(programming_languages_list);

  $('#'+ programming_languages_list[0] +'-tab').attr("class","nav-link active");
  $('#'+ programming_languages_list[0] +'-tab').attr("aria-selected","true");
  $('#'+ programming_languages_list[0]).attr("class", "tab-pane fade show active");  

/* 
  $('#programming_languages_list').change(function() {

    var values = []

    $.each($("#programming_languages_list").prop("options"), function(i, opt) {
        values.push(opt.textContent);
    });

    values.forEach(element => {
      console.log(element);
      if (element != "") {
        if (element == $(this).val()){
          $("#snippet_code_"+element).css("display", "block");
        } else {
          $("#snippet_code_"+element).css("display", "none");
        }
      }      
    });

}); */

});