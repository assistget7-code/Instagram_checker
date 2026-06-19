import os
import json
from flask import Flask, render_template, request, jsonify
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    BadCredentials,
    UserNotFound,
    LoginRequired,
    ChallengeRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    RecaptchaChallengeForm,
    SelectContactPointRecoveryForm,
    TwoFactorRequired,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check_credentials():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    cl = Client()
    cl.delay_range = [1, 3]

    try:
        cl.login(username, password)
        user_info = cl.account_info()
        return jsonify({
            "success": True,
            "status": "valid",
            "message": "Credentials are valid",
            "account": {
                "username": user_info.username,
                "full_name": user_info.full_name,
                "followers": user_info.follower_count,
                "following": user_info.following_count,
                "is_private": user_info.is_private,
                "is_verified": user_info.is_verified,
            }
        })

    except TwoFactorRequired:
        return jsonify({
            "success": True,
            "status": "2fa_required",
            "message": "Credentials are valid but two-factor authentication is enabled",
        })

    except BadPassword:
        return jsonify({
            "success": False,
            "status": "bad_password",
            "message": "Incorrect password for this account",
        })

    except (UserNotFound, BadCredentials):
        return jsonify({
            "success": False,
            "status": "invalid_user",
            "message": "This Instagram account does not exist or credentials are invalid",
        })

    except ChallengeRequired:
        return jsonify({
            "success": True,
            "status": "challenge_required",
            "message": "Credentials appear valid, but Instagram requires a security challenge (e.g. email/SMS verification)",
        })

    except FeedbackRequired:
        return jsonify({
            "success": False,
            "status": "feedback_required",
            "message": "Instagram blocked this login attempt. Try again later or log in via the app first",
        })

    except PleaseWaitFewMinutes:
        return jsonify({
            "success": False,
            "status": "rate_limited",
            "message": "Too many requests. Please wait a few minutes before trying again",
        })

    except RecaptchaChallengeForm:
        return jsonify({
            "success": True,
            "status": "recaptcha_challenge",
            "message": "Credentials appear valid, but Instagram requires a CAPTCHA verification",
        })

    except SelectContactPointRecoveryForm:
        return jsonify({
            "success": True,
            "status": "contact_point_required",
            "message": "Credentials appear valid, but Instagram requires account recovery verification",
        })

    except LoginRequired:
        return jsonify({
            "success": False,
            "status": "login_failed",
            "message": "Login failed. The account may be temporarily restricted",
        })

    except Exception as e:
        error_msg = str(e)
        if "checkpoint" in error_msg.lower() or "challenge" in error_msg.lower():
            return jsonify({
                "success": True,
                "status": "challenge_required",
                "message": "Credentials appear valid, but Instagram requires additional verification",
            })
        return jsonify({
            "success": False,
            "status": "error",
            "message": f"An unexpected error occurred: {error_msg}",
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
