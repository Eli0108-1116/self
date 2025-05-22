from __future__ import unicode_literals
from flask import Flask, request, abort, render_template
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import requests
import json
import configparser
import os
from urllib import parse

app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

config = configparser.ConfigParser()
config.read('config.ini')

configuration = Configuration(access_token=config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')

HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}

@app.route('/autobiography')
def autobiography():
    return render_template('bio.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.route('/certificates')
def certificates():
    return render_template('certificates.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    print("Received webhook body:")
    print(json.dumps(body, indent=4))  # ✅ 印出整個 webhook event

    events = body.get("events", [])
    if not events:
        print("❗ events 為空，可能是驗證 webhook 或健康檢查")
        return 'ok'

    event = events[0]
    print(f"✅ 收到事件類型：{event['type']}")

    if "replyToken" in event:
        replyToken = event["replyToken"]
        print(f"✅ replyToken: {replyToken}")

        if event["type"] == "message" and event["message"]["type"] == "text":
            text = event["message"]["text"]
            print(f"✅ 收到文字訊息：{text}")

            if text == "主選單":
                payload = {
                    "replyToken": replyToken,
                    "messages": [
                        {
                            "type": "template",
                            "altText": "請選擇功能",
                            "template": {
                                "type": "carousel",
                                "columns": [
                                    {
                                        "title": "關於我",
                                        "text": "選一個功能看看吧！",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "查看自傳",
                                                "uri": f"{end_point}/autobiography"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "履歷",
                                                "uri": f"{end_point}/resume"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "GitHub 個人頁",
                                                "uri": "https://github.com/Eli0108-1116"
                                            }
                                        ]
                                    },
                                    {
                                        "title": "其他資源",
                                        "text": "以下是我的附加資訊：",
                                        "actions": [
                                            {
                                                "type": "uri",
                                                "label": "證書",
                                                "uri": f"{end_point}/certificates"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "聯絡我",
                                                "uri": f"{end_point}/contact"
                                            },
                                            {
                                                "type": "uri",
                                                "label": "文件",
                                                "uri": f"{end_point}/docs"
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                }
                replyMessage(payload)
                print("✅ 已回應主選單")
            else:
                payload = {
                    "replyToken": replyToken,
                    "messages": [
                        {
                            "type": "text",
                            "text": f"你說了：{text}"
                        }
                    ]
                }
                replyMessage(payload)
                print("✅ 已回應文字")
        else:
            print("⚠️ 不是文字訊息，略過")
    return 'OK'


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )

@app.route("/sendTextMessageToMe", methods=['POST'])
def sendTextMessageToMe():
    pushMessage({})
    return 'OK'

def getNameEmojiMessage():
    lookUpStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    productId = "5ac21a8c040ab15980c9b43f"
    name = "Eli"
    txt_msg = "$" * len(name)
    emojis = [{"index": idx, "productId": productId, "emojiId": str(lookUpStr.index(c)+1).zfill(3)} for idx, c in enumerate(name)]
    return {"type": "text", "text": txt_msg, "emojis": emojis}

def getLocationConfirmMessage(title, latitude, longitude):
    return {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": f"是否規劃 {title} 附近景點？",
            "actions": [
                {
                    "type": "postback",
                    "label": "是",
                    "data": json.dumps({"action":"get_near","title":title,"latitude":latitude,"longitude":longitude})
                },
                {
                    "type": "uri",
                    "label": "Google",
                    "uri": "https://www.google.com?openExternalBrowser=1"
                }
            ]
        }
    }

def getPlayStickerMessage():
    return {"type": "sticker", "packageId": "446", "stickerId": "1988"}

def getImageMessage(originalContentUrl):
    return {"type": "image", "originalContentUrl": originalContentUrl, "previewImageUrl": originalContentUrl}

def replyMessage(payload):
    req_url = "https://api.line.me/v2/bot/message/reply"
    response = requests.post(req_url, headers=HEADER, json=payload)
    print("ok" if response.status_code == 200 else response.text)
    return 'OK'

def pushMessage(payload):
    req_url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(req_url, headers=HEADER, json=payload)
    print("ok" if response.status_code == 200 else response.text)
    return 'OK'

def getTotalSentMessageCount():
    url = "https://api.line.me/v2/bot/message/quota/consumption"
    response = requests.get(url, headers=HEADER)
    return f'使用量：{response.json()["totalUsage"]}' if response.status_code == 200 else 0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload_file', methods=['POST'])
def upload_file():
    payload = dict()
    if request.method == 'POST':
        file = request.files['file']
        form = request.form
        age = form['age']
        gender = ("男" if form['gender'] == "M" else "女") + "性"
        if file:
            filename = file.filename
            img_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(img_path)
            payload["to"] = my_line_id
            payload["messages"] = [getImageMessage(F"{end_point}/{img_path}"), {"type": "text", "text": F"年紀：{age}\n性別：{gender}"}]
            pushMessage(payload)
    return 'OK'

@app.route('/line_login', methods=['GET'])
def line_login():
    code = request.args.get("code", None)
    state = request.args.get("state", None)
    if code and state:
        HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = "https://api.line.me/oauth2/v2.1/token"
        FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login", "client_id": line_login_id, "client_secret":line_login_secret}
        data = parse.urlencode(FormData)
        content = json.loads(requests.post(url=url, headers=HEADERS, data=data).text)
        profile = json.loads(requests.get(url="https://api.line.me/v2/profile", headers={'Authorization': content["token_type"] + " " + content["access_token"]}).text)
        return render_template('profile.html', name=profile["displayName"], pictureURL=profile["pictureUrl"], userID=profile["userId"], statusMessage=profile.get("statusMessage",""))
    else:
        return render_template('login.html', client_id=line_login_id, end_point=end_point)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port)
