# Program Metrics dashboard

Created an interactive dashboard to provide deep insights on overall program metrics which includes ticketing process, productivity, quality, agent performance and and overall program status.
The graphs are interactive and clicking on the graphs or points on graphs will dynamically filter other related graphs and tables.
The data is dummy data and its read from excel sheets and loaded to pandas dataframe.

### Video

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/video.gif)
### Screenshots

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture1.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture2.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture3.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture4.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture5.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture6.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture7.png)

![App Screenshot](https://github.com/bharathngowda/Program_Metrics_Dashboard/blob/main/Screenshots/Picture8.png)

### Programming Language and Packages
The dashboard is built using Python 3.6+.

The main Packages used are -

- Plotly - to make the charts
- Dash - to build the interactive dashboard
- Pandas & Numpy - to process the data and convert it into a format that is required by the dashboard.


### Installation
To run this notebook interactively:

 1. Download this repository in a zip file by clicking on this [link](https://github.com/bharathngowda/Program_Metrics_Dashboard/archive/refs/heads/main.zip) or execute this from the terminal: 
 `git clone https://github.com/bharathngowda/Program_Metrics_Dashboard.git`

 2. Install virtualenv.

 3. Navigate to the directory where you unzipped or cloned the repo and create a virtual environment with virtualenv env.

 4. Activate the environment with source env/bin/activate

 5. Install the required dependencies with pip install -r requirements.txt.

 6. Execute `python Program_Metrics_Dashboard.py` from the command line or terminal.

 7. Copy the link http://localhost:8888 from command prompt and paste in browser and the dashboard will load.

 8. When you're done deactivate the virtual environment with deactivate.`.
