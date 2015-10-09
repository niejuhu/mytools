#!/usr/bin/python

##
# A gerrit helper program.
#
# pygerrit is required.
##

import argparse
import os
from requests.auth import HTTPDigestAuth
from requests.exceptions import HTTPError
from pygerrit.rest import GerritRestAPI

DEBUG = True
NDEBUG = False

def _cherrypick(rest, changeId, revision, commit, dest):
    params = {"message":commit, "destination":dest}
    response = rest.post("/changes/" + changeId + "/revisions/" + revision +
            "/cherrypick", json=params)
    return response

def _addReviewers(rest, changeId, reviewers):
    reviewUrl = "/changes/" + changeId + "/reviewers"
    for reviewer in reviewers:
        params = {"reviewer" : reviewer}
        if NDEBUG:
            print "reviewUrl: " + reviewUrl + " reviewer: " + reviewer
        rest.post(reviewUrl, json=params)

def _review(rest, change_id, revision_id, reviewScore, verifyScore):
    url = "/changes/" + change_id + "/revisions/" + revision_id + "/review"
    params = {"labels" : {"Code-Review" : reviewScore, "Verified" : verifyScore}}
    rest.post(url, json=params)

def review(rest, query_str, reviewScore, verifyScore):
    changes = rest.get("/changes/?q=" + query_str + "&o=CURRENT_REVISION")
    for ch in changes:
        try:
            _id = ch["_id"]
            revision = ch["current_revision"]
            _review(rest, _id, revision, reviewScore, verifyScore)
        except HTTPError as e:
            print "Error: " + _id
            print e

def getReviewUrls(rest, gerrit_url, query_str):
    if not gerrit_url.endswith("/"):
        gerrit_url = gerrit_url + "/"

    changes = rest.get("/changes/?q=" + query_str);
    for ch in changes:
        number = ch["_number"]
        print gerrit_url + "#/c/" + str(number)
    print "total " + str(len(changes))

def parseBranch(branch):
    if branch.startswith("v6-kk-"):
        api = "kk"
        product = branch[len("v6-kk-") : -(len("-dev"))]
    elif branch.endswith("-kk"):
        api = "kk"
        product = branch[:-len("-kk")]
    elif branch.startswith("v6-l-"):
        api = "l"
        product = branch[len("v6-l-") : -(len("-dev"))]
    elif branch.endswith("-l"):
        api = "l"
        product = branch[:-len("-l")]
    else:
        return None, None
    return api, product

def getAuthFromGerritrc(url):
    if url.startswith("http://"):
        url = url[len("http://") :]
    try:
        loc = os.path.expanduser('~/{0}'.format(".gerritrc"))
    except:
        return None, None
    if os.path.exists(loc):
        with open(loc) as f:
            for line in f.readlines():
                if line.startswith("#"):
                    continue
                tokens = line.strip("\n").split(" ")
                if len(tokens) != 3:
                    return None, None
                if url == tokens[0]:
                    return tokens[1], tokens[2]
    return None, None

def main():
    epilog = (".gerritrc file can have multi lines. Each line represents an auth item. " +
            "Each item has the format 'host[:port] username password'. lines start with " +
            "a '#' are ignored.")
    parser = argparse.ArgumentParser(description="Send request using Gerrit HTTP API",
            epilog=epilog)
    parser.add_argument("gerrit_url", help="gerrit server url")
    parser.add_argument("query", help="the query string to select changes")
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("-e", "--gerritrc", action="store_true",
            help="get user credentials from $HOME/.gerritrc")
    parser.add_argument("-a", "--reviewers",
            help="add reviewers for selected changes, seperated by ','")
    parser.add_argument("-r", "--review", help="set review for selected changes", type=int,
            choices=[-2,-1,0,1,2], default=0)
    parser.add_argument("-g", "--generate_review_url", action="store_true",
            help="generate review urls for each selected changes")
    parser.add_argument("-s", "--cherrypick_to_stable_version",
            help="cherrypick selected changes from dev branch to stable")
    parser.add_argument("-v", "--verify", help="set verify for selected changes", type=int,
            choices=[-1, 0, 1], default=0)
    parser.add_argument("-V", "--verbose", action="count", default=0,
            help="increase verbosity")
    options = parser.parse_args()

    gerrit_url = options.gerrit_url
    queryStr = options.query.replace(" ", "%20")
    reviewers = None
    if options.reviewers:
        reviewers = options.reviewers.split(",")
    stableVersion = options.cherrypick_to_stable_version

    if NDEBUG:
        print "gerrit url: ", gerrit_url
        print "query: ", queryStr
        print "reviwers: " + str(reviewers)

    if options.username and options.password:
        auth = HTTPDigestAuth(options.username, options.password)
    elif options.gerritrc:
        u, p = getAuthFromGerritrc(gerrit_url)
        if u and p:
            auth = HTTPDigestAuth(u, p)
        else:
            print "Can't find .gerritrc or no auth found in .gerritrc"
            return None
    else:
        auth = None

    rest = GerritRestAPI(url=gerrit_url, auth=auth)
    changes = rest.get("/changes/?q=" + queryStr + "&o=CURRENT_REVISION" +
            "&o=ALL_COMMITS")
    for ch in changes:
        try:
            _id = ch["id"]
            branch = ch["branch"]
            current_revision = ch["current_revision"]
            commit = ch["revisions"][current_revision]["commit"]["message"]
            _number = ch["_number"]
            if NDEBUG:
                print (str(i) + " : " + _id + " " + current_revision +
                        branch + " " + commit)
           
            if stableVersion:
                api, product = parseBranch(branch)
                if not api:
                    print "Error: " + ch["project"] + " " +  ch["subject"]
                    continue
                destBranch = "v7-" + api + "-" + product + "-" + stableVersion
                if NDEBUG:
                    print branch + " -> " + destBranch

                response = _cherrypick(rest, _id, current_revision, commit, destBranch)
                _id = response["id"]
                _number = response["_number"]

            if (reviewers):
                _addReviewers(rest, _id, reviewers)

            if options.review != 0 or options.verify != 0:
                _review(rest, _id, "current", options.review, options.verify)

            if options.generate_review_url:
                prefix = ""
                if options.verbose >= 2:
                    prefix = ("review_url: " + _id + ": ").replace("%2F", "/")
                elif options.verbose >= 1:
                    prefix = "review_url: "
                print prefix + gerrit_url + "#/c/" + str(_number)

        except HTTPError as e:
            print "Error in: " + _id
            print e
            continue

if __name__ == "__main__":
    main()
