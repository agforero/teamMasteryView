from riotwatcher import LolWatcher, ApiError
import sys
import json
import requests

def getSummonerNames(m_d):
    ret = []
    for i in range(len(m_d["participantIdentities"])):
        ret.append(m_d["participantIdentities"][i]["player"]["summonerName"])
    return ret

def getSummonerIDs(m_d):
    ret = []
    for i in range(len(m_d["participantIdentities"])):
        ret.append(m_d["participantIdentities"][i]["player"]["summonerId"])
    return ret

def findOtherTeam(arr, me):
    half = len(arr) // 2
    left = arr[:half]
    right = arr[half:]

    if me["id"] in left: return right
    elif me["id"] in right: return left
    else: return "error"

def getChampFromKey(d):
    f = open("champion.json", 'r', encoding="utf8")
    champsData = json.load(f)

    for champ in champsData["data"].keys():
        champId = champsData["data"][champ]["key"]
        if int(champId) == d: return champsData["data"][champ]["id"]

    f.close()
    return f"{d} not found" # only gets here if key not found

def main():
    # fancy: multiply a given player's mastery points by their mastery level.
    # e.g.: having 100k and mastery 7 on Jhin is worth 700k, while having 
    # 100k and mastery 6 is worth 600k instead. if this is disabled, then we
    # ignore level alltogether, and focus instead solely on mastery points.
    fancy = True
    
    mx = 5 # how many top champs are recorded
    TABSIZE = 14 # width of tabs in output

    username = sys.argv[1]
    api_key = sys.argv[2]
    watcher = LolWatcher(api_key)
    my_region = "na1"

    try: me = watcher.summoner.by_name(my_region, username)
    except requests.exceptions.HTTPError:
        print("Invalid API key.")
        return

    my_matches = watcher.match.matchlist_by_account(my_region, me["accountId"])
    match_detail = watcher.match.by_id(my_region, my_matches["matches"][0]["gameId"])

    ids = getSummonerIDs(match_detail)
    otherTeam = findOtherTeam(ids, me)
    otherMasteries = {}

    for i in range(len(otherTeam)):
        champs = watcher.champion_mastery.by_summoner(my_region, otherTeam[i])
        for dc in champs:
            if fancy:
                score = dc["championLevel"] * dc["championPoints"]
                if dc["championId"] not in otherMasteries: otherMasteries[dc["championId"]] = score
                else: otherMasteries[dc["championId"]] += score

            else:
                score = dc["championPoints"]
                if dc["championId"] not in otherMasteries: otherMasteries[dc["championId"]] = score
                else: otherMasteries[dc["championId"]] += score

    top = {}
    otherMasteriesSorted = {k: v for k, v in sorted(otherMasteries.items(), key=lambda item: item[1], reverse=True)}
    for i, m in enumerate(list(otherMasteriesSorted.keys())):
        top[m] = otherMasteriesSorted[m]
        if i == mx-1: break # break to only include top mx

    for champKey in top.keys():
        print(f"{getChampFromKey(champKey)}\t{champKey}\t{top[champKey]}".expandtabs(TABSIZE))

if __name__ == "__main__":
    main()