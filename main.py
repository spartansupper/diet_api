#
# Main for fastapi
#
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # ajax is calling OPTIONS method for CORS or something...
import json

import sys
from lib.libraries import load_data,evaluate,InitPopulation

from os import path
import pickle
import pandas
import numpy
from deap import base, creator, tools, algorithms
from cvxopt import matrix, solvers # an alternative linear programming library
solvers.options['show_progress'] = False
solvers.options['glpk'] = {'msg_lev' : 'GLP_MSG_OFF'}

import random
import multiprocessing

# Load data from nutrient database
(nutrients,reqd,limt,food_desc,nutrient_desc)=load_data()
NT_DIM=nutrients.shape[0]

cluster_food_count=0

if path.exists('clust.pkl'):
    clust=pickle.load( open( "clust.pkl", "rb" ) )
    print( '[*] Found pickle file with %d clusters and %d foods' % (clust.max()+1,len(clust)) )
    Nclust=clust.max()+1
    cluster_food_count=len(clust)
else:
    print('broken')

app = FastAPI()

# TODO: getting the CORS stuff wrong could be dangerous
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DEAP portion to set up the genetic algorithm
#   creator.create(), toolbox initialization and pool initialization have to be outside of the generate function.
#
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin) # an individual comprises a list (of food IDs)

toolbox = base.Toolbox()         
pool = multiprocessing.Pool()
toolbox.register("map", pool.map)

@app.get("/")
def generate_diet(N_FOODS=6):
       
    # Attribute generator 
    toolbox.register("attr_foodid", random.randrange, NT_DIM)
    # Structure initializers
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
        toolbox.attr_foodid, N_FOODS)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=NT_DIM, indpb=0.1)
    #toolbox.register("select", tools.selBest, k=3)
    toolbox.register("select", tools.selTournament, tournsize=10)
    toolbox.register("evaluate", evaluate, nut=nutrients,limt=limt,reqd=reqd)

    # used to make a seed population (only) ; per: https://deap.readthedocs.io/en/master/tutorials/basic/part1.html?highlight=seeding#seeding-a-population
    #toolbox.register("population_guess", InitPopulation, list, creator.Individual, N_FOODS,Nclust,Nseed,limt,reqd,nutrients )

    # Run GA
    pop = toolbox.population(n=300) # totally random initial population
    
    stats = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats.register("min", numpy.min)
    stats.register("median", numpy.median)
    stats.register("max", numpy.max)

    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=2, 
                                       stats=stats, verbose=True)    
       
    # We now have a "best" diet. re-run LP once more on best diet to get amounts
    best=tools.selBest(pop, k=1)
    best=best[0]
    evaluate(best, nut=nutrients,limt=limt,reqd=reqd)
    nt=nutrients.iloc[best,:]
    c = matrix(numpy.repeat(1.0,nt.shape[0]))
    np_G= numpy.concatenate(
                            (   nt.transpose().values, 
                                nt.transpose().multiply(-1.0).values,
                                numpy.diag(numpy.repeat(-1,nt.shape[0])) 
                            )
                           ).astype(numpy.double) 
    G = matrix( np_G ) 
    h = matrix( numpy.concatenate( (
                    limt.values, 
                    reqd.multiply(-1.0).values, 
                    numpy.repeat(0.0,nt.shape[0])
                ) ).astype(numpy.double) )    
    o = solvers.lp(c, G, h, solver='glpk')
    food_amounts=numpy.array(o['x'])[:,0]

    final_foods= [ best[i] for i in range(len(food_amounts)) if food_amounts[i]>1e-6 ] # select those with non-trivial amounts
    final_food_amounts= food_amounts[ food_amounts>1e-6 ]

    nt=nutrients.iloc[final_foods,:]
    df1= nt.join(food_desc).loc[:,['long_desc']] #food_desc.iloc[final_foods]
    df2=pandas.DataFrame(final_food_amounts*100,index=df1.index,columns=["amount"])
    df3=pandas.DataFrame(nt.loc[:,208].values * df2.loc[:,'amount'].values/100 ,columns=['calories'], index=df2.index)
    diet_table=df1.join(df2).join(df3)
    raw_json=diet_table.to_json(orient='records') # convert to "records" json (how tabulator.js expects it
    
    return( json.loads(raw_json) ) # re-read the json and return a dict of the json contents for FastAPI to deal with
    
if __name__ == "__main__":
    print('hello')
