#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, json

clean_text = lambda text: re.sub(r'[\n\r\t]', '', text)

def mystats(text):
    stats = {}
    text = clean_text(text)
    for var in ["myAchievementsData", "chatListing", "earnedAchievement", "myPicture", "myPseudo", "myId"]:
        defv = "var %s = " % var
        pos = text.find(defv)
        if pos != -1:
            stats[var] = text[pos+len(defv):text.find(";",pos+len(defv))].strip("'")
            try:
                stats[var] = json.loads(stats[var])
            except:
                pass
    if stats["myAchievementsData"]:
        stats["nb_achievements"] = len(stats["myAchievementsData"])
    if stats["chatListing"]:
        stats["nb_chats"] = len(stats["chatListing"]["contacts"])
    for var in ["mails", "visites", "basket", "chat"]:
        key = "new_%s" % var
        if var == "chat": key += "s"
        if '<li id="%s"' % var in text:
            stats[key] = int(re.search(r'<li id="%s".*?<span[^>]*>(\d+)</span>' % var, text).group(1))
    if "<span class='nb-products'>" in text:
        stats["panier"] = int(re.search(r"<span class='nb-products'>(\d+)</span>", text).group(1))
    if "Il me reste " in text:
        stats["charmes"] = int(re.search(r"Il me reste (\d+) charme", text).group(1))
    for var in ["Visites", "Mails", "Panier"]:
        key = "total_%s" % var.lower()
        if '<span class="type">%s</span>' % var in text:
            stats[key] = int(re.search(r'<span class="type">%s</span>.*?<span class="nb">(\d+)</span>' % var, text).group(1))
    if '<p id="ma-popu">' in text:
        stats["score"] = int(re.sub(r'\D', '', re.search(r'<p id="ma-popu">.*?<span>(.*?)</span>', text).group(1)))
    return stats

difflog = lambda k,s1,s2: "[INFO] - %s :\t%s\t->\t%s" % (k, s1, s2)
def diffstats(s1, s2, key=""):
    if s1 == s2:
        pass
    elif s1 is dict:
        for k in set(s1.keys()+s2.keys()):
            if k not in s1:
                print difflog(k, "_", s2[k])
            elif k not in s2:
                print difflog(k, s1[k], "_")
            else:
                diffstats(s1[k], s2[k], k)
    elif s1 is list:
        for i in range(max(len(s1), len(s2))):
            if i > len(s1)-1:
                print difflog(key, "_", s2[i])
            elif i > len(s2)-1:
                print difflog(key, s1[i], "_")
            else:
                diffstats(s1[i], s2[i], key)
    else:
        print difflog(key, s1, s2)

re_profiles = re.compile(r'(?:"id"\s*:\s*"|href="(?:http://www.adopteunmec.com)?/?profile/)(\d+)"')
def find_profiles(text, done, todo):
    for p in set(re_profiles.findall(text)):
        if p not in done and p not in todo:
            todo[p] = True

re_clean_key = re.compile(ur'[^a-z0-9é]')
re_hashtags = re.compile(r'href="(?:http://www.adopteunmec.com)?/?gogole\?q=%23(.*?)"')
def metas_profile(text):
    prof = {"actif": True}
    text = clean_text(text.encode('iso-8859-15', errors='ignore').decode('utf-8', errors='ignore'))
    if "Cet utilisateur n'existe pas" in text:
        return {"actif": False}
    if "Taux de pop" in text:
        prof["popularite_%"] = int(re.search(r"Taux de pop\s*<span>\s*(\d)+\s*%\s*</span>", text).group(1))
    for var in ["Visites", "Mails", "Panier", "Charmes"]:
        key = "total_%s" % var.lower()
        if '<th>%s</th>' % var in text:
            prof[key] = int(re.search(r'<th>%s</th>.*?<strong>(\d+)</strong>' % var, text).group(1))
    if '<th>Total</th>' in text:
        prof["score"] = int(re.sub(r'\D', '', re.search(r'<th>Total</th>.*?<span>(.*?)</span>', text).group(1)))
    if '<div class="last-cnx">' in text:
        if " En ligne " in text:
            prof["last_conn"] = "en ligne"
        else:
            prof["last_conn"] = re.search(r'<div class="last-cnx">.*?<span class="date">(.*?)</span>', text).group(1)
    if '<div class="username">' in text:
        prof["name"] = re.search(r'<div class="username">(.*?)</div>', text).group(1)
    if '<span class="age">' in text:
        prof["age"] = int(re.search(r'<span class="age">(\d+) ans</span>', text).group(1))
    if '<span class="city"' in text:
        prof["ville"] = re.search(r'<span class="city".*?>(.*?)</span>', text).group(1)
    prof["hashtags"] = "|".join(re_hashtags.findall(text))
    if '<blockquote class="title"' in text:
        prof["catchphrase"] = re.search(r'<blockquote class="title".*?<span>(.*?)</span>', text).group(1)
    for var in ["Yeux", "Profession", "Cheveux", "Alccol", "Tabac", "Mensurations", "Style", "Alimentation", "Origines", "J'aime manger", "Hobbies", "Signes particuliers", "Ce qui se cache en dessous", "Ce qui me fait craquer", "Ce qui m'excite", "Ce que je ne supporte pas", "Vices", "Fantasmes", "Au lit, j'aime...", u"Ce qui m'émoustille", "Mes accessoires"]:
        key = re_clean_key.sub('', var.lower()).encode('utf8')
        if '<strong>%s : </strong>' % var in text:
            prof[key] = re.search(r'<strong>%s : </strong>\s*(?:<![\s-]+>\s*)?(.*?)\s*</(?:div|td)>' % var, text).group(1)
    if "mensurations" in prof:
        for m in prof['mensurations'].split(', '):
            if " cm" in m:
                prof['taille'] = int(m[:m.find(' ')])
                prof["mensurations"] = re.sub(r"%s(, )?" % m, "", prof["mensurations"])
            if " kg" in m:
                prof['poids'] = int(m[:m.find(' ')])
                prof["mensurations"] = re.sub(r"%s(, )?" % m, "", prof["mensurations"])

    if 'Description</span></h2>' in text:
        prof["description"] = re.search(r'Description</span></h2>.*?<p>\s*(.*?)\s*</p>', text).group(1)
        if "pas encore fini de remplir son profil" in prof["description"]:
            prof["description"] = u"non renseigné"
    if 'Shopping List</span></h2>' in text:
        prof["shoppinglist"] = re.search(r'Shopping List</span></h2>.*?<p>\s*(.*?)\s*</p>', text).group(1)
        if "pas encore fini de remplir son profil" in prof["shoppinglist"]:
            prof["shoppinglist"] = u"non renseigné"
    for k in prof.keys():
        if prof[k] is unicode:
            prof[k] = prof[k].encode('utf-8')
    return prof
