/**
 * Build discovery result cards (Figma Data_discovery type A).
 * item: [uuid, title, abstract, category, keyword, thumbnail, geometry]
 */
function escapeDiscoveryHtml(text) {
  if (text == null) return "";
  var div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function discoveryKeywordTags(keywordStr) {
  if (!keywordStr) return "";
  var parts = String(keywordStr).split(/[,;]+/);
  var html = '<div class="discovery-result__tags">';
  for (var i = 0; i < parts.length; i++) {
    var tag = parts[i].trim();
    if (tag) {
      html += '<span class="discovery-result__tag">' + escapeDiscoveryHtml(tag) + "</span>";
    }
  }
  html += "</div>";
  return html;
}

function buildDiscoveryResultCard(item) {
  var uuid = item[0];
  var title = item[1];
  var abstract = item[2];
  var category = item[3];
  var keyword = item[4];
  var thumbnail = item[5];
  var detailUrl = "/discovery/" + uuid;

  var html = '<article class="discovery-result" id="discovery-result-' + escapeDiscoveryHtml(uuid) + '">';
  html += '<div class="discovery-result__main">';

  html += '<div class="discovery-result__media">';
  if (thumbnail) {
    html +=
      '<img class="discovery-result__img" src="' +
      escapeDiscoveryHtml(thumbnail) +
      '" alt="">';
  }
  html += "</div>";

  html += '<div class="discovery-result__body">';
  if (title) {
    html +=
      '<h2 class="discovery-result__title"><a href="' +
      detailUrl +
      '" target="_blank" rel="noopener noreferrer">' +
      escapeDiscoveryHtml(title) +
      "</a></h2>";
  }
  if (abstract) {
    html +=
      '<div class="discovery-result__abstract abstract-results"><span class="abstract_par">' +
      abstract +
      "</span></div>";
  }
  if (category) {
    html +=
      '<p class="discovery-result__repo">' + escapeDiscoveryHtml(category) + "</p>";
  }
  html +=
    '<a class="discovery-result__view-btn" href="' +
    detailUrl +
    '" target="_blank" rel="noopener noreferrer">View</a>';
  if (keyword) {
    html += discoveryKeywordTags(keyword);
  }
  html += "</div></div>";
  html += '<hr class="discovery-result__divider" aria-hidden="true">';
  html += "</article>";
  return html;
}

function renderDiscoveryResults(metadata_results) {
  var $container = $("#metadata_results");
  $container.empty();
  if (!metadata_results || metadata_results === "no results") {
    return;
  }
  for (var i = metadata_results.length - 1; i >= 0; i--) {
    $container.append(buildDiscoveryResultCard(metadata_results[i]));
  }
}
