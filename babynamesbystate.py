import sys
import numpy as np
import pandas as pd
import sklearn.cluster as cl
import sklearn.metrics as met
from collections import defaultdict

def normalize(floatlist):
    return (floatlist - np.mean(floatlist))/np.std(floatlist)

def main():
    #delete the global lines after program is complete. It's only there so I can use the command line.
    global states 
    global names
    global total_births
    global namesUSA
    global boynamesUSA
    global girlnamesUSA
    global girlsbystate
    global boysbystate
    global statevectorsboy
    global statevectorsgirl
    global kmeans_model_boy
    global kmeans_model_girl
    global labels
    global score
    global sorted_labels_boy
    global sorted_labels_girl
    global dfForR
    
    #numclusters = int(sys.argv[1])
    
    states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
    
    #forms a dataframe 'names' containing state-by-state names data for a given year
    pieces = [] 
    for state in states:
        frame = pd.read_csv(state+'.txt', names = ['state', 'sex', 'year', 'name', 'births'])
        frame = frame[frame.year == 2013]
        pieces.append(frame)
    names = pd.concat(pieces, ignore_index=True)
    names = names.drop('year', 1)
        
    #forms summary dataframe 'total_births' containing number of births in each state, by sex
    total_births = names.pivot_table('births', rows = 'state', cols = 'sex', aggfunc=sum)
    
    #forms dataframes 'boynamesUSA', 'girlnamesUSA' containing top 200 names nationwide 
    namesUSA = pd.read_csv('usa2013.txt', names=['name','sex','births'])
    boynamesUSA = namesUSA[namesUSA.sex == 'M']
    boynamesUSA = boynamesUSA.reset_index()
    girlnamesUSA = namesUSA[namesUSA.sex == 'F']
    girlnamesUSA = girlnamesUSA.reset_index(drop = True)
    boynamesUSA = boynamesUSA[boynamesUSA.index<200].drop('sex',1)
    girlnamesUSA = girlnamesUSA[girlnamesUSA.index<200].drop('sex',1)
    
    # creates 'girlsbystate' and 'boysbystate' dataframes
    # adds column 'freq' to dataframes that is 'births' if it's a common name, 0 otherwise 
    girlsbystate = names[names.sex == 'F'].copy()
    girlsbystate['freq'] = girlsbystate.births
    for idx in girlsbystate.index:
        if girlsbystate.name.ix[idx] not in list(girlnamesUSA.name):
            girlsbystate.freq.ix[idx] = 0
    boysbystate = names[names.sex == 'M'].copy()
    boysbystate['freq'] = boysbystate.births
    for idx in boysbystate.index:
        if boysbystate.name.ix[idx] not in list(boynamesUSA.name):
            boysbystate.freq.ix[idx] = 0
    
    #restricts 'girlsbystate' and 'boysbystate' to only the top 200 nationwide names
    #note that some names may be missing from some states. For ex, Alaska only has 151 of the top 200 girls names.
    girlsbystate = girlsbystate[girlsbystate.freq > 0].drop('births',1).drop('sex',1)
    girlsbystate = girlsbystate.reset_index(drop = True)
    boysbystate = boysbystate[boysbystate.freq > 0].drop('births',1).drop('sex',1)
    boysbystate = boysbystate.reset_index(drop = True)
    
    #adds a column to 'girlsbystate' and 'boysbystate' that is the pct of births of that sex in each state that got that name
    for idx in girlsbystate.index:
        girlsbystate.ix[girlsbystate.index == idx, 'pct'] = float(girlsbystate.freq.ix[idx]) / total_births.ix[girlsbystate.state.ix[idx],'F']
    for idx in boysbystate.index:
        boysbystate.ix[boysbystate.index == idx, 'pct'] = float(boysbystate.freq.ix[idx]) / total_births.ix[boysbystate.state.ix[idx],'M']
    
    #fill in names that are missing from each state
    for usstate in states:
        missingnames = list(set(girlnamesUSA.name)-set(girlsbystate[girlsbystate.state == usstate].name))
        for missname in missingnames:
            row = pd.DataFrame([dict(state=usstate, name=missname, freq=0, pct=0.0), ])
            girlsbystate = girlsbystate.append(row, ignore_index=True)
    girlsbystate = girlsbystate[['name','state','freq','pct']]
    for usstate in states:
        missingnames = list(set(boynamesUSA.name)-set(boysbystate[boysbystate.state == usstate].name))
        for missname in missingnames:
            row = pd.DataFrame([dict(state=usstate, name=missname, freq=0, pct=0.0), ])
            boysbystate = boysbystate.append(row, ignore_index=True)
    boysbystate = boysbystate[['name','state','freq','pct']]       
    
    #sort by state, then name, so that order of numbers in any vectors we form will be the same in each state
    girlsbystate = girlsbystate.sort(['state','name']).reset_index(drop = True)
    boysbystate = boysbystate.sort(['state','name']).reset_index(drop = True)
    
    #add column of z-scores
    for kidname in list(girlnamesUSA.name):
        girlsbystate.ix[girlsbystate.name == kidname, 'zscore'] = normalize(girlsbystate[girlsbystate.name == kidname].pct)
    for kidname in list(boynamesUSA.name):
        boysbystate.ix[boysbystate.name == kidname, 'zscore'] = normalize(boysbystate[boysbystate.name == kidname].pct)    
        
    #make a map (dict) from each state to a vector in R^200 that is its z-scores
    statevectorsboy = {usstate: list(boysbystate[boysbystate.state == usstate].zscore) for usstate in states}
    statevectorsgirl = {usstate: list(girlsbystate[girlsbystate.state == usstate].zscore) for usstate in states}

    pieces = []
    for numclusters in range(2,11):
        print "Clustering into", numclusters, "clusters..."
        #run KMeans clustering on the state vectors
        kmeans_model_boy = cl.KMeans(n_clusters=numclusters, n_init=20).fit(np.array(statevectorsboy.values()))
        labels_boy = kmeans_model_boy.labels_
        score_boy = met.silhouette_score(np.array(statevectorsboy.values()), labels_boy, metric='euclidean')
        kmeans_model_girl = cl.KMeans(n_clusters=numclusters, n_init=20).fit(np.array(statevectorsgirl.values()))
        labels_girl = kmeans_model_girl.labels_
        score_girl = met.silhouette_score(np.array(statevectorsgirl.values()), labels_girl, metric='euclidean')
    
        #sorts the labels and prints them to the screen
        sorted_labels_boy = sorted(zip(np.array(statevectorsboy.keys()),labels_boy), key=lambda tup: tup[0])
        boy_categories = {}
        for i, j in sorted_labels_boy:
            boy_categories.setdefault(j, []).append(i)
        sorted_labels_girl = sorted(zip(np.array(statevectorsgirl.keys()),labels_girl), key=lambda tup: tup[0])
        girl_categories = {}
        for i, j in sorted_labels_girl:
            girl_categories.setdefault(j, []).append(i)
        print 'boy categories: ', boy_categories
        print 'boy clustering score: ', score_boy
        print 'girl categories: ', girl_categories
        print 'girl clustering score: ', score_girl, '\n'
        
        dfPiece = pd.DataFrame(map(lambda x: ('M',numclusters)+x, sorted_labels_boy), columns = ['sex','numclusters','state', 'color'])
        pieces.append(dfPiece)
        dfPiece = pd.DataFrame(map(lambda x: ('F',numclusters)+x, sorted_labels_girl), columns = ['sex','numclusters','state', 'color'])
        pieces.append(dfPiece)
    
    dfForR = pd.concat(pieces, ignore_index=True)
    dfForR.to_csv('dfForR.csv')
        
#standard boilerplate
if __name__ == '__main__':
    main()
