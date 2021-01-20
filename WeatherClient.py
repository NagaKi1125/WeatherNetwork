import time
import socket
import geocoder
import sys
import os
import urllib.request
from Obj import GeoLocation
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui, sip, QtWebKitWidgets
from Layout import client
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from pyqtlet import L, MapWidget

# click count
click = 0
mapClick = 0
fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_ip = '127.0.0.1'
udp_port = 8014

# global variable for user location
currLocation = GeoLocation.GeoLocation('', '', '', '', '', '')

weather_api_key = 'b3a64e07a9cb08c942f2d1711c1d47e6'  # for weather


# get current location
def getLocation():
    options = Options()
    options.set_preference("geo.prompt.testing", True)
    options.set_preference("geo.prompt.testing.allow", True)
    options.add_argument("--headless")

    timeout = 60
    driver = webdriver.Firefox(executable_path='geckodriver/geckodriver.exe', options=options)
    driver.get("https://whatmylocation.com/")
    WebDriverWait(driver, timeout)
    time.sleep(1)

    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]')
    longitude = [x.text for x in longitude]
    longitude = str(longitude[0])

    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = str(latitude[0])

    road = driver.find_elements_by_xpath('//*[@id="street"]/span')
    road = [x.text for x in road]
    road = str(road[0])

    province = driver.find_elements_by_xpath('//*[@id="county"]/span')
    province = [x.text for x in province]
    province = str(province[0])

    district = driver.find_elements_by_xpath('//*[@id="city"]/span')
    district = [x.text for x in district]
    district = str(district[0])

    country = driver.find_elements_by_xpath('//*[@id="country"]/span[1]')
    country = [x.text for x in country]
    country = str(country[0])

    ti = datetime.today()

    driver.quit()

    g = geocoder.ip('')
    geo = GeoLocation.GeoLocation(ip=g.ip, latitude=latitude, longitude=longitude,
                                  city=road + '\n ' + district + ', ' + province, country=country, time=ti)

    return geo


# get province
def allProvince():
    provinceList = []
    provinceFile = open('Province.txt', encoding="utf8")
    lines = provinceFile.readlines()
    provinceList.append("Click to choose place")
    for i in lines:
        pr = i.split(',')
        provinceList.append(pr[0].strip() + ', ' + pr[1].strip() + ', ' + pr[2].strip())
    return provinceList


# weather icon
def showIcon(iconName, size):
    if size == 0:
        url = 'http://openweathermap.org/img/wn/' + iconName + '.png'
    else:
        url = 'http://openweathermap.org/img/wn/' + iconName + '@2x.png'
    url_data = urllib.request.urlopen(url).read()
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(url_data)
    return pixmap


def mapView(lat, lon, zoom):
    mapWidget = MapWidget()
    mapLayout = QtWidgets.QVBoxLayout()
    mapLayout.addWidget(mapWidget)
    mapWidget.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
    map = L.map(mapWidget)
    map.setView([lat, lon], zoom)
    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(map)
    marker = L.marker([lat, lon])
    marker.bindPopup('You are here now!!')
    map.addLayer(marker)

    return mapLayout


def temperatureMapView():
    # Add layout
    layout = QtWidgets.QVBoxLayout()
    # Create QWebView
    view = QtWebKitWidgets.QWebView()

    # load .html file
    view.load(QtCore.QUrl.fromLocalFile(os.path.abspath('owmLeaflet/index.html')))

    layout.addWidget(view)

    return layout


class Client(QtWidgets.QFrame, client.Ui_mainLayout):
    def __init__(self, *args, **kwargs):
        global currLocation
        super(Client, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # get current location
        currLocation = getLocation()

        # get province list
        provList = allProvince()
        # if send a or c no need lat long
        self.socketWork('a', '', '')
        self.socketWork('b', currLocation.latitude, currLocation.longitude)

        # Gui
        # map stack
        self.mapStack = QtWidgets.QStackedLayout()
        # map
        self.mapLayout = QtWidgets.QWidget()
        self.mapLayout.setLayout(mapView(currLocation.latitude, currLocation.longitude, 11))
        self.mapTempLayout = QtWidgets.QWidget()
        self.mapTempLayout.setLayout(temperatureMapView())
        self.mapStack.addWidget(self.mapLayout)
        self.mapStack.addWidget(self.mapTempLayout)
        self.mapFrame.setLayout(self.mapStack)
        self.mapStack.setCurrentIndex(0)

        self.lblInfoAddress.setText(currLocation.city + ', ' + currLocation.country)
        self.lblInfoLat.setText(currLocation.latitude)
        self.lblInfoLong.setText(currLocation.longitude)
        self.lblIpAddress.setText("Your public IP address: " + currLocation.ip)
        self.lblUsername.setText("NagaKi: Vu Hoang")

        date = str(currLocation.time).split(' ')
        self.lblInfoDate.setText(str(date[0]))
        self.lblInfoTime.setText(str(date[1]))

        self.provList.addItems(provList)
        self.btnSearch.clicked.connect(self.searchOnClick)

        # hide some value
        self.lblCloud.setVisible(False)
        self.lblInfoCloud.setVisible(False)
        self.lblHumi.setVisible(False)
        self.lblInfoHumi.setVisible(False)
        self.lblSunrise.setVisible(False)
        self.lblInfoSunRise.setVisible(False)
        self.lblSunset.setVisible(False)
        self.lblInfoSunset.setVisible(False)
        self.lblVisi.setVisible(False)
        self.lblInfoVisi.setVisible(False)
        self.lblWind.setVisible(False)
        self.lblInfoWind.setVisible(False)
        self.lblPressure.setVisible(False)
        self.lblInfoPressure.setVisible(False)

        self.btnWeatherDetails.clicked.connect(self.clickVisible)
        self.btnHome.clicked.connect(lambda: self.socketWork('c', '', ''))

        # mapView
        self.btnNormalView.setEnabled(False)
        self.btnNormalView.clicked.connect(lambda: self.setMapView(1))
        self.btnTempMap.clicked.connect(lambda: self.setMapView(2))

    def setMapView(self, key):
        if key == 1:
            self.btnTempMap.setEnabled(True)
            self.btnNormalView.setEnabled(False)
            self.btnSearch.setEnabled(True)
            self.btnHome.setEnabled(True)
            self.mapStack.setCurrentIndex(0)
        else:
            self.btnTempMap.setEnabled(False)
            self.btnNormalView.setEnabled(True)
            self.btnSearch.setEnabled(False)
            self.btnHome.setEnabled(False)
            self.mapStack.setCurrentIndex(1)

    def socketWork(self, key, lat, long):
        global currLocation
        if key == 'a':
            # socket start - send "a" to say connect
            mess = "a_"
            fd.sendto(mess.encode(), (udp_ip, udp_port))

        # b also use for get data
        elif key == 'b':
            # then send "b" for current weather request
            mess = "b_" + lat.strip() + ',' + long.strip()
            fd.sendto(mess.encode(), (udp_ip, udp_port))
            r = fd.recvfrom(10000)
            text = r[0].decode().split('--split--')
            weather = text[0].split('_')
            self.lblInfoWeather.setText('{}'.format(weather[0]))
            self.lblInfoTemp.setText('{} C'.format(weather[1]))
            self.lblInfoHumi.setText('{} %'.format(weather[2]))
            self.lblInfoVisi.setText('{} m'.format(weather[3]))
            self.lblInfoWind.setText('{} m/s'.format(weather[4]))
            self.lblIcon.setPixmap(showIcon(weather[5], 2))
            self.lblInfoSunRise.setText('{} am'.format(weather[6]))
            self.lblInfoSunset.setText('{} pm'.format(weather[7]))
            self.lblInfoFeelTemp.setText('{} C'.format(weather[8]))
            self.lblInfoCloud.setText('{} %'.format(weather[9]))
            self.lblInfoPressure.setText('{} hPa'.format(weather[10]))

            # 8 days forecast
            daily = text[1].split('+')  # list of daily object
            self.dailyForecast(daily)

            # hourly forecast
            hourly = text[2].split('+')
            self.hourlyForecast(hourly)

        # c for return back
        elif key == 'c':

            mess = "b_" + currLocation.latitude + ',' + currLocation.longitude
            fd.sendto(mess.encode(), (udp_ip, udp_port))
            r = fd.recvfrom(10000)
            text = r[0].decode().split('--split--')
            weather = text[0].split('_')
            self.lblInfoWeather.setText('{}'.format(weather[0]))
            self.lblInfoTemp.setText('{} C'.format(weather[1]))
            self.lblInfoHumi.setText('{} %'.format(weather[2]))
            self.lblInfoVisi.setText('{} m'.format(weather[3]))
            self.lblInfoWind.setText('{} m/s'.format(weather[4]))
            self.lblIcon.setPixmap(showIcon(weather[5], 2))
            self.lblInfoSunRise.setText('{} am'.format(weather[6]))
            self.lblInfoSunset.setText('{} pm'.format(weather[7]))
            self.lblInfoFeelTemp.setText('{} C'.format(weather[8]))
            self.lblInfoCloud.setText('{} %'.format(weather[9]))
            self.lblInfoPressure.setText('{} hPa'.format(weather[10]))

            self.lblInfoAddress.setText(currLocation.city + ', ' + currLocation.country)
            self.lblInfoLat.setText(currLocation.latitude)
            self.lblInfoLong.setText(currLocation.longitude)

            self.mapLayout = mapView(currLocation.latitude, currLocation.longitude, 11)

            # 8 days forecast
            daily = text[1].split('+')  # list of daily object
            self.dailyForecast(daily)

            # hourly forecast
            hourly = text[2].split('+')
            self.hourlyForecast(hourly)

        # d for search place
        elif key == 'd':
            mess = "b_" + lat.strip() + ',' + long.strip()
            fd.sendto(mess.encode(), (udp_ip, udp_port))
            r = fd.recvfrom(10000)
            text = r[0].decode().split('--split--')
            weather = text[0].split('_')
            self.lblInfoWeather.setText('{}'.format(weather[0]))
            self.lblInfoTemp.setText('{} C'.format(weather[1]))
            self.lblInfoHumi.setText('{} %'.format(weather[2]))
            self.lblInfoVisi.setText('{} m'.format(weather[3]))
            self.lblInfoWind.setText('{} m/s'.format(weather[4]))
            self.lblIcon.setPixmap(showIcon(weather[5], 2))
            self.lblInfoSunRise.setText('{} am'.format(weather[6]))
            self.lblInfoSunset.setText('{} pm'.format(weather[7]))
            self.lblInfoFeelTemp.setText('{} C'.format(weather[8]))
            self.lblInfoCloud.setText('{} %'.format(weather[9]))
            self.lblInfoPressure.setText('{} hPa'.format(weather[10]))

            self.mapLayout = mapView(lat, long, 11)

            # 8 days forecast
            daily = text[1].split('+')  # list of daily object
            self.dailyForecast(daily)

            # hourly forecast
            hourly = text[2].split('+')
            self.hourlyForecast(hourly)

    def hourlyForecast(self, hourly):
        boldFont = QtGui.QFont()
        boldFont.setBold(True)

        # split each time infor hourly[0]=''
        time1 = hourly[1].split('_')
        time2 = hourly[2].split('_')
        time3 = hourly[3].split('_')
        time4 = hourly[4].split('_')
        time5 = hourly[5].split('_')
        time6 = hourly[6].split('_')
        time7 = hourly[7].split('_')
        time8 = hourly[8].split('_')
        time9 = hourly[9].split('_')
        time10 = hourly[10].split('_')
        time11 = hourly[11].split('_')
        time12 = hourly[12].split('_')
        time13 = hourly[13].split('_')
        time14 = hourly[14].split('_')
        time15 = hourly[15].split('_')
        time16 = hourly[16].split('_')
        time17 = hourly[17].split('_')
        time18 = hourly[18].split('_')
        time19 = hourly[19].split('_')
        time20 = hourly[20].split('_')
        time21 = hourly[21].split('_')
        time22 = hourly[22].split('_')
        time23 = hourly[23].split('_')
        time24 = hourly[24].split('_')

        # adding info  0 dt, 1 temp, 2 icon, 3 desc, 4 wind, 5 cloud
        # time1
        self.lblHTime.setText('{}'.format(time1[0]))
        self.lblHtemp.setText('{}C'.format(time1[1]))
        self.lblHIcon.setPixmap(showIcon(time1[2], 0))
        self.lblHWeather.setText('{}'.format(time1[3]))
        self.lblHCloudWind.setText('{}m/s - {}%'.format(time1[4], time1[5]))
        # time2
        self.lblHTime_2.setText('{}'.format(time2[0]))
        self.lblHtemp_2.setText('{}C'.format(time2[1]))
        self.lblHIcon_2.setPixmap(showIcon(time2[2], 0))
        self.lblHWeather_2.setText('{}'.format(time2[3]))
        self.lblHCloudWind_2.setText('{}m/s - {}%'.format(time2[4], time2[5]))
        # time3
        self.lblHTime_3.setText('{}'.format(time3[0]))
        self.lblHtemp_3.setText('{}C'.format(time3[1]))
        self.lblHIcon_3.setPixmap(showIcon(time3[2], 0))
        self.lblHWeather_3.setText('{}'.format(time3[3]))
        self.lblHCloudWind_3.setText('{}m/s - {}%'.format(time3[4], time3[5]))
        # time4
        self.lblHTime_4.setText('{}'.format(time4[0]))
        self.lblHtemp_4.setText('{}C'.format(time4[1]))
        self.lblHIcon_4.setPixmap(showIcon(time4[2], 0))
        self.lblHWeather_4.setText('{}'.format(time4[3]))
        self.lblHCloudWind_4.setText('{}m/s - {}%'.format(time4[4], time4[5]))
        # time5
        self.lblHTime_5.setText('{}'.format(time5[0]))
        self.lblHtemp_5.setText('{}C'.format(time5[1]))
        self.lblHIcon_5.setPixmap(showIcon(time5[2], 0))
        self.lblHWeather_5.setText('{}'.format(time5[3]))
        self.lblHCloudWind_5.setText('{}m/s - {}%'.format(time5[4], time5[5]))
        # time6
        self.lblHTime_6.setText('{}'.format(time6[0]))
        self.lblHtemp_6.setText('{}C'.format(time6[1]))
        self.lblHIcon_6.setPixmap(showIcon(time6[2], 0))
        self.lblHWeather_6.setText('{}'.format(time6[3]))
        self.lblHCloudWind_6.setText('{}m/s - {}%'.format(time6[4], time6[5]))
        # time7
        self.lblHTime_7.setText('{}'.format(time7[0]))
        self.lblHtemp_7.setText('{}C'.format(time7[1]))
        self.lblHIcon_7.setPixmap(showIcon(time7[2], 0))
        self.lblHWeather_7.setText('{}'.format(time7[3]))
        self.lblHCloudWind_8.setText('{}m/s - {}%'.format(time7[4], time7[5]))
        # time8
        self.lblHTime_8.setText('{}'.format(time8[0]))
        self.lblHtemp_8.setText('{}C'.format(time8[1]))
        self.lblHIcon_8.setPixmap(showIcon(time8[2], 0))
        self.lblHWeather_8.setText('{}'.format(time8[3]))
        self.lblHCloudWind_8.setText('{}m/s - {}%'.format(time8[4], time8[5]))
        # time9
        self.lblHTime_9.setText('{}'.format(time9[0]))
        self.lblHtemp_9.setText('{}C'.format(time9[1]))
        self.lblHIcon_9.setPixmap(showIcon(time9[2], 0))
        self.lblHWeather_9.setText('{}'.format(time9[3]))
        self.lblHCloudWind_9.setText('{}m/s - {}%'.format(time9[4], time9[5]))
        # time10
        self.lblHTime_10.setText('{}'.format(time10[0]))
        self.lblHtemp_10.setText('{}C'.format(time10[1]))
        self.lblHIcon_10.setPixmap(showIcon(time10[2], 0))
        self.lblHWeather_10.setText('{}'.format(time10[3]))
        self.lblHCloudWind_10.setText('{}m/s - {}%'.format(time10[4], time10[5]))
        # time11
        self.lblHTime_11.setText('{}'.format(time11[0]))
        self.lblHtemp_11.setText('{}C'.format(time11[1]))
        self.lblHIcon_11.setPixmap(showIcon(time11[2], 0))
        self.lblHWeather_11.setText('{}'.format(time11[3]))
        self.lblHCloudWind_11.setText('{}m/s - {}%'.format(time11[4], time11[5]))
        # time12
        self.lblHTime_12.setText('{}'.format(time12[0]))
        self.lblHtemp_12.setText('{}C'.format(time12[1]))
        self.lblHIcon_12.setPixmap(showIcon(time12[2], 0))
        self.lblHWeather_12.setText('{}'.format(time12[3]))
        self.lblHCloudWind_12.setText('{}m/s - {}%'.format(time12[4], time12[5]))
        # time13
        self.lblHTime_13.setText('{}'.format(time13[0]))
        self.lblHtemp_13.setText('{}C'.format(time13[1]))
        self.lblHIcon_13.setPixmap(showIcon(time13[2], 0))
        self.lblHWeather_13.setText('{}'.format(time13[3]))
        self.lblHCloudWind_13.setText('{}m/s - {}%'.format(time13[4], time13[5]))
        # time14
        self.lblHTime_14.setText('{}'.format(time14[0]))
        self.lblHtemp_14.setText('{}C'.format(time14[1]))
        self.lblHIcon_14.setPixmap(showIcon(time14[2], 0))
        self.lblHWeather_14.setText('{}'.format(time14[3]))
        self.lblHCloudWind_14.setText('{}m/s - {}%'.format(time14[4], time14[5]))
        # time15
        self.lblHTime_15.setText('{}'.format(time15[0]))
        self.lblHtemp_15.setText('{}C'.format(time15[1]))
        self.lblHIcon_15.setPixmap(showIcon(time15[2], 0))
        self.lblHWeather_15.setText('{}'.format(time15[3]))
        self.lblHCloudWind_15.setText('{}m/s - {}%'.format(time15[4], time15[5]))
        # time16
        self.lblHTime_16.setText('{}'.format(time16[0]))
        self.lblHtemp_16.setText('{}C'.format(time16[1]))
        self.lblHIcon_16.setPixmap(showIcon(time16[2], 0))
        self.lblHWeather_16.setText('{}'.format(time16[3]))
        self.lblHCloudWind_16.setText('{}m/s - {}%'.format(time16[4], time16[5]))
        # time17
        self.lblHTime_17.setText('{}'.format(time17[0]))
        self.lblHtemp_17.setText('{}C'.format(time17[1]))
        self.lblHIcon_17.setPixmap(showIcon(time17[2], 0))
        self.lblHWeather_17.setText('{}'.format(time17[3]))
        self.lblHCloudWind_17.setText('{}m/s - {}%'.format(time17[4], time17[5]))
        # time8
        self.lblHTime_18.setText('{}'.format(time18[0]))
        self.lblHtemp_18.setText('{}C'.format(time18[1]))
        self.lblHIcon_18.setPixmap(showIcon(time18[2], 0))
        self.lblHWeather_18.setText('{}'.format(time18[3]))
        self.lblHCloudWind_18.setText('{}m/s - {}%'.format(time18[4], time18[5]))
        # time19
        self.lblHTime_19.setText('{}'.format(time19[0]))
        self.lblHtemp_19.setText('{}C'.format(time19[1]))
        self.lblHIcon_19.setPixmap(showIcon(time19[2], 0))
        self.lblHWeather_19.setText('{}'.format(time19[3]))
        self.lblHCloudWind_19.setText('{}m/s - {}%'.format(time19[4], time19[5]))
        # time20
        self.lblHTime_20.setText('{}'.format(time20[0]))
        self.lblHtemp_20.setText('{}C'.format(time20[1]))
        self.lblHIcon_20.setPixmap(showIcon(time20[2], 0))
        self.lblHWeather_20.setText('{}'.format(time20[3]))
        self.lblHCloudWind_20.setText('{}m/s - {}%'.format(time20[4], time20[5]))
        # time21
        self.lblHTime_21.setText('{}'.format(time21[0]))
        self.lblHtemp_21.setText('{}C'.format(time21[1]))
        self.lblHIcon_21.setPixmap(showIcon(time21[2], 0))
        self.lblHWeather_21.setText('{}'.format(time21[3]))
        self.lblHCloudWind_21.setText('{}m/s - {}%'.format(time21[4], time21[5]))
        # time22
        self.lblHTime_22.setText('{}'.format(time22[0]))
        self.lblHtemp_22.setText('{}C'.format(time22[1]))
        self.lblHIcon_22.setPixmap(showIcon(time22[2], 0))
        self.lblHWeather_22.setText('{}'.format(time22[3]))
        self.lblHCloudWind_22.setText('{}m/s - {}%'.format(time22[4], time22[5]))
        # time23
        self.lblHTime_23.setText('{}'.format(time23[0]))
        self.lblHtemp_23.setText('{}C'.format(time23[1]))
        self.lblHIcon_23.setPixmap(showIcon(time23[2], 0))
        self.lblHWeather_23.setText('{}'.format(time23[3]))
        self.lblHCloudWind_23.setText('{}m/s - {}%'.format(time23[4], time23[5]))
        # time1
        self.lblHTime_24.setText('{}'.format(time24[0]))
        self.lblHtemp_24.setText('{}C'.format(time24[1]))
        self.lblHIcon_24.setPixmap(showIcon(time24[2], 0))
        self.lblHWeather_24.setText('{}'.format(time24[3]))
        self.lblHCloudWind_24.setText('{}m/s - {}%'.format(time24[4], time24[5]))

    def dailyForecast(self, daily):
        # 0 dt, 1 tempMin, 2 tempMax, 3 weather, 4 weatherDesc, 5 icon, 6 morTemp, 7 dayTemp,
        # 8 eveTemp, 9 nightTemp, 10 sunrise, 11 sunset
        boldFont = QtGui.QFont()
        boldFont.setBold(True)

        # split to each day information daily[0] = ''
        day1 = daily[1].split('_')
        day2 = daily[2].split('_')
        day3 = daily[3].split('_')
        day4 = daily[4].split('_')
        day5 = daily[5].split('_')
        day6 = daily[6].split('_')
        day7 = daily[7].split('_')
        day8 = daily[8].split('_')

        # add info to label for each day (0 dt)
        # day date
        self.lblDateDay.setText('{}'.format(day1[0]))
        self.lblDateDay_2.setText('{}'.format(day2[0]))
        self.lblDateDay_3.setText('{}'.format(day3[0]))
        self.lblDateDay_4.setText('{}'.format(day4[0]))
        self.lblDateDay_5.setText('{}'.format(day5[0]))
        self.lblDateDay_6.setText('{}'.format(day6[0]))
        self.lblDateDay_7.setText('{}'.format(day7[0]))
        self.lblDateDay_8.setText('{}'.format(day8[0]))

        # weather tempurate (1 min - 2 max || 3 weather.4 desc)
        self.lblWeatherTempDay.setText('{}C-{}C || {}.{}'.format(day1[1], day1[2], day1[3], day1[4]))
        self.lblWeatherTempDay_2.setText('{}C-{}C || {}.{}'.format(day2[1], day2[2], day2[3], day2[4]))
        self.lblWeatherTempDay_3.setText('{}C-{}C || {}.{}'.format(day3[1], day3[2], day3[3], day3[4]))
        self.lblWeatherTempDay_4.setText('{}C-{}C || {}.{}'.format(day4[1], day4[2], day4[3], day4[4]))
        self.lblWeatherTempDay_5.setText('{}C-{}C || {}.{}'.format(day5[1], day5[2], day5[3], day5[4]))
        self.lblWeatherTempDay_6.setText('{}C-{}C || {}.{}'.format(day6[1], day6[2], day6[3], day6[4]))
        self.lblWeatherTempDay_7.setText('{}C-{}C || {}.{}'.format(day7[1], day7[2], day7[3], day7[4]))
        self.lblWeatherTempDay_8.setText('{}C-{}C || {}.{}'.format(day8[1], day8[2], day8[3], day8[4]))

        # icon (5 icon)
        self.lblIconDay.setPixmap(showIcon(day1[5], 0))
        self.lblIconDay_2.setPixmap(showIcon(day2[5], 0))
        self.lblIconDay_3.setPixmap(showIcon(day3[5], 0))
        self.lblIconDay_4.setPixmap(showIcon(day4[5], 0))
        self.lblIconDay_5.setPixmap(showIcon(day5[5], 0))
        self.lblIconDay_6.setPixmap(showIcon(day6[5], 0))
        self.lblIconDay_7.setPixmap(showIcon(day7[5], 0))
        self.lblIconDay_8.setPixmap(showIcon(day8[5], 0))

        # part of Day temp (6mornig - 7day - 8eve - 9night)
        self.lblTempMor.setText('{}C'.format(day1[6]))
        self.lblTempAfter.setText('{}C'.format(day1[7]))
        self.lblTempEve.setText('{}C'.format(day1[8]))
        self.lblTempNight.setText('{}C'.format(day1[9]))

        self.lblTempMor_2.setText('{}C'.format(day2[6]))
        self.lblTempAfter_2.setText('{}C'.format(day2[7]))
        self.lblTempEve_2.setText('{}C'.format(day2[8]))
        self.lblTempNight_2.setText('{}C'.format(day2[9]))

        self.lblTempMor_3.setText('{}C'.format(day3[6]))
        self.lblTempAfter_3.setText('{}C'.format(day3[7]))
        self.lblTempEve_3.setText('{}C'.format(day3[8]))
        self.lblTempNight_3.setText('{}C'.format(day3[9]))

        self.lblTempMor_4.setText('{}C'.format(day4[6]))
        self.lblTempAfter_4.setText('{}C'.format(day4[7]))
        self.lblTempEve_4.setText('{}C'.format(day4[8]))
        self.lblTempNight_4.setText('{}C'.format(day4[9]))

        self.lblTempMor_5.setText('{}C'.format(day5[6]))
        self.lblTempAfter_5.setText('{}C'.format(day5[7]))
        self.lblTempEve_5.setText('{}C'.format(day5[8]))
        self.lblTempNight_5.setText('{}C'.format(day5[9]))

        self.lblTempMor_6.setText('{}C'.format(day6[6]))
        self.lblTempAfter_6.setText('{}C'.format(day6[7]))
        self.lblTempEve_6.setText('{}C'.format(day6[8]))
        self.lblTempNight_6.setText('{}C'.format(day6[9]))

        self.lblTempMor_7.setText('{}C'.format(day7[6]))
        self.lblTempAfter_7.setText('{}C'.format(day7[7]))
        self.lblTempEve_7.setText('{}C'.format(day7[8]))
        self.lblTempNight_7.setText('{}C'.format(day7[9]))

        self.lblTempMor_8.setText('{}C'.format(day8[6]))
        self.lblTempAfter_8.setText('{}C'.format(day8[7]))
        self.lblTempEve_8.setText('{}C'.format(day8[8]))
        self.lblTempNight_8.setText('{}C'.format(day8[9]))

    def searchOnClick(self):
        # print(self.provList.currentText())
        text = self.provList.currentText().split(',')
        self.lblInfoAddress.setText(text[0])
        self.lblInfoLat.setText(text[1])
        self.lblInfoLong.setText(text[2])
        self.mapLayout = mapView(text[1], text[2], 11)

        self.socketWork('d', text[1], text[2])

    def clickVisible(self):
        global click
        click += 1
        if click % 2 == 1:
            self.btnWeatherDetails.setText("Show Less")
            self.lblCloud.setVisible(True)
            self.lblInfoCloud.setVisible(True)
            self.lblHumi.setVisible(True)
            self.lblInfoHumi.setVisible(True)
            self.lblSunrise.setVisible(True)
            self.lblInfoSunRise.setVisible(True)
            self.lblSunset.setVisible(True)
            self.lblInfoSunset.setVisible(True)
            self.lblVisi.setVisible(True)
            self.lblInfoVisi.setVisible(True)
            self.lblWind.setVisible(True)
            self.lblInfoWind.setVisible(True)
            self.lblPressure.setVisible(True)
            self.lblInfoPressure.setVisible(True)
        else:
            self.btnWeatherDetails.setText("Details")
            self.lblCloud.setVisible(False)
            self.lblInfoCloud.setVisible(False)
            self.lblHumi.setVisible(False)
            self.lblInfoHumi.setVisible(False)
            self.lblSunrise.setVisible(False)
            self.lblInfoSunRise.setVisible(False)
            self.lblSunset.setVisible(False)
            self.lblInfoSunset.setVisible(False)
            self.lblVisi.setVisible(False)
            self.lblInfoVisi.setVisible(False)
            self.lblWind.setVisible(False)
            self.lblInfoWind.setVisible(False)
            self.lblPressure.setVisible(False)
            self.lblInfoPressure.setVisible(False)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = Client()
    widget.show()
    try:
        sys.exit(app.exec_())
    except (SystemError, SystemExit):
        fd.sendto('exit'.encode(), (udp_ip, udp_port))
        app.exit()
