#!/usr/bin/python
import MySQLdb
from datetime import datetime, date, timedelta
import time
import calendar
import pytz

local_tz = pytz.timezone('Europe/Moscow')

def utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def timestampToHourMin(timestamp):
    someTime = datetime.fromtimestamp(timestamp)
    localStreamStart = utc_to_local(someTime)
    return localStreamStart.strftime('%H:%M')

def timestampToDate(timestamp):
    someTime = datetime.fromtimestamp(timestamp)
    localStreamStart = utc_to_local(someTime)
    return localStreamStart.strftime('%Y-%m-%d')

def findStreamTimes(workingDate, db):
    dayStart = calendar.timegm(workingDate.timetuple()) + 60*60*8
    dayEnd = calendar.timegm(workingDate.timetuple()) + 60*60*8 + 60*60*24


    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = db.cursor()

    queryStringStart = "SELECT time, game FROM bonjwa_stats WHERE time > " + str(dayStart) + " AND time < 1509865200 ORDER BY time ASC LIMIT 1"
    # Use all the SQL you like
    cur.execute(queryStringStart)

    # print all the first cell of all the rows
    #for row in cur.fetchall():
    #    print row[0]
    streamStart = dayStart
    firstGame = ""
    if cur.rowcount > 0:
        entry = cur.fetchone()
        streamStart = entry[0]
        firstGame = entry[1]

    

    queryStringEnd = "SELECT time FROM bonjwa_stats WHERE time < " + str(dayEnd) + " AND time < 1509865200 ORDER BY time DESC LIMIT 1"
    # Use all the SQL you like
    cur.execute(queryStringEnd)

    # print all the first cell of all the rows
    #for row in cur.fetchall():
    #    print row[0]
    streamEnd = dayEnd
    if cur.rowcount > 0:
        streamEnd = cur.fetchone()[0]


    if streamStart == 0 or streamEnd == 0:
        return 0

    return [streamStart, streamEnd]

def findNextGameTimestamp(startSearch, timeLimit, lastGame, db):
    queryString = """SELECT time, game FROM bonjwa_stats 
        WHERE time > """ + str(startSearch) + """ 
        AND time < """ + str(timeLimit) + """ 
        AND game != '""" + lastGame.replace("'", "\\'") + """'
        ORDER BY time ASC LIMIT 1"""

    cur = db.cursor()
    cur.execute(queryString)

    nextGame = ""
    if cur.rowcount > 0:
        entry = cur.fetchone()
        #print entry
        return entry

    return 0

def buildAbstract(streamTimes, gameTimes):
    #read vod link template, build vod link block
    vodLinkTemplateFile = open("vod_link_template.html", "r") 
    vodTemplateString = vodLinkTemplateFile.read() 
    vodLinkTemplateFile.close()
    print vodTemplateString
    vodLinkBlock = ""


    for game in gameTimes:
        oneVodStartTime = timestampToHourMin(game[0])
        oneVodLink = vodTemplateString
        oneVodLink = oneVodLink.replace("VOD_TIME", oneVodStartTime)
        oneVodLink = oneVodLink.replace("VOD_GAME", game[1])
        vodLinkBlock = vodLinkBlock + oneVodLink

    print vodLinkBlock
  
    #read day template - replace date/name, add vod link block    
    oneDayTemplateFile = open("one_day_template.html", "r") 
    oneDayTemplateString = oneDayTemplateFile.read() 
    oneDayTemplateFile.close()

    oneDayAbstract = oneDayTemplateString.replace("DAY_TITLE", timestampToDate(streamTimes[0]))
    oneDayAbstract = oneDayAbstract.replace("VOD_LINK_BOX", vodLinkBlock)


    abstractFile = open("testfile.txt","w")  
    abstractFile.write(oneDayAbstract) 
    abstractFile.close()

    return 0

def main():

    workingDate = date(2017, 10, 29)

    # my code here
    db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="ct012015",  # your password
                     db="bonjwa_stats")        # name of the data base

    streamTimes = findStreamTimes(workingDate,db)

    if streamTimes == 0:
        return

    print "stream start: " + str(streamTimes[0])
    print "stream end:   " + str(streamTimes[1])


    nextGame = findNextGameTimestamp(streamTimes[0], streamTimes[1], "", db)
    gameTimes = [nextGame]
    while nextGame != 0:
        nextGame = findNextGameTimestamp(nextGame[0], streamTimes[1], nextGame[1], db)
        if nextGame != 0:
            gameTimes.append(nextGame)
    
    print gameTimes

    buildAbstract(streamTimes, gameTimes)

    db.close()

    #wget "http://127.0.0.1:3000/render/dashboard-solo/db/views?orgId=1&from=1509791222&to=1509826562&panelId=1&width=1000&height=500&timeout=30000" -O test.png -T 30

    #SELECT time FROM bonjwa_stats WHERE time > 1509778800 AND time < 1509865200 ORDER BY time ASC LIMIT 1
    #SELECT time FROM bonjwa_stats WHERE time > 1509778800 AND time < 1509865200 ORDER BY time DESC LIMIT 1;


if __name__ == "__main__":
    main()