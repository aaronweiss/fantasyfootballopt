
"""
Created on Sun Mar  4 13:23:57 2018

@author: Aaron
"""

import pandas as pd
from pyomo.environ import *
from pyomo.opt import SolverFactory

#import salary and projection data
df1 = pd.read_excel('Week 1.xlsx')
df2 = pd.read_excel('salaryweek1.xlsx')
df3 = pd.read_excel('fandueldata1.xlsx')

#creating backtesting data
bt=df2.loc[:,['Pos','player','team','FDpoints']]
idx=(bt['Pos']=='Def')
bt.loc[idx,['player','team']]=bt.loc[idx,['team','player']].values
bt=bt.loc[:,['player','FDpoints']]

#finding average score to win a contest
idx3=df3.index[df3.isnull().any(1)]
df3=df3.drop(idx3)
df3=df3.set_index('Cash')
ptsneed=df3.loc[0.44,'Cutline']
scoretobeat=ptsneed.mean()

#setting indices and cleaning up data
df1.set_index('position',inplace=True)
df2.set_index('Pos',inplace=True)
df2=df2[df2.FDsalary>0]


#get relevant data from projections
qb1=df1.loc['QB',['player','points']]
rb1=df1.loc['RB',['player','points']]
wr1=df1.loc['WR',['player','points']]
te1=df1.loc['TE',['player','points']]
k1=df1.loc['K',['player','points']]
dst1=df1.loc['DST',['team','points']]

#get relevant data from salary info
qb2=df2.loc['QB',['player','FDsalary']]
qb2.reset_index(inplace=True)
rb2=df2.loc['RB',['player','FDsalary']]
rb2.reset_index(inplace=True)
wr2=df2.loc['WR',['player','FDsalary']]
wr2.reset_index(inplace=True)
te2=df2.loc['TE',['player','FDsalary']]
te2.reset_index(inplace=True)
k2=df2.loc['PK',['player','FDsalary']]
k2.reset_index(inplace=True)
dst2=df2.loc['Def',['team','FDsalary']]
dst2.reset_index(inplace=True)

#merge data into one data set per position (deleting missing data in process)
qb = pd.merge(qb1,qb2, how='inner', on=['player'])
qb.set_index('player',inplace=True)
rb = pd.merge(rb1,rb2, how='inner', on=['player'])
rb.set_index('player',inplace=True)
wr = pd.merge(wr1,wr2, how='inner', on=['player'])
wr.set_index('player',inplace=True)
te = pd.merge(te1,te2, how='inner', on=['player'])
te.set_index('player',inplace=True)
k = pd.merge(k1,k2, how='inner', on=['player'])
k.set_index('player',inplace=True)
dst = pd.merge(dst1,dst2, how='inner', on=['team'])
dst.set_index('team',inplace=True)

#get list of projected points per position
vqb = qb.loc[:,'points']
vrb = rb.loc[:,'points']
vwr = wr.loc[:,'points']
vte = te.loc[:,'points']
vk = k.loc[:,'points']
vdst = dst.loc[:,'points']

#get list of salaries per position
wqb = qb.loc[:,'FDsalary']
wrb = rb.loc[:,'FDsalary']
wwr = wr.loc[:,'FDsalary']
wte = te.loc[:,'FDsalary']
wk = k.loc[:,'FDsalary']
wdst = dst.loc[:,'FDsalary']

#setting salary limit
limit = 60000

#get names for binary constraints
qbs = list(sorted(vqb.keys()))
rbs = list(sorted(vrb.keys()))
wrs = list(sorted(vwr.keys()))
tes = list(sorted(vte.keys()))
ks = list(sorted(vk.keys()))
dsts = list(sorted(vdst.keys()))

# Create model
m = ConcreteModel()

# setting up our variables
m.QB = Var(qbs, domain=Binary)
m.RB = Var(rbs, domain=Binary)
m.WR = Var(wrs, domain=Binary)
m.TE = Var(tes, domain=Binary)
m.K = Var(ks, domain=Binary)
m.DST = Var(dsts, domain=Binary)

# Objective function
m.value = Objective(expr=(sum(vqb[i]*m.QB[i] for i in qbs)+sum(vrb[i]*m.RB[i] for i in rbs)+sum(vwr[i]*m.WR[i] for i in wrs)+sum(vte[i]*m.TE[i] for i in tes)+sum(vk[i]*m.K[i] for i in ks)+sum(vdst[i]*m.DST[i] for i in dsts)), sense=maximize)

# Constraints
m.weight = Constraint(expr=(sum(wqb[i]*m.QB[i] for i in qbs)+sum(wrb[i]*m.RB[i] for i in rbs)+sum(wwr[i]*m.WR[i] for i in wrs)+sum(wte[i]*m.TE[i] for i in tes)+sum(wk[i]*m.K[i] for i in ks)+sum(wdst[i]*m.DST[i] for i in dsts)) <= limit)
m.qbl = Constraint(expr=sum(m.QB[i] for i in qbs) == 1)
m.rbl = Constraint(expr=sum(m.RB[i] for i in rbs) == 2)
m.wrl = Constraint(expr=sum(m.WR[i] for i in wrs) == 3)
m.tel = Constraint(expr=sum(m.TE[i] for i in tes) == 1)
m.kl = Constraint(expr=sum(m.K[i] for i in ks) == 1)
m.dstl = Constraint(expr=sum(m.DST[i] for i in dsts) == 1)



# Optimize
solver = SolverFactory('glpk')
status = solver.solve(m)

# Print the status of the solved LP
print("Status = %s" % status.solver.termination_condition)

#salary tracker
salary = 0

#setting up dataframe to store results
c=1
final = pd.DataFrame(index=['QB','RB1','RB2','WR1','WR2','WR3','TE','K','DST'],columns=['player','proj','salary',])

# Printing lineup results with proj and salary and storing relevant results into dataframe
for i in qbs:
    if value(m.QB[i])==1:
        print(" %s: Proj = %f; Salary = %s" % (m.QB[i], vqb[i], wqb[i]))
        salary=salary + wqb[i]
        final.iloc[0,0]=i
        final.iloc[0,1]=vqb[i]
        final.iloc[0,2]=wqb[i]
for i in rbs:
    if value(m.RB[i])==1:
        print(" %s: Proj = %f; Salary = %s" % (m.RB[i], vrb[i], wrb[i]))
        salary=salary + wrb[i]
        final.iloc[c,0]=i
        final.iloc[c,1]=vrb[i]
        final.iloc[c,2]=wrb[i]
        c=c+1
for i in wrs:
    if value(m.WR[i])==1:
        print(" %s: Proj = %f; Salary = %s" % (m.WR[i], vwr[i], wwr[i]))
        salary=salary + wwr[i]
        final.iloc[c,0]=i
        final.iloc[c,1]=vwr[i]
        final.iloc[c,2]=wwr[i]
        c=c+1
for i in tes:
    if value(m.TE[i])==1:
        print(" %s: Proj = %f; Salary = %s" % (m.TE[i], vte[i], wte[i]))
        salary=salary + wte[i]
        final.iloc[c,0]=i
        final.iloc[c,1]=vte[i]
        final.iloc[c,2]=wte[i]
        c=c+1
for i in ks:
    if value(m.K[i])==1:
        print("  %s: Proj = %f; Salary = %s" % (m.K[i], vk[i], wk[i]))
        salary=salary + wk[i]
        final.iloc[c,0]=i
        final.iloc[c,1]=vk[i]
        final.iloc[c,2]=wk[i]
        c=c+1
for i in dsts:
    if value(m.DST[i])==1:
        print("%s: Proj = %f; Salary = %s" % (m.DST[i], vdst[i], wdst[i]))
        salary=salary + wdst[i]
        final.iloc[c,0]=i
        final.iloc[c,1]=vdst[i]
        final.iloc[c,2]=wdst[i]
        c=c+1

#dataframe with actual results
backtest=pd.merge(final,bt,how='inner', on='player')
actual=backtest['FDpoints'].sum()

# Print the projected score and salary spent
print("Total Salary Spent = %f" % value(salary))
print("Projected Score = %f" % value(m.value))
print("Actual Score = %f" % value(actual))
print("Average Score to Beat = %f" % value(scoretobeat))

