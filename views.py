"""Defines the app's routes. Includes OAuth2 support for DocuSign"""

from flask import render_template, url_for, redirect, session, flash, request
from flask_oauthlib.client import OAuth
from datetime import datetime, timedelta
import requests
import uuid
import  eg002_signing_via_email, eg011_embedded_sending,ds_config
            


@app.route("/")
def index():
    return render_template("home.html", title="Home - Python Code Examples")


@app.route("/index")
def r_index():
    return redirect(url_for("index"))


@app.route("/ds/must_authenticate")
def ds_must_authenticate():
    return render_template("must_authenticate.html", title="Must authenticate")


@app.route("/eg001", methods=["GET", "POST"])
def eg001():
    return eg001_embedded_signing.controller()


@app.route("/eg002", methods=["GET", "POST"])
def eg002():
    return eg002_signing_via_email.controller()


@app.route("/eg011", methods=["GET", "POST"])
def eg011():
    return eg011_embedded_sending.controller()

@app.route("/ds_return")
def ds_return():
    event = request.args.get("event")
    state = request.args.get("state")
    envelope_id = request.args.get("envelopeId")
    return render_template("ds_return.html",
        title = "Return from DocuSign",
        event =  event,
        envelope_id = envelope_id,
        state = state
    )


################################################################################
#
# OAuth support for DocuSign
#


def ds_token_ok(buffer_min=60):
    """
    :param buffer_min: buffer time needed in minutes
    :return: true iff the user has an access token that will be good for another buffer min
    """
    #token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjY4MTg1ZmYxLTRlNTEtNGNlOS1hZjFjLTY4OTgxMjIwMzMxNyJ9.eyJUb2tlblR5cGUiOjUsIklzc3VlSW5zdGFudCI6MTU3NDgzNDE1OSwiZXhwIjoxNTc0ODYyOTU5LCJVc2VySWQiOiI1MzUyYzYwMi05MDdjLTQ4NzktYTQ1Mi05NjQ3MGJjOWZkMjciLCJzaXRlaWQiOjEsInNjcCI6WyJzaWduYXR1cmUiLCJjbGljay5tYW5hZ2UiLCJvcmdhbml6YXRpb25fcmVhZCIsImdyb3VwX3JlYWQiLCJwZXJtaXNzaW9uX3JlYWQiLCJ1c2VyX3JlYWQiLCJ1c2VyX3dyaXRlIiwiYWNjb3VudF9yZWFkIiwiZG9tYWluX3JlYWQiLCJpZGVudGl0eV9wcm92aWRlcl9yZWFkIiwiZHRyLnJvb21zLnJlYWQiLCJkdHIucm9vbXMud3JpdGUiLCJkdHIuZG9jdW1lbnRzLnJlYWQiLCJkdHIuZG9jdW1lbnRzLndyaXRlIiwiZHRyLnByb2ZpbGUucmVhZCIsImR0ci5wcm9maWxlLndyaXRlIiwiZHRyLmNvbXBhbnkucmVhZCIsImR0ci5jb21wYW55LndyaXRlIl0sImF1ZCI6ImYwZjI3ZjBlLTg1N2QtNGE3MS1hNGRhLTMyY2VjYWUzYTk3OCIsImF6cCI6ImYwZjI3ZjBlLTg1N2QtNGE3MS1hNGRhLTMyY2VjYWUzYTk3OCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudC1kLmRvY3VzaWduLmNvbS8iLCJzdWIiOiI1MzUyYzYwMi05MDdjLTQ4NzktYTQ1Mi05NjQ3MGJjOWZkMjciLCJhdXRoX3RpbWUiOjE1NzQ4MzM2MTYsInB3aWQiOiIwY2VmOTVlZC03MGU1LTRjZTgtOWM3Ny0wNzU3MTNmMWQwOTUifQ.szC5or79bQbFmq8i0OO8j4KIYZd0zIc9CYsMdpxM2mlX7xqQzVNO5xInauqTINUtsllXWDiHprPOpX0I8FWiF0X7sG8suS5v2dKuLpvjobLhbIyxPSL8tl2Vv13i3Co3VcJVARaQ2bCMET10hDcaqy_L0OqcON1e8hUUk_lgESqvglhucs7Z_CBUrt_fSJv1tz7DHtTeIHISvqLvzF4phC-ZDj_lw6zHrr-RFQE-fhg-ccPYYdqLEEVpCACxVBnzVYodvKZ_LX1FBckd72Bh6hydplTIPN4-n_x3ZE4jLt2lKqBbOB-LUaAKFLjlt6t-YuiE-VRb43n0v0oSgmWgDw"
    #session['ds_access_token']=token
    ok = "ds_access_token" in session and "ds_expiration" in session
    #print(ok)
    ok = ok and (session["ds_expiration"] - timedelta(minutes=buffer_min)) > datetime.utcnow()
    return ok


base_uri_suffix = "/restapi"
oauth = OAuth(app)
request_token_params = {"scope": "signature",
                        "state": lambda: uuid.uuid4().hex.upper()}
if not ds_config.DS_CONFIG["allow_silent_authentication"]:
    request_token_params["prompt"] = "login"
docusign = oauth.remote_app(
    "docusign",
    consumer_key=ds_config.DS_CONFIG["ds_client_id"],
    consumer_secret=ds_config.DS_CONFIG["ds_client_secret"],
    access_token_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/token",
    authorize_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth",
    request_token_params=request_token_params,
    base_url=None,
    request_token_url=None,
    access_token_method="POST"
)


@app.route("/ds/login")
def ds_login():
    return docusign.authorize(callback=url_for("ds_callback", _external=True))


@app.route("/ds/logout")
def ds_logout():
    ds_logout_internal()
    flash("You have logged out from DocuSign.")
    return redirect(url_for("index"))


def ds_logout_internal():
    # remove the keys and their values from the session
    session.pop("ds_access_token", None)
    session.pop("ds_refresh_token", None)
    session.pop("ds_user_email", None)
    session.pop("ds_user_name", None)
    session.pop("ds_expiration", None)
    session.pop("ds_account_id", None)
    session.pop("ds_account_name", None)
    session.pop("ds_base_path", None)
    session.pop("envelope_id", None)
    session.pop("eg", None)
    session.pop("envelope_documents", None)
    session.pop("template_id", None)

def oauth2_token_request(root_url, username, password,
                             integrator_key):
        url = root_url + '/oauth2/token'
        data = {
            'grant_type': 'password',
            'client_id': integrator_key,
            'username': username,
            'password': password,
            'scope': 'api',
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise exceptions.DocuSignOAuth2Exception(response.json())
        session['ds_access_token']=response.json()['access_token']
        return response.json()['access_token']

def oauth2_token_revoke(root_url, token):
        url = root_url + '/oauth2/revoke'
        data = {
            'token': token,
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise exceptions.DocuSignOAuth2Exception(response.json())


@app.route("/ds/callback")
def ds_callback():
    """Called via a redirect from DocuSign authentication service """
    # Save the redirect eg if present
    redirect_url = session.pop("eg", None)
    # reset the session
    ds_logout_internal()
    
    resp = docusign.authorized_response()
    print("resp")
    print(resp)
    if resp is None or resp.get("access_token") is None:
        return "Access denied: reason=%s error=%s resp=%s" % (
            request.args["error"],
            request.args["error_description"],
            resp
        )
    # app.logger.info("Authenticated with DocuSign.")
    flash("You have authenticated with DocuSign.")
    session["ds_access_token"] = resp["access_token"]
    session["ds_refresh_token"] = resp["refresh_token"]
    session["ds_expiration"] = datetime.utcnow() + timedelta(seconds=resp["expires_in"])

    # Determine user, account_id, base_url by calling OAuth::getUserInfo
    # See https://developers.docusign.com/esign-rest-api/guides/authentication/user-info-endpoints
    url = ds_config.DS_CONFIG["authorization_server"] + "/oauth/userinfo"
    auth = {"Authorization": "Bearer " + session["ds_access_token"]}
    response = requests.get(url, headers=auth).json()
    session["ds_user_name"] = response["name"]
    session["ds_user_email"] = response["email"]
    accounts = response["accounts"]
    account = None # the account we want to use
    # Find the account...
    target_account_id = ds_config.DS_CONFIG["target_account_id"]
    if target_account_id:
        account = next( (a for a in accounts if a["account_id"] == target_account_id), None)
        if not account:
            # Panic! The user does not have the targeted account. They should not log in!
            raise Exception("No access to target account")
    else: # get the default account
        account = next((a for a in accounts if a["is_default"]), None)
        if not account:
            # Panic! Every user should always have a default account
            raise Exception("No default account")

    # Save the account information
    session["ds_account_id"] = account["account_id"]
    session["ds_account_name"] = account["account_name"]
    session["ds_base_path"] = account["base_uri"] + base_uri_suffix

    if not redirect_url:
        redirect_url = url_for("index")
    return redirect(redirect_url)

################################################################################

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

