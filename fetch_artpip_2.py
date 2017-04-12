#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib2
import urllib
import json
import os
import threading
import sys
import traceback

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
                    artistName=artistInfo['artistName']
                    artworkTitle=artistInfo['title']
                    artworkUrl=artistInfo['url']

                    #fetch cover artwork
                    coverArtwork=Artwork(artistName,artworkTitle,artworkUrl)

                    artist=Artist(url,artistName,id)

                    if new_thread:
                        task=threading.Thread(target=artist.fetch,args=())
                        coverTask=threading.Thread(target=coverArtwork.fetch,args=())
                        fetchTasks.append(task)
                        fetchTasks.append(coverTast)
                    else:
                        artist.fetch()
                        coverArtwork.fetch()

                #start all fetch tasks
                for task in fetchTasks:
                    task.start()

                #wait for all fetch tasks
                for task in fetchTasks:
                    task.join()

        except Exception,e:
            traceback.print_exc()

class Artist:
    def __init__(self,url,name,identify):
        self.url=url
        self.name=name
        self.id=identify

    def fetch(self,page=1):
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

                aw=Artwork(self.name,title,imageUrl)
                aw.fetch()

                if page != pages:
                    self.fetch(page+1)

class Artwork:
    def __init__(self,artist,title,url):
        self.artist=artist
        self.title=title
        self.url=url
        self.__BUFFER_SIZE__=8192

    def showRate(self,fileName,total,hasRead):
        percent=round((float(hasRead)/total)*100,2)
        sys.stdout.write(u'Downloaded %d of %d bytes (%0.2f%%)\r'%(hasRead,total,percent))

        if hasRead >= total:
            print '\n'

    def download(self,dirName,fileName,url,rateHook=None):
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        saveFilePath=u'%s/%s.jpg'%(dirName,fileName)
        if os.path.isfile(saveFilePath):
            os.remove(saveFilePath)

        downResponse=openUrl(url)
        totalSize=int(downResponse.info().getheader('Content-Length').strip())

        if downResponse:
            saveFile=open(saveFilePath,'a+')
            readSize=0
	    print u'downloading %s'%(saveFilePath)

            while 1:
                data=downResponse.read(self.__BUFFER_SIZE__)
                readSize+=len(data)
                saveFile.write(data)

                if not data:
                    break

                if rateHook:
                    rateHook(saveFilePath,totalSize,readSize)

            saveFile.close()
        

    def fetch(self):
	dirName='artpip/'+self.artist
        self.download(dirName,self.title,self.url,self.showRate)

base_url='http://www.artpip.com'
fetcher=ArtpipFetcher()
fetcher.start(base_url,False)
