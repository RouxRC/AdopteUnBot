#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, json, time, requests
from random import random, shuffle
from datetime import datetime
from pymongo import MongoClient

from metas import mystats, diffstats, find_profiles, metas_profile
from mongo import get_stats, save_stats, get_todo, save_todo, get_done, save_profile


class Adopte(object):

    def __init__(self, config):
        self.config = config
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

    def close(self, sig=0):
        save_todo(self.db, self.todo)
        if not sig:
            print "[INFO] Stopping now"
        exit(sig)

    def query(self, path, args=None):
    # Check hour for paying closedown
        now = datetime.today()
        if now.hour > 17 or (now.hour == 17 and now.minute > 55):
            print "[INFO] Time to close down is up, see you tomorrow!"
            self.close()

    # Set URL
        if not path.startswith("http"):
            path = "http://www.adopteunmec.com/%s" % path.lstrip('/')
        sys.stdout.write("[INFO] Query %s ... " % path)
        sys.stdout.flush()

    # Do query
        if args:
            req = self.session.post(path, data=args, **self.options)
        else:
            req = self.session.get(path, **self.options)
        self.page = req.text
        sys.stdout.write("%s\n" % req.status_code)

    # Update todo list of new profiles
        oldtodo = dict(self.todo)
        find_profiles(self.page, self.done, self.todo)
        if oldtodo != self.todo:
            print "[INFO] Found %s new profiles to visit (%s total left)" % (len(self.todo) - len(oldtodo), len(self.todo))

    # Update personal stats
        if self.logged():
            with open("test.html", "w") as f:
                f.write(self.page.encode('utf-8'))
            stats = mystats(self.page)
            if stats != self.laststats:
                print "[INFO] Stats update"
                if self.laststats:
                    diffstats(self.laststats, stats)
                self.laststats = save_stats(self.db, stats)

        time.sleep(2+8*random())
        return req

    def logged(self):
        return "var myPseudo" in self.page

    def home(self):
        self.query("home")
        if not self.logged():
            self.query("auth/login", {"username": self.config["user"], "password": self.config["pass"], "remember": "on"})
        if not self.logged():
            sys.stderr.write("[ERROR] Could not login\n")
            self.close(1)

    def search(self):
        for query in self.config["queries"]:
            self.query("gogole?q=%s" % query)

    def profiles(self):
        print "[INFO] Starting to visit %s new profiles" % len(self.todo)
        pids = self.todo.keys()
        shuffle(pids)
        for pid in self.todo.keys():
            req = self.query("profile/%s" % pid)
            prof = metas_profile(self.page)
            save_profile(self.db, prof, pid)
            del(self.todo[pid])
            self.done[pid] = True

if __name__ == '__main__':
    try:
        with open("config.json") as f:
            config = json.load(f)
    except:
        sys.stderr.write("[ERROR] Could not load config.json\n")
        exit(1)

    ad = Adopte(config)
    try:
        while True:
            ad.home()
            ad.search()
            ad.profiles()
    except KeyboardInterrupt:
        print("\n[INFO] Manually stopped, saving status...")
    except Exception as e:
        sys.stderr.write("[ERROR] Crashed: %s %s\n" % (type(e), e))
        ad.close(1)
    ad.close()

