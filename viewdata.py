import pandas as pd
import geopandas as gpd
from geodatasets import get_path
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.widgets import RadioButtons

os.environ["SHAPE_RESTORE_SHX"]="YES"

#load election data
election_data_2020 = pd.read_csv("az20.csv")
election_data_2024 = pd.read_csv("az24.csv")

#create election data columns for vote margins
election_data_2020['vote_margin'] = election_data_2020['votes_republican'] - election_data_2020['votes_democrat']
election_data_2020['percentage_margin'] = ((election_data_2020['votes_republican'] - election_data_2020['votes_democrat']) / election_data_2020['total_ballots']) * 100

election_data_2024['vote_margin'] = election_data_2024['votes_republican'] - election_data_2024['votes_democrat']
election_data_2024['percentage_margin'] = ((election_data_2024['votes_republican'] - election_data_2024['votes_democrat']) / election_data_2024['total_ballots']) * 100

#load county map shapefile data
shapefile_path = "az_county/az_county.shp"
counties = gpd.read_file(shapefile_path)

#clean data on county name column to match between datasets
counties["county"] = counties["NAME"].str.upper().str.strip() 
election_data_2020["county"] = election_data_2020["county"].str.upper().str.strip()
election_data_2024["county"] = election_data_2024["county"].str.upper().str.strip()

#merge shapefile with election results data on the county column
counties_2020 = counties.merge(election_data_2020, on="county")
counties_2024 = counties.merge(election_data_2024, on="county")

#define discrete bins for vote margin
bins = [-float('inf'), -10, -5, 0, 5, 10, float('inf')] 
labels = ['Strong Democrat', 'Moderate Democrat', 'Lean Democrat', 'Lean Republican','Moderate Republican', 'Strong Republican']

counties_2020['percentage_margin_category'] = pd.cut(counties_2020['percentage_margin'], bins=bins, labels=labels)
counties_2024['percentage_margin_category'] = pd.cut(counties_2024['percentage_margin'], bins=bins, labels=labels)
counties_data = counties_2024

#create colormap for the discrete categories
cmap = mcolors.ListedColormap(
    ['darkblue', 'blue', 'lightblue', 'lightcoral', 'red','darkred'], 
)

#format margins as D+X and R+X
def format_margin(margin):
    if margin > 0:
        return f"R+{margin:.1f}" 
    elif margin < 0:
        return f"D+{-margin:.1f}"

#plot function to update map based on selected year
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
plt.title("Arizona Presidential Election Results by County (Percentage Margin)", fontsize=16)
def update_plot(year):
    if year == 2020:
        counties_data = counties_2020
    elif year == 2024:
        counties_data = counties_2024
    
    #display data on map
    plot = counties_data.plot(
        column="percentage_margin_category", 
        cmap=cmap, 
        legend=True,
        ax=ax,
        edgecolor='black'
    )
    ax.set_title(f"Arizona {year} Presidential Election Results by County (Percentage Margin)")

    #mouse hover event handler
    def on_hover(event):
        if event.inaxes == ax:  #ensure the click is within the map
            #convert cursor coordinates to GeoDataFrame CRS
            coords = gpd.points_from_xy([event.xdata], [event.ydata], crs=counties.crs)
            point = coords[0]  # Only one point

            #determine which county was clicked
            clicked_2020 = counties_2020[counties_2020.geometry.contains(point)]
            clicked_2024 = counties_2024[counties_2024.geometry.contains(point)]
            if not clicked_2020.empty and not clicked_2024.empty:
                county_2020 = clicked_2020.iloc[0]
                county_2024 = clicked_2024.iloc[0]
                county_name = county_2020['county']

                #format margin as D+X or R+X
                margin_2020 = format_margin(county_2020['percentage_margin'])
                margin_2024 = format_margin(county_2024['percentage_margin'])
                annotation_text = (
                    f"{county_name}\n"
                    f"2020: {margin_2020} with {county_2020['turnout_percent']:.2f}% turnout\n"
                    f"2024: {margin_2024} with {county_2024['turnout_percent']:.2f}% turnout"
                )
                if hasattr(on_hover, "annotation"):
                    on_hover.annotation.remove()  # Remove the previous annotation
                on_hover.annotation = ax.annotate(
                    annotation_text,
                    xy=(event.xdata, event.ydata),
                    xytext=(event.xdata + 1, event.ydata + 1),
                    bbox=dict(boxstyle="round", fc="w"),
                    fontsize=10,
                    arrowprops=dict(arrowstyle="->")
                )
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    plt.show()

#create radio buttons to switch between 2020 and 2024 election results
def radio_func(label):
    #switch between datasets based on selected radio button
    if label == "2020":
        update_plot(2020)
    elif label == "2024":
        update_plot(2024)

radio = RadioButtons(
    ax=plt.axes([0.85, 0.2, 0.1, 0.15]),
    labels=["2020", "2024"],
    active=1,  #default to 2024
)
radio.on_clicked(radio_func)

update_plot(2024)

plt.show()