#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, json, time, requests
from pymongo import MongoClient
from metas import mystats, diffstats, find_profiles
from mongo import get_stats, save_stats, get_todo, save_todo, get_done, save_profile

class Adopte(object):

    def __init__(self, config):
        self.config = config
        self.url = None
        self.page = None

        self.db = MongoClient()['adopteunbot']
        self.laststats = get_stats(self.db)
        self.todo = get_todo(self.db)
        self.done = get_done(self.db)

        self.session = requests.Session()
        self.options = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.22 (KHTML, like Gecko) Ubuntu Chromium/25.0.1364.160 Chrome/25.0.1364.160 Safari/537.22"
            },
            "allow_redirects": True,
            "verify": False
        }

        self.start()

    def close(self):
        save_todo(self.db, self.todo)

    def set_url(self, path):
        if not path.startswith("http"):
            path = "http://www.adopteunmec.com/%s" % path.lstrip('/')
        self.url = path
        return path

    def query(self, path, args=None):
        self.set_url(path)
        sys.stdout.write("[INFO] Query %s... " % self.url)

        if args:
            req = self.session.post(self.url, data=args, **self.options)
        else:
            req = self.session.get(self.url, **self.options)
        sys.stdout.write("%s\n" % req.status_code)

        self.page = req.text

        oldtodo = dict(self.todo)
        find_profiles(self.page, self.done, self.todo)
        if oldtodo != self.todo:
            print "[INFO] Found %s new profiles to visit (%s total left)" % (len(self.todo) - len(oldtodo), len(self.todo))

        if self.logged():
            self.stats()

        time.sleep(2)
        return req

    def login(self):
        return self.query("auth/login", {"username": self.config["user"], "password": self.config["pass"], "remember": "on"})

    def logged(self):
        return "var myPseudo" in self.page

    def start(self):
        self.query("home")
        if not self.logged():
            self.login()
        if not self.logged():
            sys.stderr.write("[ERROR] Could not login")
            exit(1)

    def search(self, query):
        return self.query("gogole?q=%s" % query)

    def stats(self):
        stats = mystats(self.page)
        if stats != self.laststats:
            print "[INFO] Stats update"
            if self.laststats:
                diffstats(self.laststats, stats)
            self.laststats = save_stats(self.db, stats)

if __name__ == '__main__':
    try:
        with open("config.json") as f:
            config = json.load(f)
    except:
        sys.stderr.write("[ERROR] Could not load config.json\n")
        exit(1)

    ad = Adopte(config)

