/*
  Global variable for the input query
*/
var query;

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
  Dictionary holding all the legal code stop words
*/
var codes_stop_words = {};

/*
  Dictionary holding all the legal cases json
*/
var cases = {};

/*
  Dictionary holding all the legal cases stop words
*/
var cases_stop_words = {};

/*
  Dictionary holding all the reddit json
*/
var reddit = {};

/*
  Dictionary holding all the reddit stop words
*/
var reddit_stop_words = {};

/*
  Which category was chosen to display, either legal codes, cases, or reddit
*/
var chosen_category = "reddit_info_container";

var chosen_category_elem;

var chosen_ml = -1;

var searched_once = false;

/*
  [number of likes, number of dislikes] for each category for logistic regression
*/
var log_reg_frequency = {
  "codes_info": [0, 0],
  "cases_info": [0, 0],
  "reddit_info": [0, 0]
};

/*
  Detailed tracker of recorded feedback
  The key order goes as:
    chosen_ml -> category -> query -> doc_id ->
      {
        is_relevant: boolean,
        ranking: int
      }
*/
var feedbacks_record = {
  1: {
    "codes_info": {},
    "cases_info": {},
    "reddit_info": {}
  },
  2: {
    "codes_info": {},
    "cases_info": {},
    "reddit_info": {}
  }
};

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
  "reddit_info": 1,
  "liked_info": 1
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
 Results liked by user
*/
var liked_results = [];

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
  var mixed_request = true;
  query = document.getElementById("query_input").value
  query = query.replace(/[^ 0-9a-z]+/gi, '')
  query = query.trim().toLowerCase();
  query = query.split(" ").filter(function(c) {
    return c != "";
  }).join(" ");
  var requester = new XMLHttpRequest();
  if (query == "") {
    alert("Please input a valid legal query");
    return;
  } else if (chosen_category == "") {
    alert("Please select a category");
    return;
  } else if (chosen_ml < 0) {
    alert("Please select a relevance feedback type");
    return;
  } else if (chosen_ml === 1 && !checkLogRegFrequency()) {
    alert("Please ensure you have a mix of feedback for each category for Logistic Regression");
    mixed_request = false;
  }
  request_json_obj = {
    query: query,
    reddit_range_utc: $("#reddit_date_range").slider("option", "values"),
    max_res: $("#num_res_range").slider("option", "value"),
    ml_mode: chosen_ml,
    relevance_feedbacks: chosen_ml === 0 || !mixed_request ? null : feedbacks_record[chosen_ml]
  };
  requester.open("POST", '/postquery', true);
  requester.setRequestHeader("Content-Type", "application/json");
  requester.onreadystatechange = function() {
    if (this.readyState == XMLHttpRequest.DONE && this.status === 200) {
      json_resp = JSON.parse(this.response);
      innerHTMLHandler(json_resp);
      document.getElementById("query_submit").innerHTML = "Search";
      setCategory(chosen_category_elem !== undefined ? chosen_category_elem : document.getElementById("choose_reddit"));
      searched_once = true;
    }
  }
  document.getElementById("results_area").setAttribute("style", "visibility: hidden");
  document.getElementById("category_selection").setAttribute("style", "visibility: hidden");
  document.getElementById("query_submit").innerHTML = "Retrieving...";
  results_ready = false;
  requester.send(JSON.stringify(request_json_obj));
}

function checkLogRegFrequency() {
  return !((log_reg_frequency["codes_info"][0] != log_reg_frequency["codes_info"][1] &&
      (log_reg_frequency["codes_info"][0] == 0 || log_reg_frequency["codes_info"][1] == 0)) ||
    (log_reg_frequency["cases_info"][0] != log_reg_frequency["cases_info"][1] &&
      (log_reg_frequency["cases_info"][0] == 0 || log_reg_frequency["cases_info"][1] == 0)) ||
    (log_reg_frequency["reddit_info"][0] != log_reg_frequency["reddit_info"][1] &&
      (log_reg_frequency["reddit_info"][0] == 0 || log_reg_frequency["reddit_info"][1] == 0)))
}
/*
  Notifies corresponding http route that the document corresponding to elem
  is relevant to the query input
*/
function sendRelevanceFeedback(elem) {
  var true_doc_id = elem.id.substring(1);
  elem.blur();
  if (chosen_ml === 0) {
    alert("You are not in feedback mode, please select one first");
    return;
  }
  if (query in feedbacks_record[chosen_ml][elem.dataset.category] &&
    true_doc_id in feedbacks_record[chosen_ml][elem.dataset.category][query]) {
    alert("Feedback already given for this query and relevance feedback type");
    return;
  }
  if (!(query in feedbacks_record[chosen_ml][elem.dataset.category])) {
    feedbacks_record[chosen_ml][elem.dataset.category][query] = {};
  }
  // Recording exact feedback details
  feedbacks_record[chosen_ml][elem.dataset.category][query][true_doc_id] = {
    "is_relevant": parseInt(elem.id.substring(0, 1), 10) === 1,
    "rank": parseInt(elem.dataset.rank, 10)
  };
  if (chosen_ml === 1) {
    log_reg_frequency[elem.dataset.category][parseInt(elem.id.substring(0, 1), 10)] += 1;
  }
  if (parseInt(elem.dataset.yesrel, 10) === 1) {
    document.getElementById(elem.id).innerHTML = "Liked!";
    var temp_elem = document.getElementById('0' + elem.id.substring(1))
    if (temp_elem !== null) {
      temp_elem.setAttribute("style", "display: none");
    }
    var sib_elem = $(elem).siblings();
    var cur_ml_mode = chosen_ml === 1 ? "log. reg." : "rocchio";
    if (sib_elem.length >= 2) {
      var temp_dom = document.createElement("span");
      temp_dom.innerHTML = sib_elem[0].innerHTML;
      var temp_link = temp_dom.firstChild.getAttribute("href");
      var insertion_data = [
        "(query: " + query + ", feedback mode: " + cur_ml_mode + ") " + sib_elem[0].innerHTML,
        sib_elem[1].innerHTML,
        temp_link,
        chosen_category
      ];
      liked_results.push(insertion_data);
      if (liked_results.length <= results_per_page) {
        createIndividualLikedResult(document.getElementById("liked_info"), temp_link);
      }
    }
  } else {
    document.getElementById(elem.id).innerHTML = "Disliked!";
    var temp_elem = document.getElementById('1' + elem.id.substring(1))
    if (temp_elem !== null) {
      temp_elem.setAttribute("style", "display: none");
    }
  }
  document.getElementById(elem.id).setAttribute("style", "background-image: linear-gradient(to right, #2724FF 0%, #4445BA 51%, #3535db 100%); background-size: 200%; border-width: 0px; color: white");
}

/*
  Function that alters the color of the category selection buttons such that
  the chosen one is green; relevant results are also displayed for the selected
  category if possible.
*/
function setCategory(elem) {
  $("#choose_codes").attr("style", "background-color: inherit");
  $("#choose_cases").attr("style", "background-color: inherit");
  $("#choose_reddit").attr("style", "background-color: inherit");
  $("#choose_liked").attr("style", "background-color: inherit");
  chosen_category = elem !== undefined ? elem.dataset.category : "reddit_info_container";
  chosen_category_elem = elem
  $("#" + elem.id).attr("style", "background-image: linear-gradient(to right, #2724FF 0%, #4445BA 51%, #3535db 100%); background-size: 200%; border-width: 0px; color: white");
  if (results_ready) {
    showResults();
    populateData();
  }
}

function setML(elem) {
  chosen_ml = parseInt(elem.dataset.mltype, 10);
  if (searched_once) {
    getLegalTips();
  }
  $("#choose_no_ml").attr("style", "background-color: inherit");
  $("#choose_log_reg").attr("style", "background-color: inherit");
  $("#choose_rocchio").attr("style", "background-color: inherit");
  $("#" + elem.id).attr("style", "background-image: linear-gradient(to right, #2724FF 0%, #4445BA 51%, #3535db 100%); background-size: 200%; border-width: 0px; color: white");
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
  } else if (chosen_category == "liked_info_container") {
    var liked_page_click_elem = document.getElementById("liked_info_page_click");
    total_pages["liked_info"] = Math.ceil(liked_results.length / results_per_page);
    clearHTMLElement("liked_info_page_click");
    createPageClickRange(liked_page_click_elem, "liked_info", 1, total_pages["liked_info"]);
    pageChange(document.getElementById("liked_info"),
      "liked_info", liked_results, cur_pages["liked_info"], true);
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
  codes_stop_words = json_resp.stop_words.statutes;
  cases_stop_words = json_resp.stop_words.cases;
  reddit_stop_words = json_resp.stop_words.reddit;
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
    createIndividualResult(codes_elem, codes[i][2], codes[i][3], i + 1);
  }
  for (var i = 0; i < Math.min(cases.length, results_per_page); i++) {
    createIndividualResult(cases_elem, cases[i][2], cases[i][3], i + 1);
  }
  for (var i = 0; i < Math.min(reddit.length, results_per_page); i++) {
    createIndividualResult(reddit_elem, reddit[i][2], reddit[i][3], i + 1);
  }
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
  document.getElementById("category_selection").setAttribute("style", "visibility: visible");
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
  $("#liked_info_container").attr("style", "display: none");
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
    "reddit_info": 1,
    "liked_info": 1
  };
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

function createIndividualLikedResult(html_elem, link) {
  html_elem.insertAdjacentHTML("beforeend",
    '<div class="fixed_container"><span class="link_no_runon">' +
    '<a target="_blank" onclick="this.blur()" href="' + link + '" rel="nofollow noopener noreferrer">' +
    '</a></span><span class="no_runon"></span></div>'
  );
}
/*
  Inserts the framework HTML to display the relevant data
*/
function createIndividualResult(html_elem, id, link, rank) {
  var msg = "Like";
  var msg2 = "Dislike";
  var temp_id = "";
  var true_doc_id = id
  var yesrel = 0;
  var custom_button_styling = "background-image: linear-gradient(to right, #2724FF 0%, #4445BA 51%, #3535db 100%); background-size: 200%; border-width: 0px; color: white";
  if (chosen_ml > 0 &&
    query in feedbacks_record[chosen_ml][html_elem.id] &&
    true_doc_id in feedbacks_record[chosen_ml][html_elem.id][query]) {
    var exact_feedback = feedbacks_record[chosen_ml][html_elem.id][query][true_doc_id];
    var did_like = exact_feedback["is_relevant"];
    if (did_like) {
      temp_id = "1" + true_doc_id;
      msg = "Liked!";
      yesrel = 1;
    } else {
      temp_id = "0" + true_doc_id;
      msg = "Disliked!"
      yesrel = 0;
    }
    html_elem.insertAdjacentHTML("beforeend",
      '<div class="fixed_container"><span class="link_no_runon">' +
      '<a target="_blank" onclick="this.blur()" href="' + link + '" rel="nofollow noopener noreferrer">' +
      '</a></span><span class="no_runon"></span><br>' +
      '<button class="transparent_button_small" id=' + temp_id +
      ' onclick="sendRelevanceFeedback(this)" data-rank="' + rank.toString() +
      '" data-yesrel="' + yesrel + '" data-category="' + html_elem.id + '" style="display: inline-block; ' + custom_button_styling + '">' + msg + '</button></div>'
    );
  } else {
    html_elem.insertAdjacentHTML("beforeend",
      '<div class="fixed_container"><span class="link_no_runon">' +
      '<a target="_blank" onclick="this.blur()" href="' + link + '" rel="nofollow noopener noreferrer">' +
      '</a></span><span class="no_runon"></span><br>' +
      '<button class="transparent_button_small" id=' + '1' + true_doc_id +
      ' onclick="sendRelevanceFeedback(this)" data-rank="' + rank.toString() +
      '" data-yesrel="' + 1 + '" data-category="' + html_elem.id + '" style="display: inline-block">Like</button>' +
      '<button class="transparent_button_small" id=' + '0' + true_doc_id +
      ' onclick="sendRelevanceFeedback(this)" data-rank="' + rank.toString() +
      '" data-yesrel="' + 0 + '" data-category="' + html_elem.id + '" style="display: inline-block">Dislike</button></div>'
    );
  }
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
function pageChange(html_elem, id, data, new_page, is_liked = false) {
  if (new_page == "next") {
    cur_pages[id] += 1;
  } else if (new_page == "previous") {
    cur_pages[id] -= 1;
  } else {
    cur_pages[id] = parseInt(new_page, 10);
  }
  clearHTMLElement(id);
  for (i = (cur_pages[id] - 1) * results_per_page; i < Math.min(cur_pages[id] * results_per_page, data.length); i++) {
    if (!is_liked) {
      createIndividualResult(html_elem, data[i][2], data[i][3], i + 1);
    } else {
      createIndividualLikedResult(html_elem, data[i][2]);
    }
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
  } else if (sel.dataset.infoclass == "reddit_info") {
    data = reddit;
  } else if (sel.dataset.infoclass == "liked_info") {
    data = liked_results;
  }
  document.getElementById("results_area").setAttribute("style", "visibility: hidden");
  document.getElementById("category_selection").setAttribute("style", "visibility: hidden");
  clearHTMLElement(sel.dataset.infoclass + "_page_click");
  pageChange(document.getElementById(sel.dataset.infoclass),
    sel.dataset.infoclass, data, sel.dataset.pagenum, sel.dataset.infoclass == "liked_info");
  var new_start = Math.max(1, cur_pages[sel.dataset.infoclass] - Math.floor(max_page_options / 2));
  createPageClickRange(document.getElementById(sel.dataset.infoclass + "_page_click"),
    sel.dataset.infoclass, new_start, total_pages[sel.dataset.infoclass]);
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
  document.getElementById("category_selection").setAttribute("style", "visibility: visible");
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
  } else if (id == "liked_info") {
    handleEllipsis(id, index_holder, liked_results);
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
        .replace(new RegExp("\n", "g"), " ")
        .replace(new RegExp("\t", "g"), "&nbsp&nbsp");
      var clean_content = $("<div>" + info_holder[cur_idx][1] + "</div>").text()
        .replace(new RegExp("\n", "g"), " ")
        .replace(new RegExp("\t", "g"), "&nbsp&nbsp");
      var cur_span = $(this);
      var max_height = parseFloat(cur_span.css("max-height"));
      var cur_a;
      var stop_type = id == "liked_info" ? info_holder[cur_idx][3] : null;
      if (cur_span.find("a").length > 0) {
        var cur_a = $(cur_span.find("a").get(0));
        cleaveText(cur_span, cur_a, max_height, clean_title, false, id, stop_type);
      } else {
        cleaveText(cur_span, cur_span, max_height, clean_content, true, id, stop_type);
      }
    });
    pos++;
  });
}

/*
  Truncates text to fit within its div, places ellipses at the end, and "bolds"
  relevant query terms within the description text
*/
function cleaveText(outer_wrap, inner_wrap, max_height, words, is_content, id, stop_type) {
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
      if (badString(poss_str) || stopWord(poss_str, id, stop_type)) {
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

/*
  Determines if a string is a stop word for its category of text
*/
function stopWord(poss_str, id, stop_type) {
  stop_words = {};
  if (stop_type !== null) {
    if (stop_type == "codes_info_container") {
      stop_words = codes_stop_words;
    } else if (stop_type == "cases_info_container") {
      stop_words = cases_stop_words;
    } else if (stop_type == "reddit_info_container") {
      stop_words = reddit_stop_words;
    }
  } else if (id == "codes_info") {
    stop_words = codes_stop_words;
  } else if (id == "reddit_info") {
    stop_words = reddit_stop_words;
  } else if (id == "cases_info") {
    stop_words = cases_stop_words;
  }
  return poss_str in stop_words;
}
