import uuid
from flask import Flask, render_template, request, session, redirect
import os
from flask_session import Session
import client
import spotipy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

caches_folder = "./.spotify_caches/"
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get("uuid")


@app.route("/")
def index():
    if not session.get("uuid"):
        session["uuid"] = str(uuid.uuid4())
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-read-currently-playing",
        cache_handler=cache_handler,
        show_dialog=True,
    )

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return redirect("/currently_playing")


@app.route("/sign_out")
def sign_out():
    try:
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect("/")


@app.route("/currently_playing")
def data():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-read-currently-playing", cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    res = spotify.current_user_playing_track()
    if res is None or not res["is_playing"]:
        return "No track is currently playing"
    name = res["item"]["name"]
    artists = ""
    for art in res["item"]["artists"]:
        artists += art["name"]
        artists += ", "
    artists = artists[:-2]
    image = res["item"]["album"]["images"][0]["url"]
    c = {
        "name": name,
        "artists": artists,
        "image": image,
        "text": client.get_lyrics_azlyrics(
            name + " " + res["item"]["artists"][0]["name"]
        ),
    }
    return render_template("data.html", form_data=c)


if __name__ == "main":
    app.run()
