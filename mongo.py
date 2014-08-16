#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

def clean_stats(s):
    del(s["_id"])
    del(s["timestamp"])

def get_stats(db):
    try:
        stats = db["stats"].find(sort=[("_id", -1)])[0]
        clean_stats(stats)
    except:
        stats = {}
    return stats

def save_stats(db, stats):
    dbstats = dict(stats)
    dbstats["timestamp"] = datetime.isoformat(datetime.today())
    db["stats"].insert(dbstats)
    clean_stats(dbstats)
    return dbstats


def get_todo(db):
    return {}

def save_todo(db, todo):
    pass


def get_done(db):
    return {}

def save_profile(db, done):
    pass

