var query;
var county;
var results_per_page = 5;
var codes = {};
var cases = {};
var reddit = {};
var feedbacks_sent = {};
var feedbacks_failed = {};
var cur_pages = {
  "codes_info": 1,
  "cases_info": 1,
  "reddit_info": 1
};

function getLegalTips() {
  query = document.getElementById("query_input").value;
  county = document.getElementById("county_selection").value;
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
}

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

function innerHTMLHandler(json_resp) {
  clearResultsAndVariables();
  codes = json_resp.legal_codes;
  cases = json_resp.legal_cases;
  reddit = json_resp.reddit_posts;
  var codes_elem = document.getElementById("codes_info");
  var cases_elem = document.getElementById("cases_info");
  var reddit_elem = document.getElementById("reddit_info");
  var codes_page_elem = document.getElementById("codes_info_page_select");
  var cases_page_elem = document.getElementById("cases_info_page_select");
  var reddit_page_elem = document.getElementById("reddit_info_page_select");
  var codes_total_pages = Math.ceil(codes.length / results_per_page);
  var cases_total_pages = Math.ceil(cases.length / results_per_page);
  var reddit_total_pages = Math.ceil(reddit.length / results_per_page);
  for (var i = 0; i < codes_total_pages; i++) {
    createIndividualPageOption(codes_page_elem, i + 1);
  }
  for (var i = 0; i < cases_total_pages; i++) {
    createIndividualPageOption(cases_page_elem, i + 1);
  }
  for (var i = 0; i < reddit_total_pages; i++) {
    createIndividualPageOption(reddit_page_elem, i + 1);
  }
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
  addCleanText("codes_info", codes.length);
  addCleanText("cases_info", cases.length);
  addCleanText("reddit_info", reddit.length);
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
}

function clearResultsAndVariables() {
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
  clearHTMLElement("codes_info_page_select");
  clearHTMLElement("cases_info_page_select");
  clearHTMLElement("reddit_info_page_select");
}

function clearHTMLElement(id) {
  temp = document.getElementById(id);
  while (temp.firstChild) {
    temp.removeChild(temp.firstChild);
  }
}

function createIndividualResult(html_elem, id, link, title, content, rank) {
  var msg = "Relevant";
  if (id in feedbacks_sent) {
    msg = "Feedback sent!";
  }
  if (id in feedbacks_failed && feedbacks_failed[id]) {
    msg = "Could not send, try again"
  }
  html_elem.insertAdjacentHTML("beforeend",
    '<div class="fixed_container"><span class="link_no_runon">' +
    '<a target="_blank" href="' + link + '">' +
    '</a></span><span class="no_runon"></span><br>' +
    '<button class="btn btn-info" id=' + id +
    ' onclick="sendRelevanceFeedback(this)" data-rank=' + rank.toString() +
    ' style="font-size: 11px">' + msg + '</button></div>'
  );
}

function createIndividualPageOption(html_elem, val) {
  var selected = '';
  if (val == 1) {
    selected = ' selected="selected"'
  }
  var to_insert = '<option' + selected + ' value=' + val + '>Page ' + val + '</option>';
  html_elem.insertAdjacentHTML("beforeend", to_insert);
}

function pageChange(html_elem, id, data, new_page) {
  cur_pages[id] = new_page;
  clearHTMLElement(id);
  for (i = (new_page - 1) * results_per_page; i < Math.min(new_page * results_per_page, data.length); i++) {
    createIndividualResult(html_elem, data[i][2], data[i][3],
      data[i][0], data[i][1], i + 1);
  }
  addCleanText(id, data.length);
}

function handlePageSelect(sel) {
  document.getElementById("results_area").setAttribute("style", "visibility: hidden");
  if (sel.id == "codes_info_page_select") {
    pageChange(document.getElementById("codes_info"), "codes_info", codes, sel.value);
  }
  if (sel.id == "cases_info_page_select") {
    pageChange(document.getElementById("cases_info"), "cases_info", cases, sel.value);
  }
  if (sel.id == "reddit_info_page_select") {
    pageChange(document.getElementById("reddit_info"), "reddit_info", reddit, sel.value);
  }
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
}

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
        cleaveText(cur_span, cur_a, max_height, clean_title);
      } else {
        cleaveText(cur_span, cur_span, max_height, clean_content);
      }
    });
    pos++;
  });
}

function cleaveText(outer_wrap, inner_wrap, max_height, words) {
  var temp = ""
  var all_html = words.split(" ");
  inner_wrap.html("");
  var i = 0;
  while (outer_wrap.outerHeight() < max_height && i < all_html.length) {
    temp += all_html[i] + " ";
    i++;
    inner_wrap.html(temp);
  }
  if (i > 2 && outer_wrap.outerHeight() >= max_height) {
    temp = temp.substring(0, Math.max(0, temp.length - all_html[i - 1].length - 1)) + " ...";
  }
  inner_wrap.html(temp);
}
