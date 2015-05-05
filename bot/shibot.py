#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
しおり修論大好きbot 本体
"""

from datetime import datetime
import csv
import sys
import os
import random

# Python Twitter Tools
# https://github.com/sixohsix/twitter
from twitter import *


# Configurations from 環境変数
CONSUMER_KEY        = os.environ.get("SHIBOT_CONSUMER_KEY")
CONSUMER_SECRET     = os.environ.get("SHIBOT_CONSUMER_SECRET")
ACCESS_TOKEN        = os.environ.get("SHIBOT_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("SHIBOT_ACCESS_TOKEN_SECRET")

# その他のコンフィグ
SHIBOT         = "shi_mt_bot"
ADMINISTRATORS = ["transcend_msw", "kotarotrd"]


# リプライと反応ワードの辞書/リスト
replies = {}
random_replies = []
reactions = {}

# 実行モード
mode_silent = True


# リプライテキスト
def get_reply_text(text):
    if text in replies:
        return replies[text]
    else:
        return random.choice(random_replies)


# 反応テキスト
def get_react_text(text):
    if text in reactions:
        return reactions[text]
    else:
        return ""


# リプライする
def do_reply(t, id, screen_name, text):
    if text != "" and str(id) != "":
        status = "@" + screen_name + " " + text
        print("status: ", status)
        print("in_reply_to_status_id: ", str(id))
        if not mode_silent:
            try:
                t.statuses.update(status=status, in_reply_to_status_id=id)
            except TwitterError as e:
                print("[Exception] TwitterError!")
                print(e)
            except TwitterHTTPError as e:
                print("[Exception] TwitterHTTPError!")
                print(e)


if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)

    # オプション
    print("[Info] argvs: ", argvs)
    print("[Info] argc: ", argc)
    if (1 < argc) and (argvs[1] == "--silent"):
        mode_silent = True
    else:
        mode_silent = False
    print("[Info] mode_silent: ", mode_silent)

    # CSV読み込み (リプライ)
    with open(os.environ.get("PATH_TO_SHIBOT") + "/csv/replies.csv", "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in reader:
            if line[1] == "":
                random_replies.append(line[2])
            else:
                replies[line[1]] = line[2]

    # CSV読み込み (反応)
    with open(os.environ.get("PATH_TO_SHIBOT") + "/csv/reactions.csv", "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in reader:
            reactions[line[1]] = line[2]

    print("random_replies: ", random_replies)
    print("replies: ", replies)
    print("reactions: ", reactions)

    # Twitter OAuth 認証
    auth = OAuth(ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

    # REST
    t = Twitter(auth=auth)

    # 再起動でDM通知
    if not mode_silent:
        start_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        status = "起床なう (σω-)。о゜" + start_time
        for admin in ADMINISTRATORS:
            t.direct_messages.new(user=admin, text=status)

    # User streams
    ts = TwitterStream(auth=auth, domain="userstream.twitter.com")
    for msg in ts.user():
        print("[Info] Timeline updated!")
        print(msg)

        if ("id" in msg) and ("user" in msg):
            id = msg["id"]
            screen_name = msg["user"]["screen_name"]

            # @メンション の対応
            is_mention = False
            if ("id" in msg) and ("entities" in msg) and ("user_mentions" in msg["entities"]):
                for user_mention in msg["entities"]["user_mentions"]:
                    if user_mention["screen_name"] == SHIBOT:
                        is_mention = True

            if is_mention:
                print("[Info] Mentioned from @" + screen_name + " (id=" + str(id)+ ", text=" + msg["text"] + ")")
                reply_text = get_reply_text(msg["text"])
                if reply_text != "":
                    do_reply(t, id, screen_name, reply_text)

            # 通常postへの反応
            else:
                print("[Info] Posted from @" + screen_name + " (id=" + str(id)+ ", text=" + msg["text"] + ")")
                reply_text = get_react_text(msg["text"])
                if reply_text != "":
                    do_reply(t, id, screen_name, reply_text)