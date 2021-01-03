# diet_api

This is a FastAPI implementation of optimal diet generation. It is designed to be deployed to a cloud environment to serve json diet tables to a website.

The code is parallelized to use multiple CPU cores.

The default optimization is to find <= 6 foods that meet all adult male nutritional requirements and minimize calories. Much more customization is possible but not implemented.

## Requirements

The file `requirements.txt` contains the full library requirements, but in brief:

- DEAP for genetic algorithms
- cvxopt for linear programming (plus the glpk solver)
- multiprocessing to do parallel execution
- sqlite to handle the USDA nutritional data
- FastAPI to build the API endpoint
- uvicorn to serve the API

### Environment

```
sudo apt-get install libglpk-dev
conda create -n dietapi python=3.7
conda activate dietapi
pip install fastapi uvicorn gunicorn uvloop httptools deap pandas numpy
CVXOPT_BUILD_GLPK=1 pip install cvxopt
```
