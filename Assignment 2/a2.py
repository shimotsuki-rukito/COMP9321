import json
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from flask import Flask, request, send_file
from flask_restx import Resource, Api, fields
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app)

def parse_date(date_str):
    return datetime.strptime(date_str, "%d-%m-%Y").date()

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M:%S").time()

def is_overlapping(start_time1, end_time1, start_time2, end_time2):
    return start_time1 < end_time2 and start_time2 < end_time1

location_fields = api.model('Location', {
    'street': fields.String,
    'suburb': fields.String,
    'state': fields.String,
    'post-code': fields.String
})

event_fields = api.model('Event', {
    'id': fields.Integer,
    'name': fields.String,
    'date': fields.String,
    'from': fields.String(attribute='start_time'),
    'to': fields.String(attribute='end_time'),
    'location': fields.Nested(location_fields),
    'description': fields.String,
    'last_update': fields.String,
    'datetime': fields.String(attribute=lambda event: f"{event['date']} {event['start_time']}")
})

columns = ['id', 'name', 'date', 'start_time', 'end_time', 'location', 'description', 'last_update']
df = pd.DataFrame(columns=columns)
df.set_index('id', inplace=True)


@api.route('/events')
class EventsResource(Resource):
    @api.expect(event_fields, validate=True)
    def post(self):
        data = request.json
        date = parse_date(data['date'])
        start_time = parse_time(data['from'])
        end_time = parse_time(data['to'])
        location = data['location']
        description = data.get('description', '')

        for idx, event in df.iterrows():
            if event['date'] == date and is_overlapping(event['start_time'], event['end_time'], start_time, end_time):
                return {"message": "Event time is overlapping with an existing event."}, 400

        id = len(df) + 1
        new_event = {
            "id": id,
            "name": data['name'],
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "location": json.dumps(location),
            "description": description,
            "last_update": datetime.now()
        }
        df.loc[id] = new_event

        return {
            "id": new_event['id'],
            "last-update": new_event['last_update'].strftime("%Y-%m-%d %H:%M:%S"),
            "_links": {
                "self": {
                    "href": f"/events/{new_event['id']}"
                }
            }
        }, 201

    @api.param('order',
               'A comma-separated string value to sort the list based on the given criteria. Default is "+id".')
    @api.param('page', 'The page number for pagination. Default is 1.')
    @api.param('size', 'The number of events per page for pagination. Default is 10.')
    @api.param('filter',
               'A comma-separated string value to filter the attributes to be shown for each event. Default is "id,name".')
    def get(self):
        order = request.args.get('order', '+id')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        filter_str = request.args.get('filter', 'id,name')
        filter_attrs = filter_str.split(',')

        sorting_keys = order.split(',')
        df_sorted = df.sort_values(
            by=[key[1:] for key in sorting_keys],
            ascending=[key.startswith('+') for key in sorting_keys]
        )

        start_idx = (page - 1) * size
        end_idx = page * size
        df_paginated = df_sorted.iloc[start_idx:end_idx]

        events = []
        for _, event in df_paginated.iterrows():
            filtered_event = {attr: event[attr] for attr in filter_attrs if attr in event}
            events.append(filtered_event)

        response = {
            "page": page,
            "page-size": size,
            "events": events,
            "_links": {
                "self": {
                    "href": f"/events?order={order}&page={page}&size={size}&filter={filter_str}"
                }
            }
        }

        if end_idx < len(df_sorted):
            response["_links"]["next"] = {
                "href": f"/events?order={order}&page={page + 1}&size={size}&filter={filter_str}"
            }

        return response, 200


@api.route('/events/<int:event_id>')
class EventResource(Resource):
    def get(self, event_id):
        event = df.loc[event_id]
        if event.empty:
            return {"message": f"Event with ID {event_id} not found."}, 404

        date = event['date']
        lat = -33.865143  # latitude of Sydney, Australia
        lng = 151.209900  # longitude of Sydney, Australia
        holiday_api = f"https://date.nager.at/api/v2/publicholidays/{date.year}/AU"
        weather_api = f"https://www.7timer.info/bin/civil.php?lat={lat}&lng={lng}&ac=1&unit=metric&output=json&product=two"
        holiday_data = requests.get(holiday_api).json()
        weather_data = requests.get(weather_api).json()

        metadata = {}
        holiday = ""
        for holiday_entry in holiday_data:
            if holiday_entry['date'] == date.strftime('%Y-%m-%d'):
                holiday = holiday_entry['name']
                break
        metadata['wind-speed'] = f"{weather_data['dataseries'][0]['wind10m']['speed']} KM"
        metadata['weather'] = f"{weather_data['dataseries'][0]['weather']}"
        metadata['humidity'] = f"{weather_data['dataseries'][0]['rh2m']}"
        metadata['temperature'] = f"{weather_data['dataseries'][0]['temp2m']} C"
        metadata['holiday'] = holiday
        metadata['weekend'] = date.weekday() >= 5

        previous_event = None
        next_event = None
        for idx, event_row in df.iterrows():
            if idx == event_id:
                continue
            if event_row['date'] < date:
                if previous_event is None or previous_event['date'] < event_row['date']:
                    previous_event = event_row
            else:
                if next_event is None or next_event['date'] > event_row['date']:
                    next_event = event_row

        response = {
            "id": event_id,
            "last-update": event['last_update'].strftime("%Y-%m-%d %H:%M:%S"),
            "name": event['name'],
            "date": date.strftime("%d-%m-%Y"),
            "from": event['start_time'].strftime("%H:%M"),
            "to": event['end_time'].strftime("%H:%M"),
            "location": json.loads(event['location']),
            "description": event['description'],
            "_metadata": metadata,
            "_links": {
                "self": {
                    "href": f"/events/{event_id}"
                }
            }
        }
        if previous_event is not None:
            response["_links"]["previous"] = {"href": f"/events/{previous_event.name}"}
        if next_event is not None:
            response["_links"]["next"] = {"href": f"/events/{next_event.name}"}

        return response, 200

    def delete(self, event_id):
        if event_id not in df.index:
            return {"message": f"Event with ID {event_id} not found."}, 404

        df.drop(event_id, inplace=True)
        return {
                   "message": f"The event with id {event_id} was removed from the database!",
                   "id": event_id
               }, 200

    @api.expect(event_fields, validate=True)
    def patch(self, event_id):
        event = df.loc[event_id]
        if event.empty:
            return {"message": f"Event with ID {event_id} not found."}, 404

        data = request.json
        for key, value in data.items():
            if key == 'date':
                event['date'] = parse_date(value)
            elif key == 'from':
                event['start_time'] = parse_time(value)
            elif key == 'to':
                event['end_time'] = parse_time(value)
            elif key == 'location':
                event['location'] = json.dumps(value)
            elif key in ['name', 'description', 'last_update']:
                event[key] = value

        df.loc[event_id] = event

        return {
            "id": event_id,
            "last-update": event['last_update'].strftime("%Y-%m-%d %H:%M:%S"),
            "_links": {
                "self": {
                    "href": f"/events/{event_id}"
                }
            }
        }, 200


@api.route('/weather')
class WeatherResource(Resource):
    @api.param('date', 'The date for the weather forecast. Format: "dd-mm-yyyy".')
    def get(self):
        date_str = request.args.get('date')
        if not date_str:
            return {"message": "Missing required parameter 'date'."}, 400

        try:
            date = parse_date(date_str)
        except ValueError:
            return {"message": "Invalid date format. Must be 'dd-mm-yyyy'."}, 400

        cities = {
            "Sydney": [-33.865143, 151.209900],
            "Melbourne": [-37.813628, 144.963058],
            "Brisbane": [-27.470125, 153.021072],
            "Adelaide": [-34.928181, 138.599931],
            "Perth": [-31.952712, 115.860480],
            "Hobart": [-42.880554, 147.324997],
            "Darwin": [-12.462827, 130.841782],
            "Canberra": [-35.282001, 149.128998]
        }

        weather_data = {}
        for city, coords in cities.items():
            lat, lng = coords
            weather_api = f"https://www.7timer.info/bin/civil.php?lat={lat}&lng={lng}&ac=1&unit=metric&output=json&product=two"
            response = requests.get(weather_api).json()
            init_time = datetime.strptime(response['init'], '%Y%m%d%H')
            for series in response['dataseries']:
                series_time = init_time + timedelta(hours=series['timepoint'])
                if series_time.date() == date:
                    weather_data[city] = series
                    break

        if weather_data:
            gdf = gpd.GeoDataFrame(list(weather_data.items()), columns=["City", "Weather"],
                                   geometry=gpd.points_from_xy([coords[1] for coords in cities.values()],
                                                               [coords[0] for coords in cities.values()]))
            gdf["Weather"] = gdf["Weather"].astype(str)
            gdf = gdf.set_crs(epsg=4326).to_crs(epsg=3857)

            fig, ax = plt.subplots(figsize=(10, 10))
            gdf.plot(ax=ax, column="Weather", legend=True, markersize=100, cmap="coolwarm", categorical=True)
            ctx.add_basemap(ax, source=ctx.providers.Stamen.Terrain)
            ax.set_axis_off()

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            return send_file(buf, mimetype='image/png')
        else:
            return {"message": "No weather data available for the requested date."}, 404


@api.route('/events/statistics')
class EventStatisticsResource(Resource):
    @api.param('format', 'The format of the statistics output. Can be "json" or "image". Default is "json".')
    def get(self):
        output_format = request.args.get('format', 'json')
        if output_format not in ['json', 'image']:
            return {"message": "Invalid format. Must be 'json' or 'image'."}, 400

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        month_start = today.replace(day=1)
        month_end = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1))

        total = len(df)
        total_current_week = len(df[(df['date'] >= week_start) & (df['date'] <= week_end)])
        total_current_month = len(df[(df['date'] >= month_start) & (df['date'] <= month_end)])
        #per_days = df.groupby('date').size().to_dict()
        per_days = {date.strftime('%Y-%m-%d'): count for date, count in df.groupby('date').size().items()}

        if output_format == 'json':
            return {
                       "total": total,
                       "total-current-week": total_current_week,
                       "total-current-month": total_current_month,
                       "per-days": per_days
                   }, 200
        elif output_format == 'image':
            fig, ax = plt.subplots()
            dates = list(per_days.keys())
            events_count = list(per_days.values())
            ax.bar(dates, events_count)
            ax.set_xlabel('Dates')
            ax.set_ylabel('Number of Events')
            ax.set_title('Number of Events per Day')

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            return send_file(buf, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)
