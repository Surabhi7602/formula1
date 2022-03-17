#cd Desktop/formula1
#pipenv shell
#streamlit run main.py


import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

dataCircuit = pd.read_csv("f1db_csv/circuits.csv")
dataCircuit.rename(columns = {'name':'circuitName'}, inplace = True)
dataResults = pd.read_csv("f1db_csv/results.csv")
dataRaces = pd.read_csv("f1db_csv/races.csv")
dataDrivers = pd.read_csv("f1db_csv/drivers.csv")
dataLapTimes = pd.read_csv("f1db_csv/lap_times.csv")
dataQuali = pd.read_csv("f1db_csv/qualifying.csv")
dataConstructorResults = pd.read_csv("f1db_csv/constructor_results.csv")
dataDriverStandings = pd.read_csv("f1db_csv/driver_standings.csv")
dataConstructorStandings = pd.read_csv("f1db_csv/constructor_standings.csv")
dataPitStops = pd.read_csv("f1db_csv/pit_stops.csv")
dataConstructors = pd.read_csv("f1db_csv/constructors.csv")


st.markdown(""" <style> 
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        </style> """, unsafe_allow_html=True)

padding = 0
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)





dataDriverResults = pd.merge(dataDrivers, dataResults, on="driverId")
dataDriverResultsRaces = pd.merge(dataDriverResults, dataRaces, on="raceId")

dataDriverResultsRaces = dataDriverResultsRaces[dataDriverResultsRaces.year > 2009]
dataDriverResultsRaces["driver"] = dataDriverResultsRaces["forename"] + " " + dataDriverResultsRaces["surname"]
dataAveragePoints = dataDriverResultsRaces[['driver', 'points']].groupby("driver").mean().reset_index()
dataCountPoints = dataDriverResultsRaces[['driver', 'raceId']].groupby("driver").count().reset_index()
dataCountPoints = dataCountPoints[dataCountPoints.raceId > 100]
datafinalAverage = pd.merge(dataAveragePoints, dataCountPoints, on="driver")

avgfig = px.scatter(datafinalAverage, x = "raceId", y = "points", size="points", hover_name="driver", hover_data={'raceId':False, 'points':True})
#st.plotly_chart(avgfig)
#st.dataframe(datafinalAverage)

dataTotalPoints = dataDriverResultsRaces.groupby("driver").sum()

st.header("FORMULA 1 DASHBOARD 🏎️")
st.subheader("""
# Pole to Podium Conversion Rates
""")
dfpole = (dataResults[dataResults.grid == 1 ]).sort_values(by=['driverId'])
#dataframe of drivers starting at pole, replaced all finish positions below 3 by 0, and all podium finishes by 1
dfpole['position'] = dfpole['position'].replace(['4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','\\N'],'0')
dfpole['position'] = dfpole['position'].replace(['3','2'],'1')
dfpole.position = pd.to_numeric(dfpole.position, errors='coerce').fillna(0).astype(np.int64)

#finds total no of poles, podiums from pole, division gives conversion rate, I've calculated for drivers with >3 poles, >= 50% conversion rate
dfpole = dfpole[['driverId','grid','position']]

dfgrids = dfpole.groupby(["driverId"]).grid.sum().reset_index()
dfwins = dfpole.groupby(["driverId"]).position.sum().reset_index()
dfconcatenated=pd.merge(dfgrids, dfwins, on="driverId")
dfconcatenated = dfconcatenated[dfconcatenated.grid>3]
dfconcatenated.rename(columns = {'grid':'Total number of pole positions', 'position':'Total number of podium finishes from pole'}, inplace = True)
dfdrivers = dataDrivers[['driverId','forename','surname']]
dfconversion=pd.merge(dfdrivers, dfconcatenated, on="driverId")
dfconversion["driver"] = dfconversion["forename"] + " " + dfconversion["surname"]

def conversioncalc(row):
    return ((row['Total number of podium finishes from pole']/row['Total number of pole positions'])*100)

dfconversion["convrate"] = dfconversion.apply ((lambda row: conversioncalc(row)), axis=1)
dfconversion = dfconversion[dfconversion.convrate>=50]
dfconversion = dfconversion.sort_values(by=['convrate'], ascending=False)
del dfconversion["forename"]
del dfconversion["surname"]
dfconversion .rename(columns = {'convrate':'Pole to Podium conversion rate'}, inplace = True)
dfconversion
#conversionfig = px.scatter(dfconversion, x = "Total number of pole positions", y = "Total number of podium finishes from pole", size="Pole to Podium conversion rate", hover_name="driver",hover_data={'driverId':False, 'Total number of podium finishes from pole':False, "Total number of pole positions": False ,"Pole to Podium conversion rate":True   })
#st.plotly_chart(conversionfig)

conversionfig = px.scatter(dfconversion, x = "Total number of pole positions", y = "Pole to Podium conversion rate", size="Total number of podium finishes from pole", hover_name="driver",hover_data={'driverId':False, "Total number of pole positions": True,'Total number of podium finishes from pole':True ,"Pole to Podium conversion rate":True   })
st.plotly_chart(conversionfig)

st.sidebar.markdown('## SELECT CONSTRUCTORS YOU WISH TO COMPARE')
#multiselect for teams
teamoptions = st.sidebar.multiselect('Choose teams to compare points by year', dataConstructors.name.tolist(),  default='Mercedes')

#creating dataframe that groups points by year and team
dfConstructors = pd.merge(dataConstructorResults,dataConstructors, on="constructorId")
dfConstructors = pd.merge(dfConstructors, dataRaces, on="raceId")
dfConstructors['year'] = pd.DatetimeIndex(dfConstructors['date']).year
dfConstructors= dfConstructors[['raceId', 'year', 'constructorId', 'name_x',  'points']]
pointsBySeason = dfConstructors.groupby(['year','constructorId']).agg({'points': 'sum'}).reset_index()
pointsBySeason = pd.merge(pointsBySeason, dataConstructors, on="constructorId")
pointsBySeason= pointsBySeason[['year', 'constructorId', 'name',  'points']]

#returns dataframe with selected teams, line chart for points by season
points = pointsBySeason[pointsBySeason['name'].isin(teamoptions)]
fig = px.line(points, x="year", y="points", color='name')

#slider
fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1Y",
                     step="year",
                     stepmode="backward"),
                dict(count=5,
                     label="5Y",
                     step="year",
                     stepmode="backward"),
                dict(count=20,
                     label="20Y",
                     step="year",
                     stepmode="backward"),
                dict(label="Overall",step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)

st.plotly_chart(fig)


st.subheader("""
# Head-to-Head Stats
"""
    )

dataDrivers["Name"] = dataDrivers["forename"] + " " + dataDrivers["surname"]

dfDriver = pd.merge(dataDriverStandings, dataRaces, on="raceId")
dfDriver = pd.merge(dfDriver, dataDrivers, on="driverId")
dfDriver['year'] = pd.DatetimeIndex(dfDriver['date']).year
#df for driver points per season
dfDriverPtsByYear = dfDriver[['raceId', 'year','Name','points', 'position']]
dfDriverPtsByYear = dfDriverPtsByYear.groupby(['year','Name'])
maximums = dfDriverPtsByYear.max()
dfDriverPtsByYear = maximums.reset_index()
st.sidebar.markdown('## SELECT DRIVERS YOU WISH TO COMPARE')
driveroptions = st.sidebar.multiselect('Choose drivers to compare their performances', dfDriverPtsByYear.Name.unique().tolist(),  default="Lewis Hamilton")

#returns dataframe with selected drivers, line chart for points by season
drpoints = dfDriverPtsByYear[dfDriverPtsByYear['Name'].isin(driveroptions)]
fig2 = px.line(drpoints, x="year", y="points",  color='Name')

st.plotly_chart(fig2)


#stacked bar graph for wins in a year
dfWins = dfDriver[[ 'year','Name','wins']]
dfWins = dfWins.groupby(['year','Name'])
maximums = dfWins.max()
dfWins = maximums.reset_index()
drwins= dfWins[dfWins['Name'].isin(driveroptions)]

fig3 = px.bar(drwins, x="year", color="Name",
             y='wins',
             barmode='group',
             height=600
            )
st.plotly_chart(fig3)

# plotting the correlation coefficient to measure the similarity between the starting grid and the final result to gauge competitiveness
#group by raceid, find corr between grid and position, merge with year data, find avg corr per year
#pip install statsmodels
dfPositions = pd.merge(dataResults, dataRaces, on="raceId")
dfPositions = dfPositions[['raceId', 'year', 'grid', 'position']]
dfPositions['position'] = dfPositions['position'].replace(['\\N'],'0')
dfPositions['position']=dfPositions['position'].astype(str).astype(int)
dfPositions.set_index('raceId')
dfraceid= dfPositions[['raceId', 'year']].drop_duplicates().set_index('raceId')
dfcorr1=dfPositions.groupby('raceId')[['grid','position']].corr().iloc[0::2,-1].reset_index()
dfcorr1.set_index('raceId')
dfcorr2=dfcorr1.join(dfraceid)
dfcorr2['year']= dfcorr2['year'].replace(np.nan, 2009)
dfcorr2= dfcorr2[["year","position"]]
dfcorr2 = dfcorr2.groupby("year").mean().reset_index()
dfcorr2.rename(columns = {'position':'Correlation Coefficient'}, inplace = True)
figcorr = px.scatter(dfcorr2, x="year", y="Correlation Coefficient",trendline="ols")

st.subheader("""
# Spearman's rank correlation coefficient between starting grid and final race position 
""")
st.plotly_chart(figcorr)



#i need to fix this part
#df for average finish position per season
dfDriverPosition = dfDriver[['year', 'Name', 'position']]
#dfDriverPosition
dfDriverPosition = dfDriverPtsByYear.groupby(['year','Name'])['position'].mean().reset_index()
dfDriverPosition.rename(columns = {'position':'Mean finish position'}, inplace = True)
#dfDriverPosition
drposition = dfDriverPosition[dfDriverPosition['Name'].isin(driveroptions)]
fig3 = px.line(drposition, x="year", y="Mean finish position",  color='Name')
#st.plotly_chart(fig3)


#work for teams that do well in various circuits
circuitoption = st.selectbox('Choose circuits to see teams performance in those circuits', dataCircuit.circuitName.tolist())
dataRaceResults = pd.merge(dataRaces, dataResults, on="raceId")
dataRaceResults = dataRaceResults[['raceId', 'circuitId', 'name', 'points', 'constructorId']]
dataRaceResults = dataRaceResults.groupby(['circuitId', 'constructorId']).agg({'points': 'mean'}).reset_index()
dataCircuits = pd.merge(dataRaceResults, dataConstructors, on="constructorId")
dataCircuits = dataCircuits[['circuitId', 'constructorId', 'name', 'points']]
dataCircuits = pd.merge(dataCircuits, dataCircuit, on="circuitId") 
dataCircuits = dataCircuits[['circuitId', 'constructorId', 'name', 'points', 'circuitName']]
dataFinalCircuit=dataCircuits[dataCircuits['circuitName']==circuitoption][['constructorId','name','points']]
circuitFig=px.pie(dataFinalCircuit, names=dataFinalCircuit['name'], values=dataFinalCircuit['points'], title='Average Points teams have earned in various circuits')
st.plotly_chart(circuitFig)

st.dataframe(dataCircuits)

