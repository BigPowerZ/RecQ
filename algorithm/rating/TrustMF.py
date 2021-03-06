#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : TrustMF.py

from baseclass.SocialRecommender import SocialRecommender
import numpy as np
from tool import config


class TrustMF(SocialRecommender):

    def __init__(self, conf,trainingSet=None,testSet=None,relation=list(),fold='[1]'):
        super(TrustMF, self).__init__(conf,trainingSet,testSet,relation,fold)

    def initModel(self):
        super(TrustMF, self).initModel()
        self.Br = np.random.rand(self.dao.trainingSize()[0], self.k)  # latent user matrix
        self.Wr = np.random.rand(self.dao.trainingSize()[0], self.k)  # latent item matrix
        self.Vr = np.random.rand(self.dao.trainingSize()[1], self.k)  # latent item matrix
        self.Be = np.random.rand(self.dao.trainingSize()[0], self.k)  # latent user matrix
        self.We = np.random.rand(self.dao.trainingSize()[0], self.k)  # latent item matrix
        self.Ve = np.random.rand(self.dao.trainingSize()[1], self.k)  # latent item matrix

    def readConfiguration(self):
        super(TrustMF, self).readConfiguration()
        regular = config.LineConfig(self.config['reg.lambda'])
        self.regB = float(regular['-b'])
        self.regT = float(regular['-t'])

    def printAlgorConfig(self):
        super(TrustMF,self).printAlgorConfig()
        print 'Regularization parameter:  regT %.3f' % self.regT
        print '=' * 80

    def buildModel(self):
        # If necessary, you can fix the parameter in ./config/Trust.conf
        iteration = 0
        while iteration < self.maxIter:
            self.loss = 0
            self.trusterModel()
            self.trusteeModel()
            iteration += 1
            self.isConverged(iteration)

    def trusterModel(self):
        for entry in self.dao.trainingData:
            user, item, rating = entry
            mbu = len(self.sao.getFollowees(user))
            uid = self.dao.user[user]
            iid = self.dao.item[item]
            error = self.truserPredict(user, item) - rating
            nbu = len(self.dao.userRated(user)[0])
            nvi = len(self.dao.itemRated(item)[0])
            self.loss += error**2 + self.regB * ((mbu + nbu) * self.Br[uid].dot(self.Br[uid]) + nvi * self.Vr[iid].dot(self.Vr[iid]))
            self.Vr[iid] = self.Vr[iid] - self.lRate * (error * self.Br[uid] + self.regB * nvi * self.Vr[iid])

            relations = self.sao.getFollowees(user)
            if len(relations)==0:
                for followee in relations:
                    weight = relations[followee]

                    if self.dao.containsUser(followee):  # followee is in rating set
                        uf = self.dao.user[followee]
                        error1 = self.Br[uid].dot(self.Wr[uf]) - weight
                        mwk = len(self.sao.getFollowers(followee))
                        self.loss += self.regT * error1**2 + self.regB * mwk * self.Wr[uf].dot(self.Wr[uf])
                        self.Br[uid] = self.Br[uid] - self.lRate * (error * self.Vr[iid] + self.regB * (mbu + nbu) * self.Br[uid] + self.regT * (self.Br[uid].dot(self.Wr[uf]) - weight) * self.Wr[uf])
                        self.Wr[uf] = self.Wr[uf] - self.lRate * (self.regT * error1 * self.Br[uid] + self.regB * mwk * self.Wr[uf])


    def trusteeModel(self):
        for entry in self.dao.trainingData:
            user, item, rating = entry
            mwu = len(self.sao.getFollowers(user))
            uid = self.dao.user[user]
            iid = self.dao.item[item]
            error = self.truseePredict(user, item) - rating
            nwu = len(self.dao.userRated(user)[0])
            nvi = len(self.dao.itemRated(item)[0])
            self.loss += error**2 + self.regB * ((mwu + nwu) * self.We[uid].dot(self.We[uid]) + nvi * self.Ve[iid].dot(self.Ve[iid]))
            self.Ve[iid] = self.Ve[iid] - self.lRate * (error * self.We[uid] + self.regB * nvi * self.Ve[iid])

            relations = self.sao.getFollowers(user)
            if len(relations) == 0:
                for follower in relations:
                    weight = relations[follower]
                    if self.dao.containsUser(follower):  # follower is in rating set
                        uf = self.dao.getUserId(follower)
                        error1 = self.Be[uf].dot(self.We[uid]) - weight
                        mbk = len(self.sao.getFollowees(follower))
                        self.loss += self.regT * error1**2 + self.regB * mbk * self.Be[uf].dot(self.Be[uf])
                        self.We[uid] = self.We[uid] - self.lRate * (error * self.Vr[iid] + self.regB * (mwu + nwu) * self.We[uid] + self.regT * error1 * self.Be[uf])
                        self.Be[uf] = self.Be[uf] - self.lRate * (self.regT * error1 * self.We[uid] + self.regB * mbk * self.Be[uf])

    def truserPredict(self, u, i):
        if self.dao.containsUser(u) and self.dao.containsItem(i):
            u = self.dao.user[u]
            i = self.dao.item[i]
            return self.Br[u].dot(self.Vr[i])
        else:
            return self.dao.globalMean

    def truseePredict(self, u, i):
        if self.dao.containsUser(u) and self.dao.containsItem(i):
            u = self.dao.user[u]
            i = self.dao.item[i]
            return self.We[u].dot(self.Ve[i])
        else:
            return self.dao.globalMean

    def predict(self, u, i):
        if self.dao.containsUser(u) and self.dao.containsItem(i):
            u = self.dao.user[u]
            i = self.dao.item[i]
            return (self.Br[u] + self.We[u]).dot(self.Vr[i] + self.Ve[i]) * 0.25
        else:
            return self.dao.globalMean

    def predictForRanking(self, u):
        'invoked to rank all the items for the user'
        if self.dao.containsUser(u):
            u = self.dao.user[u]
            return (self.Vr + self.Ve).dot(self.Br[u] + self.We[u]) * 0.25
        else:
            return np.array([self.dao.globalMean] * len(self.dao.item))
