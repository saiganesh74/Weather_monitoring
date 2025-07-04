import requests
import difflib
import folium
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from io import BytesIO
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime

API_TOKEN = "2a1ad16a7202af381f23b833c11b3212aa49c5b7"

# Short form mappings
state_short_forms = {
    "AP": "Andhra Pradesh", "TS": "Telangana", "MH": "Maharashtra",
    "TN": "Tamil Nadu", "KA": "Karnataka", "DL": "Delhi", "WB": "West Bengal",
    "GJ": "Gujarat", "RJ": "Rajasthan", "MP": "Madhya Pradesh", "UP": "Uttar Pradesh"
}

city_short_forms = {
    "Hyd": "Hyderabad", "Blr": "Bengaluru", "Bom": "Mumbai", "Chenn": "Chennai",
    "Kol": "Kolkata", "Del": "Delhi", "Jaip": "Jaipur", "Luck": "Lucknow"
}

location_map = {
    "India": {
        "Telangana": ["Hyderabad", "Warangal"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
        "Tamil Nadu": ["Chennai", "Madurai"],
        "Karnataka": ["Bengaluru", "Mysuru"],
        "Delhi": ["Delhi"],
        "West Bengal": ["Kolkata"],
        "Rajasthan": ["Jaipur"],
        "Uttar Pradesh": ["Lucknow"]
    }
}

BG_COLOR = "#111827"
FG_COLOR = "#38bdf8"

root = Tk()
root.title("🌍 Environment Dashboard")
root.geometry("1100x750")
root.configure(bg=BG_COLOR)

notebook = ttk.Notebook(root)
notebook.pack(fill=BOTH, expand=True)

# ------------------ AQI TAB ------------------
aqitab = Frame(notebook, bg=BG_COLOR)
notebook.add(aqitab, text="🌫️ AQI Data")

input_frame = Frame(aqitab, bg=BG_COLOR)
input_frame.pack(pady=15)

Label(input_frame, text="State:", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 18, "bold")).grid(row=0, column=0, padx=5)
state_entry = Entry(input_frame, font=("Arial", 18), width=20)
state_entry.grid(row=0, column=1)

Label(input_frame, text="City:", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 18, "bold")).grid(row=0, column=2, padx=5)
city_entry = Entry(input_frame, font=("Arial", 18), width=20)
city_entry.grid(row=0, column=3)

output_frame = Frame(aqitab, bg=BG_COLOR)
output_frame.pack(pady=10)

def correct_input(user_input, options, short_forms={}):
    user_input = user_input.strip()
    if user_input in short_forms:
        return short_forms[user_input]
    matches = difflib.get_close_matches(user_input, options, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_aqi_category(aqi):
    if aqi <= 50: return "Good", "green"
    elif aqi <= 100: return "Moderate", "yellow"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups", "orange"
    elif aqi <= 200: return "Unhealthy", "red"
    elif aqi <= 300: return "Very Unhealthy", "purple"
    else: return "Hazardous", "maroon"

def get_aqi_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={API_TOKEN}"
    response = requests.get(url).json()
    return response if response["status"] == "ok" else None

def show_aqi():
    for widget in output_frame.winfo_children():
        widget.destroy()

    country = "India"
    states = list(location_map[country].keys())

    state = correct_input(state_entry.get(), states, state_short_forms)
    if not state:
        Label(output_frame, text="Invalid state", fg="red", bg=BG_COLOR).pack()
        return

    cities = location_map[country][state]
    city = correct_input(city_entry.get(), cities, city_short_forms)
    if not city:
        Label(output_frame, text="Invalid city", fg="red", bg=BG_COLOR).pack()
        return

    search_url = f"https://api.waqi.info/search/?token={API_TOKEN}&keyword={city}"
    response = requests.get(search_url).json()
    if response["status"] != "ok" or not response["data"]:
        Label(output_frame, text="❌ No AQI station found.", fg="red", bg=BG_COLOR).pack()
        return

    lat, lon = response["data"][0]["station"]["geo"]
    data = get_aqi_data(lat, lon)
    if not data:
        Label(output_frame, text="❌ Failed to fetch AQI data.", fg="red", bg=BG_COLOR).pack()
        return

    aqi_data = data["data"]
    aqi = aqi_data["aqi"]
    category, color = get_aqi_category(aqi)
    iaqi = aqi_data["iaqi"]

    Label(output_frame, text=f"📍 AQI Report - {city}", font=("Arial", 18, "bold"), fg=FG_COLOR, bg=BG_COLOR).pack(pady=10)
    details = f"""
Station: {aqi_data['city']['name']}
AQI: {aqi} ({category})
PM2.5: {iaqi.get('pm25', {}).get('v', 'N/A')} µg/m³
PM10 : {iaqi.get('pm10', {}).get('v', 'N/A')} µg/m³
CO   : {iaqi.get('co', {}).get('v', 'N/A')} ppm
NO₂  : {iaqi.get('no2', {}).get('v', 'N/A')} ppb
O₃   : {iaqi.get('o3', {}).get('v', 'N/A')} ppb
SO₂  : {iaqi.get('so2', {}).get('v', 'N/A')} ppb
    """
    Label(output_frame, text=details, justify=LEFT, font=("Courier", 11), fg="white", bg=BG_COLOR).pack()

    # Chart
    pollutants = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2']
    values = [iaqi.get(p, {}).get('v', 0) for p in pollutants]
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=BG_COLOR)
    bars = ax.bar(pollutants, values, color='skyblue')
    ax.set_title('Pollutant Levels', color=FG_COLOR)
    ax.tick_params(colors=FG_COLOR)
    for bar in bars:
        ax.text(bar.get_x() + 0.15, bar.get_height() + 0.3, f'{bar.get_height():.1f}', color="white")

    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", facecolor=BG_COLOR)
    buf.seek(0)
    img = Image.open(buf).resize((400, 250))
    tkimg = ImageTk.PhotoImage(img)
    Label(output_frame, image=tkimg, bg=BG_COLOR).pack(pady=10)
    Label(output_frame, text="(Click button below to open map)", bg=BG_COLOR, fg=FG_COLOR).pack()

    fmap = folium.Map(location=[lat, lon], zoom_start=11)
    folium.Marker([lat, lon], tooltip=f"AQI: {aqi}").add_to(fmap)
    fmap.save("AQI_Map.html")
    Button(output_frame, text="🗺️ View Map", bg="#3085d6", fg="white", command=lambda: webbrowser.open("AQI_Map.html")).pack(pady=5)

Button(input_frame, text="Show AQI", font=("Arial", 12), command=show_aqi, bg="#1f4068", fg="white").grid(row=0, column=4, padx=10)

# ------------------ CO2 TAB ------------------
co2_tab = Frame(notebook, bg=BG_COLOR)
notebook.add(co2_tab, text="🌍 CO₂ Emission")

csv_path = "carbon-monitor-GLOBAL-maingraphdatas.csv"
df = pd.read_csv(csv_path)
df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors='coerce')
df = df[df["country"] == "India"]
df["MtCO2 per day"] = pd.to_numeric(df["MtCO2 per day"], errors='coerce')

all_dates = df["date"].dt.date.unique()
years = sorted(set(d.year for d in all_dates))
months = list(range(1, 13))
days = list(range(1, 32))
sectors = ["Total"] + sorted(df["sector"].unique())

controls = Frame(co2_tab, bg=BG_COLOR)
controls.pack(pady=15)

Label(controls, text="Year", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 12)).grid(row=0, column=0, padx=5)
year_cb = ttk.Combobox(controls, values=years, width=10)
year_cb.set(years[0])
year_cb.grid(row=1, column=0)

Label(controls, text="Month", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 12)).grid(row=0, column=1, padx=5)
month_cb = ttk.Combobox(controls, values=months, width=10)
month_cb.set(1)
month_cb.grid(row=1, column=1)

Label(controls, text="Day", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 12)).grid(row=0, column=2, padx=5)
day_cb = ttk.Combobox(controls, values=days, width=10)
day_cb.set(1)
day_cb.grid(row=1, column=2)

Label(controls, text="Sector", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 12)).grid(row=0, column=3, padx=5)
sector_cb = ttk.Combobox(controls, values=sectors, width=20)
sector_cb.set("Total")
sector_cb.grid(row=1, column=3)

plot_frame = Frame(co2_tab, bg=BG_COLOR)
plot_frame.pack(fill=BOTH, expand=True)

fig, ax = plt.subplots(figsize=(12, 5))
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

def plot_emission():
    try:
        selected_sector = sector_cb.get()
        selected_date = datetime.strptime(f"{year_cb.get()}-{int(month_cb.get()):02d}-{int(day_cb.get()):02d}", "%Y-%m-%d").date()
        ax.clear()

        if selected_sector == "Total":
            data_df = df.groupby("date")["MtCO2 per day"].sum().reset_index()
            color = '#FF0033'
            title = "📈 Total CO₂ Emissions Over Time"
        else:
            data_df = df[df["sector"] == selected_sector].groupby("date")["MtCO2 per day"].sum().reset_index()
            color = '#36454F'
            title = f"📈 {selected_sector} CO₂ Emissions Over Time"

        ax.plot(data_df["date"], data_df["MtCO2 per day"], color=color, label=selected_sector)
        ax.axvline(selected_date, color='red', linestyle='--', label='Selected Date')
        ax.set_title(title, fontsize=14, color=FG_COLOR)
        ax.set_xlabel("Date", color=FG_COLOR)
        ax.set_ylabel("MtCO₂ per day", color=FG_COLOR)
        ax.grid(True)
        ax.legend()
        ax.tick_params(colors=FG_COLOR)
        fig.tight_layout()
        canvas.draw()
    except Exception as e:
        print("❌", e)

Button(controls, text="📊 Show Emission", command=plot_emission,
       font=("Arial", 11), bg="#1f4068", fg="white").grid(row=1, column=4, padx=10)

root.mainloop()
# guys this basic working you can update it 
