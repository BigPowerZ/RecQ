from baseclass.Recommender import Recommender
from tool import qmath
from structure.symmetricMatrix import SymmetricMatrix
from tool.config import LineConfig


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
        self.v = int(TW['-v'])
        self.twNum = int (TW['-tw'])


    def printAlgorConfig(self):
        "show algorithm's configuration"
        super(TSWalker, self).printAlgorConfig()
        print 'Specified Arguments of', self.config['recommender'] + ':'
        print 'num.neighbors:', self.config['num.neighbors']
        print 'num.shrinkage:', self.config['num.shrinkage']
        print 'similarity:', self.config['similarity']
        print 'step: %d' %self.k
        print 'Random Walk times: %d' %self.twNum
        print 'The trust value of u: %d' %self.v
        print '=' * 80

    def initModel(self):
        self.computeUCorr()

    def predict(self, u, i):
        twcount = 0
        while twcount < self.tw:
            p = 1/tcount
            q = random.randrange(0,len(self.userSim[u]))
            u1 = self.userSim[u][0]
            if self.userSim[u][q][1] == 1:
                if self.dao.rating(u1,i) != 0:
                    rating = self.dao.rating(u1,i)
                    twcount += 1
                else:
                    
                        
                
        # find the closest neighbors of user u
        topUsers = sorted(self.userSim[u].iteritems(), key=lambda d: d[1], reverse=True)
        userCount = self.neighbors
        if userCount > len(topUsers):
            userCount = len(topUsers)
        # predict
        sum, denom = 0, 0
        for n in range(userCount):
            # if user n has rating on item i
            similarUser = topUsers[n][0]
            if self.dao.rating(similarUser, i) != 0:
                similarity = topUsers[n][1]
                rating = self.dao.rating(similarUser, i)
                sum += similarity * (rating - self.dao.userMeans[similarUser])
                denom += similarity
        if sum == 0:
            # no users have rating on item i,return the average rating of user u
            if not self.dao.containsUser(u):
                # user u has no ratings in the training set,return the global mean
                return self.dao.globalMean
            return self.dao.userMeans[u]
        pred = self.dao.userMeans[u] + sum / float(denom)
        return pred

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
                if self.userSim[u1][i][1]==1:
                    tcount += 1
            print 'user ' + u1 + ' finished.'
        print 'The user correlation has been figured out.'
        
    def selSimItem(self,u1,u2,i):
        for k,v in 
