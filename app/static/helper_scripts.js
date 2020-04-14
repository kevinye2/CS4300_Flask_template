var checkBoxStatus = {}
var query;
var county;
var feedback_mode = false;

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
      document.getElementById("query_submit").innerHTML = "Search"
    }
  }
  document.getElementById("results_area").setAttribute("style", "visibility: hidden")
  requester.send(JSON.stringify(request_json_obj));
  document.getElementById("query_submit").innerHTML = "Retrieving..."
}

function sendRelevanceFeedback() {
  if (!feedback_mode) {
    feedback_mode = true
    document.getElementById("feedback_submit").innerHTML = "Send feedback for relevant results"
    showAllCheckBoxes();
    return
  }
  var requester = new XMLHttpRequest();
  requester.open("POST", '/postfeedback', true);
  requester.setRequestHeader("Content-Type", "application/json");
  requester.onreadystatechange = function() {
    if (this.readyState == XMLHttpRequest.DONE && this.status === 200) {
      document.getElementById("feedback_submit").innerHTML = "Send feedback for relevant results";
    }
  }
  var temp_list = [];
  for (var k in checkBoxStatus) {
    if (checkBoxStatus[k][0]) {
      temp_list.push([k, checkBoxStatus[k][1]]);
    }
  }
  var request_json_obj = {
    query: query,
    county: county,
    relevant_ratings: temp_list
  };
  document.getElementById("feedback_submit").innerHTML = "Sending feedback...";
  requester.send(JSON.stringify(request_json_obj));
}

function innerHTMLHandler(json_resp) {
  clearInnerHTMLAndVariables();
  var codes = json_resp.legal_codes;
  var cases = json_resp.legal_cases;
  var reddit = json_resp.reddit_posts;
  var codes_elem = document.getElementById("codes_info");
  var cases_elem = document.getElementById("cases_info");
  var reddit_elem = document.getElementById("reddit_info");
  for (var i = 0; i < codes.length; i++) {
    checkBoxStatus[codes[i][2]] = [false, i + 1];
    codes_elem.insertAdjacentHTML("beforeend",
      '<input type="checkbox"' +
      'onchange="handleCheck(this)"' + 'id="' + codes[i][2] + '" ' +
      'style="bottom: .42em; visibility: hidden" /><a target="_blank" href="' + codes[i][3] +
      '" ' + 'style="font-size: 20">' +
      codes[i][0] + '</a><span style="display: block">' +
      codes[i][1] + '</span><br>'
    );
  }
  for (var i = 0; i < cases.length; i++) {
    checkBoxStatus[cases[i][2]] = [false, i + 1];
    cases_elem.insertAdjacentHTML("beforeend",
      '<input type="checkbox"' +
      'onchange="handleCheck(this)"' + 'id="' + cases[i][2] + '" ' +
      'style="bottom: .42em; visibility: hidden" /><a target="_blank" href="' + cases[i][3] +
      '" ' + 'style="font-size: 20">' +
      cases[i][0] + '</a><span style="display: block">' +
      cases[i][1] + '</span><br>'
    );
  }
  for (var i = 0; i < reddit.length; i++) {
    checkBoxStatus[reddit[i][2]] = [false, i + 1];
    reddit_elem.insertAdjacentHTML("beforeend",
      '<input type="checkbox"' +
      'onchange="handleCheck(this)"' + 'id="' + reddit[i][2] + '" ' +
      'style="bottom: .42em; visibility: hidden" /><a target="_blank" href="' + reddit[i][3] +
      '" ' + 'style="font-size: 20">' +
      reddit[i][0] + '</a><span style="display: block">' +
      reddit[i][1] + '</span><br>'
    );
  }
  document.getElementById("results_area").setAttribute("style", "visibility: visible");
}

function clearInnerHTMLAndVariables() {
  checkBoxStatus = {}
  feedback_mode = false
  document.getElementById("feedback_submit").innerHTML = "Click to start feedback mode"
  var temp = document.getElementById("codes_info");
  while (temp.firstChild) {
    temp.removeChild(temp.firstChild);
  }
  temp = document.getElementById("cases_info");
  while (temp.firstChild) {
    temp.removeChild(temp.firstChild);
  }
  temp = document.getElementById("reddit_info");
  while (temp.firstChild) {
    temp.removeChild(temp.firstChild);
  }
}

function handleCheck(cb) {
  if (cb.checked) {
    checkBoxStatus[cb.id] = [true, checkBoxStatus[cb.id][1]]
  }
}

function showAllCheckBoxes() {
  for (k in checkBoxStatus) {
    document.getElementById(k).setAttribute('style', 'bottom: .42em; visibility: visible');
  }
}
