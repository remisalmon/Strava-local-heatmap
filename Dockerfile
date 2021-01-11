FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./strava_local_heatmap.py" ]

# Example to use bounds, this will only print Manhattan in NY
#CMD [ "python", "./strava_local_heatmap.py", "--bounds", "40.685845", "40.910918", "-74.048278", "-73.817411" ]