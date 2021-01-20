import socket
import requests
import json
import sys
from PyQt5 import QtWidgets, QtCore
from Obj import GeoLocation, WeatherForecast
from Layout import server

# socket port and address - UDP
udp_ip = '127.0.0.1'
udp_port = 8014
fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

weather_api_key = '1fdb699c63b1b0850fc992244633f070'  # for weather
mode = 'json'
units = 'metric'
exclude = ',minutely,'

# global variable for user location
geoSelection = GeoLocation.GeoLocation('', '', '', '', '', '')
current = WeatherForecast.CurrentWeather('', '', '', '', '', '', '', '', '', '', '', '', '')
daily = WeatherForecast.DailyForecast('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
hourly = WeatherForecast.HourlyForecast('', '', '', '', '', '')


# also get the current weather for user
def getCurrentWeather(lat, long, key):
    weather_url = 'https://api.openweathermap.org/data/2.5/onecall?' \
                  'lat=' + lat + \
                  '&lon=' + long + \
                  '&mode=' + mode + \
                  '&units=' + units + \
                  '&exclude=,' + exclude + \
                  '&appid=' + weather_api_key
    r = requests.get(weather_url)
    weather = json.loads(r.text)
    print(weather)
    if key == 0:
        # get current weather
        curr_dt = weather['current']['dt']
        curr_sunrise = weather['current']['sunrise']
        curr_sunset = weather['current']['sunset']
        curr_temp = weather['current']['temp']
        curr_feel = weather['current']['feels_like']
        curr_pressure = weather['current']['pressure']
        curr_humidity = weather['current']['humidity']
        curr_visibility = weather['current']['visibility']
        curr_windSpeed = weather['current']['wind_speed']
        curr_clouds = weather['current']['clouds']
        curr_weatherMain = ''
        curr_weatherDesc = ''
        curr_weatherIcon = ''
        for k in weather['current']['weather']:
            curr_weatherMain = k['main']
            curr_weatherDesc = k['description']
            curr_weatherIcon = k['icon']

        current = WeatherForecast.CurrentWeather(curr_dt, curr_sunrise, curr_sunset, curr_temp, curr_feel,
                                                 curr_pressure, curr_humidity, curr_visibility, curr_windSpeed,
                                                 curr_weatherMain, curr_weatherDesc, curr_weatherIcon, curr_clouds)
        # get daily forecast
        dailyForecast = []
        for i in weather['daily']:
            daily_dt = i['dt']
            daily_sunrise = i['sunrise']
            daily_sunset = i['sunset']
            daily_tempDay = i['temp']['day']
            daily_tempMin = i['temp']['min']
            daily_tempMax = i['temp']['max']
            daily_tempNight = i['temp']['night']
            daily_tempEve = i['temp']['eve']
            daily_tempMorn = i['temp']['morn']
            daily_pressure = i['pressure']
            daily_humidity = i['humidity']
            daily_windSpeed = i['wind_speed']
            daily_cloud = i['clouds']
            daily_weatherMain, daily_weatherDesc, daily_weatherIcon = '', '', ''
            for k in i['weather']:
                daily_weatherMain = k['main']
                daily_weatherDesc = k['description']
                daily_weatherIcon = k['icon']
            daily = WeatherForecast.DailyForecast(daily_dt, daily_sunrise, daily_sunset, daily_tempDay, daily_tempMorn,
                                                  daily_tempEve, daily_tempNight, daily_tempMin, daily_tempMax,
                                                  daily_pressure,
                                                  daily_humidity, daily_windSpeed, daily_weatherMain, daily_weatherDesc,
                                                  daily_weatherIcon, daily_cloud)
            dailyForecast.append(daily)

        # hourly forecast
        hourlyForecast = []
        for i in weather['hourly']:
            hourly_dt = i['dt']
            hourly_temp = i['temp']
            hourly_windSpeed = i['wind_speed']
            hourly_clouds = i['clouds']
            hourly_weatherDesc, hourly_weatherIcon = '', ''
            for k in i['weather']:
                hourly_weatherDesc = k['description']
                hourly_weatherIcon = k['icon']
            hourly = WeatherForecast.HourlyForecast(hourly_dt, hourly_temp, hourly_windSpeed, hourly_weatherDesc,
                                                    hourly_weatherIcon, hourly_clouds)
            hourlyForecast.append(hourly)

        return current, dailyForecast, hourlyForecast
    else:
        print(weather)


class ServerThread(QtCore.QThread):

    # emit to gui (text, code)
    # if code == log text update for logsArea
    # else text update for online list

    updateGui = QtCore.pyqtSignal(str, str)

    def run(self):
        while True:
            r = fd.recvfrom(10000)
            client_address = r[1]
            text = r[0].decode().split('_')
            request = text[0]
            # a for connect request
            if request == 'a':
                client_ip, client_port = client_address
                self.updateGui.emit('Receiving connect of Client: ' + str(client_port), 'logs')
                self.updateGui.emit(str(client_port), 'onl')
            # b for weather request
            elif request == 'b':
                geo = text[1].split(',')

                self.updateGui.emit("\n-----------------------------------", 'logs')
                self.updateGui.emit("\nGetting current  weather of client: " + str(
                    client_address), 'logs')
                currWeather, dailyList, hourlyList = getCurrentWeather(geo[0], geo[1], 0)

                # weather send  0 weather _ 1 temp _ 2 Humidity _ 3 Visibility _ 4 Wind Speed _ 5 icon
                # 6 sun rise _ 7 sun set _ 8 Feel _ 9 cloud _ 10 Pressure
                nowWeather = '{}_{}_{}_{}_{}_{}_{}_{}_{}_{}_{}' \
                             ''.format(currWeather.getMainWeather(), currWeather.getTemp(), currWeather.getHumidity(),
                                       currWeather.getVisibility(), currWeather.getWindSpeed(),
                                       currWeather.getWeatherIcon(), currWeather.getSunriseTime(),
                                       currWeather.getSunSetTime(), currWeather.getTempFeelsLike(),
                                       currWeather.getPercentClouds(), currWeather.getPressure())
                # 0 dt, 1 tempmin, 2 tepmmax, 3 weather, 4 weatherDesc, 5 icon, 6 morTemp, 7 dayTemp,
                # 8 eveTemp, 9 nightTemp, 10 sunrise, 11 sunset
                dailyForeCast = ''
                for i in dailyList:
                    dailyFore = '{}_{}_{}_{}_{}_{}_{}_{}_{}_{}_{}_{}' \
                                ''.format(i.getDtInDate(), i.getTempMin(), i.getTempMax(), i.getMainWeather(),
                                          i.getWeatherDescription(), i.getWeatherIcon(),
                                          i.getTempAtMorning(), i.getTempAtDay(), i.getTempAtEvening(),
                                          i.getTempAtNight(), i.getSunriseTime(), i.getSunSetTime())
                    dailyForeCast += '+{}'.format(dailyFore)

                # 0 dt, 1 temp, 2 icon, 3 desc, 4 wind, 5 cloud
                hourlyForecast = ''
                for i in hourlyList:
                    hourlyFore = '{}_{}_{}_{}_{}_{}' \
                                 ''.format(i.getDtInTime(), i.getTemp(), i.getWeatherIcon(), i.getWeatherDescription()
                                           , i.getWindSpeed(), i.getPercentClouds())
                    hourlyForecast += '+{}'.format(hourlyFore)

                mess = '{}--split--{}--split--{}'.format(nowWeather, dailyForeCast, hourlyForecast).encode()
                self.updateGui.emit("\nForwarding information......", 'logs')
                self.updateGui.emit("\n-----------------------------------", 'logs')

                fd.sendto(mess, client_address)


class Server(QtWidgets.QFrame, server.Ui_ServerFrame):
    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # thread
        self.work = ServerThread()

        # setup socket
        fd.bind((udp_ip, udp_port))

        # Gui
        self.logsTextArea.appendPlainText("Server started..\nWaiting for connection...")

        # start thread
        self.startThread()

    def startThread(self):
        self.work.updateGui.connect(self.updateGui)

        try:
            self.work.start()
        except (SystemExit, SystemError):
            self.work.destroyed()
        except Exception as e:
            print(e)

    def updateGui(self, value, which):
        if which == 'logs':
            self.logsTextArea.appendPlainText(value)
        elif which == 'onl':
            self.onlUserTextArea.appendPlainText(value)
        elif which == 'remove':
            text = self.onlUserTextArea.toPlainText()
            if value in text:
                text.replace(value, '')
                self.onlUserTextArea.setPlainText(text)
            else:
                self.onlUserTextArea.setPlainText(text)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = Server()
    widget.show()

    sys.exit(app.exec_())
