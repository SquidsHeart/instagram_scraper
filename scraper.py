import requests
import json
import re

import datetime

from config import *

#######################INIT

class scraper:
    def find_csrf_token(self):
        r = requests.get("https://www.instagram.com/login")
        csrf = re.findall("csrf_token\":\"(.*?)\"", r.text)
        return csrf[0]

    def login(self, username, password):
        time = int(datetime.datetime.now().timestamp())

        login_payload = {
        "username": username,
        "enc_password": "#PWD_INSTAGRAM_BROWSER:0:{time}:{password}".format(time=time, password=password),
        "queryParams": {},
        "optIntoOneTap": "false"
        }

        login_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "x-csrftoken": self.find_csrf_token()
        }

        login_link = "https://www.instagram.com/accounts/login/ajax/"
        r = requests.post(url=login_link, data=login_payload, headers=login_headers)
        saved_cookies = r.cookies
        try:
            cookie_str = "csrftoken={csrf}; mid={mid}; ig_did={ig_did}; ds_user_id={user_id}; sessionid={session_id}; rur={rur}".format(csrf=saved_cookies["csrftoken"], mid=saved_cookies["mid"], ig_did=saved_cookies["ig_did"], user_id=saved_cookies["ds_user_id"], session_id=saved_cookies["sessionid"], rur=saved_cookies["rur"])
        except KeyError:
            raise RuntimeError("login failed")
        return cookie_str

    def __init__(self, username, password):
        saved_cookie = self.login(username, password)
 
        self.find_user_data_headers={
        "Host": "www.instagram.com",
        "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": saved_cookie,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "DNT": "1",
        "Sec-GPC": "1",
        "Cache-Control": "max-age=0",
        "TE": "trailers"
        }

        self.find_followers_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "X-IG-App-ID": "936619743392459",
        "X-ASBD-ID": "198387",
        "X-IG-WWW-Claim": "0",
        "Cookie": saved_cookie,
        "X-Mid": "YcndvgAEAAGDX8wUvAXXYHlCv_1H"
        }


    def find_user_data(self, username):
        target_url = "https://www.instagram.com/{username}/".format(username=username)
        r = requests.get(url=target_url, headers=self.find_user_data_headers)
        html = r.text
        comma_cleared_html = html.replace(",", "")
        id = re.findall("profilePage_(\d*?)\"", html)
        followers = re.findall("content=\"(\d*?) followers", comma_cleared_html)
        following = re.findall("content=\"\d*? followers (\d*?) following", comma_cleared_html)
        posts = re.findall("content=\"\d* followers \d* following (\d*) posts", comma_cleared_html)
        email = re.findall("\"business_email\":(\w*?),", html)
        phone = re.findall("\"business_phone_number\":(\w*),", html)
        private = re.findall("\"is_private\":(\w*?),", html)

        if private[0] == "true":
            private = True
        else:
            private = False
        return {"id": id[0], "follower_count": followers[0], "following_count": following[0], "post_amount": posts[0], "email_address": email[0], "phone_number": phone[0], "private": private}

    def find_followers(self, id, count=100):
        target_url = "https://i.instagram.com/api/v1/friendships/{id}/followers/?count={count}&search_surface=follow_list_page".format(id=id, count=count)
        r = requests.get(url=target_url, headers=self.find_followers_headers)
        json_text = json.loads(r.text)
        user_data = []
        for i in json_text["users"]:
            user_data.append({"username": i["username"], "name": i["full_name"],"id": i["pk"],"private": i["is_private"]})
        return user_data

    def find_following(self, id, count=100):
        target_url = "https://i.instagram.com/api/v1/friendships/{id}/following/?count={count}&search_surface=follow_list_page".format(id=id, count=count)
        r = requests.get(url=target_url, headers=self.find_followers_headers)
        json_text = json.loads(r.text)
        user_data = []
        for i in json_text["users"]:
            user_data.append({"username": i["username"], "name": i["full_name"],"id": i["pk"],"private": i["is_private"]})
        return user_data

    def find_mutuals(self, id, count=100):
        followers = self.find_followers(id, count)
        following = self.find_following(id, count)
        mutuals = []
        for i in followers:
           if i in following:
                mutuals.append(i)
        return mutuals

    def common_followers(self, usernamelist, count=100):
        main_followers = self.find_followers(self.find_user_data(usernamelist[0])["id"])
        mutuals = []
        #makes mutuals list a list of ids which first person follows
        for i in main_followers:
            mutuals.append(i[2])

        index_list = []
        for i in range(0,len(mutuals)):
            index_list.append(i)

        for list in usernamelist[1:]:
            created_list = []
            followers = self.find_followers(self.find_user_data(list)["id"])
            followers_id = []
            ####bottom line makes followers_id list of ids for each account
            for i in followers:
                followers_id.append(i[2])
            for i in mutuals:
                if not i in followers_id:
                    index_list.remove(mutuals.index(i))
        final_list = []
        for i in index_list:
            final_list.append(main_followers[i])

        return final_list

    ########is this just common followers but with followers changed to following? yes
    def common_following(self, usernamelist, count=100):
        main_following = self.find_following(self.find_user_data(usernamelist[0])["id"])
        mutuals = []
        #makes mutuals list a list of ids which first person follows
        for i in main_following:
            mutuals.append(i[2])

        index_list = []
        for i in range(0,len(mutuals)):
            index_list.append(i)

        for list in usernamelist[1:]:
            created_list = []
            following = self.find_following(self.find_user_data(list)["id"])
            following_id = []
            ####bottom line makes following_id list of ids for each account
            for i in following:
                following_id.append(i[2])
            for i in mutuals:
                if not i in following_id:
                    index_list.remove(mutuals.index(i))
        final_list = []
        for i in index_list:
            final_list.append(main_following[i])

        return final_list
