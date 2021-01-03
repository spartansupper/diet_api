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

## GCP app engine

The below works, but I don't think multiprocessing is possible within GCP. I also suspect that *libglpk-dev* will be unavailable in production.

I think I can change this to use docker to ensure that *libglpk* is available, but parallel execution is still an issue.

- https://console.cloud.google.com/
- create new project (eg, dietapi-x8yy)
- activate *cloud shell*
  - `git clone https://github.com/spartansupper/diet_api.git`
  - `sudo apt-get install libglpk-dev`
  - `virtualenv env`
  - `source env/bin/activate`
  - `cd diet-api`
  - `pip install -r requirements.txt`
  - `gcloud app create` (pick a region like *us-east-1*)
  - `gcloud app deploy app.yaml`
  
