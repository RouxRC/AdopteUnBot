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
    todo = {}
    for t in db["profiles"].find({"todo": True}, fields=['_id']):
        todo[t['_id']] = True
    return todo

def save_todo(db, todo):
    for pid in todo.keys():
        db["profiles"].update({"_id": pid}, {"_id": pid, "todo": True}, upsert=True)


def get_done(db):
    done = {}
    for t in db["profiles"].find({"todo": False}, fields=['_id']):
        done[t['_id']] = True
    return done

def save_profile(db, profile, pid):
    profile["_id"] = pid
    profile["todo"] = False
    db["profiles"].update({"_id": pid}, profile)
    pass

