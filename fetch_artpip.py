#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib2
import urllib
import json
import os
import threading
import sys
import traceback
import time

from WorkPool import *

__MULTI_THREAD__ = True
running=False

def openUrl(url):
    if url.strip():
        user_agent='Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
        header={'User-Agent':user_agent}

        try:
            req=urllib2.Request(url,headers=header)
            res=urllib2.urlopen(req)
            return res
        except Exception,e:
	    print u'error in %s'%(url)

def readData(url):
    response=openUrl(url)

    if response:
        try:
            data=response.read()
            return data
        except Exception,e:
	    print u'error in %s'%(url)
            
class ArtpipFetcher:

    def __init__(self,worker_num=10):
        self.workPool=WorkPool(worker_num)

    def getArtpipList(self,url):
        artistInfo=url+'/api/featured'
        jsonStr=readData(artistInfo)
        jsonData={}
        try:
            jsonData=json.loads(jsonStr)
        except:
            print "no JsonData"

        return jsonData


    def start(self,url,new_thread):
        try:
            artistList=self.getArtpipList(url)
            if artistList:
                artworksList=artistList['artworks']
                fetchTasks=[] 

                for artistInfo in artworksList:
                    id=artistInfo['_id']
                    artistId=artistInfo['artist']
                    artistName=artistInfo['artistName']
                    artworkTitle=artistInfo['title']
                    artworkUrl=artistInfo['url']

                    #fetch cover artwork
                    coverArtwork=Artwork(artistName,artworkTitle,artworkUrl,self.workPool)

                    artist=Artist(url,artistName,artistId,self.workPool)

                    self.workPool.add_task(coverArtwork.fetch)#无参
                    artist.fetch()

                    #if new_thread:
                    #    task=threading.Thread(target=artist.fetch,args=())
                    #    coverTask=threading.Thread(target=coverArtwork.fetch,args=())
                    #    fetchTasks.append(task)
                    #    fetchTasks.append(coverTask)
                    #else:
                    #    artist.fetch()
                    #    coverArtwork.fetch()

                #start all fetch tasks
                #for task in fetchTasks:
                #    task.start()

                #wait for all fetch tasks
                #for task in fetchTasks:
                #    task.join()

        except Exception,e:
            traceback.print_exc()

class Artist:
    def __init__(self,url,name,identify,workpool):
        self.url=url
        self.name=name
        self.id=identify
        self.workPool=workpool

    def fetch(self,page=1):
        if not running:
            return

        print u'fetching %s\'s artworks....'%(self.name)

        artistUrl=u'%s/api/artists/%s?page=%d'%(self.url,self.id,page)
        artworksInfo=readData(artistUrl)
        if artworksInfo:
            artworksData=json.loads(artworksInfo)
            pages=artworksData['pages']
            artworksList=artworksData['artworks'] 

            for artwork in artworksList:
                imageUrl=artwork['url'] #fetch from wiki
                title=artwork['title']

                aw=Artwork(self.name,title,imageUrl,self.workPool)
                aw.fetch()

            if page != pages:
                self.fetch(page+1)

class Artwork:
    def __init__(self,artist,title,url,workpool):
        self.__BUFFER_SIZE__=8192
        self.artist=artist
        self.title=title
        self.url=url
        self.workPool=workpool

    def showRate(self,fileName,total,hasRead):
        percent=round((float(hasRead)/total)*100,2)
        sys.stdout.write(u'Downloaded %d of %d bytes (%0.2f%%) about %s by %s \r'%(hasRead,total,percent,self.title,self.artist))
        sys.stdout.flush()

        if hasRead >= total:
            print '\n'

    def download(self,dirName,fileName,url,rateHook=None):
        if not os.path.exists(dirName):
            try:
                os.makedirs(dirName)
            except OSError,e:
                print dirName + ' has existed'

        saveFilePath=u'%s/%s.jpg'%(dirName,fileName)
        if os.path.isfile(saveFilePath):
            os.remove(saveFilePath)

        downResponse=openUrl(url)
        totalSize=int(downResponse.info().getheader('Content-Length').strip())

        if downResponse:
            saveFile=open(saveFilePath,'a+')
            readSize=0
	    #print u'downloading %s'%(saveFilePath)

            while 1:
                data=downResponse.read(self.__BUFFER_SIZE__)
                readSize+=len(data)
                saveFile.write(data)

                if not data or not running:
                    break

                if rateHook:
                    rateHook(saveFilePath,totalSize,readSize)

            saveFile.close()
        

    def fetch(self):
        if not running:
            return

	dirName='artpip/'+self.artist
        rateHandler=self.showRate

        #print u'printing %s from %s'%(self.title,self.artist)

        self.workPool.add_task(self.download,dirName,self.title,self.url)
        #self.download(dirName,self.title,self.url,rateHandler)


def test(i):
    print i

if __name__ == '__main__':
    base_url='http://www.artpip.com'
    running=True
    fetcher=ArtpipFetcher()
    fetcher.start(base_url,__MULTI_THREAD__)


def counter(count):
    while count>0:
        sys.stdout.write(u'waiting for unfinished jobs...%d\r'%count)
        sys.stdout.flush()
        time.sleep(1)
        count-=1

    print ('has exited\r')
    sys.stdout.flush()

#while 1:
#    cmd=raw_input('command: ')

#    if 'quit' == cmd:
#        running=False
#        counter(9)
#        sys.exit()
#        break
