from baseclass.Recommender import Recommender
from tool import qmath
from structure.symmetricMatrix import SymmetricMatrix
from tool.config import LineConfig
from math import exp,sqrt
from random import random,choice

class TSWalker(Recommender):
    def __init__(self,conf, trainingSet=None, testSet=None, fold='[1]'):
        super(TSWalker, self).__init__(conf, trainingSet, testSet, fold)
        self.userSim = SymmetricMatrix(len(self.dao.user))
        self.itemSim = SymmetricMatrix(len(self.dao.item))
        

    def readConfiguration(self):
        self.sim = self.config['similarity']
        self.shrinkage = int(self.config['num.shrinkage'])
        self.neighbors = int(self.config['num.neighbors'])
        TW = LineConfig(self.config['TSWalker'])
        self.k = int(TW['-k'])
        self.v = float(TW['-v'])
        self.tw = int (TW['-tw'])


    def printAlgorConfig(self):
        "show algorithm's configuration"
        super(TSWalker, self).printAlgorConfig()
        print 'Specified Arguments of', self.config['recommender'] + ':'
        print 'num.neighbors:', self.config['num.neighbors']
        print 'num.shrinkage:', self.config['num.shrinkage']
        print 'similarity:', self.config['similarity']
        print 'step: %d' %self.k
        print 'Random Walk times: %d' %self.tw
        print 'The trust value of u: %f' %self.v
        print '=' * 80

    def initModel(self):
        self.computeICorr()
        self.computeUCorr()

    def predict(self, u, i):
        twcount = 0
        pre = []
        tk = 0
        rating = 0
        while twcount < self.tw:
            while tk < self.k:
                u1 = choice(list(self.dao.user))
                if u1 not in pre:
                    pre.append(u1)
                else:
                    continue
                pu = self.dao.getUserId(u1)
                if self.userSim[u][u1] != 1:
                    continue
                else:
                    if self.dao.rating(u1,i) != 0:
                        rating += self.dao.rating(u1,i)
                        twcount += 1
                    else:
                        tk += 1
                        pk = self.proOfK(u1,i,tk)
                        pv = random.randrange(0,1)
                        if pv < pk:
                            uj = self.dao.trainingmatrix.matrix_User[pu].keys()
                            temp = 0
                            bitem = None
                            for j in uj:
                                if self.itemSim[i][self.dao.getItemStr(j)] > temp:
                                    temp = self.itemSim[i][self.dao.getItemStr(j)]
                                    bitem = j
                            rating += self.dao.rating(u1,self.dao.getItemStr(bitem))
                            twcount += 1
                        else:
                            u = u1
        rating = rating / float(self.tw)
        return rating

    def computeUCorr(self):
        'compute correlation among users'
        print 'Computing user correlation...'
        for u1 in self.dao.testSet_u:
            for u2 in self.dao.user:
                if u1 <> u2:
                    if self.userSim.contains(u1, u2):
                        continue
                    sim = qmath.similarity(self.dao.row(u1), self.dao.row(u2), self.sim)
                    if sim >= self.v:
                        self.userSim.set(u1, u2, 1)
                    else:
                        self.userSim.set(u1, u2, 0)
            tcount = 0
            for i in range (len(self.userSim[u1])):
                us = list(self.userSim[u1])
                if us[i][1]==1:
                    tcount += 1
            print 'user ' + u1 + ' finished.'
        print 'The user correlation has been figured out.'
        
    def computeICorr(self):
        'compute correlation among items'
        for i in self.dao.item:
            for j in self.dao.item:
                if i <> j :
                    if self.itemSim.contains(i,j):
                        continue
                    aui = self.dao.itemRated(i)
                    auj = self.dao.itemRated(j)
                    cuser = []
                    for u in aui[0]:
                        for v in auj[0]:
                            if u == v:
                                cuser.append(u)
                    sum = 0
                    d1 = 0
                    d2 = 0
                    for cu in cuser:
                        rui = self.dao.rating(self.dao.getUserStr(cu),i)
                        ruj = self.dao.rating(self.dao.getUserStr(cu),j)
                        umean = self.dao.userMeans[self.dao.getUserStr(cu)]
                        sum += (rui-umean)*(ruj-umean)
                        d1 += (rui-umean)**2
                    for r in self.dao.user:
                        ui = self.dao.rating(r,i)
                        um = self.dao.userMeans[r]
                        d2 += (ui-um)**2
                    try:
                        denom = sqrt(d1*d2)
                        corr = float(sum) / denom
                    except ZeroDivisionError:
                        corr = 0
                    finally:
                        l = float(len(cuser)) / 2
                        sim = corr / (1 + exp(-l))
                        self.itemSim.set(i,j,sim)
            print 'item ' + i + ' finished.'
        print 'The item correlation has been figured out.'
    def proOfK(self,u,i,k):
        res = []
        urj = []
        nk = float(k / 2)
        for x,y in self.dao.trainingmatrix.matrix_User[self.dao.getUserId(u)]:
            if y <> 0:
                urj.append(x)
        for j in urj:
            res.append(self.itemSim[i][j][1])
        map(lambda x:x / (1+exp(-nk)), res)
        nres = list(res)
        return max(nres)
                            
          
