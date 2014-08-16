#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, json, time, requests, signal
from random import random, shuffle
from datetime import datetime
from pymongo import MongoClient

from metas import log, mystats, diffstats, find_profiles, metas_profile
from mongo import get_stats, save_stats, get_todo, save_todo, get_done, save_profile, get_good


class Adopte(object):

    def __init__(self, config):
        self.config = config
        self.debug = "debug" in config and config["debug"]
        self.page = None

        self.db = MongoClient()['adopteunbot']
        self.laststats = get_stats(self.db)
        self.todo = get_todo(self.db)
        self.done = get_done(self.db)
        self.nbgood = get_good(self.db)

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
            log("Stopping now with %s profiles left in pile (already %s done including %s active)" % (len(self.todo), len(self.done), self.nbgood))
        exit(sig)

    def query(self, path, args=None):
    # Check hour for paying closedown
        now = datetime.today()
        if now.hour > 17 or (now.hour == 17 and now.minute > 55):
            log("Time to close down is up, see you tomorrow!")
            self.close()

    # Set URL
        if not path.startswith("http"):
            path = "http://www.adopteunmec.com/%s" % path.lstrip('/')
        sys.stdout.write("[%s - INFO] Query %s ... " % (datetime.isoformat(now)[:19], path))
        sys.stdout.flush()

    # Do query
        if args:
            req = self.session.post(path, data=args, **self.options)
        else:
            req = self.session.get(path, **self.options)
        self.page = req.text
        sys.stdout.write("%s\n" % req.status_code)
        sys.stdout.flush()

    # Update todo list of new profiles
        oldtodo = dict(self.todo)
        find_profiles(self.page, self.done, self.todo)
        if oldtodo != self.todo:
            log("Found %s new profiles to visit (%s total left)" % (len(self.todo) - len(oldtodo), len(self.todo)))

        time.sleep(2+8*random())

    # Update personal stats
        if self.logged():
            if self.debug:
                with open("test.html", "w") as f:
                    f.write(self.page.encode('utf-8'))
            stats = mystats(self.page)
            if stats != self.laststats:
                log("Stats update")
                if self.laststats:
                    diffstats(self.laststats, stats)
                self.laststats = save_stats(self.db, stats)
            return req
    # Login if necessary
        else:
            if path.endswith("auth/login"):
                log("Could not login", True)
                return self.close(1)
            else:
                self.query("auth/login", {"username": self.config["user"], "password": self.config["pass"], "remember": "on"})
                return self.query(path, args)

    def logged(self):
        return "var myPseudo" in self.page

    def run(self):
        log("Start new session with %s profiles in pile (already %s done including %s active)" % (len(self.todo), len(self.done), self.nbgood))

    # Go to home
        self.query("home")

    # Visit search queries to find new profiles
        for query in self.config["queries"]:
            self.query("gogole?q=%s" % query)

    # Visit new profiles
        log("Starting to visit %s new profiles" % len(self.todo))
        pids = self.todo.keys()
        shuffle(pids)
        for pid in self.todo.keys():
            req = self.query("profile/%s" % pid)
            prof = metas_profile(self.page)
            save_profile(self.db, prof, pid)
            del(self.todo[pid])
            self.done[pid] = True
            if prof["actif"]:
                self.nbgood += 1

if __name__ == '__main__':
    try:
        with open("config.json") as f:
            config = json.load(f)
        assert("user" in config and config["user"] and type(config["user"]) == unicode)
        assert("pass" in config and config["pass"] and type(config["pass"]) == unicode)
        assert("queries" in config and type(config["queries"]) == list)
    except:
        log("Could not load config.json", True)
        exit(1)

    ad = Adopte(config)
    def terminater(signum, frame):
        log("SIGTERM caught")
        ad.close()
    signal.signal(signal.SIGTERM, terminater)

    try:
        while True:
            ad.run()
    except KeyboardInterrupt:
        print("\n")
        log("Manually stopped, saving status...")
    except Exception as e:
        log("Crashed: %s %s" % (type(e), e), True)
        ad.close(1)
    ad.close()

