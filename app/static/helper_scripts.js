/*
  Global variable for the input query
*/
var query;

/*
  Global variable for the input county
*/
var county;

/*
  Maximum number of results shown per page
*/
var results_per_page = 5;

/*
  Maximum page options actively displayed to the user
*/
var max_page_options = 10;

/*
  Dictionary holding all the legal code json
*/
var codes = {};

/*
  Dictionary holding all the legal cases json
*/
var cases = {};

/*
  Dictionary holding all the reddit json
*/
var reddit = {};

/*
  Dictionary identifying which documents had feedback sent successfully
*/
var feedbacks_sent = {};

/*
  Dictionary identifying which documents had feedback sent unsuccessfully
*/
var feedbacks_failed = {};

/*
  Which category was chosen to display, either legal codes, cases, or reddit
*/
var chosen_category = '';

/*
  The total number of pages for the code, case, and reddit categories
*/
var total_pages = {
  "codes_info": 1,
  "cases_info": 1,
  "reddit_info": 1
};

/*
  The current page to be displayed for code, case, and reddit categories
*/
var cur_pages = {
  "codes_info": 1,
  "cases_info": 1,
  "reddit_info": 1
};

/*
  Dictionary indicating which categories have data populated on them
*/
var populate_status = {
  "codes_info": false,
  "cases_info": false,
  "reddit_info": false
};

/*
  True if the user has successfully requested results for a query
*/
var results_ready = false;

/*
  Function that triggers upon a searh button press
  The query is trimmed, turned entirely into lowercase, and excess whitespace
  between words is removed.
  There are various checks for the legitimacy of the inputs, including
  how the query must be alphanumeric, all input options must be selected, etc.
  Once the http request to the corresponding query route is successful,
  innerHTMLHandler is called, and data is constructed and displayed
*/
function getLegalTips() {
  query = document.getElementById("query_input").value.trim().toLowerCase();
  query = query.split(" ").filter(function(c) {
    return c != "";
  }).join(" ");
  if (!query.match(/^[ 0-9a-z]+$/)) {
    alert("Please ensure query is alphanumeric");
    return;
  }
  county = document.getElementById("county_selection").value.toLowerCase();
  var requester = new XMLHttpRequest();
  if (county == "" || query == "") {
    alert("Please input a valid legal query and county");
    return;
  } else if (query == "") {
    alert("Please input a valid legal query");
    return;
  } else if (county == "") {
    alert("Please input a valid county");
    return;
  } else if (chosen_category == "") {
    alert("Please select a category");
    return;
  }
  request_json_obj = {
    query: query,
    county: county
  };
  requester.open("POST", '/postquery', true);
  requester.setRequestHeader("Content-Type", "application/json");
  requester.onreadystatechange = function() {
    if (this.readyState == XMLHttpRequest.DONE && this.status === 200) {
      json_resp = JSON.parse(this.response);
      innerHTMLHandler(json_resp);
      document.getElementById("query_submit").innerHTML = "Search";
    }
  }
  document.getElementById("results_area").setAttribute("style", "visibility: hidden");
  requester.send(JSON.stringify(request_json_obj));
  document.getElementById("query_submit").innerHTML = "Retrieving...";
  results_ready = false;
}

/*
  Notifies corresponding http route that the document corresponding to elem
  is relevant to the query and county input
*/
function sendRelevanceFeedback(elem) {
  if (elem.id in feedbacks_sent) {
    alert("Feedback already sent");
    return;
  }
  var requester = new XMLHttpRequest();
  requester.open("POST", '/postfeedback', true);
  requester.setRequestHeader("Content-Type", "application/json");
  requester.onreadystatechange = function() {
    if (this.readyState == XMLHttpRequest.DONE && this.status === 200) {
      feedbacks_sent[elem.id] = true;
      feedbacks_failed[elem.id] = false;
      document.getElementById(elem.id).innerHTML = "Feedback sent!";
    } else {
      feedbacks_failed[elem.id] = true;
      document.getElementById(elem.id).innerHTML = "Could not send, try again";
    }
  }
  var request_json_obj = {
    query: query,
    county: county,
    relevant_rating: [elem.id, parseInt(elem.dataset.rank)]
  };
  document.getElementById(elem.id).innerHTML = "Sending...";
  requester.send(JSON.stringify(request_json_obj));
}

/*
  Function that alters the color of the category selection buttons such that
  the chosen one is green; relevant results are also displayed for the selected
  category if possible.
*/
function setCategory(elem) {
  $("#choose_codes").attr("style", "background-color: #999");
  $("#choose_cases").attr("style", "background-color: #999");
  $("#choose_reddit").attr("style", "background-color: #999");
  chosen_category = elem.dataset.category;
  $("#" + elem.id).attr("style", "background-color: #38ca3f");
  if (results_ready) {
    showResults();
    populateData();
  }
}

/*
  Fills the result area with relevant information of whatever category was
  chosen
*/
function populateData() {
  if (chosen_category == "codes_info_container" && !populate_status['codes_info']) {
    populate_status['codes_info'] = true;
    addCleanText("codes_info", codes.length);
  } else if (chosen_category == "cases_info_container" && !populate_status['cases_info']) {
    populate_status['cases_info'] = true;
    addCleanText("cases_info", cases.length);
  } else if (chosen_category == "reddit_info_container" && !populate_status['reddit_info']) {
    populate_status['reddit_info'] = true;
    addCleanText("reddit_info", reddit.length);
  }
}

/*
  Takes the result of the query request and creates the appropriate page
  navigation structure and displays the relevant data
*/
function innerHTMLHandler(json_resp) {
  clearResultsAndVariables();
  codes = json_resp.legal_codes;
  cases = json_resp.legal_cases;
  reddit = json_resp.reddit_posts;
  var codes_elem = document.getElementById("codes_info");
  var cases_elem = document.getElementById("cases_info");
  var reddit_elem = document.getElementById("reddit_info");
  var codes_page_click_elem = document.getElementById("codes_info_page_click");
  var cases_page_click_elem = document.getElementById("cases_info_page_click");
  var reddit_page_click_elem = document.getElementById("reddit_info_page_click");
  total_pages["codes_info"] = Math.ceil(codes.length / results_per_page);
  total_pages["cases_info"] = Math.ceil(cases.length / results_per_page);
  total_pages["reddit_info"] = Math.ceil(reddit.length / results_per_page);
  createPageClickRange(codes_page_click_elem, "codes_info", 1, total_pages["codes_info"]);
  createPageClickRange(cases_page_click_elem, "cases_info", 1, total_pages["cases_info"]);
  createPageClickRange(reddit_page_click_elem, "reddit_info", 1, total_pages["reddit_info"]);
  for (var i = 0; i < Math.min(codes.length, results_per_page); i++) {
    createIndividualResult(codes_elem, codes[i][2], codes[i][3],
      codes[i][0], codes[i][1], i + 1);
  }
  for (var i = 0; i < Math.min(cases.length, results_per_page); i++) {
    createIndividualResult(cases_elem, cases[i][2], cases[i][3],
      cases[i][0], cases[i][1], i + 1);
  }
  for (var i = 0; i < Math.min(reddit.length, results_per_page); i++) {
    createIndividualResult(reddit_elem, reddit[i][2], reddit[i][3],
      reddit[i][0], reddit[i][1], i + 1);
  }
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
  results_ready = true;
  showResults();
  populateData();
}

/*
  Alters the display attributes of the display containers
*/
function showResults() {
  $("#codes_info_container").attr("style", "display: none");
  $("#cases_info_container").attr("style", "display: none");
  $("#reddit_info_container").attr("style", "display: none");
  $("#" + chosen_category).attr("style", "display: block");
}

/*
  Resets relevant global variables and display area
*/
function clearResultsAndVariables() {
  populate_status = {
    "codes_info": false,
    "cases_info": false,
    "reddit_info": false
  };
  cur_pages = {
    "codes_info": 1,
    "cases_info": 1,
    "reddit_info": 1
  };
  feedbacks_sent = {};
  feedbacks_failed = {};
  clearHTMLElement("codes_info");
  clearHTMLElement("cases_info");
  clearHTMLElement("reddit_info");
  clearHTMLElement("codes_info_page_click");
  clearHTMLElement("cases_info_page_click");
  clearHTMLElement("reddit_info_page_click");
}

/*
  Completely clears an html element of all child elements
*/
function clearHTMLElement(id) {
  temp = document.getElementById(id);
  while (temp.firstChild) {
    temp.removeChild(temp.firstChild);
  }
}

/*
  Inserts the framework HTML to display the relevant data
*/
function createIndividualResult(html_elem, id, link, title, content, rank) {
  var msg = "Relevant";
  if (id in feedbacks_sent) {
    msg = "Feedback sent!";
  }
  if (id in feedbacks_failed && feedbacks_failed[id]) {
    msg = "Could not send, try again";
  }
  html_elem.insertAdjacentHTML("beforeend",
    '<div class="fixed_container"><span class="link_no_runon">' +
    '<a target="_blank" href="' + link + '">' +
    '</a></span><span class="no_runon"></span><br>' +
    '<button class="btn btn-info" id=' + id +
    ' onclick="sendRelevanceFeedback(this)" data-rank="' + rank.toString() +
    '" style="font-size: 11px">' + msg + '</button></div>'
  );
}

/*
  Creates the page navigation structure through html insertion
*/
function createPageClickRange(html_elem, id, start_page, total_pages) {
  if (cur_pages[id] > 1) {
    html_elem.insertAdjacentHTML("beforeend",
      '<a href="#" data-pagenum="previous" ' +
      'data-infoclass="' + id +
      '" onclick="handlePageClick(this)">previous</a>&nbsp&nbsp&nbsp&nbsp');
  }
  var to_insert = '';
  for (i = start_page; i <= Math.min(total_pages, start_page + max_page_options - 1); i++) {
    var styling = '';
    if (i == cur_pages[id]) {
      styling = 'style="font-weight: bold; text-decoration: underline" ';
    }
    to_insert += '<a ' + styling + 'href="#" data-pagenum="' + i.toString() +
      '" data-infoclass="' + id + '" onclick="handlePageClick(this)">' +
      i + '</a> ';
  }
  html_elem.insertAdjacentHTML("beforeend", to_insert);
  if (total_pages > start_page + max_page_options - 1) {
    html_elem.insertAdjacentHTML("beforeend",
      '&nbsp&nbsp&nbsp<a href="#" data-pagenum="next" ' +
      'data-infoclass="' + id +
      '" onclick="handlePageClick(this)">next</a>');
  }
}

/*
  Changes the data displayed based on the new page the user navigates to
*/
function pageChange(html_elem, id, data, new_page) {
  if (new_page == "next") {
    cur_pages[id] += 1;
  } else if (new_page == "previous") {
    cur_pages[id] -= 1;
  } else {
    cur_pages[id] = parseInt(new_page);
  }
  clearHTMLElement(id);
  for (i = (cur_pages[id] - 1) * results_per_page; i < Math.min(cur_pages[id] * results_per_page, data.length); i++) {
    createIndividualResult(html_elem, data[i][2], data[i][3],
      data[i][0], data[i][1], i + 1);
  }
  addCleanText(id, data.length);
}

/*
  Deals with a page click action and initiates process of page change
*/
function handlePageClick(sel) {
  if (sel.dataset.pagenum == cur_pages[sel.dataset.infoclass]) {
    return;
  }
  var data = {}
  if (sel.dataset.infoclass == "codes_info") {
    data = codes;
  } else if (sel.dataset.infoclass == "cases_info") {
    data = cases;
  } else {
    data = reddit;
  }
  document.getElementById("results_area").setAttribute("style", "visibility: hidden");
  clearHTMLElement(sel.dataset.infoclass + "_page_click");
  pageChange(document.getElementById(sel.dataset.infoclass),
    sel.dataset.infoclass, data, sel.dataset.pagenum);
  var new_start = Math.max(1, cur_pages[sel.dataset.infoclass] - Math.floor(max_page_options / 2));
  createPageClickRange(document.getElementById(sel.dataset.infoclass + "_page_click"),
    sel.dataset.infoclass, new_start, total_pages[sel.dataset.infoclass]);
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
}

/*
  Initiates the specific action of cleaning, modifying the data to be displayed
*/
function addCleanText(id, max_length) {
  var cur_page = cur_pages[id];
  var index_holder = [];
  for (i = (cur_page - 1) * results_per_page; i < Math.min(cur_page * results_per_page, max_length); i++) {
    index_holder.push(i);
  }
  if (id == "codes_info") {
    handleEllipsis(id, index_holder, codes);
  } else if (id == "cases_info") {
    handleEllipsis(id, index_holder, cases);
  } else if (id == "reddit_info") {
    handleEllipsis(id, index_holder, reddit);
  }
}

/*
  Removes excess HTML from data to be displayed and sends the clean
  result to cleaveText for appropriate text truncation and ellipse placement
*/
function handleEllipsis(id, idxs, info_holder) {
  var pos = 0;
  $("#" + id).find("div").each(function() {
    $(this).find("span").each(function() {
      if (pos >= idxs.length) {
        return;
      }
      var cur_idx = idxs[pos];
      var clean_title = $("<div>" + info_holder[cur_idx][0] + "</div>").text()
        .replace(new RegExp("\n", "g"), "<br>")
        .replace(new RegExp("\t", "g"), "&nbsp&nbsp&nbsp&nbsp");
      var clean_content = $("<div>" + info_holder[cur_idx][1] + "</div>").text()
        .replace(new RegExp("\n", "g"), "<br>")
        .replace(new RegExp("\t", "g"), "&nbsp&nbsp&nbsp&nbsp");
      var cur_span = $(this);
      var max_height = parseFloat(cur_span.css("max-height"));
      var cur_a;
      if (cur_span.find("a").length > 0) {
        var cur_a = $(cur_span.find("a").get(0));
        cleaveText(cur_span, cur_a, max_height, clean_title, false);
      } else {
        cleaveText(cur_span, cur_span, max_height, clean_content, true);
      }
    });
    pos++;
  });
}

/*
  Truncates text to fit within its div, places ellipses at the end, and "bolds"
  relevant query terms within the description text
*/
function cleaveText(outer_wrap, inner_wrap, max_height, words, is_content) {
  var temp = ""
  var all_html = words.split(" ");
  inner_wrap.html("");
  var i = 0;
  while (outer_wrap.outerHeight() < (max_height - 1) && i < all_html.length) {
    temp += all_html[i] + " ";
    i++;
    inner_wrap.html(temp);
  }
  if (i > 2 && outer_wrap.outerHeight() >= max_height) {
    temp = temp.substring(0, Math.max(0, temp.length - all_html[i - 2].length - all_html[i - 1].length - 2)) + " ...";
  }
  if (is_content) {
    if (badString(query)) {
      inner_wrap.html(temp);
      return;
    }
    temp = $('<div>' + temp + '</div>').html()
      .replace(new RegExp('(' + query + ')', "ig"),
        '<span style="text-shadow: 1px 0 0">$1</span>');
    var poss_strs = query.split(" ");
    for (var x = 0; x < poss_strs.length; x++) {
      var poss_str = poss_strs[x];
      if (badString(poss_str)) {
        continue;
      }
      if (poss_str.length >= 3) {
        temp = $('<div>' + temp + '</div>').html()
          .replace(new RegExp('(' + poss_str + ')', "ig"),
            '<span style="text-shadow: 1px 0 0">$1</span>');
      }
    }
  }
  inner_wrap.html(temp);
}

/*
  Determines if a string potentially corresponds to html tag terms
*/
function badString(str) {
  return str == 'br' || str == 'nbsp' || str == 'span' || str == 'style' ||
    str == 'text' || str == 'shadow' || str == '1px';
}
