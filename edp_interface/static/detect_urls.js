function detect_urls (textToParse) {
 
    var expression = /(https?:\/\/)?[\w\-~]+(\.[\w\-~]+)+(\/[\w\-~@:%]*)*(#[\w\-]*)?(\?[^\s]*)?/gi;
   //*more code to follow here

   var url_parsed = text.replace(expression, function(url) {
        return '<a href="' + url + '">' + url + '</a>';
    });
    console.log(url_parsed);
  }