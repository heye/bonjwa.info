#!/usr/bin/python
import MySQLdb
from datetime import datetime, date, timedelta
import time
import calendar
import pytz
import os.path
import subprocess
import argparse

local_tz = pytz.timezone('Europe/Moscow')
webrootPath = "/var/www/bonjwa.info/webroot/"

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
    day = localStreamStart.strftime('%d').lstrip('0')
    month = localStreamStart.strftime('%m').lstrip('0')
    year = localStreamStart.strftime('%Y')
    return day + "-" + month + "-" + year

def timestampToDay(timestamp):
    someTime = datetime.fromtimestamp(timestamp)
    localStreamStart = utc_to_local(someTime)
    return localStreamStart.strftime('%d').lstrip('0')
def timestampToMonth(timestamp):
    someTime = datetime.fromtimestamp(timestamp)
    localStreamStart = utc_to_local(someTime)
    return localStreamStart.strftime('%m').lstrip('0')

def timestampToYear(timestamp):
    someTime = datetime.fromtimestamp(timestamp)
    localStreamStart = utc_to_local(someTime)
    return localStreamStart.strftime('%Y')

def weekDayFromTimestamp(timestamp):
    days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    weekday = datetime.fromtimestamp(timestamp).weekday()
    return days[weekday]

def findStreamTimes(workingDate, db):
    dayStart = calendar.timegm(workingDate.timetuple()) + 60*60*8
    dayEnd = calendar.timegm(workingDate.timetuple()) + 60*60*8 + 60*60*24


    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = db.cursor()

    queryStringStart = "SELECT time, game FROM bonjwa_stats WHERE time > " + str(dayStart) + " AND time < " + str(dayEnd) + " ORDER BY time ASC LIMIT 1"
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

    

    queryStringEnd = "SELECT time FROM bonjwa_stats WHERE time < " + str(dayEnd) + " AND time > " + str(streamStart) + " ORDER BY time DESC LIMIT 1"
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

def buildAbstract(streamTimes, gameTimes, workingDateTimestamp):
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

    oneDayTitle = weekDayFromTimestamp(workingDateTimestamp) + " " + timestampToDate(workingDateTimestamp).replace("-", ".")

    oneDayAbstract = oneDayTemplateString.replace("DAY_TITLE", oneDayTitle)
    oneDayAbstract = oneDayAbstract.replace("VOD_LINK_BOX", vodLinkBlock)
    oneDayAbstract = oneDayAbstract.replace("DAY_VIEW_GRAPH", timestampToDate(workingDateTimestamp))
    oneDayAbstract = oneDayAbstract.replace("DATE_DAY", timestampToDay(workingDateTimestamp))
    oneDayAbstract = oneDayAbstract.replace("DATE_MONTH", timestampToMonth(workingDateTimestamp))
    oneDayAbstract = oneDayAbstract.replace("DATE_YEAR", timestampToYear(workingDateTimestamp))

    fileName = timestampToDate(workingDateTimestamp) + ".html"    
    print "GENERATING: " + fileName

    abstractFile = open(webrootPath + fileName,"w")  
    abstractFile.write(oneDayAbstract) 
    abstractFile.close()

    return 0

def generateGraph(streamTimes, workingDateTimestamp):
    fileName = timestampToDate(workingDateTimestamp) + ".png"
    baseURL = "\"http://127.0.0.1:3000/"
    renderURL = "render/dashboard-solo/db/views"
    paramURL = "?orgId=1&from=" + str(streamTimes[0]) + "000&to=" + str(streamTimes[1]) + "000&panelId=1&width=1000&height=500\""
    outputParam = " -O " + webrootPath + fileName

    cmd = "wget " + baseURL + renderURL + paramURL + outputParam
    print "calling: " + cmd
    subprocess.call(cmd, shell=True)

    return os.path.isfile(webrootPath + fileName) 

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',help='an integer for the accumulator')
    args = parser.parse_args()
    print args

    workingDate = date(args.integers[2], args.integers[1], args.integers[0])
    workingDateTimestamp = calendar.timegm(workingDate.timetuple())

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

    #if not generateGraph(streamTimes, workingDateTimestamp):
    #    print "cannot generate graph"
    #    return



    nextGame = findNextGameTimestamp(streamTimes[0], streamTimes[1], "", db)
    gameTimes = [nextGame]
    while nextGame != 0:
        nextGame = findNextGameTimestamp(nextGame[0], streamTimes[1], nextGame[1], db)
        if nextGame != 0:
            gameTimes.append(nextGame)
    
    print gameTimes

    buildAbstract(streamTimes, gameTimes, workingDateTimestamp)

    db.close()

if __name__ == "__main__":
    main()