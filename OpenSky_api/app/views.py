from django.shortcuts import render, redirect
import requests as rq
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.tile_providers import get_provider,STAMEN_TERRAIN
from bokeh.models import HoverTool,LabelSet,ColumnDataSource
import numpy as np
import json
# Create your views here.

def landing_page(request):
    return render(request, "others/landingpage.html")


def flight_tracking(requests):
    #FUNCTION TO CONVERT GCS WGS84 TO WEB MERCATOR
    #POINT
    def wgs84_web_mercator_point(lon,lat):
        k = 6378137
        x= lon * (k * np.pi/180.0)
        y= np.log(np.tan((90 + lat) * np.pi/360.0)) * k
        return x,y
    #DATA FRAME
    def wgs84_to_web_mercator(df, lon="long", lat="lat"):
        k = 6378137
        df["x"] = df[lon] * (k * np.pi/180.0)
        df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k
        return df
    #AREA EXTENT COORDINATE WGS4
    lon_min,lat_min=-125.974,30.038
    lon_max,lat_max=-68.748,52.214
    #COORDINATE CONVERSION
    xy_min=wgs84_web_mercator_point(lon_min,lat_min)
    xy_max=wgs84_web_mercator_point(lon_max,lat_max)
    #COORDINATE RANGE IN WEB MERCATOR
    x_range,y_range=([xy_min[0],xy_max[0]], [xy_min[1],xy_max[1]])
    #REST API QUERY
    user_name=''
    password=''
    url_data='https://'+user_name+':'+password+'@opensky-network.org/api/states/all?'+'lamin='+str(lat_min)+'&lomin='+str(lon_min)+'&lamax='+str(lat_max)+'&lomax='+str(lon_max)
    response=rq.get(url_data).json()
    with open('data.html', 'w') as outfile:
        json.dump(response, outfile)
    # init bokeh column data source
    flight_source = ColumnDataSource({
        'icao24':[],'callsign':[],'origin_country':[],
        'time_position':[],'last_contact':[],'long':[],'lat':[],
        'baro_altitude':[],'on_ground':[],'velocity':[],'true_track':[],
        'vertical_rate':[],'sensors':[],'geo_altitude':[],'squawk':[],'spi':[],'position_source':[],'x':[],'y':[],
        'rot_angle':[],'url':[]
    })
    #LOAD TO PANDAS DATAFRAME
    col_name=['icao24','callsign','origin_country','time_position','last_contact','long','lat','baro_altitude','on_ground','velocity',       
    'true_track','vertical_rate','sensors','geo_altitude','squawk','spi','position_source']
    flight_data=response['states']
    flight_df=pd.DataFrame(flight_data,columns=col_name)
    wgs84_to_web_mercator(flight_df)
    flight_df=flight_df.fillna('No Data')
    flight_df['rot_angle']=flight_df['true_track']*-1
    icon_url='https://img.icons8.com/emoji/48/000000/airplane-emoji.png' #icon url
    flight_df['url']=icon_url
    # CONVERT TO BOKEH DATASOURCE AND STREAMING
    n_roll=len(flight_df.index)
    flight_source.stream(flight_df.to_dict(orient='list'),n_roll)
    #FIGURE SETTING
    p=figure(x_range=x_range,y_range=y_range,x_axis_type='mercator',y_axis_type='mercator',sizing_mode='scale_width',plot_height=300)
    #PLOT BASEMAP AND AIRPLANE POINTS
    tile_prov=get_provider(STAMEN_TERRAIN)
    p.add_tile(tile_prov,level='image')
    p.image_url(url='url', x='x', y='y',source=flight_source,anchor='center',angle_units='deg',angle='rot_angle',h_units='screen',w_units='screen',w=40,h=40)
    p.circle('x','y',source=flight_source,fill_color='red',hover_color='yellow',size=5,fill_alpha=0.8,line_width=0)
    #HOVER INFORMATION AND LABEL
    my_hover=HoverTool()
    my_hover.tooltips=[('Call sign','@callsign'),('Origin Country','@origin_country'),('velocity(m/s)','@velocity'),('Altitude(m)','@baro_altitude')]
    labels = LabelSet(x='x', y='y', text='callsign', level='glyph',
                x_offset=5, y_offset=5, source=flight_source, render_mode='canvas',background_fill_color='white',text_font_size="8pt")
    p.add_tools(my_hover)
    p.add_layout(labels)
    show(p)   
    return redirect("landing_page")