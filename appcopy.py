from flask import Flask, render_template, redirect, request, session, url_for
import os
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import requests
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
SCOPES = ['https://www.googleapis.com/auth/androidmanagement']
CLIENT_SECRETS_FILE = "client_secret.json"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('page2'))

@app.route('/page2')
def page2():
    return render_template('page2.html')

@app.route('/b1')  # List enterprises
def b1():
    if 'credentials' not in session:
        return redirect('auth')

    creds = google.oauth2.credentials.Credentials(**session['credentials'])
    service = build('androidmanagement', 'v1', credentials=creds)

    response = service.enterprises().list(projectId='prismatic-petal-460714-t9').execute()
    return render_template('result.html', title="Enterprises", data=response)

@app.route('/b2')  # Create enterprise
def b2():
    if 'credentials' not in session:
        return redirect('/')

    creds = Credentials(**session['credentials'])
    access_token = creds.token

    project_id = 'prismatic-petal-460714-t9'  # Replace with your GCP project ID

    url = f'https://androidmanagement.googleapis.com/v1/signupUrls?projectId={project_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        signup_url = response.json().get('url')
        return render_template('result.html', title="Signup URL", data={"signupUrl": signup_url})
    else:
        return f"<h3>Error {response.status_code}: {response.text}</h3>"
    

@app.route('/b3')  # List policies
def b3():
    if 'credentials' not in session:
        return redirect('auth')

    creds = google.oauth2.credentials.Credentials(**session['credentials'])
    service = build('androidmanagement', 'v1', credentials=creds)

    enterprise_name = "enterprises/your_enterprise_id"  # Replace with actual enterprise ID
    response = service.enterprises().policies().list(parent=enterprise_name).execute()
    return render_template('result.html', title="Policies", data=response)

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(debug=True)
