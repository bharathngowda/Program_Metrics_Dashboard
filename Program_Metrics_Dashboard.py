#!/usr/bin/env python
# coding: utf-8

# In[19]:



# Importing required Libraries/Modules

import pandas as pd
import numpy as np
import datetime
from datetime import timezone
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output,State
from dash.exceptions import PreventUpdate
import dash_table
import re
import json
from plotly.subplots import make_subplots
from business_duration import businessDuration
import calendar


# In[20]:


# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
app.config['suppress_callback_exceptions'] = True


# In[21]:


def No_Data_Available():
    fig=go.Figure()
    fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',
                      font=dict(color='white'),annotations=[{"text": "No Data Available","xref": "paper","yref": "paper",
                        "showarrow": False,"font": {"size": 28}}])
    fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
    fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False,visible=False)
    return fig


# In[22]:


# Reading Data to DataFrame

Tickets=pd.read_excel('Dummy_Data\Dummy_Tickets.xlsx')
FTE=pd.read_excel('Dummy_Data\Dummy_FTE.xlsx',sheet_name=1)
Current_FTE=pd.read_excel('Dummy_Data\Dummy_FTE.xlsx',sheet_name=0)
GPH=pd.read_excel('Dummy_Data\Dummy_GPH.xlsx')
PKT=pd.read_excel('Dummy_Data\Dummy_PKT.xlsx')
Escalations=pd.read_excel('Dummy_Data\Dummy_Escalations & Unplanned Leaves.xlsx',sheet_name=0).fillna(0)
Unplanned_Leaves=pd.read_excel('Dummy_Data\Dummy_Escalations & Unplanned Leaves.xlsx',sheet_name=1).fillna(0)

biz_open_time=datetime.time(0,0,0)
biz_close_time=datetime.time(23,59,59)
unit_hour='hour'


PKT=PKT.drop('Enterprise ID',axis=1)
PKT=PKT.groupby(['Region','Name']).mean()
PKT = PKT.stack().astype(str).reset_index(level=2)
PKT.columns = ['Date', 'PKT (%)']
PKT.reset_index(inplace=True)
PKT['PKT (%)']=PKT['PKT (%)'].astype(str).astype(float)

Escalations=Escalations.drop('Enterprise ID',axis=1)
Escalations=Escalations.groupby(['Region','Name']).mean()
Escalations = Escalations.stack().astype(str).reset_index(level=2)
Escalations.columns = ['Date', 'Escalations (Nos.)']
Escalations.reset_index(inplace=True)
Escalations['Escalations (Nos.)']=Escalations['Escalations (Nos.)'].astype(str).astype(float)

Unplanned_Leaves=Unplanned_Leaves.drop('Enterprise ID',axis=1)
Unplanned_Leaves=Unplanned_Leaves.groupby(['Region','Name']).mean()
Unplanned_Leaves = Unplanned_Leaves.stack().astype(str).reset_index(level=2)
Unplanned_Leaves.columns = ['Date', 'Unplanned_Leaves (Nos.)']
Unplanned_Leaves.reset_index(inplace=True)
Unplanned_Leaves['Unplanned_Leaves (Nos.)']=Unplanned_Leaves['Unplanned_Leaves (Nos.)'].astype(str).astype(float)

Metrics=['ManualAck_TAT (%)','RCA_TAT (%)','Internal_Quality_Score (%)','PKT (%)','Capacity_Utilization (%)',
         'Efficiency (%)','Utilization (%)','No_Shows (Nos.)','Escalations (Nos.)',
         'Unplanned_Leaves (Nos.)']

pd.options.mode.chained_assignment = None
Open_Incidents=Tickets.loc[Tickets.State=='Work in progress']
Open_Incidents.reset_index(drop=True,inplace=True)
Open_Incidents['currentTime']=pd.to_datetime(datetime.datetime.now(timezone.utc).strftime("%m-%d-%Y %H:%M:%S"))
Open_Incidents['TAT (Hours)']=Open_Incidents['Urgency'].apply(lambda x: 6 if x=='0 - Critical' 
                                                              else 48 if (x=='2 - Medium') | (x=='1 - High') else 72)
Open_Incidents['RCA Miss TAT (Hours)']=Open_Incidents[['Created','Reported date','currentTime']].apply(lambda x:np.round(businessDuration(startdate=x['Created'],
                                                                                              enddate=x['currentTime'],
                                                                                              starttime=biz_open_time,
                                                                                              endtime=biz_close_time,
                                                                                              unit=unit_hour),2) if pd.isnull(x['Reported date']) else np.nan,axis=1)
Open_Incidents['Time Inqueue (Hours)']=Open_Incidents[['Created','currentTime']].apply(lambda x: round(((x['currentTime']-x['Created']).total_seconds())/3600,2),axis=1)
Open_Incidents['RCA Provided TAT (Hours)']=Open_Incidents[['Created','Reported date','TAT (Hours)']].apply(lambda x:np.round(x['TAT (Hours)']-( np.round(businessDuration(startdate=x['Created'],
                                                                                              enddate=x['Reported date'],
                                                                                              starttime=biz_open_time,
                                                                                              endtime=biz_close_time,
                                                                                              unit=unit_hour),2)),2) if pd.isnull(x['Reported date'])==False else np.nan,axis=1)
Open_Incidents['Reported_date_captured']=Open_Incidents['Reported date'].apply(lambda x: 'Yes' if pd.notnull(x) else 'No')
Open_Incidents['Ageing']=Open_Incidents.Created.map(lambda x:(datetime.datetime.today()-x).days)

Closed_Incidents=Tickets.loc[(Tickets.State!='Work in progress') & (Tickets.State!='Cancelled') & (Tickets.State!='Open')]
Closed_Incidents['Resolved_Date']=Closed_Incidents['Resolved Date'].dt.date
Closed_Incidents['Resolved_Week']=Closed_Incidents['Resolved Date'].dt.strftime('WK %U-%Y')
Closed_Incidents['Resolved_Month']=Closed_Incidents['Resolved Date'].dt.strftime('%b-%Y')
Closed_Incidents['Resolved_Quarter']=Closed_Incidents['Resolved_Month'].apply(lambda x: 'Q1' if re.split('-',x)[0] in ['Sep','Oct','Nov'] 
                                                                                 else 'Q2' if re.split('-',x)[0] in ['Dec','Jan','Feb']
                                                                                 else 'Q3' if re.split('-',x)[0] in ['Mar','Apr','May']
                                                                                 else 'Q4')
Closed_Incidents['Resolved_Year']=Closed_Incidents['Resolved Date'].dt.year

table_cols=['Number','Created', 'Reported date', 'State','Urgency', 'Requested for','Location', 'Assignment group', 'Assigned to',
 'Category', 'Type','Contact type', 'Short description','Owner']

closed_table_cols=['Number', 'Created', 'Reported date','Resolved Date','Urgency', 'Requested for','Location','Category', 
                   'Type','Short description','Owner', 'Score %', 'Manual_Ack_Date', 'RCA_Date','Avg_Time_For_RCA (Hrs.)', 
                   'RCA_TAT (%)', 'Avg_Time_For_Closing (Hrs.)','Avg_Time_For_ManualAck (Hrs.)','ManualAck_TAT (%)']

GPH_table_cols=['Date', 'User Name', 'Shift', 'Shift Schedule', 'Work Hours','Login Threshold (min)', 'Grace Period (min)', 
                'Is Workday?', 'Log In','Log Out', 'Total Time', 'Attendance Status','Tardiness','Overtime', 
                'Night Differential', 'Productive Time (hrs)','Shrinkage Time (hrs)', 'Break Time (hrs)']

SQF_table_cols=['Number','Created', 'Reported date','Resolved Date','Urgency', 'Requested for','Location','Category','Type','Owner','Audit_Date', 'Score %', 'Audited By']


# In[23]:



# Styling

page_bg={'backgroundColor':'#FF6700'}
performance_tab_bg={'backgroundColor':'#000000'}
black_bg={'backgroundColor':'#000000'}
heading_text_style={'textAlign':'center','color':'white','fontWeight': 'bold'}
region_color={'Global':'blue','Region 1':'orange','Region 3':'yellow','Region 2':'green'}

dropdown_style={
    'margin-left':'5px',
    'background-color': 'white',
    'border':'none',
    'width':'100%',
    "fontColor": "black",
    "font-color": "black",
    "font-size": "medium",
    
}

datepicker_style={
    'background-color': 'white',
    'border':'none',
    "fontColor": "black",
    "font-color": "black",
    "font-size": "medium",
    'height':'25px'
    
}

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'backgroundColor': 'black',
    'border':'none',
    'padding': '6px',
    'fontWeight': 'bold',
    'color': 'white',
}

tab_selected_style = {
    'borderTop': '4px solid #0000FF',
    'borderBottom': '1px solid black',
    'borderLeft': '1px solid black',
    'borderRight': '1px solid black',
    'backgroundColor': '#1F1F1F',
    'color': 'white',
    'padding': '6px'
}

data_table_header_style={'backgroundColor': 'rgb(30, 30, 30)'}
data_table_cell_style={'backgroundColor': 'rgb(50, 50, 50)','color': 'white','fontWeight': 'bold','font_family': 'cursive',
                       'font_size': '14px','text_align': 'center'}
tickets_table_cell_style={'backgroundColor': 'rgb(50, 50, 50)','color': 'white','fontWeight': 'bold','font_family': 'cursive',
                       'font_size': '14px','text_align': 'left','whiteSpace': 'normal','height': 'auto'}
data_table_data_style=[{'if': {'filter_query': '{ManualAck_TAT (%)} > 95','column_id': 'ManualAck_TAT (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{ManualAck_TAT (%)} = 95','column_id': 'ManualAck_TAT (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{ManualAck_TAT (%)} < 95','column_id': 'ManualAck_TAT (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{RCA_TAT (%)} > 95','column_id': 'RCA_TAT (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{RCA_TAT (%)} = 95','column_id': 'RCA_TAT (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{RCA_TAT (%)} < 95','column_id': 'RCA_TAT (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Internal_Quality_Score (%)} > 95','column_id': 'Internal_Quality_Score (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Internal_Quality_Score (%)} = 95','column_id': 'Internal_Quality_Score (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{Internal_Quality_Score (%)} < 95','column_id': 'Internal_Quality_Score (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{PKT (%)} > 90','column_id': 'PKT (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{PKT (%)} = 90','column_id': 'PKT (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{PKT (%)} < 90','column_id': 'PKT (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Capacity_Utilization (%)} > 85 && {Capacity_Utilization (%)} < 95','column_id': 'Capacity_Utilization (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Capacity_Utilization (%)} = 85','column_id': 'Capacity_Utilization (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{Capacity_Utilization (%)} < 85 || {Capacity_Utilization (%)} > 95','column_id': 'Capacity_Utilization (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Efficiency (%)} > 95 && {Efficiency (%)} <= 100','column_id': 'Efficiency (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Efficiency (%)} = 95','column_id': 'Efficiency (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{Efficiency (%)} < 95 || {Efficiency (%)} > 100','column_id': 'Efficiency (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Utilization (%)} > 90','column_id': 'Utilization (%)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Utilization (%)} = 95','column_id': 'Utilization (%)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{Utilization (%)} < 90','column_id': 'Utilization (%)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Ideas_Submitted (Nos.)} > 1','column_id': 'Ideas_Submitted (Nos.)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Ideas_Submitted (Nos.)} = 1','column_id': 'Ideas_Submitted (Nos.)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{Ideas_Submitted (Nos.)} < 1','column_id': 'Ideas_Submitted (Nos.)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{No_Shows (Nos.)} < 2','column_id': 'No_Shows (Nos.)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{No_Shows (Nos.)} = 2','column_id': 'No_Shows (Nos.)'},
                        'backgroundColor': '#FFFF00','color': 'white'},
                      {'if': {'filter_query': '{No_Shows (Nos.)} > 2','column_id': 'No_Shows (Nos.)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Escalations (Nos.)} = 0','column_id': 'Escalations (Nos.)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Escalations (Nos.)} > 0','column_id': 'Escalations (Nos.)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{Unplanned_Leaves (Nos.)} = 0','column_id': 'Unplanned_Leaves (Nos.)'},
                        'backgroundColor': '#00FF00','color': 'white'},
                      {'if': {'filter_query': '{Unplanned_Leaves (Nos.)} > 0','column_id': 'Unplanned_Leaves (Nos.)'},
                        'backgroundColor': '#FF0000','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('ManualAck_TAT (%)'),'column_id': 'ManualAck_TAT (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Escalations (Nos.)'),'column_id': 'Escalations (Nos.)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('RCA_TAT (%)'),'column_id': 'RCA_TAT (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Internal_Quality_Score (%)'),'column_id': 'Internal_Quality_Score (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('PKT (%)'),'column_id': 'PKT (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Capacity_Utilization (%)'),'column_id': 'Capacity_Utilization (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Efficiency (%)'),'column_id': 'Efficiency (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Utilization (%)'),'column_id': 'Utilization (%)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Ideas_Submitted (Nos.)'),'column_id': 'Ideas_Submitted (Nos.)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('No_Shows (Nos.)'),'column_id': 'No_Shows (Nos.)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
                      {'if': {'filter_query': '{{{}}} is blank'.format('Unplanned_Leaves (Nos.)'),'column_id': 'Unplanned_Leaves (Nos.)'},
                        'backgroundColor': 'rgb(50, 50, 50)','color': 'white'}]


# In[24]:



#Layout

app.layout=html.Div([
    html.Div([
        html.H1(children='Program Metrics Dashboard',style=heading_text_style)
    ],className='row',style=page_bg),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='Region',
                options=[
                {'label':'Global','value':'Global'},
                {'label':'Region 1','value':'Region 1'},
                {'label':'Region 3','value':'Region 3'},
                {'label':'Region 2','value':'Region 2'}
                ],
                value='Global',
                clearable=False,
                multi=False,
                placeholder='Select Region',
                style=dropdown_style)],className='two columns'),
        html.Div([
            dcc.DatePickerRange(
                id='DateRange',
                min_date_allowed=datetime.datetime(2018,6,19),
                max_date_allowed=datetime.datetime.today().date(),
                initial_visible_month=datetime.datetime.today().date(),
                style=datepicker_style)],className='three columns'),
        html.Div(
            dcc.Dropdown(id='Quick_Filter',
                options=[
                {'label':'Week to Date','value':'Week to Date'},
                {'label':'Previous Week','value':'Previous Week'},
                {'label':'Last 7 Days','value':'Last 7 Days'},
                {'label':'Month to Date','value':'Month to Date'},
                {'label':'Previous Month','value':'Previous Month'},
                {'label':'Last 30 Days','value':'Last 30 Days'},
                {'label':'Year to Date','value':'Year to Date'},
                {'label':'Previous Year','value':'Previous Year'},
                {'label':'All Time','value':'All Time'}],
                value='Last 30 Days',
                clearable=False,
                multi=False,
                placeholder='Select Date Range',
                style=dropdown_style),className='two columns')],className='row',style=page_bg),
    html.Div([html.Br()],className='row',style=page_bg),
    html.Div(
        id="Tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="Apps Tab",
                value="tab1",
                className="custom-tabs",
                style={'borderTop': '4px solid #FF6600'},
                children=[
                    dcc.Tab(
                        id="Tickets Tab",
                        label="Incident Summary",
                        value="tab1",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                            dcc.Tabs(
                                id='Sub Tickets Tab',
                                value="tab2-1",
                                className="custom-tabs",
                                style=tabs_styles,
                                children=[
                                    dcc.Tab(
                                        id="Count Tab",
                                        label="Total Incidents Summary",
                                        value="tab2-1",
                                        className="custom-tab",
                                        selected_className="custom-tab--selected",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                        children=[html.Div(html.Div(dcc.Dropdown(id='Tickets_Span',options=[
                                            {'label':'Daily','value':'Created_Date'},{'label':'Weekly','value':'Created_Week'},
                                            {'label':'Monthly','value':'Created_Month'},{'label':'Quaterly','value':'Created_Quarter'},
                                            {'label':'Yearly','value':'Created_Year'}],value='Created_Date',clearable=False,multi=False,
                                            style=dropdown_style),className='two columns',style=black_bg),className='row',style=black_bg),
                                            html.Div(dcc.Graph(id='Count_Graph'),className='row',style=black_bg),
                                            html.Div([html.Div(dcc.Graph(id='Category_Graph_'),className='six columns',style=black_bg),
                                                      html.Div(dcc.Graph(id='Type_Graph'),className='six columns',style=black_bg)],
                                                      className='row',style=black_bg),
                                            html.Div(id='Tickets_Table',className='row',style=black_bg),
                                            html.Div(id='Ticket_Details_Table',className='row',style=black_bg), 
                                            html.Div(dcc.Store(id='Count_DF',storage_type='memory'),
                                                      className='row',style=black_bg),
                                            html.Div(dcc.Store(id='Details_DF',storage_type='memory'),
                                                      className='row',style=black_bg)]),
                                    dcc.Tab(
                                        id="Open Tab",
                                        label="Open Incident Summary",
                                        value="tab2-2",
                                        className="custom-tab",
                                        selected_className="custom-tab--selected",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                        children=[html.Div(html.H6('Total Open Tickets = '+str(Open_Incidents.shape[0]),
                                                                    style={'textAlign':'left','color':'white','fontWeight': 'bold'}),
                                                           className='row',style=black_bg),
                                                  html.Div([
                                                        html.Div(dcc.Graph(id='Tickets_by_Aging_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Weekly_Ticket_Count_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Ticket_by_Priority_Graph'),className='four columns')
                                                  ],className='row',style=black_bg),        
                                                  html.Div([     
                                                        html.Div(dcc.Graph(id='Ticket_Count_by_Region_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Ticket_Count_by_Shift_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Reported_Date_Captured_Graph'),className='four columns')
                                                  ],className='row',style=black_bg),
                                                  html.Div([
                                                        html.Div(dcc.Graph(id='Tickets_by_Category_Graph'),className='six columns'),
                                                        html.Div(dcc.Graph(id='Ticket_by_Type_Graph'),className='six columns')
                                                  ],className='row',style=black_bg),
                                                  html.Div([
                                                        html.Div(dcc.Graph(id='Ticket_by_Contact_Type_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Tickets_by_Assignment_Group_Graph'),className='four columns'),
                                                        html.Div(dcc.Graph(id='Ticket_by_Assigned_To_Graph'),className='four columns')
                                                  ],className='row',style=black_bg),
                                                  html.Div(id='Open_Tickets_Table',className='row',style=black_bg),
                                                  html.Div(id='Open_Ticket_Details_Table',className='row',style=black_bg), 
                                                  html.Div(dcc.Store(id='Open_DF',storage_type='memory'),
                                                          className='row',style=black_bg)]),
                                    dcc.Tab(
                                        id="Closed Tab",
                                        label="Closed Incident Summary",
                                        value="tab2-3",
                                        className="custom-tab",
                                        selected_className="custom-tab--selected",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                        children=[html.Div(html.Div(dcc.Dropdown(id='Closed_Tickets_Span',options=[
                                            {'label':'Daily','value':'Resolved_Date'},{'label':'Weekly','value':'Resolved_Week'},
                                            {'label':'Monthly','value':'Resolved_Month'},{'label':'Quaterly','value':'Resolved_Quarter'},
                                            {'label':'Yearly','value':'Resolved_Year'}],value='Resolved_Date',clearable=False,multi=False,
                                            style=dropdown_style),className='two columns',style=black_bg),className='row',style=black_bg),
                                            html.Div([
                                                html.Div(dcc.Graph(id='Closed_Tickets_Manual_Ack_Trend_Graph'),className='six columns'),
                                                html.Div(dcc.Graph(id='Closed_Tickets_RCA_Trend_Graph'),className='six columns')
                                                ],className='row',style=black_bg),
                                            html.Div([     
                                                html.Div(dcc.Graph(id='Closed_Tickets_Priority_Graph'),className='four columns'),
                                                html.Div(dcc.Graph(id='Closed_Tickets_Location_Graph'),className='four columns'),
                                                html.Div(dcc.Graph(id='Closed_Tickets_Shift_Graph'),className='four columns')
                                                ],className='row',style=black_bg),
                                            html.Div([
                                                html.Div(dcc.Graph(id='Closed_Tickets_Category_Graph'),className='six columns'),
                                                html.Div(dcc.Graph(id='Closed_Tickets_Type_Graph'),className='six columns')
                                                ],className='row',style=black_bg),
                                            html.Div([     
                                                html.Div(dcc.Graph(id='Closed_Tickets_Contact_Type_Graph'),className='four columns'),
                                                html.Div(dcc.Graph(id='Closed_Tickets_Weekly_Count_Graph'),className='eight columns')
                                                ],className='row',style=black_bg),
                                            html.Div(id='Closed_Tickets_Table',className='row',style=black_bg),
                                            html.Div(id='Closed_Ticket_Details_Table',className='row',style=black_bg), 
                                            html.Div(dcc.Store(id='Closed_DF',storage_type='memory'),className='row',style=black_bg)
                                ]
                            )])
                        ]
                    ),
                    dcc.Tab(
                        id="SQF Tab",
                        label="Standard Quality Framework",
                        value="tab3",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                            html.Div(html.Div(dcc.Dropdown(id='SQF_Span',options=[
                            {'label':'Daily','value':'Audit_Date'},{'label':'Weekly','value':'Audit_Week'},
                            {'label':'Monthly','value':'Audit_Month'},{'label':'Quaterly','value':'Audit_Quarter'},
                            {'label':'Yearly','value':'Audit_Year'}],value='Audit_Date',clearable=False,multi=False,
                            style=dropdown_style),className='two columns',style=black_bg),className='row',style=black_bg),
                            html.Div([html.Div(dcc.Graph(id='SQF_Graph'),className='six columns',style=black_bg),
                                     html.Div(dcc.Graph(id='SQF_Count_Graph'),className='six columns',style=black_bg)
                                     ],className='row',style=black_bg),
                            html.Div([html.Div(dcc.Graph(id='SQF_Category_Graph_'),className='six columns',style=black_bg),
                                      html.Div(dcc.Graph(id='SQF_Type_Graph_'),className='six columns',style=black_bg)],
                                      className='row',style=black_bg),
                            html.Div(id='SQF_Audit_Table',className='row',style=black_bg), 
                            html.Div(dcc.Store(id='SQF_DF',storage_type='memory'),className='row',style=black_bg),
                            html.Div(html.Pre(id='new'),className='row',style=black_bg)
                        ]),
                    dcc.Tab(
                        id="GPH Tab",
                        label="Global Productivity Hub",
                        value="tab4",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                            html.Div(html.Div(dcc.Dropdown(id='GPH_Span',options=[
                                            {'label':'Daily','value':'Date'},{'label':'Weekly','value':'Week'},
                                            {'label':'Monthly','value':'Month'},{'label':'Quaterly','value':'Quarter'},
                                            {'label':'Yearly','value':'Year'}],value='Date',clearable=False,multi=False,
                                            style=dropdown_style),className='two columns',style=black_bg),className='row',style=black_bg),
                            html.Div([
                                html.Div(dcc.Graph(id='GPH_Efficiency_Graph'),className='six columns',style=black_bg),
                                html.Div(dcc.Graph(id='GPH_Utilization_Graph'),className='six columns',style=black_bg)
                            ],className='row',style=black_bg),
                            html.Div([
                                html.Div(dcc.Graph(id='GPH_Capacity_Utilization_Graph'),className='six columns',style=black_bg),
                                html.Div(dcc.Graph(id='GPH_Leave_Graph'),className='six columns',style=black_bg)
                            ],className='row',style=black_bg),
                            html.Div(id='GPH_Details_Table',className='row',style=black_bg)
                        ]),
                    dcc.Tab(
                        id="PKT Tab",
                        label="Process Knowledge Test",
                        value="tab5",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[dcc.Graph(id='PKT_Graph')]),
                    dcc.Tab(
                        id="Performance Tab",
                        label="Performance",
                        value="tab6",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                           dcc.Tabs(
                               id='Sub Performance Tab',
                               value='tab6-1',
                               className='custom-tab',
                               style=tabs_styles,
                               children=[
                                   dcc.Tab(
                                       id='Agent Performance Tab',
                                       label='Agent Performance',
                                       value='tab6-1',
                                       className='custom-tab',
                                       selected_className="custom-tab--selected",
                                       style=tab_style,
                                       selected_style=tab_selected_style,
                                       children=[
                                           html.Div([html.Br()],className='row',style=performance_tab_bg),
                                           html.Div([
                                               html.Div([
                                                   dcc.Dropdown(
                                                       id='Agent_Name',
                                                       value='All',
                                                       multi=False,
                                                       clearable=False,
                                                       placeholder='Select Agent',
                                                       style=dropdown_style)],
                                                       className='three columns'),
                                               html.Div([
                                                   dcc.Dropdown(
                                                       id='Metrics',
                                                       options=[{'label':x,'value':x} for x in Metrics],
                                                       value=Metrics,
                                                       multi=True,
                                                       placeholder='Select Metrics',
                                                       style=dropdown_style)],
                                                       className='six columns')],
                                               className='row',style=performance_tab_bg
                                           ),
                                           html.Div([html.Br()],className='row',style=performance_tab_bg),
                                           html.Div([dash_table.DataTable(
                                               id='AgentPerformance',
                                               export_format='xlsx',
                                               export_headers='display',
                                               style_table={'maxWidth': '1600px', 'overflowY': 'auto'},
                                               style_header=data_table_header_style,
                                               style_cell=data_table_cell_style,
                                               style_cell_conditional=[{'if': {'column_id': c},
                                                                        'textAlign': 'left'} for c in ['Agent Name','Date']],
                                               style_data_conditional=data_table_data_style,fixed_columns={'headers':True,'data':2}
                                           )],className='row',style=performance_tab_bg),
                                           html.Div([dcc.Graph(id='KPI')],className='row',style=performance_tab_bg)
                                       ]
                                   ),
                                   dcc.Tab(
                                       id='Stats Tab',
                                        label='Program Stats',
                                        value='tab6-2',
                                        className='custom-tab',
                                        selected_className="custom-tab--selected",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                        children=[
                                            html.Div(html.H6('Tickets Stats',
                                                             style={'textAlign':'left','color':'white','fontWeight': 'bold'}
                                                            ),style=page_bg),
                                            html.Div([
                                                html.Div([dash_table.DataTable(id='Tickets_Stats_Table',
                                                                               style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                                                               export_format='xlsx',
                                                                               export_headers='display',
                                                                               row_selectable='single',                                                                                       style_cell=data_table_cell_style,
                                                                               style_cell_conditional=[{'if':{'column_id':'Parameter'}
                                                                                                        ,'textAlign':'left'}]
                                                                              )],className='three columns',style=black_bg),
                                                html.Div([dcc.Graph(id='Tickets_Stats_Graph')],className='nine columns',style=black_bg)
                                                        ],className='row',style=black_bg),
                                            html.Div(html.H6('Tickets by Category',
                                                             style={'textAlign':'left','color':'white','fontWeight': 'bold'}),
                                                     style=page_bg),
                                            html.Div(html.Br(),style=black_bg),
                                            html.Div([
                                                html.Div(dcc.Dropdown(id='Category_Options',multi=False,
                                                                      style=dropdown_style,placeholder='Select Category'),
                                                         className='three columns',style=black_bg),
                                                html.Div(dcc.Dropdown(id='Type_Options',multi=False,style=dropdown_style,
                                                                      placeholder='Select Type'),
                                                         className='five columns',style=black_bg)
                                                   ],className='row',style=black_bg),
                                            html.Div(dcc.Graph(id='Category_Graph'),className='row',style=black_bg),
                                            html.Div(html.H6('Gloal Productivity Hub Stats',
                                                             style={'textAlign':'left','color':'white','fontWeight': 'bold'}),
                                                     style=page_bg),
                                            html.Div([
                                                html.Div([dash_table.DataTable(id='GPH_Stats_Table', 
                                                                               style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                                                               export_format='xlsx',
                                                                               export_headers='display',
                                                                               row_selectable='single',
                                                                               style_cell=data_table_cell_style,
                                                                               style_cell_conditional=[{'if':{'column_id':'Parameter'},
                                                                                                        'textAlign':'left'}])
                                                        ],className='three columns',style=black_bg),
                                                        html.Div([dcc.Graph(id='GPH_Stats_Graph')],className='nine columns',style=black_bg)
                                                    ],className='row',style=black_bg),
                                            html.Div(html.H6('Process Knowledge Test Stats',
                                                            style={'textAlign':'left','color':'white','fontWeight': 'bold'})),
                                            html.Div(dcc.Graph(id='PKT_Graph_2'),style=black_bg)
                                            ]),
                               ]
                           )
                        ]
                    )
                ],
            )
        ],
    ),
],className='row',style=black_bg)


# In[25]:


# Seting Date Range

def span_collection(span_type):
    if span_type=='Previous Week':
        start_date=datetime.date.today()-datetime.timedelta(days=datetime.date.today().weekday()+1,weeks=1)
        end_date=start_date+datetime.timedelta(days=6)
    elif span_type=='Week to Date':
        start_date=datetime.date.today()-datetime.timedelta(days=datetime.date.today().weekday()+1)
        end_date=datetime.date.today()
    elif span_type=='Previous Month':
        start_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month-1,1)
        end_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month-1,
                               calendar.monthrange(datetime.datetime.today().year,datetime.datetime.today().month-1)[1])
    elif span_type=='Month to Date':
        start_date=datetime.date(datetime.datetime.today().year,datetime.datetime.today().month,1)
        end_date=datetime.date.today()
    elif span_type=='Year to Date':
        start_date=datetime.date(datetime.datetime.today().year,1,1)
        end_date=datetime.date.today()
    elif span_type=='Previous Year':
        start_date=datetime.date(datetime.datetime.today().year-1,1,1)
        end_date=datetime.date(datetime.datetime.today().year-1,12,31)
    elif span_type=='All Time':
        start_date=datetime.datetime(2018,6,19)
        end_date=datetime.datetime.today().date()
    elif span_type=='Last 7 Days':
        start_date=datetime.date.today()-datetime.timedelta(days=6)
        end_date=datetime.date.today()
    elif span_type=='Last 30 Days':
        start_date=datetime.date.today()-datetime.timedelta(days=30)
        end_date=datetime.date.today()
    return start_date,end_date
        
@app.callback(
[Output('DateRange','start_date'),
Output('DateRange','end_date')],
[Input('Quick_Filter','value')])

def Update_Date_Range(value):
    start_date=span_collection(value)[0]
    end_date=span_collection(value)[1]
    return start_date,end_date


# In[26]:



#Total_Incidents_Summary

@app.callback(
[Output('Count_Graph','figure'),
Output('Count_DF','data')],
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Tickets_Span','value')])

def Update_Count_Graph(Region,Start_Date,End_Date,span_selected):
            
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    if Region=='Global':
        Tickets_Pivot=Tickets.loc[(Tickets.Created >=Start_Date) & (Tickets.Created<=End_Date)]
    else:
        Tickets_Pivot=Tickets.loc[(Tickets.Created >=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.Shift==Region)]
    if Tickets_Pivot.empty==False:
        tickets_count=pd.DataFrame(data=Tickets_Pivot[span_selected].value_counts().values,
                           index=Tickets_Pivot[span_selected].value_counts().index,
             columns=['count']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)
        data=Tickets_Pivot.to_dict('records')
        if span_selected =='Month':
            tickets_count['index']=pd.to_datetime(tickets_count['Month'])
            tickets_count.sort_values('index',ignore_index=True,inplace=True) 
        fig=go.Figure(go.Scatter(x=tickets_count[re.sub('_',' ',span_selected)],y=tickets_count['count'],name=Region,
                                marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=8,color='white'),
                          tickfont=dict(color='white',size=10),tickmode='array' if (tickets_count.columns[0]=='Created Date') and ((End_Date-Start_Date).days>7) else 'linear'
                )
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=8),title_text='Count',rangemode='tozero',
                         title_font=dict(size=10,color='white'))
        fig.update_layout(title='Tickets Count Trend by '+re.sub('_',' ',span_selected),height=350,plot_bgcolor='black',paper_bgcolor='black',
                      font=dict(color='white'),title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        dummy=pd.DataFrame()
        data=dummy.to_dict('records')
        fig=No_Data_Available()
    return [fig,data]
    

@app.callback(
Output('Category_Graph_','figure'),
[Input('Count_Graph','relayoutData'),
Input('Count_DF','data'),
Input('Region','value')])

def Category_Graph(relayoutData,data,Region):
    
    category_df=pd.DataFrame(data)
    if category_df.empty==False:
        key1='xaxis.range[0]'
        if relayoutData is not None and key1 in relayoutData.keys():
            startdate=re.split('\s',relayoutData['xaxis.range[0]'])[0]
            enddate=re.split('\s',relayoutData['xaxis.range[1]'])[0]
            new_df=category_df.loc[(category_df.Created>=startdate) & (category_df.Created<=enddate)]
            category_count=pd.DataFrame(data=new_df['Category'].value_counts().values,index=new_df['Category'].value_counts().index,
                             columns=['count']).reset_index().sort_values('index',ignore_index=True)
        else:
            category_count=pd.DataFrame(data=category_df['Category'].value_counts().values,
                                        index=category_df['Category'].value_counts().index,
             columns=['count']).reset_index().sort_values('index',ignore_index=True)
            
        category_count['category']=category_count['index'].apply(lambda x: re.sub('\s','<br>',x))
        fig=go.Figure(go.Bar(x=category_count['category'],y=category_count['count'],name=Region,
                                marker_color=region_color[Region],showlegend=True))
        fig.update_xaxes(gridcolor='#121212',title_text='Category',title_font=dict(size=8,color='white'),
                    tickfont=dict(color='white',size=10)
                )
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=8),title_text='Count',rangemode='tozero',
                         title_font=dict(size=10,color='white'))
        fig.update_layout(title='Tickets Count Trend by Category',height=350,plot_bgcolor='black',paper_bgcolor='black',
                      font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        fig=No_Data_Available()
    return fig

@app.callback(
Output('Type_Graph','figure'),
[Input('Count_Graph','relayoutData'),
Input('Category_Graph_','selectedData'),
Input('Count_DF','data'),
Input('Region','value')])

def Type_Graph(relayoutData,selectedData,data,Region):
    
    type_df=pd.DataFrame(data)
    if type_df.empty==False:
        key1='xaxis.range[0]'
        if relayoutData is not None and key1 in relayoutData.keys():
            startdate=re.split('\s',relayoutData['xaxis.range[0]'])[0]
            enddate=re.split('\s',relayoutData['xaxis.range[1]'])[0]
            new_df=type_df.loc[(type_df.Created>=startdate) & (type_df.Created<=enddate)]
            if selectedData is not None:
                category=re.sub('<br>',' ',selectedData['points'][0]['x'])
                type_count=pd.DataFrame(data=new_df.loc[new_df.Category==category,'Type'].value_counts().values,
                                index=new_df.loc[new_df.Category==category,'Type'].value_counts().index,
                                columns=['count']).reset_index().sort_values('index',ignore_index=True)
            else:
                type_count=pd.DataFrame(data=new_df['Type'].value_counts().values,
                                        index=new_df['Type'].value_counts().index,
                         columns=['count']).reset_index().sort_values('index',ignore_index=True)
            type_count['type']=type_count['index'].apply(lambda x: re.sub('\s','<br>',x))
        else:
            if selectedData is not None:
                category=re.sub('<br>',' ',selectedData['points'][0]['x'])
                type_count=pd.DataFrame(data=type_df.loc[type_df.Category==category,'Type'].value_counts().values,
                                index=type_df.loc[type_df.Category==category,'Type'].value_counts().index,
                                columns=['count']).reset_index().sort_values('index',ignore_index=True)
            else:
                type_count=pd.DataFrame(data=type_df['Type'].value_counts().values,
                                        index=type_df['Type'].value_counts().index,
                         columns=['count']).reset_index().sort_values('index',ignore_index=True)
            type_count['type']=type_count['index'].apply(lambda x: re.sub('\s','<br>',x))
            
        fig=go.Figure(go.Bar(x=type_count['type'],y=type_count['count'],name=Region,
                                marker_color=region_color[Region],showlegend=True))
        fig.update_xaxes(gridcolor='#121212',title_text='Type',title_font=dict(size=8,color='white'),
                    tickfont=dict(color='white',size=10)
                )
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=8),title_text='Count',rangemode='tozero',
                         title_font=dict(size=10,color='white'))
        fig.update_layout(title='Tickets Count Trend by Type',height=350,plot_bgcolor='black',paper_bgcolor='black',
                      font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        fig=No_Data_Available()
    return fig


@app.callback(
[Output('Tickets_Table','children'),
Output('Details_DF','data')],
[Input('Count_Graph','relayoutData'),
 Input('Category_Graph_','selectedData'),
 Input('Type_Graph','selectedData'),
Input('Count_DF','data')])

def update_tickets_table(relayoutData,category_selected,type_selected,data):
    tickets_df=pd.DataFrame(data)
    if tickets_df.empty==False:
        key1='xaxis.range[0]'
        if relayoutData is not None and key1 in relayoutData.keys():
            startdate=re.split('\s',relayoutData['xaxis.range[0]'])[0]
            enddate=re.split('\s',relayoutData['xaxis.range[1]'])[0]
            new_df=tickets_df.loc[(tickets_df.Created>=startdate) & (tickets_df.Created<=enddate)]
            if category_selected is not None and type_selected is None:
                category=re.sub('<br>',' ',category_selected['points'][0]['x'])
                table_data=new_df.loc[new_df.Category==category].to_dict('records')
            elif category_selected is None and type_selected is not None:
                type_=re.sub('<br>',' ',type_selected['points'][0]['x'])
                table_data=new_df.loc[new_df.Type==type_].to_dict('records')
            elif category_selected is not None and type_selected is not None:
                type_=re.sub('<br>',' ',type_selected['points'][0]['x'])
                category=re.sub('<br>',' ',category_selected['points'][0]['x'])
                table_data=new_df.loc[(new_df.Type==type_) & (new_df.Category==category)].to_dict('records')
                           
            else:
                table_data=new_df.to_dict('records')
        else:
            if category_selected is not None and type_selected is None:
                category=re.sub('<br>',' ',category_selected['points'][0]['x'])
                table_data=tickets_df.loc[tickets_df.Category==category].to_dict('records')
            elif category_selected is None and type_selected is not None:
                type_=re.sub('<br>',' ',type_selected['points'][0]['x'])
                table_data=tickets_df.loc[tickets_df.Type==type_].to_dict('records')
            elif category_selected is not None and type_selected is not None:
                type_=re.sub('<br>',' ',type_selected['points'][0]['x'])
                category=re.sub('<br>',' ',category_selected['points'][0]['x'])
                table_data=tickets_df.loc[(tickets_df.Type==type_) & (tickets_df.Category==category)].to_dict('records')
            else:
                table_data=[]
        if len(table_data)>0:
            table=dash_table.DataTable(id='Tickets_Info_Table',style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                               export_format='xlsx',export_headers='display',filter_action="native",
                               sort_action="native",sort_mode="multi",style_cell=tickets_table_cell_style,
                               columns=[{'name':i,'id':i} for i in table_cols],row_selectable='single',
                               style_table={'maxWidth': '1600px', 'overflowY': 'auto'},data=table_data,page_size=10)
            data=table_data
        else:
            table=html.Br()
            data=[]
    else:
        table=html.Br()
        data=[]

    return [html.Div(table,className='row',style=black_bg),data]


# In[27]:


# Tickets_by_Aging

@app.callback(
Output('Tickets_by_Aging_Graph','figure'),
[Input('Region','value')])

def Update_Ageing(Region):
    
    if Open_Incidents.empty==False:      
        fig=go.Figure(go.Histogram(x=Open_Incidents['Ageing'],xbins={'start':0,'end':Open_Incidents['Ageing'].max(),
                                                                     'size':int(np.round(Open_Incidents['Ageing'].max()/4))}
                                   ,name=Region,marker_color=region_color[Region],showlegend=True))

        fig.update_xaxes(gridcolor='#121212',title_text='Aging Bucket',title_font=dict(size=14,color='white'),
                        tickfont=dict(color='white',size=12))
        fig.update_yaxes(gridcolor='#121212',title_text='Days',title_font=dict(size=14,color='white'),
                        tickfont=dict(color='white',size=12))
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Aging',
                          font=dict(color='white'),title_font_color='white',clickmode='event+select'
                         ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        fig=No_Data_Available()


    return fig


# In[28]:


# Weekly_Ticket_Count

@app.callback(
Output('Weekly_Ticket_Count_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Weekly_Ticket_Count(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,AG,CT,AT):
    
    if Week_Num is None:
        if Open_Incidents.empty==False:
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()

            wk_group=pd.DataFrame(data=temp_df_['Created_Week'].value_counts().values,
                 index=temp_df_['Created_Week'].value_counts().index,
                 columns=['count']).rename_axis('Week Number').reset_index().sort_values('Week Number',ignore_index=True)
            if wk_group.empty==False and Week_Num is None:

                fig=go.Figure(go.Bar(x=wk_group['Week Number'],y=wk_group['count'],name=Region,marker_color=region_color[Region],
                        showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Week Number',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array',tickvals=[x for x in wk_group['Week Number']])
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(wk_group.max()['count']/2,0) if wk_group.max()['count']<10 else round(wk_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Week',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()

    else:
        raise PreventUpdate
    return fig


# In[29]:


# Ticket_Count_by_Region

@app.callback(
Output('Ticket_Count_by_Region_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_Count_by_Region(Region,Ageing,Week_Num,Priority,Shift,RDC,Category,Type,Location,AG,CT,AT):
    if Location is None:
        if Open_Incidents.empty==False:
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()

            Location_group=pd.DataFrame(data=temp_df_['Location'].value_counts().values,
                                index=temp_df_['Location'].value_counts().index,
                                columns=['count']).rename_axis('Location').reset_index().sort_values('Location',
                                                                                                     ignore_index=True)

            if Location_group.empty==False:
                fig=go.Figure(go.Bar(x=Location_group['Location'],y=Location_group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Location',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Location_group.max()['count']/2,0) if Location_group.max()['count']<10 else round(Location_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Location',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[30]:


# Ticket_Count_by_Shift

@app.callback(
Output('Ticket_Count_by_Shift_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_Count_by_Shift(Region,Ageing,Week_Num,Priority,Location,RDC,Category,Type,Shift,AG,CT,AT):
    if Shift is None:
        if Open_Incidents.empty==False:

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Region':Region if Region !='Global' else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()

            shift_group=pd.DataFrame(data=temp_df_['Shift'].value_counts().values,
                                index=temp_df_['Shift'].value_counts().index,
                                columns=['count']).rename_axis('shift').reset_index().sort_values('shift',
                                                                                                     ignore_index=True)
            if shift_group.empty==False:
                fig=go.Figure(go.Bar(x=shift_group['shift'],y=shift_group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Shift',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(shift_group.max()['count']/2,0) if shift_group.max()['count']<10 else round(shift_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Shift',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[31]:


# Ticket_by_Priority

@app.callback(
Output('Ticket_by_Priority_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Priority(Region,Ageing,Week_Num,Location,Shift,RDC,Category,Type,Priority,AG,CT,AT):
    if Priority is None:
        if Open_Incidents.empty==False:
            params={'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()

            priority_group=pd.DataFrame(data=temp_df_['Urgency'].value_counts().values,
                                index=temp_df_['Urgency'].value_counts().index,
                                columns=['count']).rename_axis('priority').reset_index().sort_values('priority',
                                                                                                     ignore_index=True)

            if priority_group.empty==False:
                fig=go.Figure(go.Bar(x=priority_group['priority'],y=priority_group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Priority',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(priority_group.max()['count']/2,0) if priority_group.max()['count']<10 else round(priority_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Priority',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()

    else:
        raise PreventUpdate
    return fig
    


# In[32]:


# Reported Date Captured

@app.callback(
Output('Reported_Date_Captured_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Reported_Date_Captured_Graph(Region,Ageing,Week_Num,Priority,Location,Shift,Category,Type,RDC,AG,CT,AT):
    if RDC is None:
        if Open_Incidents.empty==False:
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()

            Reported_date_captured_group=pd.DataFrame(data=temp_df_['Reported_date_captured'].value_counts().values,
                                index=temp_df_['Reported_date_captured'].value_counts().index,
                                columns=['count']).rename_axis('Reported_date_captured').reset_index().sort_values('Reported_date_captured',
                                                                                                     ignore_index=True)

            if Reported_date_captured_group.empty==False:
                fig=go.Figure(go.Bar(x=Reported_date_captured_group['Reported_date_captured'],y=Reported_date_captured_group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Reported_date_captured',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Reported_date_captured_group.max()['count']/2,0) if Reported_date_captured_group.max()['count']<10 else round(Reported_date_captured_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Reported Date Captured',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[33]:


# Ticket_by_Category

@app.callback(
Output('Tickets_by_Category_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Category(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Type,Category,AG,CT,AT):
    if Category is None:
        if Open_Incidents.empty==False:
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()
            Category___group=pd.DataFrame(data=temp_df_['Category'].value_counts().values,
                                index=temp_df_['Category'].value_counts().index,
                                columns=['count']).rename_axis('Category').reset_index().sort_values('Category',
                                                                                                     ignore_index=True)

            if Category___group.empty==False:
                fig=go.Figure(go.Bar(x=Category___group['Category'],y=Category___group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Category',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Category___group.max()['count']/2,0) if Category___group.max()['count']<10 else round(Category___group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Category',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig
    


# In[34]:


# Ticket_by_Type

@app.callback(
Output('Ticket_by_Type_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Type(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,AG,CT,AT):
    if Type is None:
        if Open_Incidents.empty==False:

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()
            Type___group=pd.DataFrame(data=temp_df_['Type'].value_counts().values,
                                index=temp_df_['Type'].value_counts().index,
                                columns=['count']).rename_axis('Type').reset_index().sort_values('Type',ignore_index=True)
            
            if Type___group.empty==False:
                fig=go.Figure(go.Bar(x=Type___group['Type'],y=Type___group['count'],name=Region,marker_color=region_color[Region],
                                showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Type',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Type___group.max()['count']/2,0) if Type___group.max()['count']<10 else round(Type___group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Type',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig
    


# In[35]:


# Tickets by Assignment Group

@app.callback(
Output('Tickets_by_Assignment_Group_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Assignment_Group(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,AG,CT,AT):
    if AG is None:
        if Open_Incidents.empty==False:

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()
            Assignment_group=pd.DataFrame(data=temp_df_['Assignment group'].value_counts().values,
                                index=temp_df_['Assignment group'].value_counts().index,
                                columns=['count']).rename_axis('Assignment group').reset_index().sort_values('Assignment group',ignore_index=True)
            
            if Assignment_group.empty==False:
                fig=go.Figure(go.Bar(x=Assignment_group['Assignment group'],y=Assignment_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Assignment Group',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Assignment_group.max()['count']/2,0) if Assignment_group.max()['count']<10 
                                 else round(Assignment_group.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Assignment Group',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[36]:


# Tickets by Contact Type

@app.callback(
Output('Ticket_by_Contact_Type_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Contact_Type(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,AG,CT,AT):
    if CT is None:
        if Open_Incidents.empty==False:

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None,
                'Assigned to':AT['points'][0]['x'] if AT is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()
            Contact_type=pd.DataFrame(data=temp_df_['Contact type'].value_counts().values,
                                index=temp_df_['Contact type'].value_counts().index,
                                columns=['count']).rename_axis('Contact type').reset_index().sort_values('Contact type',ignore_index=True)
            
            if Contact_type.empty==False:
                fig=go.Figure(go.Bar(x=Contact_type['Contact type'],y=Contact_type['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Contact Type',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Contact_type.max()['count']/2,0) if Contact_type.max()['count']<10 
                                 else round(Contact_type.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Contact Type',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[37]:


# Assigned to

# Tickets by Assigned to

@app.callback(
Output('Ticket_by_Assigned_To_Graph','figure'),
[Input('Region','value'),
Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Ticket_by_Assigned_to(Region,Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,AG,CT,AT):
    if AT is None:
        if Open_Incidents.empty==False:

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
                'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Assignment group':AG['points'][0]['x'] if AG is not None else None}
            
            temp_df_=Open_Incidents.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Open_Incidents.copy()
            Assigned_to=pd.DataFrame(data=temp_df_['Assigned to'].value_counts().values,
                                index=temp_df_['Assigned to'].value_counts().index,
                                columns=['count']).rename_axis('Assigned to').reset_index().sort_values('Assigned to',ignore_index=True)
            
            if Assigned_to.empty==False:
                fig=go.Figure(go.Bar(x=Assigned_to['Assigned to'],y=Assigned_to['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Assigned to',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,
                                 dtick=round(Assigned_to.max()['count']/2,0) if Assigned_to.max()['count']<10 
                                 else round(Assigned_to.max()['count']/5,0))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Assigned to',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[38]:


@app.callback(
[Output('Open_Tickets_Table','children'),
Output('Open_DF','data')],
[Input('Tickets_by_Aging_Graph','selectedData'),
Input('Weekly_Ticket_Count_Graph','selectedData'),
Input('Ticket_by_Priority_Graph','selectedData'),
Input('Ticket_Count_by_Region_Graph','selectedData'),
Input('Ticket_Count_by_Shift_Graph','selectedData'),
Input('Reported_Date_Captured_Graph','selectedData'),
Input('Tickets_by_Category_Graph','selectedData'),
Input('Ticket_by_Type_Graph','selectedData'),
Input('Region','value'),
Input('Tickets_by_Assignment_Group_Graph','selectedData'),
Input('Ticket_by_Contact_Type_Graph','selectedData'),
Input('Ticket_by_Assigned_To_Graph','selectedData')])

def Update_Open_Tickets_Table(Ageing,Week_Num,Priority,Location,Shift,RDC,Category,Type,Region,AG,CT,AT):

    params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
            'Shift':Shift['points'][0]['x'] if Shift is not None else None,
            'Location':Location['points'][0]['x'] if Location is not None else None,
            'Created_Week':Week_Num['points'][0]['x'] if Week_Num is not None else None,
            'Reported_date_captured':RDC['points'][0]['x'] if RDC is not None else None,
            'Category':Category['points'][0]['x'] if Category is not None else None,
            'Type':Type['points'][0]['x'] if Type is not None else None,
            'Ageing':Ageing['points'][0]['x'] if Ageing is not None else None,
            'Region':Region if Region != 'Global' else None,
            'Assignment group':AG['points'][0]['x'] if AG is not None else None,
            'Contact type':CT['points'][0]['x'] if CT is not None else None,
            'Assigned to':AT['points'][0]['x'] if AT is not None else None}
    
    temp_df_=Open_Incidents.copy()
    if all(i is None for i in params.values())==False:
        for i,j in zip(params.keys(),params.values()):
            if j is not None:
                temp_df_=temp_df_.loc[temp_df_[i]==j]
        data=temp_df_.to_dict('records')       
        temp_df_=temp_df_[table_cols+['Time Inqueue (Hours)','RCA Miss TAT (Hours)','RCA Provided TAT (Hours)']]
        data_table=temp_df_.to_dict('records')
        table2=dash_table.DataTable(id='Open_Tickets_Table_',style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                   export_format='xlsx',export_headers='display',filter_action='native',
                                   sort_action="native",sort_mode="multi",style_cell=tickets_table_cell_style,
                                   columns=[{'name':i,'id':i} for i in temp_df_.columns],row_selectable='single',
                                   style_table={'maxWidth': '1600px', 'overflowY': 'auto'},data=data_table)
        return [table2,data]
    else:
        return [html.Br(),[]]


# In[39]:


# Manual Acknowledgement Trend

@app.callback(
Output('Closed_Tickets_Manual_Ack_Trend_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Manual_Ack_Trend_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,CT,MAT,RCAT,Closed_Count,span_selected):
    if MAT is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]

        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else None
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}

            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
            MAT_group=pd.DataFrame(data=temp_df_.groupby(span_selected).mean()['ManualAck_TAT (%)'].values,
            index=temp_df_.groupby(span_selected).mean()['ManualAck_TAT (%)'].index,
            columns=['Avg. Percentage']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)

            if span_selected =='Monthly':
                MAT_group['index']=pd.to_datetime(MAT_group['Resolved Month'])
                MAT_group.sort_values('index',ignore_index=True,inplace=True)

            if MAT_group.empty==False:
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=MAT_group[re.sub('_',' ',span_selected)],y=[100]*len(MAT_group),mode='lines',
                                        marker_color='red',showlegend=True,name='Threshold',hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=MAT_group[re.sub('_',' ',span_selected)],y=MAT_group['Avg. Percentage'],name=Region,
                                                     marker_color=region_color[Region],showlegend=True,connectgaps=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=re.sub('_',' ',span_selected),title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (MAT_group.columns[0]=='Resolved Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20,rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Manual Acknowledgement Trend by '+re.sub('_',' ',span_selected),
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[40]:


# RCA TAT Trend

@app.callback(
Output('Closed_Tickets_RCA_Trend_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_RCA_Trend_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,CT,MAT,RCAT,Closed_Count,span_selected):
    if RCAT is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]

        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else None
            else:
                span_= MAT['points'][0]['x'] if MAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else None
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
        
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
            RCAT_group=pd.DataFrame(data=temp_df_.groupby(span_selected).mean()['RCA_TAT (%)'].values,
            index=temp_df_.groupby(span_selected).mean()['RCA_TAT (%)'].index,
            columns=['Avg. Percentage']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)

            if span_selected =='Monthly':
                RCAT_group['index']=pd.to_datetime(RCAT_group['Resolved Month'])
                RCAT_group.sort_values('index',ignore_index=True,inplace=True)

            if RCAT_group.empty==False:
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=RCAT_group[re.sub('_',' ',span_selected)],y=[100]*len(RCAT_group),mode='lines',
                                        marker_color='red',showlegend=True,name='Threshold',hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=RCAT_group[re.sub('_',' ',span_selected)],y=RCAT_group['Avg. Percentage'],name=Region,
                                                     marker_color=region_color[Region],showlegend=True,connectgaps=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=re.sub('_',' ',span_selected),title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (RCAT_group.columns[0]=='Resolved Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20,rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='RCA Trend by '+re.sub('_',' ',span_selected),
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[41]:


# Priority

@app.callback(
Output('Closed_Tickets_Priority_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Priority_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,CT,MAT,RCAT,Closed_Count,span_selected):
    if Priority is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
        
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            priority_group=pd.DataFrame(data=temp_df_['Urgency'].value_counts().values,
            index=temp_df_['Urgency'].value_counts().index,
            columns=['count']).rename_axis('priority').reset_index().sort_values('priority',ignore_index=True)

                
            if priority_group.empty==False:
                fig=go.Figure(go.Bar(x=priority_group['priority'],y=priority_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Priority',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Priority',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[42]:


# Location

@app.callback(
Output('Closed_Tickets_Location_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Location_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):
    if Location is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None 
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Shift':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
        
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            location_group=pd.DataFrame(data=temp_df_['Location'].value_counts().values,
            index=temp_df_['Location'].value_counts().index,
            columns=['count']).rename_axis('Location').reset_index().sort_values('Location',ignore_index=True)

                
            if location_group.empty==False:
                fig=go.Figure(go.Bar(x=location_group['Location'],y=location_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Location',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Location',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[43]:


# Shift

@app.callback(
Output('Closed_Tickets_Shift_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Shift_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):
    if Shift is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
            
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            shift_group=pd.DataFrame(data=temp_df_['Shift'].value_counts().values,
            index=temp_df_['Shift'].value_counts().index,
            columns=['count']).rename_axis('Shift').reset_index().sort_values('Shift',ignore_index=True)

                
            if shift_group.empty==False:
                fig=go.Figure(go.Bar(x=shift_group['Shift'],y=shift_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Shift',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Shift',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[44]:


# Category

@app.callback(
Output('Closed_Tickets_Category_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Category_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):
    if Category is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
            
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            category_group=pd.DataFrame(data=temp_df_['Category'].value_counts().values,
            index=temp_df_['Category'].value_counts().index,
            columns=['count']).rename_axis('Category').reset_index().sort_values('Category',ignore_index=True)

                
            if category_group.empty==False:
                fig=go.Figure(go.Bar(x=category_group['Category'],y=category_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Category',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Category',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[45]:


# Type

@app.callback(
Output('Closed_Tickets_Type_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Type_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):
    if Type is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
        
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            type_group=pd.DataFrame(data=temp_df_['Type'].value_counts().values,
            index=temp_df_['Type'].value_counts().index,
            columns=['count']).rename_axis('Type').reset_index().sort_values('Type',ignore_index=True)

                
            if type_group.empty==False:
                fig=go.Figure(go.Bar(x=type_group['Type'],y=type_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Type',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Type',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[46]:


# Contact Type

@app.callback(
Output('Closed_Tickets_Contact_Type_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Contact_Type_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):
    if CT is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]
    
        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
    

            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
        
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()
                
            ct_group=pd.DataFrame(data=temp_df_['Contact type'].value_counts().values,
            index=temp_df_['Contact type'].value_counts().index,
            columns=['count']).rename_axis('Contact type').reset_index().sort_values('Contact type',ignore_index=True)

                
            if ct_group.empty==False:
                fig=go.Figure(go.Bar(x=ct_group['Contact type'],y=ct_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Contact Type',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets by Contact Type',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[47]:


# Closing Count

@app.callback(
Output('Closed_Tickets_Weekly_Count_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Weekly_Count_Graph(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,CT,MAT,RCAT,Closed_Count,span_selected):
    if Closed_Count is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]

        if Closed_Incidents_.empty==False:
            
            if span_selected == 'Resolved_Date':
                span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(MAT['points'][0]['x']) if MAT is not None else None
            else:
                span_= RCAT['points'][0]['x'] if RCAT is not None else MAT['points'][0]['x'] if MAT is not None else None
    
            params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
                'Shift':Shift['points'][0]['x'] if Shift is not None else None,
                'Location':Location['points'][0]['x'] if Location is not None else None,
                'Category':Category['points'][0]['x'] if Category is not None else None,
                'Type':Type['points'][0]['x'] if Type is not None else None,
                'Region':Region if Region != 'Global' else None,
                'Contact type':CT['points'][0]['x'] if CT is not None else None,
                span_selected:span_}
            
            temp_df_=Closed_Incidents_.copy()
            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df_=temp_df_.loc[temp_df_[i]==j]
            else:
                temp_df_=Closed_Incidents_.copy()

            count_group=pd.DataFrame(data=temp_df_[span_selected].value_counts().values,
            index=temp_df_[span_selected].value_counts().index,
            columns=['count']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)    

            if span_selected =='Monthly':
                count_group['index']=pd.to_datetime(count_group['Resolved Month'])
                count_group.sort_values('index',ignore_index=True,inplace=True)    

            if count_group.empty==False:
                fig=go.Figure(go.Scatter(x=count_group[re.sub('_',' ',span_selected)],y=count_group['count'],name=Region,
                                     marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=re.sub('_',' ',span_selected),title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (count_group.columns[0]=='Resolved Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                                tickfont=dict(color='white',size=12),rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Tickets Closure Trend by '+re.sub('_',' ',span_selected),
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()

        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[48]:


@app.callback(
[Output('Closed_Tickets_Table','children'),
Output('Closed_DF','data')],
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Closed_Tickets_Priority_Graph','selectedData'),
Input('Closed_Tickets_Location_Graph','selectedData'),
Input('Closed_Tickets_Shift_Graph','selectedData'),
Input('Closed_Tickets_Category_Graph','selectedData'),
Input('Closed_Tickets_Type_Graph','selectedData'),
Input('Closed_Tickets_Manual_Ack_Trend_Graph','selectedData'),
Input('Closed_Tickets_RCA_Trend_Graph','selectedData'),
Input('Closed_Tickets_Weekly_Count_Graph','selectedData'),
Input('Closed_Tickets_Contact_Type_Graph','selectedData'),
Input('Closed_Tickets_Span','value')])

def Update_Closed_Tickets_Table(Region,Start_Date,End_Date,Priority,Location,Shift,Category,Type,MAT,RCAT,Closed_Count,CT,span_selected):

    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Closed_Incidents_=Closed_Incidents.loc[(Closed_Incidents['Resolved Date']>=Start_Date) & (Closed_Incidents['Resolved Date']<=End_Date)]

    if Closed_Incidents_.empty==False:
        
        if span_selected == 'Resolved_Date':
            span_= pd.to_datetime(RCAT['points'][0]['x']) if RCAT is not None else pd.to_datetime(Closed_Count['points'][0]['x']) if Closed_Count is not None else None
        else:
            span_= RCAT['points'][0]['x'] if RCAT is not None else Closed_Count['points'][0]['x'] if Closed_Count is not None else None
    
        params={'Urgency':Priority['points'][0]['x'] if Priority is not None else None,
            'Shift':Shift['points'][0]['x'] if Shift is not None else None,
            'Location':Location['points'][0]['x'] if Location is not None else None,
            'Category':Category['points'][0]['x'] if Category is not None else None,
            'Type':Type['points'][0]['x'] if Type is not None else None,
            'Region':Region if Region != 'Global' else None,
            'Contact type':CT['points'][0]['x'] if CT is not None else None,
            span_selected:span_}
        
    temp_df_=Closed_Incidents_.copy()
    if all(i is None for i in params.values())==False:
        for i,j in zip(params.keys(),params.values()):
            if j is not None:
                temp_df_=temp_df_.loc[temp_df_[i]==j]
        data=temp_df_.to_dict('records')       
        temp_df_=temp_df_[closed_table_cols]
        data_table=temp_df_.to_dict('records')
        table2=dash_table.DataTable(id='Closed_Tickets_Table_',style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                   export_format='xlsx',export_headers='display',filter_action='native',
                                   sort_action="native",sort_mode="multi",style_cell=tickets_table_cell_style,
                                   columns=[{'name':i,'id':i} for i in temp_df_.columns],row_selectable='single',
                                   style_table={'maxWidth': '1600px', 'overflowY': 'auto'},data=data_table,page_size= 10)
        return [table2,data]
    else:
        return [html.Br(),[]]


# In[49]:


# Global Productivity Hub Efficiency

@app.callback(
Output('GPH_Efficiency_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('GPH_Leave_Graph','selectedData'),
Input('GPH_Efficiency_Graph','selectedData'),
Input('GPH_Utilization_Graph','selectedData'),
Input('GPH_Capacity_Utilization_Graph','selectedData'),
Input('GPH_Span','value')])

def Update_GPH_Efficiency_Graph(Region,Start_Date,End_Date,Leave,Efficiency,Utilization,CU,span_selected):
    
    if Efficiency is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        temp_df=GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)]

        if temp_df.empty==False:
            params={'Attendance Status':Leave['points'][0]['x'] if Leave is not None else None,
                    span_selected:Utilization['points'][0]['x'] if Utilization is not None else CU['points'][0]['x'] if CU is not None else None,
                    'Shift':Region if Region != 'Global' else None}

            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df=temp_df.loc[temp_df[i]==j]

            group=pd.DataFrame(data=temp_df.groupby([span_selected]).mean()['Efficiency (%)'].values,
                               index=temp_df.groupby([span_selected]).mean()['Efficiency (%)'].index,
                               columns=['Efficiency (%)']).rename_axis(span_selected).reset_index().sort_values(span_selected,
                                                                                                           ignore_index=True)
            if group.empty==False:
                if span_selected =='Month':
                    group['index']=pd.to_datetime(group['Month'])
                    group.sort_values('index',ignore_index=True,inplace=True) 

                fig=go.Figure()
                fig.add_trace(go.Scatter(x=group[span_selected],y=[95]*len(group),mode='lines',
                                         name='Threshold', marker_color='red',showlegend=True,hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=group[span_selected],y=group['Efficiency (%)'],name=Region, 
                                         marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=span_selected,title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                            tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20 if group['Efficiency (%)'].max()<200 else 100,rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Effieciency (%) Trend by '+span_selected,
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select',
                                 title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[50]:


# Global Productivity Hub Utilization

@app.callback(
Output('GPH_Utilization_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('GPH_Leave_Graph','selectedData'),
Input('GPH_Efficiency_Graph','selectedData'),
Input('GPH_Utilization_Graph','selectedData'),
Input('GPH_Capacity_Utilization_Graph','selectedData'),
Input('GPH_Span','value')])

def Update_GPH_Utilization_Graph(Region,Start_Date,End_Date,Leave,Efficiency,Utilization,CU,span_selected):
    
    if Utilization is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        temp_df=GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)]

        if temp_df.empty==False:
            params={'Attendance Status':Leave['points'][0]['x'] if Leave is not None else None,
                        span_selected:Efficiency['points'][0]['x'] if Efficiency is not None else CU['points'][0]['x'] if CU is not None else None,
                        'Shift':Region if Region != 'Global' else None}

            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df=temp_df.loc[temp_df[i]==j]

            group=pd.DataFrame(data=temp_df.groupby([span_selected]).mean()['Utilization (%)'].values,
                               index=temp_df.groupby([span_selected]).mean()['Utilization (%)'].index,
                               columns=['Utilization (%)']).rename_axis(span_selected).reset_index().sort_values(span_selected,
                                                                                                           ignore_index=True)
            if group.empty==False:
                if span_selected =='Month':
                    group['index']=pd.to_datetime(group['Month'])
                    group.sort_values('index',ignore_index=True,inplace=True) 

                fig=go.Figure()
                fig.add_trace(go.Scatter(x=group[span_selected],y=[95]*len(group),mode='lines',
                                             name='Threshold', marker_color='red',showlegend=True,hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=group[span_selected],y=group['Utilization (%)'],name=Region, 
                                         marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=span_selected,title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                            tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20 if group['Utilization (%)'].max()<200 else 100,rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Utilization (%) Trend by '+span_selected,
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[51]:


# Global Productivity Hub Capacity Utilization

@app.callback(
Output('GPH_Capacity_Utilization_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('GPH_Leave_Graph','selectedData'),
Input('GPH_Efficiency_Graph','selectedData'),
Input('GPH_Utilization_Graph','selectedData'),
Input('GPH_Capacity_Utilization_Graph','selectedData'),
Input('GPH_Span','value')])

def Update_GPH_Capacity_Utilization_Graph(Region,Start_Date,End_Date,Leave,Efficiency,Utilization,CU,span_selected):
    
    if CU is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        temp_df=GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)]

        if temp_df.empty==False:
            params={'Attendance Status':Leave['points'][0]['x'] if Leave is not None else None,
                        span_selected:Utilization['points'][0]['x'] if Utilization is not None else Efficiency['points'][0]['x'] if Efficiency is not None else None,
                        'Shift':Region if Region != 'Global' else None}

            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df=temp_df.loc[temp_df[i]==j]

            group=pd.DataFrame(data=temp_df.groupby([span_selected]).mean()['CU% (Based on Running Time)'].values,
                               index=temp_df.groupby([span_selected]).mean()['CU% (Based on Running Time)'].index,
                               columns=['CU% (Based on Running Time)']).rename_axis(span_selected).reset_index().sort_values(span_selected,
                                                                                                           ignore_index=True)
            if group.empty==False:
                if span_selected =='Month':
                    group['index']=pd.to_datetime(group['Month'])
                    group.sort_values('index',ignore_index=True,inplace=True) 

                fig=go.Figure()
                fig.add_trace(go.Scatter(x=group[span_selected],y=[95]*len(group),mode='lines',
                                             name='Threshold', marker_color='red',showlegend=True,hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=group[span_selected],y=group['CU% (Based on Running Time)'],name=Region, 
                                         marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
                fig.update_xaxes(gridcolor='#121212',title_text=span_selected,title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12),tickmode='array' if (group.columns[0]=='Date') and ((End_Date-Start_Date).days>7) else 'linear')
                fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                            tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20 if group['CU% (Based on Running Time)'].max()<200 else 100,rangemode='tozero')
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Capacity Utilization (%) Trend by '+span_selected,
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[52]:


# Global Productivity Hub Attendance

@app.callback(
Output('GPH_Leave_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('GPH_Leave_Graph','selectedData'),
Input('GPH_Efficiency_Graph','selectedData'),
Input('GPH_Utilization_Graph','selectedData'),
Input('GPH_Capacity_Utilization_Graph','selectedData'),
Input('GPH_Span','value')])

def Update_GPH_Leave_Graph(Region,Start_Date,End_Date,Leave,Efficiency,Utilization,CU,span_selected):
    
    if Leave is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

        temp_df=GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)]
    
        if temp_df.empty==False:
            params={'Attendance Status':Leave['points'][0]['x'] if Leave is not None else None,
                    span_selected:Utilization['points'][0]['x'] if Utilization is not None else CU['points'][0]['x'] if CU is not None else Efficiency['points'][0]['x'] if Efficiency is not None else None,
                    'Shift':Region if Region != 'Global' else None}

            if all(i is None for i in params.values())==False:
                for i,j in zip(params.keys(),params.values()):
                    if j is not None:
                        temp_df=temp_df.loc[temp_df[i]==j]

            group=pd.DataFrame(data=temp_df['Attendance Status'].value_counts().values,
                               index=temp_df['Attendance Status'].value_counts().index,
                               columns=['count']).rename_axis('Attendance').reset_index().sort_values('Attendance',
                                                                                                           ignore_index=True)
            if group.empty==False:
                fig=go.Figure()
                fig.add_trace(go.Bar(x=group['Attendance'],y=group['count'],name=Region, 
                                         marker_color=region_color[Region],showlegend=True))
                fig.update_xaxes(gridcolor='#121212',title_text='Attendance Status',title_font=dict(size=14,color='white'),
                                        tickfont=dict(color='white',size=12))
                fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=14,color='white'),
                            tickfont=dict(color='white',size=12))
                fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',title='Attendance Trend',
                                  font=dict(color='white'),title_font_color='white',clickmode='event+select'
                                 ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
            else:
                fig=No_Data_Available()
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


# In[53]:


@app.callback(
Output('GPH_Details_Table','children'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('GPH_Leave_Graph','selectedData'),
Input('GPH_Efficiency_Graph','selectedData'),
Input('GPH_Utilization_Graph','selectedData'),
Input('GPH_Capacity_Utilization_Graph','selectedData'),
Input('GPH_Span','value')])

def Update_GPH_Details_Table(Region,Start_Date,End_Date,Leave,Efficiency,Utilization,CU,span_selected):
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

    temp_df=GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)]

    if temp_df.empty==False:
        params={'Attendance Status':Leave['points'][0]['x'] if Leave is not None else None,
                span_selected:Utilization['points'][0]['x'] if Utilization is not None else CU['points'][0]['x'] if CU is not None else None,
                'Shift':Region if Region != 'Global' else None}

        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
            temp_df=temp_df[GPH_table_cols]
            data_table=temp_df[GPH_table_cols].to_dict('records')
            table2=dash_table.DataTable(id='GPH_Details_Table_',style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                       export_format='xlsx',export_headers='display',filter_action='native',
                                       sort_action="native",sort_mode="multi",style_cell=tickets_table_cell_style,
                                       columns=[{'name':i,'id':i} for i in temp_df.columns],page_size= 10,
                                       style_table={'maxWidth': '1600px', 'overflowY': 'auto'},data=data_table)
            return table2
        else:
            return html.Br()
    
    else:
        return html.Br()
    


# In[54]:



#Standard Quality Framework

@app.callback(
Output('SQF_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('SQF_Span','value'),
Input('SQF_Graph','selectedData'),
Input('SQF_Count_Graph','selectedData'),
Input('SQF_Category_Graph_','selectedData'),
Input('SQF_Type_Graph_','selectedData')])

def Update_SQF_Graph(Region,Start_Date,End_Date,span_selected,sqf,audit_count,category_selected,type_selected):
    
    if sqf is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
        
        temp_df=Closed_Incidents.loc[(Closed_Incidents['Audit Date'] >=Start_Date) & 
                                     (Closed_Incidents['Audit Date']<=End_Date)]
        
        if span_selected == 'Audit_Date':
            span_= pd.to_datetime(audit_count['points'][0]['x']) if audit_count is not None else None
        else:
            span_= audit_count['points'][0]['x'] if audit_count is not None else None
    
        params={'Region':Region if Region !='Global' else None,
               span_selected:span_,
               'Category': re.sub('<br>',' ',category_selected['points'][0]['x']) if category_selected is not None else None,
               'Type':re.sub('<br>',' ',type_selected['points'][0]['x']) if type_selected is not None else None}
        
        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
        
        if temp_df.empty==False:
            tickets_count=pd.DataFrame(data=temp_df.groupby([span_selected]).mean()['Score %'].values,
                               index=temp_df.groupby([span_selected]).mean()['Score %'].index,
                 columns=['score']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)

            if span_selected =='Audit_Month':
                tickets_count['index']=pd.to_datetime(tickets_count['Audit Month'])
                tickets_count.sort_values('index',ignore_index=True,inplace=True) 

            fig=go.Figure()
            fig.add_trace(go.Scatter(x=tickets_count[re.sub('_',' ',span_selected)],y=[95]*len(tickets_count),name='Threshold',mode='lines',
                                    marker_color='red',showlegend=True,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=tickets_count[re.sub('_',' ',span_selected)],y=tickets_count['score'],name=Region,
                                    marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
            fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=14,color='white'),
                              tickfont=dict(color='white',size=12),tickmode='array' if (tickets_count.columns[0]=='Audit Date') and ((End_Date-Start_Date).days>7) else 'linear'
                    )
            fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=14),title_text='Avg. Score Percentage',
                             title_font=dict(size=12,color='white'),rangemode='tozero',tickmode='linear',dtick=20,tick0=0)
            fig.update_layout(title='Tickets Quality Score Trend by ' + re.sub('_',' ',span_selected),height=350,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig
    
@app.callback(
Output('SQF_Count_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('SQF_Span','value'),
Input('SQF_Graph','selectedData'),
Input('SQF_Count_Graph','selectedData'),
Input('SQF_Category_Graph_','selectedData'),
Input('SQF_Type_Graph_','selectedData')])

def Update_SQF_Count_Graph(Region,Start_Date,End_Date,span_selected,sqf,audit_count,category_selected,type_selected):
    
    if audit_count is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
        
        temp_df=Closed_Incidents.loc[(Closed_Incidents['Audit Date'] >=Start_Date) & 
                                     (Closed_Incidents['Audit Date']<=End_Date)]
        
        if span_selected == 'Audit_Date':
            span_= pd.to_datetime(sqf['points'][0]['x']) if sqf is not None else None
        else:
            span_= sqf['points'][0]['x'] if sqf is not None else None
    
        params={'Region':Region if Region !='Global' else None,
               span_selected:span_,
               'Category': re.sub('<br>',' ',category_selected['points'][0]['x']) if category_selected is not None else None,
               'Type':re.sub('<br>',' ',type_selected['points'][0]['x']) if type_selected is not None else None}
        
        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
        
        if temp_df.empty==False:
            tickets_count=pd.DataFrame(data=temp_df.groupby([span_selected]).count()['Number'].values,
                               index=temp_df.groupby([span_selected]).count()['Number'].index,
                 columns=['count']).rename_axis(re.sub('_',' ',span_selected)).reset_index().sort_values(re.sub('_',' ',span_selected),ignore_index=True)

            if span_selected =='Audit_Month':
                tickets_count['index']=pd.to_datetime(tickets_count['Audit Month'])
                tickets_count.sort_values('index',ignore_index=True,inplace=True) 

            fig=go.Figure()
            fig.add_trace(go.Scatter(x=tickets_count[re.sub('_',' ',span_selected)],y=tickets_count['count'],name=Region,
                                    marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
            fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=14,color='white'),
                              tickfont=dict(color='white',size=12),tickmode='array' if (tickets_count.columns[0]=='Audit Date') and ((End_Date-Start_Date).days>7) else 'linear'
                    )
            fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=14),title_text='Count',
                             title_font=dict(size=12,color='white'),rangemode='tozero')
            fig.update_layout(title='Tickets Audited Count Trend by '+ re.sub('_',' ',span_selected),height=350,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig

@app.callback(
Output('SQF_Category_Graph_','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('SQF_Span','value'),
Input('SQF_Graph','selectedData'),
Input('SQF_Count_Graph','selectedData'),
Input('SQF_Category_Graph_','selectedData'),
Input('SQF_Type_Graph_','selectedData')])

def SQF_Category_Graph(Region,Start_Date,End_Date,span_selected,sqf,audit_count,category_selected,type_selected):
    
    if category_selected is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
        
        temp_df=Closed_Incidents.loc[(Closed_Incidents['Audit Date'] >=Start_Date) & (Closed_Incidents['Audit Date']<=End_Date)]
        
        if span_selected == 'Audit_Date':
            span_= pd.to_datetime(sqf['points'][0]['x']) if sqf is not None else pd.to_datetime(audit_count['points'][0]['x']) if audit_count is not None else None
        else:
            span_= sqf['points'][0]['x'] if sqf is not None else audit_count['points'][0]['x'] if audit_count is not None else None
    
        params={'Region':Region if Region !='Global' else None,
               span_selected:span_,
               'Category': re.sub('<br>',' ',category_selected['points'][0]['x']) if category_selected is not None else None,
               'Type':re.sub('<br>',' ',type_selected['points'][0]['x']) if type_selected is not None else None}
        
        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
        
        if temp_df.empty==False:
            category_count=pd.DataFrame(data=temp_df.groupby(['Category']).mean()['Score %'].values,
                                        index=temp_df.groupby(['Category']).mean()['Score %'].index,
                                        columns=['count']).reset_index().sort_values('Category',ignore_index=True)
            
            category_count['category']=category_count['Category'].apply(lambda x: re.sub('\s','<br>',x))

            fig=go.Figure()
            fig.add_trace(go.Scatter(x=category_count['category'],y=[95]*len(category_count),name='Threshold',mode='lines',
                                    marker_color='red',showlegend=True,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=category_count['category'],y=category_count['count'],name=Region,
                                    marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
            fig.update_xaxes(gridcolor='#121212',title_text='Category',title_font=dict(size=14,color='white'),
                        tickfont=dict(color='white',size=12))
            fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=14),title_text='Avg. Score Percentage',rangemode='tozero',
                             title_font=dict(size=12,color='white'),tickmode='linear',dtick=20,tick0=0)
            fig.update_layout(title='Tickets Quality Score Trend by Category',height=350,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig

@app.callback(
Output('SQF_Type_Graph_','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('SQF_Span','value'),
Input('SQF_Graph','selectedData'),
Input('SQF_Count_Graph','selectedData'),
Input('SQF_Category_Graph_','selectedData'),
Input('SQF_Type_Graph_','selectedData')])

def SQF_Type_Graph(Region,Start_Date,End_Date,span_selected,sqf,audit_count,category_selected,type_selected):
    
    if type_selected is None:
        Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
        End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
        
        temp_df=Closed_Incidents.loc[(Closed_Incidents['Audit Date'] >=Start_Date) & (Closed_Incidents['Audit Date']<=End_Date)]
        
        if span_selected == 'Audit_Date':
            span_= pd.to_datetime(sqf['points'][0]['x']) if sqf is not None else pd.to_datetime(audit_count['points'][0]['x']) if audit_count is not None else None
        else:
            span_= sqf['points'][0]['x'] if sqf is not None else audit_count['points'][0]['x'] if audit_count is not None else None
    
        params={'Region':Region if Region !='Global' else None,
               span_selected:span_,
               'Category': re.sub('<br>',' ',category_selected['points'][0]['x']) if category_selected is not None else None,
               'Type':re.sub('<br>',' ',type_selected['points'][0]['x']) if type_selected is not None else None}
        
        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
        
        if temp_df.empty==False:
            type_count=pd.DataFrame(data=temp_df.groupby(['Type']).mean()['Score %'].values,
                                        index=temp_df.groupby(['Type']).mean()['Score %'].index,
                                        columns=['count']).reset_index().sort_values('Type',ignore_index=True)
            
            type_count['type']=type_count['Type'].apply(lambda x: re.sub('\s','<br>',x))

            fig=go.Figure()
            fig.add_trace(go.Scatter(x=type_count['type'],y=[95]*len(type_count),name='Threshold',mode='lines',
                                    marker_color='red',showlegend=True,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=type_count['type'],y=type_count['count'],name=Region,
                                    marker_color=region_color[Region],showlegend=True,mode='lines+markers'))
            fig.update_xaxes(gridcolor='#121212',title_text='Category',title_font=dict(size=14,color='white'),
                        tickfont=dict(color='white',size=12))
            fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=14),title_text='Avg. Score Percentage',rangemode='tozero',
                             title_font=dict(size=12,color='white'),tickmode='linear',dtick=20,tick0=0)
            fig.update_layout(title='Tickets Quality Score Trend by Category',height=350,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),clickmode='event+select',title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        else:
            fig=No_Data_Available()
    else:
        raise PreventUpdate
    return fig


@app.callback(
Output('SQF_Audit_Table','children'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('SQF_Span','value'),
Input('SQF_Graph','selectedData'),
Input('SQF_Count_Graph','selectedData'),
Input('SQF_Category_Graph_','selectedData'),
Input('SQF_Type_Graph_','selectedData')])

def Update_SQF_tickets_table(Region,Start_Date,End_Date,span_selected,sqf,audit_count,category_selected,type_selected):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')

    temp_df=Closed_Incidents.loc[(Closed_Incidents['Audit Date'] >=Start_Date) & (Closed_Incidents['Audit Date']<=End_Date)]
    if temp_df.empty==False:    
        if span_selected == 'Audit_Date':
            span_= pd.to_datetime(sqf['points'][0]['x']) if sqf is not None else pd.to_datetime(audit_count['points'][0]['x']) if audit_count is not None else None
        else:
            span_= sqf['points'][0]['x'] if sqf is not None else audit_count['points'][0]['x'] if audit_count is not None else None
    
        params={'Region':Region if Region !='Global' else None,
               span_selected:span_,
               'Category': re.sub('<br>',' ',category_selected['points'][0]['x']) if category_selected is not None else None,
               'Type':re.sub('<br>',' ',type_selected['points'][0]['x']) if type_selected is not None else None}

        if all(i is None for i in params.values())==False:
            for i,j in zip(params.keys(),params.values()):
                if j is not None:
                    temp_df=temp_df.loc[temp_df[i]==j]
            temp_df=temp_df[SQF_table_cols]
            data_table=temp_df.to_dict('records')
            table2=dash_table.DataTable(id='SQF_Details_Table_',style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                       export_format='xlsx',export_headers='display',filter_action='native',
                                       sort_action="native",sort_mode="multi",style_cell=tickets_table_cell_style,
                                       columns=[{'name':i,'id':i} for i in temp_df.columns],page_size= 10,
                                       style_table={'maxWidth': '1600px', 'overflowY': 'auto'},data=data_table)
            return table2
        else:
            return html.Br()
    
    else:
        return html.Br()


# In[55]:



# Process_Knowledge_Test

@app.callback(
Output('PKT_Graph','figure'),
[Input('Region','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_PKT_Graph(Region,Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d') 
    
    if Region=='Global':
        PKT_Graph=PKT.loc[(PKT.Date>=Start_Date) & (PKT.Date<=End_Date)].groupby(['Date']).mean().reset_index().sort_values('Date')
    else:
        PKT_Graph=PKT.loc[(PKT.Date>=Start_Date) & (PKT.Date<=End_Date) & (PKT.Region==Region)].groupby(['Date']).mean().reset_index().sort_values('Date')
        
    if PKT_Graph.empty==False:
        PKT_Graph['Month']=PKT_Graph['Date'].dt.strftime('%b-%Y')
        
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=PKT_Graph['Month'],y=[95]*len(PKT_Graph),mode='lines',
                                                     name='Threshold', marker_color='red',showlegend=True,hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=PKT_Graph['Month'],y=PKT_Graph['PKT (%)'],name=Region,marker_color=region_color[Region],
                                 showlegend=True))
        fig.update_xaxes(gridcolor='#121212',title_text='Month',title_font=dict(size=14,color='white'),tickmode='array')
        fig.update_yaxes(gridcolor='#121212',title_text='Avg. Percentage',title_font=dict(size=14,color='white'),
                                    tickfont=dict(color='white',size=12),tickmode='linear',tick0=0,dtick=20,rangemode='tozero')
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',font=dict(color='white')
                         ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9,title='Monthly PKT Scores')
        
    else:
        fig=No_Data_Available()
        
    return fig
    


# In[56]:



# Performance

@app.callback(
[Output('Agent_Name','options'),
Output('AgentPerformance','data'),
Output('AgentPerformance','columns'),
Output('KPI','figure')],
[Input('Region','value'),
Input('Agent_Name','value'),
Input('Metrics','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_Performance(Region,Agent_Name,Metrics,Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    # Ticket Related DataFrame
    Tickets_Current=Tickets[Tickets['Owner'].isin ([x for x in Current_FTE['Name']])]
    Performance=np.round(Tickets_Current.loc[(Tickets_Current.Created>=Start_Date) & (Tickets_Current.Created<=End_Date) & 
                        (Tickets_Current.State!='Work in progress') & (Tickets_Current.State!='Cancelled'),
                       ['Shift','Owner','Created','ManualAck_TAT (%)','RCA_TAT (%)','Score %','No_Shows (Nos.)'
                        ]].groupby(['Shift','Owner',Tickets_Current.Created.dt.strftime('%Y-%m'),
                                                        Tickets_Current.Created.dt.strftime('%B-%Y')]).mean(),2)
    Performance=Performance.rename_axis(index={'Created':'Date'})
    
    # PKT DataFrame
    PKT_Pivot=np.round(PKT.loc[(PKT.Date>=Start_Date) & 
                               (PKT.Date<=End_Date)].groupby(['Region','Name', PKT.Date.dt.strftime('%Y-%m'),
                                                                             PKT.Date.dt.strftime('%B-%Y')]).mean(),2)
    PKT_Pivot=PKT_Pivot.rename_axis(index={'Region':'Shift','Name':'Owner'})
    
    # GPH DataFrame
    GPH_Current=GPH[GPH['Name'].isin([x for x in Current_FTE['Name']])]
    CEU_Pivot=np.round(GPH_Current.loc[(GPH_Current.Date>=Start_Date) & 
                              (GPH_Current.Date<=End_Date)].groupby(['Shift','Name',GPH_Current.Date.dt.strftime('%Y-%m')
                                                             ,GPH_Current.Date.dt.strftime('%B-%Y')]).mean()[['CU% (Based on Running Time)',
                                                                                                    'Efficiency (%)',
                                                                                                    'Utilization (%)']],2)
    CEU_Pivot=CEU_Pivot.rename_axis(index={'Name':'Owner'})
    
#     # Ideas DataFrame
#     Ideas['Submitted On']=pd.to_datetime(Ideas['Submitted On'])
#     Ideas_Current=Ideas[Ideas['Owner'].isin ([x for x in Current_FTE['Name']])]
#     Ideas_Pivot=Ideas_Current.loc[(Ideas_Current['Submitted On']>=Start_Date) & 
#                           (Ideas_Current['Submitted On']<=End_Date)].groupby(['Shift','Owner',Ideas_Current['Submitted On'].dt.strftime('%Y-%m'),
#                                                                       Ideas_Current['Submitted On'].dt.strftime('%B-%Y')]).count()['Idea Title']
    
    # Escalations DataFrame
    Escalations_Pivot=np.round(Escalations.loc[(Escalations.Date>=Start_Date) & (Escalations.Date<=End_Date)].groupby(['Region','Name', Escalations.Date.dt.strftime('%Y-%m'),
                                                                             Escalations.Date.dt.strftime('%B-%Y')]).mean(),0)
    
    # Unplanned DataFrame
    Unplanned_Leaves_Pivot=np.round(Unplanned_Leaves.loc[(Unplanned_Leaves.Date>=Start_Date) & (Unplanned_Leaves.Date<=End_Date)].groupby(['Region','Name', Unplanned_Leaves.Date.dt.strftime('%Y-%m'),
                                                                             Unplanned_Leaves.Date.dt.strftime('%B-%Y')]).mean(),0)
    
    # Joining all DataFrames
    Performance=pd.concat([Performance,PKT_Pivot,CEU_Pivot,Escalations_Pivot,Unplanned_Leaves_Pivot],axis=1,sort=False)
    
    # Resetting index to so we get Agent Name and Date as columns 
    Performance.reset_index(level=3,inplace=True)
    Performance.reset_index(level=1,inplace=True)
    
    # Renaming Columns appropraitely
    Performance.rename(columns={'level_1':'Agent Name','Owner':'Agent Name','Score %':'Internal_Quality_Score (%)',
                                'CU% (Based on Running Time)':'Capacity_Utilization (%)',
                               'level_3':'Date'},inplace=True)
    
    # Outputs
    Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE['Name']]]
    Data=Performance.to_dict('records')
    Columns=[{'id':x,'name':x} for x in Performance.columns]
    
    Weights=[15,15,10,10,10,10,10,10,10]
    
    MetricWeightage=Performance[['Agent Name','Date','ManualAck_TAT (%)', 'RCA_TAT (%)', 'Internal_Quality_Score (%)',
       'No_Shows (Nos.)', 'PKT (%)', 'Capacity_Utilization (%)', 
       'Escalations (Nos.)', 'Unplanned_Leaves (Nos.)']].reset_index().set_index(['level_0','level_1','Agent Name','Date'])
    MetricWeightage['Escalations (Nos.)'].fillna(value=0,inplace=True)
    MetricWeightage['Unplanned_Leaves (Nos.)'].fillna(value=0,inplace=True)
    MetricWeightage['No_Shows (Nos.)']=MetricWeightage['No_Shows (Nos.)'].apply(lambda x: 100 if (x<=2) else 0)
    MetricWeightage['Unplanned_Leaves (Nos.)']=MetricWeightage['Unplanned_Leaves (Nos.)'].apply(lambda x: 100 if (x==0) else 0)
    MetricWeightage['Escalations (Nos.)']=MetricWeightage['Escalations (Nos.)'].apply(lambda x: 100 if (x==0) else 0)

    for  i,j in zip(MetricWeightage.columns,Weights):
        MetricWeightage[i]=MetricWeightage[i].apply(lambda x: x*j)

    MetricWeightage['KPI']=MetricWeightage.sum(axis=1)
    MetricWeightage['KPI']=MetricWeightage['KPI'].apply(lambda x: x/100)
    MetricWeightage=MetricWeightage.astype('float64')
    MetricWeightage=MetricWeightage.reset_index().set_index(['level_0','level_1'])
    
    fig=No_Data_Available()

    if Region=='Global' and Agent_Name=='All' and Metrics is None:
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE['Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]
    
        return Options,Data,Columns,fig
    
    elif Region=='Global' and Agent_Name !='All' and Metrics is not None:
        
        Performance=Performance.loc[Performance['Agent Name']==Agent_Name][['Agent Name','Date']+Metrics]
        
        MW=MetricWeightage.loc[MetricWeightage['Agent Name']==Agent_Name]

        fig=px.line(MW,x='Date',y='KPI')
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=14,color='white'))
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=12),title_text='Count',
                             title_font=dict(size=14,color='white'),tickmode='linear',tick0=0,dtick=20)
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',font=dict(color='white')
                         ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE['Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]
    
        return Options,Data,Columns,fig
    
    elif Region=='Global' and Agent_Name=='All' and Metrics is not None:
        
        Performance=Performance[['Agent Name','Date']+Metrics]
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE['Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]
        
        return Options,Data,Columns,fig
    
    elif Region != 'Global' and Agent_Name=='All' and Metrics is None:
        
        Performance=Performance.loc[Region]
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in Current_FTE.loc[Current_FTE.Region==Region,'Name']]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]
        
        return Options,Data,Columns,fig
    
    elif Region != 'Global' and Agent_Name is not None and Metrics is None:
        
        Performance=Performance.loc[Performance['Agent Name']==Agent_Name]
        
        MW=MetricWeightage.loc[MetricWeightage['Agent Name']==Agent_Name]

        fig=px.line(MW,x='Date',y='KPI')
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=14,color='white'))
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=12),title_text='Count',
                             title_font=dict(size=14,color='white'),tickmode='linear',tick0=0,dtick=20)
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',font=dict(color='white')
                         ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE.loc[Current_FTE.Region==Region,'Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]
        
        return Options,Data,Columns,fig
    
    elif Region != 'Global' and Agent_Name=='All' and Metrics is not None:

        Performance=Performance.loc[Region][['Agent Name','Date']+Metrics]

        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE.loc[Current_FTE.Region==Region,'Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]

        return Options,Data,Columns,fig
    
    elif Region != 'Global' and Agent_Name !='All' and Metrics is not None:

        Performance=Performance.loc[Performance['Agent Name']==Agent_Name][['Agent Name','Date']+Metrics]

        MW=MetricWeightage.loc[MetricWeightage['Agent Name']==Agent_Name]

        fig=px.line(MW,x='Date',y='KPI')
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=14,color='white'))
        fig.update_yaxes(gridcolor='#121212',tickfont=dict(color='white',size=12),title_text='Count',
                             title_font=dict(size=14,color='white'),tickmode='linear',tick0=0,dtick=20)
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',font=dict(color='white')
                         ,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        
        Options=[{'label':'All','value':'All'}]+[{'label':x,'value':x} for x in [x for x in Current_FTE.loc[Current_FTE.Region==Region,'Name']]]
        Data=Performance.to_dict('records')
        Columns=[{'id':x,'name':x} for x in Performance.columns]

        return Options,Data,Columns,fig


# In[57]:



## Program Stats

@app.callback(
[Output('Tickets_Stats_Table','data'),
Output('Tickets_Stats_Table','columns')],
[Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_Tickets_Stats_Table(Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Total_Tickets=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date),'Number'].count()
    Total_WIP_Tickets=Tickets.loc[Tickets.State=='Work in progress','Number'].count()
    Total_Resolved_Tickets=Tickets.loc[((Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & 
                                        (Tickets.State=='Resolved')) | ((Tickets['Resolved Date']>=Start_Date) & 
                                                                        (Tickets['Resolved Date']<=End_Date) & 
                                                                        (Tickets.State=='Closed Complete')) ,'Number'].count()

    Total_Cancelled_Tickets=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & 
                                       (Tickets.State=='Cancelled'),'Number'].count()
    Tickets_with_Defects=Tickets.loc[(Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & (Tickets['Score %']<100),'Number'].count()
    Tickets_without_Defects=Tickets.loc[(Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & (Tickets['Score %']==100),'Number'].count()
    Avg_Quality_Score=np.round(Tickets.loc[(Tickets.Created>=Start_Date) & 
                                  (Tickets.Created<=End_Date),'Score %'].mean(),2)
    Avg_Manual_Ack_TAT=np.round(Tickets.loc[(Tickets.Created>=Start_Date) & 
                                  (Tickets.Created<=End_Date),'ManualAck_TAT (%)'].mean(),2)
    Avg_RCA_TAT=np.round(Tickets.loc[(Tickets.Created>=Start_Date) & 
                                  (Tickets.Created<=End_Date),'RCA_TAT (%)'].mean(),2)
    Tickets_Stats=pd.DataFrame(data=[['Total Tickets', np.nan, Total_Tickets],['Total WIP Tickets', np.nan, Total_WIP_Tickets],
                                  ['Total Resolved Tickets', np.nan, Total_Resolved_Tickets],['Total Cancelled Tickets', np.nan, Total_Cancelled_Tickets],
                                  ['Total Defective Tickets', 0, Tickets_with_Defects],['Total Non-Defective Tickets', np.nan, Tickets_without_Defects],
                                  ['Average Quality Score(%)', 100, Avg_Quality_Score],['Average Manual Ack TAT (%)', 100, Avg_Manual_Ack_TAT],
                                  ['Average RCA TAT (%)', 100, Avg_RCA_TAT]],columns=['Parameter','Target','Value'],dtype='int64')

    data=Tickets_Stats.to_dict('records')
    columns=[{'id':x,'name':x} for x in Tickets_Stats.columns ]

    return data,columns

@app.callback(Output('Tickets_Stats_Graph','figure'),
             [Input('Tickets_Stats_Table','selected_rows'),
             Input('DateRange','start_date'),
             Input('DateRange','end_date')])

def Update_Tickets_TAT_Graph(row_id,Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Para=['Total Tickets','Total WIP Tickets','Total Resolved Tickets','Total Cancelled Tickets',
                                 'Total Defective Tickets','Total Non-Defective Tickets','Average Quality Score(%)',
                                'Average Manual Ack TAT (%)','Average RCA TAT (%)']

    Total_Tickets_Graph=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date)].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                    Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1).rename(columns={'Number':'Total Tickets'})
    Total_WIP_Tickets_Graph=Tickets.loc[Tickets.State=='Work in progress'].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                        Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1).rename(columns={'Number':'Total WIP Tickets'})
    Total_Resolved_Tickets_Graph=Tickets.loc[((Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & 
                                        (Tickets.State=='Resolved')) | ((Tickets['Resolved Date']>=Start_Date) & 
                                                                        (Tickets['Resolved Date']<=End_Date) & 
                                                                        (Tickets.State=='Closed Complete'))].groupby([Tickets['Resolved Date'].dt.strftime('%Y-%m'),
                                                        Tickets['Resolved Date'].dt.strftime('%B-%Y')]).count()[['Number','Resolved Date']].drop(['Resolved Date'],axis=1).rename(columns={'Number':'Total Resolved Tickets'})

    Total_Cancelled_Tickets_Graph=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & 
                                       (Tickets.State=='Cancelled')].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                        Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1).rename(columns={'Number':'Total Cancelled Tickets'})
    Tickets_with_Defects_Graph=Tickets.loc[(Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & (Tickets['Score %']<100)].groupby([Tickets['Resolved Date'].dt.strftime('%Y-%m'),
                                                        Tickets['Resolved Date'].dt.strftime('%B-%Y')]).count()[['Number','Resolved Date']].drop(['Resolved Date'],axis=1).rename(columns={'Number':'Total Defective Tickets'})
    Tickets_without_Defects_Graph=Tickets.loc[(Tickets['Resolved Date']>=Start_Date) & (Tickets['Resolved Date']<=End_Date) & (Tickets['Score %']==100)].groupby([Tickets['Resolved Date'].dt.strftime('%Y-%m'),
                                                        Tickets['Resolved Date'].dt.strftime('%B-%Y')]).count()[['Number','Resolved Date']].drop(['Resolved Date'],axis=1).rename(columns={'Number':'Total Non-Defective Tickets'})
    Avg_Quality_Score_Graph=np.round(Tickets.loc[(Tickets.Created>=Start_Date) & 
                                  (Tickets.Created<=End_Date)].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                        Tickets.Created.dt.strftime('%B-%Y')]).mean()[['Score %','ManualAck_TAT (%)','RCA_TAT (%)']],2).rename(columns={'Score %':'Average Quality Score(%)','ManualAck_TAT (%)':'Average Manual Ack TAT (%)','RCA_TAT (%)':'Average RCA TAT (%)'})

    Tickets_Stats_Graph_2=pd.concat([Total_Tickets_Graph,Total_WIP_Tickets_Graph,Total_Resolved_Tickets_Graph,Total_Cancelled_Tickets_Graph
                                ,Tickets_with_Defects_Graph,Tickets_without_Defects_Graph,Avg_Quality_Score_Graph],axis=1)

    try:
        for i in row_id:
            row=Para[i]
            if i>5:
                tt='Percentage (%)'
            else:
                tt='Count'
        x=[x for x in Tickets_Stats_Graph_2.index.get_level_values(1)]
        y=[x for x in Tickets_Stats_Graph_2[row]]
        fig=go.Figure(go.Scatter(x=x,y=y,mode='lines+markers'))
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                    tickfont=dict(color='white',size=10))
        fig.update_yaxes(gridcolor='#121212',title_text=tt,title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
        fig.update_layout(title=row,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),height=300,margin={'l':0,'b':0},title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    except TypeError:
        fig=go.Figure()
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),annotations=[{"text": "Choose a Parameter for Visualization","xref": "paper","yref": "paper",
                            "showarrow": False,"font": {"size": 28}}],height=300,margin={'l':0,'b':0})
        fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False)
        fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False)
        
    return fig

@app.callback(
Output('Category_Options','options'),
[Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_Category(Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Category=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.State!='Cancelled'),'Category'].unique()
    options=[{'label':x,'value':x} for x in Category]
    
    return options

@app.callback(
Output('Type_Options','options'),
[Input('Category_Options','value'),
Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_Type(Category,Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Type=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.Category==Category) & (Tickets.State!='Cancelled'),'Type'].unique()
    options=[{'label':x,'value':x} for x in Type]
    
    return options

@app.callback(
Output('Category_Graph','figure'),
[Input('DateRange','start_date'),
Input('DateRange','end_date'),
Input('Category_Options','value'),
Input('Type_Options','value')])

def Update_Tickets_by_Category(Start_Date,End_Date,Category,Type):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    if Category is not None and Type is None:
        
        Cat_Grp=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.Category==Category) & (Tickets.State!='Cancelled')].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                    Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1)
        
        x=[x for x in Cat_Grp.index.get_level_values(1)]
        y=[x for x in Cat_Grp['Number']]
        
        fig=go.Figure(go.Scatter(x=x,y=y))
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                    tickfont=dict(color='white',size=10))
        fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
        fig.update_layout(title=Category,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),height=300,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        
    elif Category is not None and Type is not None:
        
        Type_Grp=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.Category==Category) & (Tickets.Type==Type) & (Tickets.State!='Cancelled')
           ].groupby([Tickets.Created.dt.strftime('%Y-%m'),Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1)
        
        if Type_Grp.empty:
            Cat_Grp=Tickets.loc[(Tickets.Created>=Start_Date) & (Tickets.Created<=End_Date) & (Tickets.Category==Category) & (Tickets.State!='Cancelled')].groupby([Tickets.Created.dt.strftime('%Y-%m'),
                                                    Tickets.Created.dt.strftime('%B-%Y')]).count()[['Number','Created']].drop(['Created'],axis=1)
        
            x=[x for x in Cat_Grp.index.get_level_values(1)]
            y=[x for x in Cat_Grp['Number']]

            fig=go.Figure(go.Scatter(x=x,y=y))
            fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
            fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=12,color='white'),
                            tickfont=dict(color='white',size=10))
            fig.update_layout(title=Category,plot_bgcolor='black',paper_bgcolor='black',
                              font=dict(color='white'),height=300,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
        else:   
            x=[x for x in Type_Grp.index.get_level_values(1)]
            y=[x for x in Type_Grp['Number']]

            fig=go.Figure(go.Scatter(x=x,y=y))
            fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
            fig.update_yaxes(gridcolor='#121212',title_text='Count',title_font=dict(size=12,color='white'),
                            tickfont=dict(color='white',size=10))
            fig.update_layout(title=Category +'-'+ Type,plot_bgcolor='black',paper_bgcolor='black',
                              font=dict(color='white'),height=300,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        
        fig=go.Figure()
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),annotations=[{"text": "Choose a Category for Visualization","xref": "paper","yref": "paper",
                            "showarrow": False,"font": {"size": 28}}],height=300)
        fig.update_xaxes(showgrid=False,zeroline=False,showticklabels=False)
        fig.update_yaxes(showgrid=False,zeroline=False,showticklabels=False)
    
    return fig

@app.callback(
[Output('GPH_Stats_Table','data'),
Output('GPH_Stats_Table','columns')],
[Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_GPH_Table(Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Avg_Capacity_Utlization=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'CU% (Based on Running Time)'].mean(),2)
    Avg_Efficiency=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'Efficiency (%)'].mean(),2)
    Avg_Utilization=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'Utilization (%)'].mean(),2)
    Avg_Productive_Time=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'Productive Time (hrs)'].mean(),2)
    Avg_Shrinkage=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'Shrinkage Time (hrs)'].mean(),2)
    Avg_Break=np.round(GPH.loc[(GPH.Date>=Start_Date) & 
                              (GPH.Date<=End_Date),'Break Time (hrs)'].mean(),2)

    GPH_Stats=pd.DataFrame(data=[['Average Capacity Utilization (%)',85,Avg_Capacity_Utlization],
                            ['Average Efficiency (%)',95,Avg_Efficiency],['Average Utilization',85,Avg_Utilization],
                            ['Average Productive Hours',8,Avg_Productive_Time],['Average Shrinkage Hours',0.75,Avg_Shrinkage],
                            ['Average Break Hours',0.75,Avg_Break]],columns=['Parameter','Target','Value'])
    data=GPH_Stats.to_dict('records')
    columns=[{'id':x,'name':x} for x in GPH_Stats.columns ]

    return data,columns

@app.callback(Output('GPH_Stats_Graph','figure'),
             [Input('GPH_Stats_Table','selected_rows'),
             Input('DateRange','start_date'),
             Input('DateRange','end_date')])

def Update_GPH_TAT_Graph(row_id,Start_Date,End_Date):
    
    Start_Date = datetime.datetime.strptime(re.split('T| ', Start_Date)[0], '%Y-%m-%d')
    End_Date = datetime.datetime.strptime(re.split('T| ', End_Date)[0], '%Y-%m-%d')
    
    Para=['Average Capacity Utilization (%)','Average Efficiency (%)','Average Utilization (%)','Average Productive Hours',
         'Average Shrinkage Hours','Average Break Hours']
    
    GPH_Stats_Graph_2=np.round(GPH.loc[(GPH.Date>=Start_Date) & (GPH.Date<=End_Date)].groupby([GPH.Date.dt.strftime('%Y-%m')
                    ,GPH.Date.dt.strftime('%B-%Y')]).mean()[['CU% (Based on Running Time)',
            'Efficiency (%)','Utilization (%)','Productive Time (hrs)','Shrinkage Time (hrs)','Break Time (hrs)']].rename(
            columns={'CU% (Based on Running Time)':'Average Capacity Utilization (%)','Efficiency (%)':'Average Efficiency (%)','Utilization (%)':'Average Utilization (%)','Productive Time (hrs)':'Average Productive Hours','Shrinkage Time (hrs)':'Average Shrinkage Hours','Break Time (hrs)':'Average Break Hours'}),2)

    
    try:
        for i in row_id:
            row=Para[i]
            if i<3:
                tt='Percentage (%)'
            else:
                tt='Hours'
        x=[x for x in GPH_Stats_Graph_2.index.get_level_values(1)]
        y=[x for x in GPH_Stats_Graph_2[row]]
        fig=go.Figure(go.Scatter(x=x,y=y,mode='lines+markers'))
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                    tickfont=dict(color='white',size=10))
        fig.update_yaxes(gridcolor='#121212',title_text=tt,title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
        fig.update_layout(title=row,plot_bgcolor='black',paper_bgcolor='black',
                          font=dict(color='white'),height=300,margin={'l':0,'b':0},title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    except TypeError:
        fig=No_Data_Available()
        
    return fig

@app.callback(
Output('PKT_Graph_2','figure'),
[Input('DateRange','start_date'),
Input('DateRange','end_date')])

def Update_PKT_Graph_2(Start_Date,End_Date):
    
    PKT_Graph_2=np.round(PKT.loc[(PKT.Date>=Start_Date) & (PKT.Date<=End_Date)].groupby([PKT.Date.dt.strftime('%Y-%m'),PKT.Date.dt.strftime('%B-%Y')]).mean(),2)
    
    if PKT_Graph_2.empty==False:
        x=[x for x in PKT_Graph_2.index.get_level_values(1)]
        y=[x for x in PKT_Graph_2['PKT (%)']]
        fig=go.Figure(go.Scatter(x=x,y=y,mode='lines+markers'))
        fig.update_xaxes(gridcolor='#121212',title_text='Date Range',title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10))
        fig.update_yaxes(gridcolor='#121212',title_text='Percentage (%)',title_font=dict(size=12,color='white'),
                        tickfont=dict(color='white',size=10),tickmode='linear',tick0=0,dtick=20)
        fig.update_layout(plot_bgcolor='black',paper_bgcolor='black',
                              font=dict(color='white'),height=300,title_xanchor='center',title_yanchor='top',title_x=.5,title_y=.9)
    else:
        fig=No_Data_Available()
    
    return fig


# In[58]:


if __name__=='__main__':
    app.run_server(debug=True,use_reloader=False)

