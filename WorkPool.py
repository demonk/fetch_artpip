#!/usr/bin/python
# -*- coding:utf-8 -*-

import Queue
import threading
import time
import traceback

class WorkPool:
    def __init__(self,worker_num=5):
        self.workers=[]
        for i in range(0,worker_num):
            self.workers.append(Worker(i))

    def selectWorker(self): 
        worker = None
        for w in self.workers:
            if worker == None or w.task_num() < worker.task_num():
                worker=w

        return worker
            
    def add_task(self,func,*args):
        availableWorker = self.selectWorker()
        if availableWorker:
            availableWorker.add_task(func,args)

class Worker(threading.Thread):
    def __init__(self,id):
        threading.Thread.__init__(self)
        self.id=id
        self.work_queue=Queue.Queue()
        self.running=False
        self.size=0

    def getId(self):
        return self.id

    def add_task(self,func,args):#由于这个args是从外边*args传进来的，不需要再取地址,否则多个参数会被打包成一个对象
        self.work_queue.put((func,args))
        self.size+=1

        if not self.running:
            self.start()

    def task_num(self):
        return self.size

    def isRunning(self):
        return self.running

    def run(self):
        self.running=True
        while self.running:
            try:
                func,args=self.work_queue.get(block=False)
                func(*args)#重新取值，避免直接函数调用时参数个数匹配不上
                self.size-=1
                self.work_queue.task_done()
            except Exception,e:
                #traceback.print_exc()
                break
        

def test(i,j):
    #print threading.current_thread(),i
    print i+j
    time.sleep(0.1)

def test2():
    time.sleep(0.1)

if __name__ == '__main__':
    workPool=WorkPool(5)
    for k in range(1,100):
        workPool.add_task(test,k,k+1)

