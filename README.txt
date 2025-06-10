Project title: 2024 S2 R&D Adaptive Network Management
Client: 2degrees

# ------------ How to operate command line (Mac) -----------------------
# To run backend
#   Open terminal on Visual Studio Code and go to Backend Branch
#   Install venv to ranking folder:  python3 -m venv venv 
#   Activate virtual machine: "source venv/bin/activate"
#   Install indenpendencies from requirements.txt: "pip install -r requirements.txt"
#    (To update requirements.txt: pip freeze > requirements.txt)
#   Run api server: "uvicorn api_main:app --reload"
# To run frontend
#   Open terminal on Visual Studio Code and go to Frontend Branch
#   Run: "php -S localhost:8080"

--------------------File Structure----------------------
2024-S2-R-D-ADAPTIVE-NETWORK-MANAGEMENT/
├── Backend/
│   ├── __pycache__/
│   ├── data/
│   ├── logs/
│   ├── output/
│   ├── static/
│   ├── tower_analysis/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── coverage_analysis.py
│   │   ├── file_utils.py
│   │   ├── logger_utils.py
│   │   ├── preprocessing.py
│   │   └── ranking.py
│   ├── venv/
│   ├── api_main.py
│   └── requirements.txt
├── Frontend/
│   ├── index.php
│   └── styles.css
├── .gitignore
└── README.txt
