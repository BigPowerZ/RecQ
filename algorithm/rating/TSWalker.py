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
        super(TSWalker, self).readConfiguration()
        self.sim = self.config['similarity']
        TW = LineConfig(self.config['TSWalker'])
        self.k = int(TW['-k'])
        self.v = float(TW['-v'])
        self.tw = int (TW['-tw'])


    def printAlgorConfig(self):
        "show algorithm's configuration"
        super(TSWalker, self).printAlgorConfig()
        print 'Specified Arguments of', self.config['recommender'] + ':'
        print 'similarity:', self.config['similarity']
        print 'step: %d' %self.k
        print 'Random Walk times: %d' %self.tw
        print 'The trust value of u: %f' %self.v
        print '=' * 80

    def initModel(self):
        self.computeICorr()
        self.computeUCorr()

    def predict(self, u, i):
        u0 = u
        twcount = 0
        pre = []
        rating = 0
        while twcount < self.tw:
            tk = 0
            while tk < self.k:
                u1 = choice(list(self.dao.user))
                if (u0<>u1) and (u1 not in pre):
                    pre.append(u1)
                else:
                    continue
                pu = self.dao.getUserId(u1)
                if self.userSim[u][u1] != 1:
                    continue
                else:
                    if self.dao.rating(u1,i) != 0:
                        rating += self.dao.rating(u1,i)
                        tk += 1
                        twcount += 1
                        print 'Finished TSWalker for %d time in %d step-1'%(twcount ,tk)
                    else:
                        tk += 1
                        pk = self.proOfK(u1,i,tk)
                        pv = random()
                        if pv < pk:
                            uj = self.dao.trainingMatrix.matrix_User[pu].keys()
                            temp = 0
                            bitem = 0
                            for j in uj:
                                if self.itemSim[i][self.dao.id2item[j]] > temp:
                                    temp = self.itemSim[i][self.dao.id2item[j]]
                                    bitem = j
                            rating += self.dao.rating(u1,self.dao.id2item[bitem])
                            twcount += 1
                            print 'Finished TSWalker for %d time in %d step-2' % (twcount, tk)
                        else:
                            u0 = u1
        print rating
        pred = rating / float(self.tw)
        return pred

    def computeUCorr(self):
        'compute correlation among users'
        print 'Computing user correlation...'
        for u1 in self.dao.testSet_u:
            for u2 in self.dao.user:
                if u1 <> u2:
                    if self.userSim.contains(u1, u2):
                        continue
                    sim = qmath.similarity(self.dao.sRow(u1), self.dao.sRow(u2), self.sim)
                    if sim >= self.v:
                        self.userSim.set(u1, u2, 1)
                    else:
                        self.userSim.set(u1, u2, 0)
            tcount = 0
            for i in range (len(self.userSim[u1])):
                us = list(self.userSim[u1].iteritems())
                if us[i][1] ==1:
                    tcount += 1
            print 'user ' + u1 + ' finished.'
        print 'The user correlation has been figured out.'
        
    def computeICorr(self):
        'compute correlation among items'
        for i in self.dao.item:
            d1 = 0
            for r in self.dao.user:
                ui = self.dao.rating(r, i)
                um = self.dao.userMeans[r]
                d1 += (ui - um) ** 2
            for j in self.dao.item:
                if i <> j :
                    if self.itemSim.contains(i,j):
                        continue
                    aui,rui = self.dao.itemRated(i)
                    auj,ruj = self.dao.itemRated(j)
                    cuser = set(aui).intersection(set(auj))
                    sum = 0
                    d2 = 0
                    for cu in cuser:
                        rui = self.dao.rating(self.dao.id2user[cu],i)
                        ruj = self.dao.rating(self.dao.id2user[cu],j)
                        umean = self.dao.userMeans[self.dao.id2user[cu]]
                        sum += (rui-umean)*(ruj-umean)
                        d2 += (rui-umean)**2
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
        nk = float(k) / 2
        ui,ur = self.dao.userRated(u)
        for j in ui:
            res.append(self.itemSim[i][self.dao.id2item[j]])
        denom = 1+exp(-nk)
        nres = map(lambda x:(x/denom), res)
        return max(nres)
                            
          
